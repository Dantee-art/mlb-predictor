import requests

BASE = "https://statsapi.mlb.com/api/v1"


def obtener_partidos(fecha):
    url = f"{BASE}/schedule"

    params = {
        "sportId": 1,
        "date": fecha,
        "hydrate": "team,probablePitcher,linescore"
    }

    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()

    datos = r.json()
    partidos = []

    for d in datos.get("dates", []):
        for g in d.get("games", []):

            home = g["teams"]["home"]
            away = g["teams"]["away"]

            partidos.append({
                "gamePk": g["gamePk"],
                "estado": g["status"]["detailedState"],
                "local": home["team"]["name"],
                "visitante": away["team"]["name"],
                "home_id": home["team"]["id"],
                "away_id": away["team"]["id"],
                "hora": g["gameDate"],
                "venue_id": g.get("venue", {}).get("id"),

                # Marcador en vivo/final. "score" solo existe una vez que el
                # partido arrancó; antes de eso lo dejamos en 0.
                "marcador_local": home.get("score", 0),
                "marcador_visitante": away.get("score", 0),

                # Inning actual y si está en alta/baja, útil para mostrar
                # "Top 5ta", "Fin 7ma", etc. en la UI si se quiere.
                "inning": g.get("linescore", {}).get("currentInning"),
                "inning_estado": g.get("linescore", {}).get("inningState"),

                "pitcher_local": (
                    home["probablePitcher"]["fullName"]
                    if "probablePitcher" in home
                    else "Sin anunciar"
                ),

                "pitcher_local_id": (
                    home["probablePitcher"]["id"]
                    if "probablePitcher" in home
                    else None
                ),

                "pitcher_visitante": (
                    away["probablePitcher"]["fullName"]
                    if "probablePitcher" in away
                    else "Sin anunciar"
                ),

                "pitcher_visitante_id": (
                    away["probablePitcher"]["id"]
                    if "probablePitcher" in away
                    else None
                )
            })

    return partidos


def obtener_standings():
    r = requests.get(
        f"{BASE}/standings",
        params={"leagueId": "103,104"},
        timeout=30
    )
    r.raise_for_status()
    return r.json()


def obtener_lideres():
    r = requests.get(
        f"{BASE}/stats/leaders",
        params={
            "leaderCategories":
                "homeRuns,runsBattedIn,battingAverage,"
                "earnedRunAverage,strikeOuts,wins"
        },
        timeout=30
    )
    r.raise_for_status()
    return r.json()


def obtener_estadisticas_pitcher(pitcher_id):
    if pitcher_id is None:
        return {
            "era": 4.20,
            "whip": 1.30,
            "wins": 0,
            "losses": 0,
            "fip": 4.20,
            "k9": 8.0,
        }

    r = requests.get(
        f"{BASE}/people/{pitcher_id}/stats",
        params={
            "stats": "season",
            "group": "pitching"
        },
        timeout=30
    )

    r.raise_for_status()

    datos = r.json()

    if (
        "stats" not in datos
        or len(datos["stats"]) == 0
        or len(datos["stats"][0]["splits"]) == 0
    ):
        return {
            "era": 4.20,
            "whip": 1.30,
            "wins": 0,
            "losses": 0,
            "fip": 4.20,
            "k9": 8.0,
        }

    s = datos["stats"][0]["splits"][0]["stat"]

    fip = calcular_fip(s)
    k9 = calcular_k9(s)

    return {
        "era": float(s.get("era", 4.20)),
        "whip": float(s.get("whip", 1.30)),
        "wins": int(s.get("wins", 0)),
        "losses": int(s.get("losses", 0)),
        "fip": fip,
        "k9": k9,
        }


# Constante estándar de FIP para la temporada (varía levemente año a año;
# 3.10 es un valor de referencia típico de MLB moderno). Se usa para que
# el FIP quede en una escala comparable al ERA (ambos "menor es mejor",
# rondando los mismos números, ~3.00-4.50).
FIP_CONSTANT = 3.10


def _innings_a_float(ip_str):
    """La API devuelve innings pitched como string tipo '123.1' donde el
    decimal representa outs (.1 = 1 out = 1/3 de inning, .2 = 2 outs = 2/3),
    no una fracción decimal real. Hay que convertirlo correctamente."""
    try:
        ip_str = str(ip_str)
        if "." in ip_str:
            enteros, decimales = ip_str.split(".")
            enteros = int(enteros)
            outs = int(decimales)  # 0, 1 o 2
            return enteros + outs / 3
        return float(ip_str)
    except (ValueError, TypeError):
        return 0.0


def calcular_fip(stat):
    """FIP = ((13*HR + 3*BB - 2*K) / IP) + constante
    Aísla lo que el pitcher controla (jonrones, bases por bolas, ponches)
    de lo que depende de la defensa detrás de él."""
    ip = _innings_a_float(stat.get("inningsPitched", 0))
    if ip <= 0:
        return 4.20

    hr = float(stat.get("homeRuns", 0))
    bb = float(stat.get("baseOnBalls", 0))
    k = float(stat.get("strikeOuts", 0))

    fip = ((13 * hr) + (3 * bb) - (2 * k)) / ip + FIP_CONSTANT
    return round(fip, 2)


def calcular_k9(stat):
    """Ponches cada 9 innings lanzados."""
    ip = _innings_a_float(stat.get("inningsPitched", 0))
    if ip <= 0:
        return 8.0

    k = float(stat.get("strikeOuts", 0))
    return round((k / ip) * 9, 2)
    
