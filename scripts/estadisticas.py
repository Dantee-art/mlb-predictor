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

        wins = int(h.get("wins", 81))
        losses = int(h.get("losses", 81))

        games = wins + losses
        win_pct = wins / games if games > 0 else 0.5

        elo = 1500 + (win_pct - 0.5) * 400

        run_diff = int(h.get("runs", 500)) - int(p.get("runs", 450))

        home_wins = wins // 2
        home_losses = losses // 2

        away_wins = wins - home_wins
        away_losses = losses - home_losses

        return {
            "RS": int(h.get("runs", 500)),
            "RA": int(p.get("runs", 450)),
            "AVG": float(h.get("avg", ".250")),
            "ERA": float(p.get("era", "4.20")),

            "elo": round(elo),

            "ultimos10": 5,
            "bullpen": 0,

            "wins": wins,
            "losses": losses,
            "win_pct": round(win_pct, 3),
            "run_diff": run_diff,

            "home_wins": home_wins,
            "home_losses": home_losses,
            "away_wins": away_wins,
            "away_losses": away_losses
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
            "bullpen": 0,

            "wins": 81,
            "losses": 81,
            "win_pct": 0.500,
            "run_diff": 0,

            "home_wins": 40,
            "home_losses": 41,
            "away_wins": 41,
            "away_losses": 40
        }
