import requests

BASE = "https://statsapi.mlb.com/api/v1"

def obtener_estadisticas_equipo(team_id):
    url = f"{BASE}/teams/{team_id}/stats"

    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.json()
    except:
        return {}
