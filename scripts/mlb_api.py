import requests

BASE = "https://statsapi.mlb.com/api/v1"


def obtener_partidos(fecha):
    url = f"{BASE}/schedule"

    params = {
        "sportId": 1,
        "date": fecha,
        "hydrate": "team,probablePitcher"
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
