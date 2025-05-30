import requests
import json
from datetime import datetime
import base64

class SuitesFeria:
    def __init__(self, username, password) -> None:
        self.username = username
        self.password = password
        self.url = "https://hotelsuitesferia.greenhotel.cloud"
        self.session = None  # 🔹 Aquí se guardará la sesión activa
        self.base_headers = {
            'User-Agent': 'Mozilla/5.0',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    
    def get_data_by_query(self):
        # Datos
        url = ""  # o Custom/TableFields
        cid = ""
        password = ""
        authorization = f"Query.API: {base64.b64encode(password.encode()).decode()}"
        date_header = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

        # JSON de la consulta
        payload = {
            "queryRequest": {
                "table": "RESUME",
                "fields": ["FACTURA", "YEAR", "FECHAEMI", "IMP_TOTA"],
                "conditions": [
                    {"field": "SERIE", "oper": "=", "value": "T"},
                    {
                        "field": "FECHAEMI",
                        "oper": "in",
                        "startRangeValue": "2025-05-30",
                        "endRangeValue": "2025-06-30"
                    }
                ]
            },
            "control": {
                "uniqueId": "654315758",
                "timestamp": "2025-06-30T18:12:41+02:00"
            }
        }
        # Headers
        headers = {
            "CID": cid,
            "Authorization": authorization,
            "Date": date_header,
            "Content-Type": "application/json"
        }

        # Realizar POST
        response = requests.post(url, headers=headers, data=json.dumps(payload), verify=False)

        # Procesar respuesta
        if response.status_code == 200:
            print(response.json())
        else:
            print("Error:", response.status_code, response.text)

    def get_fields_data_by_query(self):
        # Datos
        url = ""  # o Custom/TableFields
        cid = ""
        password = ""
        authorization = f"Query.API: {base64.b64encode(password.encode()).decode()}"
        date_header = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

        # JSON de la consulta
        payload = {
            "queryRequest": {
                "table": "RESUME",
                "fields": ["FACTURA", "YEAR", "FECHAEMI", "IMP_TOTA"],
                "conditions": [
                    {"field": "SERIE", "oper": "=", "value": "T"},
                    {
                        "field": "FECHAEMI",
                        "oper": "in",
                        "startRangeValue": "2025-05-30",
                        "endRangeValue": "2025-06-30"
                    }
                ]
            },
            "control": {
                "uniqueId": "654315758",
                "timestamp": "2025-06-30T18:12:41+02:00"
            }
        }
        # Headers
        headers = {
            "CID": cid,
            "Authorization": authorization,
            "Date": date_header,
            "Content-Type": "application/json"
        }

        # Realizar POST
        response = requests.post(url, headers=headers, data=json.dumps(payload), verify=False)

        # Procesar respuesta
        if response.status_code == 200:
            print(response.json())
        else:
            print("Error:", response.status_code, response.text)

    def login(self):
        self.session = requests.Session()
        headers = self.base_headers.copy()

        payload = {
            'login': self.username,
            'password': self.password
        }

        response = self.session.post(f"{self.url}/auth/login", headers=headers, data=payload, allow_redirects=True)
        resp = response.text

        if "Usuario logueado: " in resp:
            return {
                "message": "Usuario logueado",
                "code": 200,
                "resp": str(resp)
            }
        elif "Redirecting to https://hotelsuitesferia.greenhotel.cloud/auth/login" in resp:
            return {
                "message": "Fallo el inicio de sesion.",
                "code": 400,
                "resp": "Redirecting to https://hotelsuitesferia.greenhotel.cloud/auth/login"
            }
        else:
            return {
                "message": "Fallo el inicio de sesion.",
                "code": 400,
                "resp": "Inicio de sesión" if "Inicio de sesión" in resp else "Verificar en logs.",
                "data": str(resp)
            }

    def disponibilidad(self, _date):
        if not self.session:
            return {"message": "Sesión no iniciada.", "code": 401}

        try:
            response = self.session.get(f"{self.url}/api/planning/avail/data/{_date}/365")
            data = response.json()
            return {
                "message": "Datos de disponibilidad obtenidos.",
                "code": 200,
                "data": data
            }
        except Exception:
            return {
                "message": "Fallo al obtener la disponibilidad.",
                "code": 400
            }

    def format_avail(self, resp_sf):
        dispon = []
        _keys = list(resp_sf["data"]["data"]["availByRt"].keys())
        by_date = list(resp_sf["data"]["data"]["availByRt"][_keys[0]]["byDate"].keys())

        for d in by_date:
            dispon_dict = {"date": d, "avail": {"1": "", "2": "", "3": "", "4": ""}}
            for key in _keys:
                dispon_dict["avail"][key] = resp_sf["data"]["data"]["availByRt"][key]["byDate"][d]
            dispon.append(dispon_dict)
        return dispon

    def logout(self):
        if not self.session:
            return {"message": "Sesión no iniciada.", "code": 401}

        response = self.session.get(f"{self.url}/auth/logout")
        resp = response.text

        if "Sesión cerrada correctamente." in resp:
            return {
                "message": "Sesión cerrada correctamente.",
                "code": 200
            }
        else:
            return {
                "message": "Fallo el cierre de sesion.",
                "code": 400
            }


if __name__ == "__main__":
    suites_feria = SuitesFeria("", "")
    suites_feria.get_data_by_query()
    #suites_feria.get_fields_data_by_query()
    # resp = suites_feria.login()
    # print(resp)
    # if resp["code"] == 200:
    #     resp_sf = suites_feria.disponibilidad("2025-03-25")
    #     resp_sf = suites_feria.format_avail(resp_sf)
    #     print(resp_sf)
    #     resp_l = suites_feria.logout()
    #     print(resp_l)