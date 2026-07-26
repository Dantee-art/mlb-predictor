from math import pow

HOME_ADV = 0.54

def pythag(win, lose):
    if win + lose == 0:
        return 0.5
    return pow(win, 1.83) / (pow(win, 1.83) + pow(lose, 1.83))

def log5(a, b):
    return (a - a*b) / (a + b - 2*a*b)

def elo_prob(a, b):
    return 1 / (1 + 10 ** ((b - a) / 400))

def prediction(home, away):

    home_py = pythag(home["RS"], home["RA"])
    away_py = pythag(away["RS"], away["RA"])

    log = log5(home_py, away_py)

    elo = elo_prob(home["elo"], away["elo"])

    prob = (log*0.45)+(elo*0.35)+(HOME_ADV*0.20)

    if prob > 0.99:
        prob = 0.99

    if prob < 0.01:
        prob = 0.01

    return round(prob*100,1)
predicciones = []

for fecha in partidos.get("dates", []):

    for juego in fecha.get("games", []):

        local = juego["teams"]["home"]["team"]["name"]
        visitante = juego["teams"]["away"]["team"]["name"]

        # Datos de ejemplo (después los reemplazaremos por estadísticas reales)
        home = {
            "RS": 500,
            "RA": 420,
            "elo": 1550
        }

        away = {
            "RS": 470,
            "RA": 450,
            "elo": 1500
        }

        prob = prediction(home, away)

        predicciones.append({
            "local": local,
            "visitante": visitante,
            "probabilidad": prob
        })
        favoritos = obtener_favoritos(predicciones)

with open("datos/partidos.json", "w", encoding="utf-8") as f:
    json.dump(partidos, f, ensure_ascii=False, indent=4)

with open("datos/standings.json", "w", encoding="utf-8") as f:
    json.dump(standings, f, ensure_ascii=False, indent=4)

with open("datos/lideres.json", "w", encoding="utf-8") as f:
    json.dump(lideres, f, ensure_ascii=False, indent=4)

with open("datos/predicciones.json", "w", encoding="utf-8") as f:
    json.dump(predicciones, f, ensure_ascii=False, indent=4)

with open("datos/favoritos.json", "w", encoding="utf-8") as f:
    json.dump(favoritos, f, ensure_ascii=False, indent=4)

print("Actualización terminada.")
