from math import pow

HOME_ADV = 0.54


def pythag(rs, ra):
    return pow(rs, 1.83) / (pow(rs, 1.83) + pow(ra, 1.83))


def log5(a, b):
    return (a - a * b) / (a + b - 2 * a * b)


def elo_prob(a, b):
    return 1 / (1 + 10 ** ((b - a) / 400))


def prediccion(home, away, pitcher_home=None, pitcher_away=None):

    py_home = pythag(home["RS"], home["RA"])
    py_away = pythag(away["RS"], away["RA"])

    p5 = log5(py_home, py_away)

    elo = elo_prob(home["elo"], away["elo"])

    avg = (home["AVG"] - away["AVG"]) * 0.60
    era = (away["ERA"] - home["ERA"]) * 0.08

    ultimos = (home["ultimos10"] - away["ultimos10"]) * 0.02
    bullpen = (home["bullpen"] - away["bullpen"]) * 0.01

    local = 0.03

    # Ventaja del pitcher abridor
    pitcher = 0

    if pitcher_home and pitcher_away:
        pitcher = (
            pitcher_away["era"] - pitcher_home["era"]
        ) * 0.03

    prob = (
        p5 * 0.45 +
        elo * 0.30 +
        HOME_ADV * 0.10 +
        avg +
        era +
        ultimos +
        bullpen +
        local +
        pitcher
    )

    if prob > 0.99:
        prob = 0.99

    if prob < 0.01:
        prob = 0.01

    return round(prob * 100, 1)
