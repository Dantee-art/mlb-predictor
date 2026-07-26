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

            partidos.append({
                "gamePk": g["gamePk"],
                "estado": g["status"]["detailedState"],
                "local": g["teams"]["home"]["team"]["name"],
                "visitante": g["teams"]["away"]["team"]["name"],
                "home_id": g["teams"]["home"]["team"]["id"],
                "away_id": g["teams"]["away"]["team"]["id"],
                "hora": g["gameDate"]
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
