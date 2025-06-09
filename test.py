import requests
import uuid
from datetime import datetime, timezone

# 1. Datos específicos de tu consulta
URL = "https://83.48.12.213:1281/api/customquery"
TOKEN = "Gr51tR703859711965RiEEbp"          # Si tu API necesita auth
function_name = "GetAvailableExtras"
date_from = "2019-01-01"
date_to = "2021-12-31"

# 2. Construir el payload
payload = {
    "customQuery": {
        "function": function_name,
        "params": [date_from, date_to]
    },
    "control": {
        "uniqueId": str(uuid.uuid4()).upper(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
}

print(payload)
# 3. Encabezados HTTP
headers = {
    "Content-Type": "application/json",
}
if TOKEN:
    headers["Authorization"] = f"Bearer {TOKEN}"

# 4. Enviar la solicitud
try:
    resp = requests.post(URL, json=payload, headers=headers, timeout=30, verify=False)
    resp.raise_for_status()           # Lanza excepción si el status no es 2xx
except requests.RequestException as e:
    print("Error al llamar al servicio:", e)
    raise

# 5. Procesar la respuesta
data = resp.json()
query_result = data.get("queryResult", [])

print("Filas devueltas:", len(query_result))
for fila in query_result:
    print(fila)   # o procesa según tu lógica
