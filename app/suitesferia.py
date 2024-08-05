import requests

class SuitesFeria:
    def __init__(self) -> None:
        self.headers = {
            'Cookie': 'greenhotelcloud_session=eyJpdiI6InlTZjVrQzh3MjNFR25aSWhBRUQ0cWc9PSIsInZhbHVlIjoiMmZBR1VyQ2ZPTW9zbkp3Um1ZZFRHWnA1dEJqN1dVRDcwanY1YjFWUzJDQUtVOVRRRnlaZHY3ai9raFl0K0wyTE0xUXJXTUp4MCtyRG83bWJTL1lHYXhIZkI2WGVyb1JuZEZielB0SnBLcG5ZdnBoQk9nSjhjTC9JUjEvY0RhN0IiLCJtYWMiOiI5YTFjODJmZGI1MzczZmU5YTU0OTIyNWNiN2IzOGI1NTVkOWQ1MmUyMGRiMDU0NzMyZmNlZGI3MWFmZWU2ZjVhIiwidGFnIjoiIn0%3D'
        }
        self.username = 'karine@hotelsuitesferia.com'
        self.password = 'APkfBHj77V'
        self.url = "https://hotelsuitesferia.greenhotel.cloud"

    def login(self):
        payload = {
            'login': self.username,
            'password': self.password
        }
        files=[]
        response = requests.request("POST", self.url+"/auth/login", headers=self.headers, data=payload, files=files)
        resp = response.text
        if "Usuario logueado: " in resp:
            result = {
                "message": "Usuario logueado",
                "code": 200
            }
        else:
            result =  {
                "message": "Fallo el inicio de sesion.",
                "code": 400
            }
        return result

    def disponibilidad(self):
        response = requests.request("GET", self.url+"/api/planning/avail/data/2024-08-05/365", headers=self.headers, data={})
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
        resp_sf = suites_feria.disponibilidad()
        resp_sf = suites_feria.format_avail(resp_sf)
        print(resp_sf)
        resp_l = suites_feria.logout()
        print(resp_l)