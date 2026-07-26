import json
from datetime import datetime

from mlb_api import (
    obtener_partidos,
    obtener_standings,
    obtener_lideres
)

from estadisticas import obtener_estadisticas_equipo
from predictor import prediction
from favoritos import obtener_favoritos

HOY = datetime.now().strftime("%Y-%m-%d")

print("Descargando datos...")

partidos = obtener_partidos(HOY)
standings = obtener_standings()
lideres = obtener_lideres()

predicciones = []

for juego in partidos:

    home = obtener_estadisticas_equipo(juego["home_id"])
    away = obtener_estadisticas_equipo(juego["away_id"])

    prob = prediction(home, away)

    predicciones.append({
        "local": juego["local"],
        "visitante": juego["visitante"],
        "probabilidad": prob,
        "estado": juego["estado"],
        "hora": juego["hora"]
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
