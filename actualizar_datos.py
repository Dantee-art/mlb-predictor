"""
Script de actualización diaria — MLB Predictor
Corre dentro de GitHub Actions (no requiere API key).
Genera datos.json con: partidos de hoy, standings de las 30 franquicias,
y líderes de bateo. El HTML lee este archivo al cargar la página.
"""

import json
import urllib.request
from datetime import datetime, timezone, timedelta

# Mapa de teamId numérico (API de MLB) -> código interno usado por el HTML
TEAM_ID_A_CODIGO = {
    147: "NYY", 139: "TB", 141: "TOR", 110: "BAL", 111: "BOS",
    114: "CLE", 145: "CHW", 142: "MIN", 116: "DET", 118: "KC",
    136: "SEA", 133: "ATH", 140: "TEX", 117: "HOU", 108: "LAA",
    144: "ATL", 143: "PHI", 146: "MIA", 120: "WSH", 121: "NYM",
    158: "MIL", 138: "STL", 112: "CHC", 134: "PIT", 113: "CIN",
    119: "LAD", 135: "SD", 109: "ARI", 137: "SF", 115: "COL",
}

NOMBRES_EQUIPO = {
    "NYY": "New York Yankees", "TB": "Tampa Bay Rays", "TOR": "Toronto Blue Jays",
    "BAL": "Baltimore Orioles", "BOS": "Boston Red Sox", "CLE": "Cleveland Guardians",
    "CHW": "Chicago White Sox", "MIN": "Minnesota Twins", "DET": "Detroit Tigers",
    "KC": "Kansas City Royals", "SEA": "Seattle Mariners", "ATH": "Athletics",
    "TEX": "Texas Rangers", "HOU": "Houston Astros", "LAA": "Los Angeles Angels",
    "ATL": "Atlanta Braves", "PHI": "Philadelphia Phillies", "MIA": "Miami Marlins",
    "WSH": "Washington Nationals", "NYM": "New York Mets", "MIL": "Milwaukee Brewers",
    "STL": "St. Louis Cardinals", "CHC": "Chicago Cubs", "PIT": "Pittsburgh Pirates",
    "CIN": "Cincinnati Reds", "LAD": "Los Angeles Dodgers", "SD": "San Diego Padres",
    "ARI": "Arizona Diamondbacks", "SF": "San Francisco Giants", "COL": "Colorado Rockies",
}

DIVISIONES = {
    "NYY": ("AL", "Este"), "TB": ("AL", "Este"), "TOR": ("AL", "Este"), "BAL": ("AL", "Este"), "BOS": ("AL", "Este"),
    "CLE": ("AL", "Central"), "CHW": ("AL", "Central"), "MIN": ("AL", "Central"), "DET": ("AL", "Central"), "KC": ("AL", "Central"),
    "SEA": ("AL", "Oeste"), "ATH": ("AL", "Oeste"), "TEX": ("AL", "Oeste"), "HOU": ("AL", "Oeste"), "LAA": ("AL", "Oeste"),
    "ATL": ("NL", "Este"), "PHI": ("NL", "Este"), "MIA": ("NL", "Este"), "WSH": ("NL", "Este"), "NYM": ("NL", "Este"),
    "MIL": ("NL", "Central"), "STL": ("NL", "Central"), "CHC": ("NL", "Central"), "PIT": ("NL", "Central"), "CIN": ("NL", "Central"),
    "LAD": ("NL", "Oeste"), "SD": ("NL", "Oeste"), "ARI": ("NL", "Oeste"), "SF": ("NL", "Oeste"), "COL": ("NL", "Oeste"),
}


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fecha_hoy_et():
    # Usamos hora del Este de EE.UU. (donde se rige el calendario de MLB)
    ahora_utc = datetime.now(timezone.utc)
    ahora_et = ahora_utc - timedelta(hours=4)  # aproximación EDT
    return ahora_et.strftime("%Y-%m-%d")


