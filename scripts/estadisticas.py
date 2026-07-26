import requests

BASE = "https://statsapi.mlb.com/api/v1"


def obtener_estadisticas_equipo(team_id):

    return {
        "RS": 500,
        "RA": 450,
        "elo": 1500,
        "ultimos10": 5,
        "bullpen": 0
    }
