"""
Calcula el "ballpark factor" de cada estadio de la MLB para la temporada
actual: cuánto favorece (o perjudica) la anotación de carreras respecto
al promedio de la liga.

Método (el estándar sabermétrico simplificado a nivel de carreras totales):

  Para cada equipo local, comparamos:
    - Carreras totales anotadas por AMBOS equipos en los partidos que jugó
      de LOCAL (en su propio estadio).
    - Carreras totales anotadas por AMBOS equipos en los partidos que jugó
      de VISITANTE (en estadios ajenos).

  factor_equipo = (carreras_por_partido_en_casa) / (carreras_por_partido_de_visita)

Ese "factor_equipo" se asigna al estadio de ese equipo (asumiendo que cada
equipo juega de local siempre en el mismo estadio, cierto en MLB salvo
excepciones puntuales que este cálculo simplificado ignora).

Un factor de 1.15 significa que ese estadio produce ~15% más carreras que
el promedio de cuando esos mismos equipos juegan en otro lado.
Un factor de 0.90 significa que favorece al pitcheo (menos carreras).

Este script es pesado (baja TODO el calendario jugado de la temporada) y
está pensado para correr 1 vez por día, no junto al resto de los datos.
"""

import json
import time
from datetime import datetime

import requests

BASE = "https://statsapi.mlb.com/api/v1"
SEASON = datetime.now().year

# team.id de la MLB Stats API -> código usado en el resto del proyecto
TEAM_ID_A_CODIGO = {
    147: "NYY", 139: "TB", 141: "TOR", 110: "BAL", 111: "BOS",
    114: "CLE", 145: "CHW", 142: "MIN", 116: "DET", 118: "KC",
    136: "SEA", 133: "ATH", 140: "TEX", 117: "HOU", 108: "LAA",
    144: "ATL", 143: "PHI", 146: "MIA", 120: "WSH", 121: "NYM",
    158: "MIL", 138: "STL", 112: "CHC", 134: "PIT", 113: "CIN",
    119: "LAD", 135: "SD", 109: "ARI", 137: "SF", 115: "COL",
}


def obtener_partidos_temporada():
    """Trae todos los partidos de temporada regular ya finalizados, con
    su marcador, usando el endpoint de schedule con rango de fechas."""
    url = f"{BASE}/schedule"
    params = {
        "sportId": 1,
        "season": SEASON,
        "gameType": "R",  # Regular season únicamente
        "hydrate": "team,linescore",
    }
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    datos = r.json()

    partidos = []
    for bloque in datos.get("dates", []):
        for g in bloque.get("games", []):
            estado = g.get("status", {}).get("abstractGameState", "")
            if estado != "Final":
                continue  # solo partidos ya jugados

            home = g["teams"]["home"]
            away = g["teams"]["away"]

            home_score = home.get("score")
            away_score = away.get("score")
            if home_score is None or away_score is None:
                continue

            home_id = home["team"]["id"]
            away_id = away["team"]["id"]

            if home_id not in TEAM_ID_A_CODIGO or away_id not in TEAM_ID_A_CODIGO:
                continue

            partidos.append({
                "home_id": home_id,
                "away_id": away_id,
                "total_carreras": home_score + away_score,
            })

    return partidos


def calcular_factores(partidos):
    """Para cada equipo, promedia carreras totales (ambos lados) en sus
    partidos de local vs. sus partidos de visitante, y saca el ratio."""
    stats = {cod: {"casa_carreras": 0, "casa_juegos": 0, "visita_carreras": 0, "visita_juegos": 0}
              for cod in TEAM_ID_A_CODIGO.values()}

    for p in partidos:
        cod_home = TEAM_ID_A_CODIGO[p["home_id"]]
        cod_away = TEAM_ID_A_CODIGO[p["away_id"]]

        stats[cod_home]["casa_carreras"] += p["total_carreras"]
        stats[cod_home]["casa_juegos"] += 1

        stats[cod_away]["visita_carreras"] += p["total_carreras"]
        stats[cod_away]["visita_juegos"] += 1

    factores = {}
    for cod, s in stats.items():
        if s["casa_juegos"] == 0 or s["visita_juegos"] == 0:
            factores[cod] = 1.0  # sin datos suficientes -> neutro
            continue

        promedio_casa = s["casa_carreras"] / s["casa_juegos"]
        promedio_visita = s["visita_carreras"] / s["visita_juegos"]

        if promedio_visita == 0:
            factores[cod] = 1.0
            continue

        factor = promedio_casa / promedio_visita

        # Límites razonables para evitar factores absurdos con poca muestra
        # (ej. principio de temporada con pocos partidos jugados).
        factor = max(0.75, min(1.35, factor))

        factores[cod] = round(factor, 3)

    return factores


def main():
    print("Descargando calendario completo de la temporada...")
    inicio = time.time()
    partidos = obtener_partidos_temporada()
    print(f"  {len(partidos)} partidos finalizados encontrados en {time.time() - inicio:.1f}s")

    factores = calcular_factores(partidos)

    salida = {
        "temporada": SEASON,
        "actualizado": datetime.now().isoformat(),
        "partidos_analizados": len(partidos),
        "factores": factores,
    }

    with open("datos/ballpark_factors.json", "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=4)

    print("datos/ballpark_factors.json generado.")
    for cod, factor in sorted(factores.items(), key=lambda x: -x[1]):
        etiqueta = "favorece ataque" if factor > 1.03 else ("favorece pitcheo" if factor < 0.97 else "neutro")
        print(f"  {cod}: {factor}  ({etiqueta})")


if __name__ == "__main__":
    main()
          
