import requests

BASE = "https://statsapi.mlb.com/api/v1"

# Pesos estándar de wOBA (versión de referencia, se actualizan poco año
# a año; estos son valores típicos de temporadas recientes de MLB).
W_BB = 0.69
W_HBP = 0.72
W_1B = 0.89
W_2B = 1.27
W_3B = 1.62
W_HR = 2.10

FIP_CONSTANT = 3.10


def _innings_a_float(ip_str):
    """Convierte innings pitched tipo '123.1' (donde el decimal son OUTS,
    no una fracción real) a un número decimal correcto."""
    try:
        ip_str = str(ip_str)
        if "." in ip_str:
            enteros, decimales = ip_str.split(".")
            return int(enteros) + int(decimales) / 3
        return float(ip_str)
    except (ValueError, TypeError):
        return 0.0


def calcular_woba(h):
    """wOBA simplificado: pondera cada tipo de embasada según su valor
    real de generación de carreras, en vez de tratarlas todas igual (AVG)
    o casi igual (OPS)."""
    ab = float(h.get("atBats", 0))
    bb = float(h.get("baseOnBalls", 0))
    hbp = float(h.get("hitByPitch", 0))
    hits = float(h.get("hits", 0))
    dobles = float(h.get("doubles", 0))
    triples = float(h.get("triples", 0))
    hr = float(h.get("homeRuns", 0))
    sf = float(h.get("sacFlies", 0))

    singles = hits - dobles - triples - hr

    denominador = ab + bb + sf + hbp
    if denominador <= 0:
        return 0.320  # wOBA promedio de liga aproximado, como respaldo

    numerador = (
        W_BB * bb + W_HBP * hbp + W_1B * singles +
        W_2B * dobles + W_3B * triples + W_HR * hr
    )

    return round(numerador / denominador, 3)


def calcular_fip_equipo(p):
    """FIP agregado del staff de pitcheo completo del equipo (abridores +
    bullpen), útil como medida de equipo distinta del abridor puntual."""
    ip = _innings_a_float(p.get("inningsPitched", 0))
    if ip <= 0:
        return 4.20

    hr = float(p.get("homeRuns", 0))
    bb = float(p.get("baseOnBalls", 0))
    k = float(p.get("strikeOuts", 0))

    fip = ((13 * hr) + (3 * bb) - (2 * k)) / ip + FIP_CONSTANT
    return round(fip, 2)


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

        record = requests.get(
            f"{BASE}/teams/{team_id}",
            params={"hydrate": "record"},
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

        # Split real de local/visitante (antes se estimaba wins/2, wins/2,
        # lo cual ocultaba equipos que rinden distinto en su propio estadio).
        home_wins, home_losses = wins // 2, losses // 2
        away_wins, away_losses = wins - home_wins, losses - home_losses

        bullpen = float(p.get("era", 4.20))

        woba = calcular_woba(h)
        fip = calcular_fip_equipo(p)

        ultimos10 = 5

        try:
            records = record["teams"][0]["record"]["records"]

            for r in records:
                if r["type"] == "lastTen":
                    ultimos10 = int(r["wins"])
                elif r["type"] == "home":
                    home_wins = int(r["wins"])
                    home_losses = int(r["losses"])
                elif r["type"] == "away":
                    away_wins = int(r["wins"])
                    away_losses = int(r["losses"])
        except Exception:
            pass  # si algo falla, quedan los valores estimados como respaldo

        return {
            "RS": int(h.get("runs", 500)),
            "RA": int(p.get("runs", 450)),
            "AVG": float(h.get("avg", ".250")),
            "ERA": float(p.get("era", "4.20")),
            "WOBA": woba,
            "FIP": fip,

            "elo": round(elo),

            "ultimos10": ultimos10,
            "bullpen": bullpen,

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
        print(e)

        return {
            "RS": 500,
            "RA": 450,
            "AVG": 0.250,
            "ERA": 4.20,
            "WOBA": 0.320,
            "FIP": 4.20,

            "elo": 1500,

            "ultimos10": 5,
            "bullpen": 4.20,

            "wins": 81,
            "losses": 81,
            "win_pct": 0.500,
            "run_diff": 0,

            "home_wins": 40,
            "home_losses": 41,
            "away_wins": 41,
            "away_losses": 40
    }
    
