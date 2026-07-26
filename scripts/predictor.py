from math import pow

HOME_ADV = 0.54


def pythag(rs, ra):
    return pow(rs, 1.83) / (pow(rs, 1.83) + pow(ra, 1.83))


def log5(a, b):
    return (a - a * b) / (a + b - 2 * a * b)


def elo_prob(a, b):
    return 1 / (1 + 10 ** ((b - a) / 400))


def prediccion(home, away, pitcher_home, pitcher_away):

    py_home = pythag(home["RS"], home["RA"])
    py_away = pythag(away["RS"], away["RA"])

    p5 = log5(py_home, py_away)

    elo = elo_prob(home["elo"], away["elo"])

    avg = (home["AVG"] - away["AVG"]) * 0.60

    era = (away["ERA"] - home["ERA"]) * 0.08

    pitcher = (pitcher_away["era"] - pitcher_home["era"]) * 0.05

    whip = (pitcher_away["whip"] - pitcher_home["whip"]) * 0.03

    run_diff = (home["run_diff"] - away["run_diff"]) * 0.0005

    home_record = (
        (home["home_wins"] - home["home_losses"])
        - (away["away_wins"] - away["away_losses"])
    ) * 0.002

    ultimos = (home["ultimos10"] - away["ultimos10"]) * 0.02

    bullpen = (home["bullpen"] - away["bullpen"]) * 0.01

    local = 0.03

    prob = (
        p5 * 0.38 +
        elo * 0.25 +
        HOME_ADV * 0.10 +
        avg +
        era +
        pitcher +
        whip +
        run_diff +
        home_record +
        ultimos +
        bullpen +
        local
    )

    if prob > 0.99:
        prob = 0.99

    if prob < 0.01:
        prob = 0.01

    return round(prob * 100, 1)
