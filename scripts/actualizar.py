import json
from datetime import datetime

from mlb_api import (
    obtener_partidos,
    obtener_standings,
    obtener_lideres,
)
# CAMBIO 1: Importamos "prediction" en lugar de "prediccion"
from predictor import prediction
from favoritos import obtener_favoritos
from estadisticas import obtener_estadisticas_equipo

HOY = datetime.now().strftime("%Y-%m-%d")

print("Descargando partidos...")
partidos = obtener_partidos(HOY)

print("Descargando standings...")
standings = obtener_standings()

print("Descargando líderes...")
lideres = obtener_lideres()

predicciones = []

for fecha in partidos.get("dates", []):
    for juego in fecha.get("games", []):

        local = juego["teams"]["home"]["team"]["name"]
        visitante = juego["teams"]["away"]["team"]["name"]

        home_id = juego["teams"]["home"]["team"]["id"]
        away_id = juego["teams"]["away"]["team"]["id"]

        home_stats = obtener_estadisticas_equipo(home_id)
        away_stats = obtener_estadisticas_equipo(away_id)

        home = {
            "RS": home_stats["RS"],
            "RA": home_stats["RA"],
            "elo": home_stats["elo"],
            "ultimos10": home_stats["ultimos10"],
            "bullpen": home_stats["bullpen"],
        }

        away = {
            "RS": away_stats["RS"],
            "RA": away_stats["RA"],
            "elo": away_stats["elo"],
            "ultimos10": away_stats["ultimos10"],
            "bullpen": away_stats["bullpen"],
        }

        # CAMBIO 2: Usamos "prediction" acá adentro del bucle
        prob = prediction(home, away)

        predicciones.append({
            "local": local,
            "visitante": visitante,
            "probabilidad": prob
        })

favoritos = obtener_favoritos(predicciones)

with open("datos/partidos.json", "w", encoding="utf-8") as f:
    json.dump(partidos, f, ensure_ascii=False, indent=4)

with open("datos/standings.json", "w", encoding="utf-8") as f:
    json.dump(standings, f, ensure_ascii=False, indent=4)

with open("datos/lideres.json", "w", encoding="utf-8") as f:
    json.dump(lideres, f, ensure_ascii=False, indent=4)

with open("datos/predicciones.json", "w", encoding="utf-8") as f:
    json.dump(predicciones, f, ensure_ascii=False, indent=4)

with open("datos/favoritos.json", "w", encoding="utf-8") as f:
    json.dump(favoritos, f, ensure_ascii=False, indent=4)

print("Actualización terminada.")
