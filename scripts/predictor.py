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
