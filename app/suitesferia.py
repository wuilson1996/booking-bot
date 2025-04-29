import requests

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

        response = self.session.get(f"{self.url}/api/planning/avail/data/{_date}/365")
        try:
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
    suites_feria = SuitesFeria("karine@hotelsuitesferia.com", "APkfBHj77V")
    resp = suites_feria.login()
    print(resp)
    if resp["code"] == 200:
        resp_sf = suites_feria.disponibilidad("2025-03-25")
        resp_sf = suites_feria.format_avail(resp_sf)
        print(resp_sf)
        resp_l = suites_feria.logout()
        print(resp_l)