import json
from datetime import datetime

from mlb_api import (
    obtener_partidos,
    obtener_standings,
    obtener_lideres
)

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

        # Datos de ejemplo (después los reemplazaremos por estadísticas reales)
        home = {
            "RS": 500,
            "RA": 420,
            "elo": 1550
        }

        away = {
            "RS": 470,
            "RA": 450,
            "elo": 1500
        }

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