def cargar_partidos(fecha_iso):
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={fecha_iso}&hydrate=team,linescore"
    data = fetch_json(url)
    bloques = data.get("dates", [])
    bloque = next((b for b in bloques if b["date"] == fecha_iso), None)
    if not bloque:
        return []

    partidos = []
    for g in bloque.get("games", []):
        away_id = g.get("teams", {}).get("away", {}).get("team", {}).get("id")
        home_id = g.get("teams", {}).get("home", {}).get("team", {}).get("id")
        cod_vis = TEAM_ID_A_CODIGO.get(away_id)
        cod_loc = TEAM_ID_A_CODIGO.get(home_id)
        if not cod_vis or not cod_loc:
            continue  # ignoramos juegos de equipos no reconocidos (ej. exhibición)

        estado_mlb = g.get("status", {}).get("abstractGameState", "Preview")
        estado = "final" if estado_mlb == "Final" else ("en_vivo" if estado_mlb == "Live" else "programado")

        # Detalle de inning actual, solo relevante si el partido está en vivo
        linescore = g.get("linescore", {}) or {}
        inning_actual = linescore.get("currentInningOrdinal")  # ej. "5th"
        mitad_inning = linescore.get("inningState")  # "Top", "Bottom", "Middle", "End"
        detalle_vivo = None
        if estado == "en_vivo" and inning_actual:
            mitad_es = {"Top": "Alta", "Bottom": "Baja", "Middle": "Medio", "End": "Fin"}.get(mitad_inning, "")
            detalle_vivo = f"{mitad_es} del {inning_actual}".strip()

        game_date = g.get("gameDate", "")
        hora = "Hora a confirmar"
        try:
            dt = datetime.fromisoformat(game_date.replace("Z", "+00:00"))
            dt_et = dt - timedelta(hours=4)
            hora = dt_et.strftime("%I:%M %p ET").lstrip("0")
        except Exception:
            pass

        partidos.append({
            "visitante": cod_vis,
            "local": cod_loc,
            "hora": hora,
            "estadio": g.get("venue", {}).get("name", "Estadio a confirmar"),
            "estado": estado,
            "detalleVivo": detalle_vivo,
            "marcadorVis": g.get("teams", {}).get("away", {}).get("score"),
            "marcadorLocal": g.get("teams", {}).get("home", {}).get("score"),
        })
    return partidos


def cargar_standings():
    url = "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026"
    data = fetch_json(url)
    equipos = {}
    for record in data.get("records", []):
        for tr in record.get("teamRecords", []):
            team_id = tr.get("team", {}).get("id")
            cod = TEAM_ID_A_CODIGO.get(team_id)
            if not cod:
                continue
            liga, division = DIVISIONES.get(cod, ("AL", "Este"))

            splits = tr.get("records", {}).get("splitRecords", [])

            def buscar_split(tipo):
                s = next((x for x in splits if x.get("type") == tipo), None)
                if not s:
                    return None
                w, l = s.get("wins", 0), s.get("losses", 0)
                return {"w": w, "l": l}

            equipos[cod] = {
                "nombre": NOMBRES_EQUIPO.get(cod, cod),
                "liga": liga,
                "division": division,
                "w": tr.get("wins", 0),
                "l": tr.get("losses", 0),
                "rs": tr.get("runsScored", 0),
                "ra": tr.get("runsAllowed", 0),
                "strk": tr.get("streak", {}).get("streakCode", "—"),
                "l10": next(
                    (s.get("value", "—") for s in splits if s.get("type") == "lastTen"),
                    "—",
                ),
                "local": buscar_split("home"),
                "visitante": buscar_split("away"),
                "ultimo20": buscar_split("lastTwenty") or buscar_split("lastThirty"),
            }
    return equipos


def cargar_lideres_bateo():
    # Líderes por categoría, temporada 2026, liga completa (sportId=1)
    categorias = {
        "avg": "AVG", "homeRuns": "HR", "runsBattedIn": "RBI",
        "hits": "H", "runs": "R", "ops": "OPS", "stolenBases": "SB",
    }
    resultado = {}
    for stat_key, label in categorias.items():
        url = (
            "https://statsapi.mlb.com/api/v1/stats/leaders"
            f"?leaderCategories={stat_key}&season=2026&sportId=1&limit=5"
        )
        try:
            data = fetch_json(url)
            leaders = data.get("leagueLeaders", [{}])[0].get("leaders", [])
            resultado[label] = [
                {
                    "jugador": ld.get("person", {}).get("fullName", "—"),
                    "equipo": TEAM_ID_A_CODIGO.get(ld.get("team", {}).get("id"), "—"),
                    "valor": ld.get("value", "—"),
                }
                for ld in leaders
            ]
        except Exception as e:
            resultado[label] = []
            print(f"No se pudo cargar líderes de {label}: {e}")
    return resultado


def main():
    fecha = fecha_hoy_et()
    print(f"Actualizando datos para {fecha}...")

    partidos = cargar_partidos(fecha)
    print(f"  {len(partidos)} partidos cargados")

    equipos = cargar_standings()
    print(f"  {len(equipos)} equipos con standings")

    lideres = cargar_lideres_bateo()
    print(f"  Líderes cargados: {list(lideres.keys())}")

    salida = {
        "fecha": fecha,
        "actualizado": datetime.now(timezone.utc).isoformat(),
        "partidos": partidos,
        "equipos": equipos,
        "lideres": lideres,
    }

    with open("datos.json", "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)

    print("datos.json generado correctamente.")


if __name__ == "__main__":
    main()
