"""
Ajusta automáticamente los pesos del modelo de predicción (predictor.py)
usando el historial real de aciertos/fallos acumulado en
datos/historial_predicciones.json.

Cómo funciona (resumen simple):
  Cada partido evaluado ya tiene guardado el "score" que arrojaron las
  distintas señales del modelo (pitagórico, wOBA, FIP, bullpen, etc.) y
  si el favorito ganó o no. Con eso se entrena una regresión logística
  chica: encuentra qué combinación de pesos hubiera predicho mejor los
  resultados reales, en vez de usar los pesos que elegimos a mano.

Salvaguardas para no romper el modelo con poca data o datos ruidosos:
  - No hace NADA hasta juntar un mínimo de partidos evaluados (MIN_PARTIDOS).
  - Los pesos nuevos quedan limitados a un rango alrededor de los pesos
    "base" (los que ya validamos con criterio sabermétrico), para que el
    ajuste sea una afinación fina, no un cambio salvaje de la fórmula.
  - Se reentrena con TODO el historial disponible cada vez (no solo lo
    último), así que un mal racha de pocos partidos no puede desviar el
    modelo de forma exagerada.
  - Si el entrenamiento falla o hay algún dato corrupto, no se toca nada
    y se sigue usando los pesos anteriores.

Pensado para correr con MENOS frecuencia que el resto (ej. 1 vez por día),
ya que ajustar pesos partido a partido no tiene sentido — reentrenar con
1-2 partidos nuevos de diferencia no cambia nada significativo.
"""

import json
import os

RUTA_HISTORIAL = "datos/historial_predicciones.json"
RUTA_PESOS = "datos/pesos_modelo.json"

MIN_PARTIDOS = 100  # no ajustar nada por debajo de este piso

# Pesos "base" (los mismos valores que ya usamos a mano en predictor.py,
# elegidos con criterio sabermétrico). El ajuste automático se mueve
# alrededor de estos, nunca los reemplaza del todo.
PESOS_BASE = {
    "p5": 0.38,
    "elo": 0.25,
    "home_adv": 0.10,
    "woba": 0.60,
    "fip": 0.08,
    "pitcher_fip": 0.05,
    "pitcher_whip": 0.03,
    "pitcher_k9": 0.01,
    "bullpen": 0.02,
    "ballpark": 0.10,
}

# Cuánto se puede alejar cada peso de su valor base, como fracción.
# 0.30 = el ajuste automático puede mover un peso hasta un 30% arriba
# o abajo de su valor original, nunca más que eso.
LIMITE_AJUSTE = 0.30

TASA_APRENDIZAJE = 0.05
ITERACIONES = 500


def cargar_historial():
    if not os.path.exists(RUTA_HISTORIAL):
        return {}
    try:
        with open(RUTA_HISTORIAL, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def sigmoid(x):
    # Recorte para evitar overflow con valores extremos
    x = max(-30, min(30, x))
    return 1 / (1 + 2.718281828 ** (-x))


def entrenar_pesos(historial):
    """Entrena una regresión logística muy simple: usa como única señal
    de entrada la probabilidad que el modelo actual le dio al LOCAL
    (ya combinando todas las variables), y ajusta un factor de escala +
    sesgo para recalibrar qué tan agresivas o conservadoras deberían ser
    las probabilidades del modelo en general.

    Esto es intencionalmente simple (recalibración global, no un ajuste
    variable por variable) para ser robusto con la cantidad de datos que
    se puede tener en una temporada, evitando sobreajuste."""

    evaluados = [r for r in historial.values() if r.get("resultado") is not None]
    if len(evaluados) < MIN_PARTIDOS:
        return None, len(evaluados)

    # x_i = probabilidad que el modelo le dio al local (0-1)
    # y_i = 1 si ganó el local, 0 si ganó el visitante
    xs = []
    ys = []
    for r in evaluados:
        prob_local = r.get("probabilidad_local")
        if prob_local is None:
            continue
        xs.append(prob_local / 100.0)
        ys.append(1.0 if r.get("resultado") == "local" else 0.0)

    if len(xs) < MIN_PARTIDOS:
        return None, len(xs)

    # Regresión logística de 1 variable: sigmoid(a * x + b)
    # a = qué tan bien discrimina la probabilidad del modelo (a=1 ideal)
    # b = sesgo general (si el modelo está sistemáticamente corrido)
    a, b = 1.0, 0.0
    n = len(xs)

    for _ in range(ITERACIONES):
        grad_a = 0.0
        grad_b = 0.0
        for x, y in zip(xs, ys):
            pred = sigmoid(a * x + b)
            error = pred - y
            grad_a += error * x
            grad_b += error
        grad_a /= n
        grad_b /= n
        a -= TASA_APRENDIZAJE * grad_a
        b -= TASA_APRENDIZAJE * grad_b

    # "a" nos dice si el modelo es demasiado tímido (a > 1, hay que
    # exagerar más las probabilidades) o demasiado confiado (a < 1).
    # Lo usamos como factor de escala general sobre los pesos base,
    # limitado por LIMITE_AJUSTE para no permitir saltos bruscos.
    factor_escala = max(1 - LIMITE_AJUSTE, min(1 + LIMITE_AJUSTE, a))

    pesos_ajustados = {
        clave: round(valor * factor_escala, 4)
        for clave, valor in PESOS_BASE.items()
    }

    # El sesgo "b" indica si el modelo favorece sistemáticamente de más
    # o de menos al LOCAL en general; lo guardamos aparte como un ajuste
    # fino adicional (en puntos de probabilidad, chico y acotado).
    ajuste_sesgo_local = round(max(-0.03, min(0.03, b * 0.05)), 4)

    return {
        "pesos": pesos_ajustados,
        "factor_escala": round(factor_escala, 4),
        "ajuste_sesgo_local": ajuste_sesgo_local,
        "partidos_usados": n,
    }, n


def main():
    historial = cargar_historial()
    resultado, n_evaluados = entrenar_pesos(historial)

    if resultado is None:
        salida = {
            "activo": False,
            "motivo": f"Todavía no hay suficiente historial ({n_evaluados}/{MIN_PARTIDOS} partidos evaluados).",
            "pesos": PESOS_BASE,
            "factor_escala": 1.0,
            "ajuste_sesgo_local": 0.0,
        }
        print(salida["motivo"])
    else:
        salida = {
            "activo": True,
            "motivo": f"Pesos recalibrados con {resultado['partidos_usados']} partidos evaluados.",
            **resultado,
        }
        print(f"Pesos actualizados. Factor de escala: {resultado['factor_escala']}, "
              f"sesgo local: {resultado['ajuste_sesgo_local']}")

    with open(RUTA_PESOS, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()

