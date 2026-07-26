import requests

BASE = "https://statsapi.mlb.com/api/v1"

def obtener_estadisticas_equipo(team_id):
    url = f"{BASE}/teams/{team_id}/stats?stats=season"

    try:
        respuesta = requests.get(url, timeout=30)
        respuesta.raise_for_status()
        datos = respuesta.json()

        return {
            "RS": 500,
            "RA": 450,
            "elo": 1500,
            "ultimos10": 5,
            "bullpen": 0
        }

    except Exception as e:
        print(f"Error obteniendo estadísticas: {e}")

        return {
            "RS": 500,
            "RA": 450,
            "elo": 1500,
            "ultimos10": 5,
            "bullpen": 0
        }
