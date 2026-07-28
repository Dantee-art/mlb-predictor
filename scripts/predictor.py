import json
import os
from math import pow

HOME_ADV = 0.54

RUTA_PESOS = "datos/pesos_modelo.json"

# Pesos base (los mismos valores validados con criterio sabermétrico que
# se usaron desde el principio). Sirven como respaldo si todavía no hay
# suficiente historial para el auto-ajuste, o si ese archivo falla.
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


def cargar_pesos():
    """Lee datos/pesos_modelo.json (generado por auto_ajuste.py). Si no
    existe, no está "activo" todavía (poco historial), o falla la lectura
    por cualquier motivo, se usan los pesos base sin romper nada."""
    if not os.path.exists(RUTA_PESOS):
        return dict(PESOS_BASE), 0.0

    try:
        with open(RUTA_PESOS, "r", encoding="utf-8") as f:
            datos = json.load(f)
        if not datos.get("activo"):
            return dict(PESOS_BASE), 0.0
        pesos = datos.get("pesos", PESOS_BASE)
        sesgo = datos.get("ajuste_sesgo_local", 0.0)
        # Nos aseguramos de que estén todas las claves esperadas, por si
        # el archivo quedó de una versión vieja del modelo.
        pesos_completos = {**PESOS_BASE, **pesos}
        return pesos_completos, sesgo
    except Exception:
        return dict(PESOS_BASE), 0.0


def pythag(rs, ra):
    return pow(rs, 1.83) / (pow(rs, 1.83) + pow(ra, 1.83))


def log5(a, b):
    return (a - a * b) / (a + b - 2 * a * b)


def elo_prob(a, b):
    return 1 / (1 + 10 ** ((b - a) / 400))


def comprimir_extremos(prob, fuerza=0.6):
    """Suaviza probabilidades que se alejan mucho de 0.5, para que hagan
    falta señales realmente contundentes (no la simple suma de muchos
    empujones chicos en la misma dirección) para llegar a un resultado
    extremo tipo 85%-15%. fuerza=1.0 no cambia nada; fuerza más baja
    comprime más hacia el centro."""
    desvio = prob - 0.5
    return 0.5 + desvio * fuerza


def _offset_centrado(pesos):
    """La combinación p5*peso + elo*peso + 0.03 NO da 0.5 cuando p5=elo=0.5
    (equipos parejos en fuerza) — da un número más bajo, porque los pesos
    no suman 1. Esto generaba un sesgo sistemático: hacían falta señales
    extra positivas solo para "empatar" en fuerza pura. Este offset corrige
    SOLO esa parte (p5 + elo), sin tocar la ventaja de localía, que debe
    seguir sumando su propio efecto real incluso entre equipos idénticos."""
    neutral_sin_localia = 0.5 * pesos["p5"] + 0.5 * pesos["elo"] + 0.03
    return 0.5 - neutral_sin_localia


def prediccion(home, away, pitcher_home, pitcher_away, ballpark_factor=1.0):
    pesos, sesgo_local = cargar_pesos()

    py_home = pythag(home["RS"], home["RA"])
    py_away = pythag(away["RS"], away["RA"])

    p5 = log5(py_home, py_away)
    elo = elo_prob(home["elo"], away["elo"])

    # --- Señal ancla: win% real + pitagórico + ventaja de localía ---
    # Estas son las señales más confiables y con menos ruido de muestra.
    # El resto de las señales (wOBA, FIP, pitchers, bullpen, forma
    # reciente, ballpark, etc.) se tratan como AJUSTES sobre esta ancla,
    # no como sumandos libres sin límite — así una alineación casual de
    # varias señales chicas no puede disparar el resultado a extremos.
    ancla = (
        p5 * pesos["p5"] +
        elo * pesos["elo"] +
        HOME_ADV * pesos["home_adv"] +
        0.03 +
        _offset_centrado(pesos)
    )

    # wOBA reemplaza a AVG: pondera cada tipo de embasada según su valor
    # real de generación de carreras, en vez de tratarlas todas igual.
    woba = (home["WOBA"] - away["WOBA"]) * pesos["woba"]

    # FIP reemplaza a ERA: aísla lo que el staff de pitcheo controla
    # (HR, BB, K) de lo que depende de la defensa detrás.
    fip = (away["FIP"] - home["FIP"]) * pesos["fip"]

    # Pitchers abridores
    pitcher_fip_proxy = (pitcher_away["fip"] - pitcher_home["fip"]) * pesos["pitcher_fip"]
    pitcher_whip = (pitcher_away["whip"] - pitcher_home["whip"]) * pesos["pitcher_whip"]
    pitcher_k9 = (pitcher_home["k9"] - pitcher_away["k9"]) * pesos["pitcher_k9"]
    pitcher_record = (
        (pitcher_home["wins"] - pitcher_home["losses"])
        - (pitcher_away["wins"] - pitcher_away["losses"])
    ) * 0.002

    run_diff = (home["run_diff"] - away["run_diff"]) * 0.0005

    home_record = (
        (home["home_wins"] - home["home_losses"])
        - (away["away_wins"] - away["away_losses"])
    ) * 0.002

    ultimos = (home["ultimos10"] - away["ultimos10"]) * 0.02

    bullpen = (away["bullpen"] - home["bullpen"]) * pesos["bullpen"]

    # --- Ballpark factor ---
    ballpark = (ballpark_factor - 1.0) * pesos["ballpark"]

    # --- OPS+ aproximado ---
    ops_plus_ajuste = (home["WOBA"] / max(ballpark_factor, 0.75)
                       - away["WOBA"] / 1.0) * 0.15

    señales_extra = (
        woba + fip + pitcher_fip_proxy + pitcher_whip + pitcher_k9 +
        pitcher_record + run_diff + home_record + ultimos + bullpen +
        ballpark + ops_plus_ajuste + sesgo_local
    )

    # Las señales "extra" se comprimen a un 65% de su efecto crudo: cada
    # una individualmente sigue pesando lo mismo que antes en relación a
    # las demás, pero el CONJUNTO no puede acumularse sin límite cuando
    # todas apuntan para el mismo lado (que es justo lo que producía
    # brechas de 84%-16% para equipos con niveles reales muy parejos).
    FACTOR_COMPRESION_EXTRA = 0.65
    prob = ancla + señales_extra * FACTOR_COMPRESION_EXTRA

    # Compresión final adicional: aleja menos el resultado de 50% salvo
    # que la evidencia combinada sea realmente grande.
    prob = comprimir_extremos(prob, fuerza=0.85)

    if prob > 0.97:
        prob = 0.97

    if prob < 0.03:
        prob = 0.03

    return round(prob * 100, 1)
    
