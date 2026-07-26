import requests

BASE = "https://statsapi.mlb.com/api/v1"


def obtener_partidos(fecha):

    url = f"{BASE}/schedule?sportId=1&date={fecha}&hydrate=probablePitcher,team"

    r = requests.get(url, timeout=30)

    return r.json()


def obtener_standings():

    url = f"{BASE}/standings?leagueId=103,104"

    return requests.get(url, timeout=30).json()


def obtener_boxscore(gamePk):

    url = f"{BASE}/game/{gamePk}/boxscore"

    return requests.get(url, timeout=30).json()


def obtener_live(gamePk):

    url = f"{BASE}/game/{gamePk}/feed/live"

    return requests.get(url, timeout=30).json()


def obtener_lideres():

    url = (
        f"{BASE}/stats/leaders"
        "?leaderCategories=homeRuns,runsBattedIn,battingAverage,"
        "earnedRunAverage,strikeOuts,wins"
    )

    return requests.get(url, timeout=30).json()
