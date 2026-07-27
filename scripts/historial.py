import json
import os

RUTA = "datos/historial.json"


def cargar_historial():

    if not os.path.exists(RUTA):
        return {
            "partidos": [],
            "estadisticas": {
                "predicciones": 0,
                "aciertos": 0,
                "errores": 0,
                "precision": 0
            }
        }

    with open(RUTA, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar_historial(datos):

    with open(RUTA, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)
