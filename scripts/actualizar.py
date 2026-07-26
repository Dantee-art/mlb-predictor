import json
from datetime import datetime

from mlb_api import obtener_partidos, obtener_standings, obtener_lideres
from estadisticas import obtener_estadisticas_equipo
from predictor import prediction
from favoritos import obtener_favoritos

HOY = datetime.now().strftime("%Y-%m-%d")

print("Descargando datos...")

partidos_api = obtener_partidos(HOY)

partidos = []
predicciones = []

for juego in partidos_api:

    home = obtener_estadisticas_equipo(juego["home_id"])
    away = obtener_estadisticas_equipo(juego["away_id"])

    prob = prediction(home, away)

    partido = {
        "gamePk": juego["gamePk"],
        "local": juego["local"],
        "visitante": juego["visitante"],
        "estado": juego["estado"],
        "hora": juego["hora"],
        "probabilidad": prob
    }

    partidos.append(partido)
    predicciones.append(partido)

favoritos = obtener_favoritos(predicciones)

standings = obtener_standings()
lideres = obtener_lideres()

with open("datos/partidos.json", "w", encoding="utf-8") as f:
    json.dump(partidos, f, ensure_ascii=False, indent=4)

with open("datos/predicciones.json", "w", encoding="utf-8") as f:
    json.dump(predicciones, f, ensure_ascii=False, indent=4)

with open("datos/favoritos.json", "w", encoding="utf-8") as f:
    json.dump(favoritos, f, ensure_ascii=False, indent=4)

with open("datos/standings.json", "w", encoding="utf-8") as f:
    json.dump(standings, f, ensure_ascii=False, indent=4)

with open("datos/lideres.json", "w", encoding="utf-8") as f:
    json.dump(lideres, f, ensure_ascii=False, indent=4)

print(f"Se encontraron {len(partidos)} partidos.")
print("Actualización terminada.")
