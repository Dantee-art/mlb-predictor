"""
Guarda un registro histórico de predicciones, para poder comparar después
contra el resultado real (backtesting).

Cada partido se guarda UNA sola vez en datos/historial_predicciones.json,
la primera vez que lo vemos con un pitcher abridor confirmado (no cada
corrida del workflow, para no duplicar el mismo partido 50 veces).

Este archivo queda separado de datos/partidos.json (que se pisa cada
corrida) — acá se van ACUMULANDO partidos con el tiempo.
"""

import json
import os

RUTA_HISTORIAL = "datos/historial_predicciones.json"


def cargar_historial():
    if not os.path.exists(RUTA_HISTORIAL):
        return {}
    try:
        with open(RUTA_HISTORIAL, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def guardar_historial(historial):
    with open(RUTA_HISTORIAL, "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)


def registrar_predicciones(partidos):
    """Recibe la lista de partidos ya calculados por actualizar.py (con
    su 'probabilidad') y guarda los nuevos en el historial, indexados por
    gamePk. Si un gamePk ya está guardado, no lo vuelve a tocar (para no
    pisar la predicción original con una posterior, que ya tendría en
    cuenta información que en el momento real del "pick" no existía)."""
    historial = cargar_historial()
    nuevos = 0

    for p in partidos:
        game_pk = str(p.get("gamePk"))
        if not game_pk or game_pk == "None":
            continue

        # Solo registramos si el partido ya tiene pitchers confirmados
        # (si dice "Sin anunciar" todavía, la predicción es menos fiable
        # y preferimos esperar a que se confirme el abridor real).
        sin_confirmar = (
            p.get("pitcher_local") == "Sin anunciar"
            or p.get("pitcher_visitante") == "Sin anunciar"
        )

        if game_pk not in historial and not sin_confirmar:
            historial[game_pk] = {
                "local": p.get("local"),
                "visitante": p.get("visitante"),
                "hora": p.get("hora"),
                "probabilidad_local": p.get("probabilidad"),
                "pitcher_local": p.get("pitcher_local"),
                "pitcher_visitante": p.get("pitcher_visitante"),
                "resultado": None,  # se completa después, cuando termine
                "marcador_local_final": None,
                "marcador_visitante_final": None,
                "acerto": None,
            }
            nuevos += 1

    if nuevos > 0:
        guardar_historial(historial)
        print(f"Backtesting: {nuevos} predicciones nuevas registradas en el historial.")

    return historial
              
