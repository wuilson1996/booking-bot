import requests

class SuitesFeria:
    def __init__(self, username, password) -> None:
        self.headers = {
            'Cookie': 'greenhotelcloud_session=eyJpdiI6InlTZjVrQzh3MjNFR25aSWhBRUQ0cWc9PSIsInZhbHVlIjoiMmZBR1VyQ2ZPTW9zbkp3Um1ZZFRHWnA1dEJqN1dVRDcwanY1YjFWUzJDQUtVOVRRRnlaZHY3ai9raFl0K0wyTE0xUXJXTUp4MCtyRG83bWJTL1lHYXhIZkI2WGVyb1JuZEZielB0SnBLcG5ZdnBoQk9nSjhjTC9JUjEvY0RhN0IiLCJtYWMiOiI5YTFjODJmZGI1MzczZmU5YTU0OTIyNWNiN2IzOGI1NTVkOWQ1MmUyMGRiMDU0NzMyZmNlZGI3MWFmZWU2ZjVhIiwidGFnIjoiIn0%3D'
        }
        self.username = username
        self.password = password
        self.url = "https://hotelsuitesferia.greenhotel.cloud"

    def login(self):
        session = requests.Session()
        payload = {
            'login': self.username,
            'password': self.password
        }

        headers = self.headers.copy()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'

        response = session.post(f"{self.url}/auth/login", headers=headers, data=payload, allow_redirects=True)
        resp = response.text

        if "Usuario logueado: " in resp:
            result = {
                "message": "Usuario logueado",
                "code": 200,
                "resp": str(resp)
            }
        elif "Redirecting to https://hotelsuitesferia.greenhotel.cloud/auth/login" in resp:
            result = {
                "message": "Fallo el inicio de sesion.",
                "code": 400,
                "resp": "Redirecting to https://hotelsuitesferia.greenhotel.cloud/auth/login"
            }
        else:
            result = {
                "message": "Fallo el inicio de sesion.",
                "code": 400,
                "resp": "Inicio de sesión" if "Inicio de sesión" in resp else "Verificar en logs.",
                "data": str(resp)
            }

        return result

    def disponibilidad(self, _date):
        response = requests.request("GET", self.url+f"/api/planning/avail/data/{_date}/365", headers=self.headers, data={})
        try:
            data = response.json()
            result = {
                "message": "Sesión cerrada correctamente.",
                "code": 200,
                "data": data
            }
        except Exception as e:
            result = {
                "message": "Fallo el cierre de sesion.",
                "code": 400
            }
        return result

    def format_avail(self, resp_sf):
        dispon = []
        _keys = list(resp_sf["data"]["data"]["availByRt"].keys())
        by_date = list(resp_sf["data"]["data"]["availByRt"][_keys[0]]["byDate"].keys())
        for d in by_date:
            dispon_dict = {"date": d, "avail":{"1": "", "2": "", "3": "", "4": ""}}
            for key in _keys:
                dispon_dict["avail"][key] = resp_sf["data"]["data"]["availByRt"][key]["byDate"][d]
            dispon.append(dispon_dict)
        return dispon

    def logout(self):
        response = requests.request("GET", self.url+"/auth/logout", headers=self.headers, data={})
        resp = response.text
        if "Sesión cerrada correctamente." in resp:
            result = {
                "message": "Sesión cerrada correctamente.",
                "code": 200
            }
        else:
            result =  {
                "message": "Fallo el cierre de sesion.",
                "code": 400
            }
        return result

if __name__ == "__main__":
    suites_feria = SuitesFeria()
    resp = suites_feria.login()
    print(resp)
    if resp["code"] == 200:
        resp_sf = suites_feria.disponibilidad("2025-03-25")
        resp_sf = suites_feria.format_avail(resp_sf)
        print(resp_sf)
        resp_l = suites_feria.logout()
        print(resp_l)