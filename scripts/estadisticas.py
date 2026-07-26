import requests

BASE = "https://statsapi.mlb.com/api/v1"

def obtener_estadisticas_equipo(team_id):
    try:
        url = f"{BASE}/teams/{team_id}/stats?stats=season&group=hitting"
        r = requests.get(url, timeout=30)
        datos = r.json()

        stats = datos["stats"][0]["splits"][0]["stat"]

        carreras = stats.get("runs", 500)

        url2 = f"{BASE}/teams/{team_id}/stats?stats=season&group=pitching"
        r2 = requests.get(url2, timeout=30)
        datos2 = r2.json()

        stats2 = datos2["stats"][0]["splits"][0]["stat"]

        carreras_recibidas = stats2.get("runs", 450)

        return {
            "RS": carreras,
            "RA": carreras_recibidas,
            "elo": 1500,
            "ultimos10": 5,
            "bullpen": 0
        }

    except Exception as e:
        print(e)
        return {
            "RS": 500,
            "RA": 450,
            "elo": 1500,
            "ultimos10": 5,
            "bullpen": 0
        }
