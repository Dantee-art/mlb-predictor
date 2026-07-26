import json
import os

os.makedirs("datos", exist_ok=True)

with open("datos/partidos.json", "w") as f:
    json.dump([], f)

with open("datos/standings.json", "w") as f:
    json.dump([], f)

with open("datos/lideres.json", "w") as f:
    json.dump([], f)

with open("datos/predicciones.json", "w") as f:
    json.dump([], f)

with open("datos/favoritos.json", "w") as f:
    json.dump([], f)

print("Archivos JSON creados correctamente.")
