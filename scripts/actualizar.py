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

# Ballpark factors: los calcula un workflow aparte una vez por día
# (scripts/ballpark.py) y los deja en datos/ballpark_factors.json.
# Si el archivo todavía no existe (primera corrida) o falla la lectura,
# usamos 1.0 (neutro) para todos los equipos y seguimos sin romper nada.
try:
    with open("datos/ballpark_factors.json", "r", encoding="utf-8") as f:
        ballpark_factors = json.load(f).get("factores", {})
except Exception:
    ballpark_factors = {}

# Nombre completo de equipo (como viene de mlb_api) -> código corto usado
# en ballpark_factors.json.
NOMBRE_A_CODIGO = {
    "New York Yankees": "NYY", "Tampa Bay Rays": "TB", "Toronto Blue Jays": "TOR",
    "Baltimore Orioles": "BAL", "Boston Red Sox": "BOS", "Cleveland Guardians": "CLE",
    "Chicago White Sox": "CHW", "Minnesota Twins": "MIN", "Detroit Tigers": "DET",
    "Kansas City Royals": "KC", "Seattle Mariners": "SEA", "Athletics": "ATH",
    "Oakland Athletics": "ATH", "Texas Rangers": "TEX", "Houston Astros": "HOU",
    "Los Angeles Angels": "LAA", "Atlanta Braves": "ATL", "Philadelphia Phillies": "PHI",
    "Miami Marlins": "MIA", "Washington Nationals": "WSH", "New York Mets": "NYM",
    "Milwaukee Brewers": "MIL", "St. Louis Cardinals": "STL", "Chicago Cubs": "CHC",
    "Pittsburgh Pirates": "PIT", "Cincinnati Reds": "CIN", "Los Angeles Dodgers": "LAD",
    "San Diego Padres": "SD", "Arizona Diamondbacks": "ARI", "San Francisco Giants": "SF",
    "Colorado Rockies": "COL",
}

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

    cod_local = NOMBRE_A_CODIGO.get(juego["local"])
    factor_estadio = ballpark_factors.get(cod_local, 1.0)

    prob = prediccion(
        home,
        away,
        pitcher_home,
        pitcher_away,
        ballpark_factor=factor_estadio
    )

    partido = {
        "gamePk": juego["gamePk"],
        "local": juego["local"],
        "visitante": juego["visitante"],
        "estado": juego["estado"],
        "hora": juego["hora"],

        "marcador_local": juego.get("marcador_local", 0),
        "marcador_visitante": juego.get("marcador_visitante", 0),
        "inning": juego.get("inning"),
        "inning_estado": juego.get("inning_estado"),

        "pitcher_local": juego["pitcher_local"],
        "pitcher_visitante": juego["pitcher_visitante"],

        "pitcher_local_id": juego["pitcher_local_id"],
        "pitcher_visitante_id": juego["pitcher_visitante_id"],

        "ballpark_factor": factor_estadio,

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
