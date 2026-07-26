def obtener_favoritos(predicciones):
    """
    Devuelve los 3 equipos con mayor probabilidad de ganar.
    """

    ordenados = sorted(
        predicciones,
        key=lambda x: x["probabilidad"],
        reverse=True
    )

    return ordenados[:3]
