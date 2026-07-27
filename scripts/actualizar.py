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
try:
    with open("datos/ballpark_factors.json", "r", encoding="utf-8") as f:
        ballpark_factors = json.load(f).get("factores", {})
except Exception:
    ballpark_factors = {}

# Nombre completo de equipo (como viene de mlb_api) -> código corto usado
# en el resto del proyecto (EQUIPOS en index.html, ballpark_factors.json).
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

# Código de equipo -> team_id de la MLB Stats API (inverso del anterior,
# usado para poder pedir estadísticas de TODOS los equipos, no solo los
# que juegan hoy, y así alimentar el simulador manual del sitio).
CODIGO_A_TEAM_ID = {
    "NYY": 147, "TB": 139, "TOR": 141, "BAL": 110, "BOS": 111,
    "CLE": 114, "CHW": 145, "MIN": 142, "DET": 116, "KC": 118,
    "SEA": 136, "ATH": 133, "TEX": 140, "HOU": 117, "LAA": 108,
    "ATL": 144, "PHI": 143, "MIA": 146, "WSH": 120, "NYM": 121,
    "MIL": 158, "STL": 138, "CHC": 112, "PIT": 134, "CIN": 113,
    "LAD": 119, "SD": 135, "ARI": 109, "SF": 137, "COL": 115,
}

partidos = []
predicciones = []

# Estadísticas ya calculadas por equipo, para no volver a pedirlas al
# armar equipos_avanzado.json más abajo (varios partidos de hoy comparten
# equipo local/visitante, y en el loop de todos los equipos los volvemos
# a necesitar igual, pero así evitamos pedirlas dos veces para los que ya
# jugamos arriba).
stats_por_codigo = {}

for juego in partidos_api:

    home = obtener_estadisticas_equipo(juego["home_id"])
    away = obtener_estadisticas_equipo(juego["away_id"])

    cod_local = NOMBRE_A_CODIGO.get(juego["local"])
    cod_visitante = NOMBRE_A_CODIGO.get(juego["visitante"])
    if cod_local:
        stats_por_codigo[cod_local] = home
    if cod_visitante:
        stats_por_codigo[cod_visitante] = away

    pitcher_home = obtener_estadisticas_pitcher(
        juego["pitcher_local_id"]
    )

    pitcher_away = obtener_estadisticas_pitcher(
        juego["pitcher_visitante_id"]
    )

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

# --- equipos_avanzado.json: wOBA, FIP, bullpen y ballpark factor de los
# 30 equipos, para que el simulador manual del sitio (donde el usuario
# elige dos equipos cualquiera, no solo los que juegan hoy) pueda usar
# las mismas métricas avanzadas que el motor de predicción de partidos
# reales, en vez de un modelo más pobre aparte.
print("Completando estadísticas avanzadas de los 30 equipos...")

equipos_avanzado = {}
for cod, team_id in CODIGO_A_TEAM_ID.items():
    if cod in stats_por_codigo:
        s = stats_por_codigo[cod]
    else:
        s = obtener_estadisticas_equipo(team_id)

    equipos_avanzado[cod] = {
        "woba": s["WOBA"],
        "fip": s["FIP"],
        "bullpen": s["bullpen"],
        "ballpark_factor": ballpark_factors.get(cod, 1.0),
    }

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

with open("datos/equipos_avanzado.json", "w", encoding="utf-8") as f:
    json.dump(equipos_avanzado, f, ensure_ascii=False, indent=4)

print(f"Se encontraron {len(partidos)} partidos.")
print(f"Estadísticas avanzadas guardadas para {len(equipos_avanzado)} equipos.")
