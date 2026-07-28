"""
Revisa el historial de predicciones guardado (datos/historial_predicciones.json)
y, para los partidos que ya terminaron, completa el resultado real y si el
modelo acertó o no.

Después arma un resumen agrupado por rango de probabilidad (ej. "cuando
dijimos 60-70% a favor del favorito, ¿realmente ganó entre 60-70% de las
veces?") y lo guarda en datos/backtesting.json para mostrar en el sitio.

Pensado para correr junto con actualizar.py (cada ~10 min). Consulta la
MLB Stats API directamente por cada gamePk pendiente (no depende de
datos/partidos.json, que solo tiene el día actual y se pisa en cada corrida).
"""

import json
import os

import requests

RUTA_HISTORIAL = "datos/historial_predicciones.json"
RUTA_RESUMEN = "datos/backtesting.json"

BASE = "https://statsapi.mlb.com/api/v1"

# Rangos de probabilidad para agrupar la calibración (todo en términos
# del FAVORITO del modelo, no siempre del local: normalizamos para que
# "favorito con 70%" agrupe indistintamente de qué lado haya quedado).
RANGOS = [
    (50, 60), (60, 70), (70, 80), (80, 90), (90, 101),
]


def cargar_json(ruta, default):
    if not os.path.exists(ruta):
        return default
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def consultar_resultado_partido(game_pk):
    """Consulta directamente el estado/marcador de UN partido puntual por
    su gamePk, usando el feed completo del partido (más pesado que pedir
    solo linescore, pero mucho más confiable: sin depender de parámetros
    de filtrado de campos que pueden no funcionar como se espera).
    Devuelve None si todavía no terminó o si falla la consulta."""
    try:
        r = requests.get(
            f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live",
            timeout=20,
        )
        r.raise_for_status()
        datos = r.json()
    except Exception:
        return None

    estado = (
        datos.get("gameData", {})
        .get("status", {})
        .get("abstractGameState", "")
    )
    if estado != "Final":
        return None  # todavía no terminó, o el partido fue suspendido/cancelado

    linescore = datos.get("liveData", {}).get("linescore", {})
    teams = linescore.get("teams", {})
    home_runs = teams.get("home", {}).get("runs")
    away_runs = teams.get("away", {}).get("runs")

    if home_runs is None or away_runs is None:
        return None

    return {
        "marcador_local": home_runs,
        "marcador_visitante": away_runs,
    }


def completar_resultados(historial):
    """Para cada partido del historial que todavía no tiene resultado,
    consulta la API puntualmente por su gamePk."""
    actualizados = 0

    for game_pk, registro in historial.items():
        if registro.get("resultado") is not None:
            continue  # ya se completó antes

        resultado = consultar_resultado_partido(game_pk)
        if resultado is None:
            continue  # todavía no terminó, o falló la consulta

        m_local = resultado["marcador_local"]
        m_visitante = resultado["marcador_visitante"]

        gano_local = m_local > m_visitante
        prob_local = registro.get("probabilidad_local", 50.0)
        favorito_era_local = prob_local >= 50.0
        acerto = favorito_era_local == gano_local

        registro["marcador_local_final"] = m_local
        registro["marcador_visitante_final"] = m_visitante
        registro["resultado"] = "local" if gano_local else "visitante"
        registro["acerto"] = acerto

        actualizados += 1

    return actualizados


def calcular_resumen(historial):
    """Agrupa los partidos ya completados por rango de probabilidad del
    FAVORITO (no del local), para medir calibración real."""
    grupos = {f"{a}-{b}": {"total": 0, "aciertos": 0} for a, b in RANGOS}

    total_partidos = 0
    total_aciertos = 0

    for registro in historial.values():
        if registro.get("resultado") is None:
            continue  # todavía no terminó ese partido

        prob_local = registro.get("probabilidad_local", 50.0)
        # Probabilidad del FAVORITO (si el local tenía 30%, el favorito
        # real era el visitante con 70%; normalizamos a ese número).
        prob_favorito = prob_local if prob_local >= 50.0 else (100 - prob_local)

        total_partidos += 1
        acerto = bool(registro.get("acerto"))
        if acerto:
            total_aciertos += 1

        for a, b in RANGOS:
            if a <= prob_favorito < b:
                clave = f"{a}-{b}"
                grupos[clave]["total"] += 1
                if acerto:
                    grupos[clave]["aciertos"] += 1
                break

    resumen_rangos = []
    for a, b in RANGOS:
        clave = f"{a}-{b}"
        g = grupos[clave]
        pct_real = round((g["aciertos"] / g["total"]) * 100, 1) if g["total"] > 0 else None
        resumen_rangos.append({
            "rango": clave,
            "partidos": g["total"],
            "aciertos": g["aciertos"],
            "pct_acierto_real": pct_real,
        })

    precision_general = (
        round((total_aciertos / total_partidos) * 100, 1) if total_partidos > 0 else None
    )
    total_errores = total_partidos - total_aciertos
    error_general = (
        round((total_errores / total_partidos) * 100, 1) if total_partidos > 0 else None
    )

    # Lista de partidos recientes evaluados, para mostrar partido por
    # partido en el sitio (más recientes primero). Se guarda junto con
    # el game_pk para poder ordenar y el detalle de cada uno.
    partidos_recientes = []
    for game_pk, registro in historial.items():
        if registro.get("resultado") is None:
            continue
        prob_local = registro.get("probabilidad_local", 50.0)
        partidos_recientes.append({
            "gamePk": game_pk,
            "local": registro.get("local"),
            "visitante": registro.get("visitante"),
            "hora": registro.get("hora"),
            "probabilidad_local": prob_local,
            "resultado": registro.get("resultado"),
            "marcador_local_final": registro.get("marcador_local_final"),
            "marcador_visitante_final": registro.get("marcador_visitante_final"),
            "acerto": bool(registro.get("acerto")),
        })

    # Más recientes primero (por hora del partido)
    partidos_recientes.sort(key=lambda p: p.get("hora") or "", reverse=True)
    partidos_recientes = partidos_recientes[:50]  # no acumular sin límite en el JSON

    return {
        "total_partidos_evaluados": total_partidos,
        "total_aciertos": total_aciertos,
        "total_errores": total_errores,
        "precision_general": precision_general,
        "error_general": error_general,
        "por_rango": resumen_rangos,
        "partidos_recientes": partidos_recientes,
    }


def main():
    historial = cargar_json(RUTA_HISTORIAL, {})

    actualizados = completar_resultados(historial)
    if actualizados > 0:
        with open(RUTA_HISTORIAL, "w", encoding="utf-8") as f:
            json.dump(historial, f, ensure_ascii=False, indent=2)
        print(f"Backtesting: {actualizados} resultados completados.")

    resumen = calcular_resumen(historial)
    with open(RUTA_RESUMEN, "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)

    print(f"Backtesting: {resumen['total_partidos_evaluados']} partidos evaluados en total, "
          f"precisión general: {resumen['precision_general']}%")


if __name__ == "__main__":
    main()
        
