def obtener_favoritos(predicciones):
    favoritos = []

    for p in predicciones:
        if p["probabilidad"] >= 55:
            favoritos.append({
                "equipo": p["local"],
                "probabilidad": p["probabilidad"]
            })
        elif p["probabilidad"] <= 45:
            favoritos.append({
                "equipo": p["visitante"],
                "probabilidad": round(100 - p["probabilidad"], 1)
            })

    favoritos.sort(key=lambda x: x["probabilidad"], reverse=True)

    return favoritos
