import json
from datetime import datetime

from mlb_api import (
    obtener_partidos,
    obtener_standings,
    obtener_lideres,
    obtener_estadisticas_pitcher,
)

from estadisticas import obtener_estadisticas_equipo
from predictor import prediccion
from favoritos import obtener_favoritos

HOY = datetime.now().strftime("%Y-%m-%d")

print("Descargando datos...")

partidos_api = obtener_partidos(HOY)

partidos = []
predicciones = []

for juego in partidos_api:

    home = obtener_estadisticas_equipo(juego["home_id"])
    away = obtener_estadisticas_equipo(juego["away_id"])

    pitcher_home = obtener_estadisticas_pitcher(
        juego["pitcher_local_id"]
    )

    pitcher_away = obtener_estadisticas_pitcher(
        juego["pitcher_visitante_id"]
    )

    prob = prediccion(
        home,
        away,
        pitcher_home,
        pitcher_away
    )

    partido = {
        "gamePk": juego["gamePk"],
        "local": juego["local"],
        "visitante": juego["visitante"],
        "estado": juego["estado"],
        "hora": juego["hora"],

        # Marcador en vivo/final (0 si el partido todavía no arrancó)
        "marcador_local": juego.get("marcador_local", 0),
        "marcador_visitante": juego.get("marcador_visitante", 0),
        "inning": juego.get("inning"),
        "inning_estado": juego.get("inning_estado"),

        "pitcher_local": juego["pitcher_local"],
        "pitcher_visitante": juego["pitcher_visitante"],

        "pitcher_local_id": juego["pitcher_local_id"],
        "pitcher_visitante_id": juego["pitcher_visitante_id"],

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
