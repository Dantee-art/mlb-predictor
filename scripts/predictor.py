from math import pow

HOME_ADV = 0.54


def pythag(rs, ra):
    return pow(rs, 1.83) / (pow(rs, 1.83) + pow(ra, 1.83))


def log5(a, b):
    return (a - a * b) / (a + b - 2 * a * b)


def elo_prob(a, b):
    return 1 / (1 + 10 ** ((b - a) / 400))


def prediccion(home, away, pitcher_home, pitcher_away, ballpark_factor=1.0):
    py_home = pythag(home["RS"], home["RA"])
    py_away = pythag(away["RS"], away["RA"])

    p5 = log5(py_home, py_away)
    elo = elo_prob(home["elo"], away["elo"])

    # wOBA reemplaza a AVG: pondera cada tipo de embasada según su valor
    # real de generación de carreras, en vez de tratarlas todas igual.
    woba = (home["WOBA"] - away["WOBA"]) * 0.60

    # FIP reemplaza a ERA: aísla lo que el staff de pitcheo controla
    # (HR, BB, K) de lo que depende de la defensa detrás.
    fip = (away["FIP"] - home["FIP"]) * 0.08

    # Pitchers abridores
    pitcher_fip_proxy = (pitcher_away["fip"] - pitcher_home["fip"]) * 0.05
    pitcher_whip = (pitcher_away["whip"] - pitcher_home["whip"]) * 0.03
    # K/9: dominancia del abridor más allá de si tuvo o no suerte con la
    # defensa. Peso moderado porque ya se solapa parcialmente con FIP.
    pitcher_k9 = (pitcher_home["k9"] - pitcher_away["k9"]) * 0.01
    pitcher_record = (
        (pitcher_home["wins"] - pitcher_home["losses"])
        - (pitcher_away["wins"] - pitcher_away["losses"])
    ) * 0.002

    run_diff = (home["run_diff"] - away["run_diff"]) * 0.0005

    home_record = (
        (home["home_wins"] - home["home_losses"])
        - (away["away_wins"] - away["away_losses"])
    ) * 0.002

    ultimos = (home["ultimos10"] - away["ultimos10"]) * 0.02

    bullpen = (away["bullpen"] - home["bullpen"]) * 0.02

    # --- Ballpark factor ---
    # ballpark_factor > 1.0: el estadio del local favorece el ataque en
    # general (más carreras de ambos equipos). Un estadio así ayuda un
    # poco más al equipo local porque juega ahí la mayoría de sus partidos
    # y está más habituado a esas condiciones (dimensiones, altura, viento).
    # El efecto se mantiene chico a propósito: es una ventaja de contexto,
    # no un cambio de nivel real entre los equipos.
    # factor 1.15 -> +0.015 aprox a favor del local; factor 0.85 -> -0.015
    ballpark = (ballpark_factor - 1.0) * 0.10

    # --- OPS+ aproximado ---
    # Sin OPS+ "oficial" disponible en la API pública, lo aproximamos
    # ajustando el wOBA de cada equipo por el ballpark factor de SU propio
    # estadio: un equipo con buen wOBA que juega en un parque de pitcheo
    # (factor bajo) está rindiendo mejor de lo que ese número sugiere en
    # términos relativos, y viceversa. Esto separa "qué tan bueno es el
    # equipo bateando" de "cuánto ayuda su estadio" — la misma idea que
    # OPS+ pero calculada con lo que ya tenemos, sin fuentes nuevas.
    ops_plus_ajuste = (home["WOBA"] / max(ballpark_factor, 0.75)
                       - away["WOBA"] / 1.0) * 0.15

    prob = (
        p5 * 0.38 +
        elo * 0.25 +
        HOME_ADV * 0.10 +
        woba +
        fip +
        pitcher_fip_proxy +
        pitcher_whip +
        pitcher_k9 +
        pitcher_record +
        run_diff +
        home_record +
        ultimos +
        bullpen +
        ballpark +
        ops_plus_ajuste +
        0.03
    )

    if prob > 0.99:
        prob = 0.99

    if prob < 0.01:
        prob = 0.01

    return round(prob * 100, 1)
    
