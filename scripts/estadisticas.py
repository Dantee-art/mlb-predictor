import requests

BASE = "https://statsapi.mlb.com/api/v1"


def obtener_estadisticas_equipo(team_id):
    try:
        hit = requests.get(
            f"{BASE}/teams/{team_id}/stats?stats=season&group=hitting",
            timeout=30
        ).json()

        pit = requests.get(
            f"{BASE}/teams/{team_id}/stats?stats=season&group=pitching",
            timeout=30
        ).json()

        h = hit["stats"][0]["splits"][0]["stat"]
        p = pit["stats"][0]["splits"][0]["stat"]

        return {
            "RS": int(h.get("runs", 500)),
            "RA": int(p.get("runs", 450)),
            "AVG": float(h.get("avg", ".250")),
            "ERA": float(p.get("era", "4.20")),
            "elo": 1500,
            "ultimos10": 5,
            "bullpen": 0
        }

    except Exception as e:
        print(f"Error obteniendo estadísticas del equipo {team_id}: {e}")

        return {
            "RS": 500,
            "RA": 450,
            "AVG": 0.250,
            "ERA": 4.20,
            "elo": 1500,
            "ultimos10": 5,
            "bullpen": 0
        }
