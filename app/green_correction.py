import requests
import json
from datetime import datetime, timedelta
import base64
from time import sleep, time

class SuitesFeria:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.url = "https://hotelsuitesferia.greenhotel.cloud"
        self.session = None
        self.base_headers = {
            'User-Agent': 'Mozilla/5.0',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

    def get_data_by_query_asghab(self, startRangeValue, endRangeValue):
        url = "https://83.48.12.213:1281/api/Query/Table/"
        cid = "b21b8d9c6eeec87d6bc5d71b39aab97df03ebbfe"
        password = "Gr51tR703859711965RiEEbp"
        authorization = f"Query.API: {base64.b64encode(password.encode()).decode()}"
        date_header = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

        payload = {
            "queryRequest": {
                "table": "ASGHAB",
                "fields": ["NRESERVA", "FEC_LLEG", "DIAS_EST", "SALIDA", "CHEKOUT", "TIPO_HAB"],
                #"logicalOperator": "AND",
                "conditions": [
                    {
                        "field": "FEC_LLEG",
                        "oper": "<",
                        "value": startRangeValue,
                    },
                    {
                        "field": "SALIDA",
                        "oper": ">",
                        "value": endRangeValue
                    }
                ]
            },
            "control": {
                "uniqueId": "654315758",
                "timestamp": "2025-06-30T18:12:41+02:00"
            }
        }

        headers = {
            "CID": cid,
            "Authorization": authorization,
            "Date": date_header,
            "Content-Type": "application/json"
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload), verify=False)
        if response.status_code == 200:
            result = response.json()
            return result["queryResult"]
        else:
            print("Error:", response.status_code, response.text)
            return None

    def get_data_by_query_habsol(self, startRangeValue, endRangeValue, status):
        url = "https://83.48.12.213:1281/api/Query/Table/"
        cid = "b21b8d9c6eeec87d6bc5d71b39aab97df03ebbfe"
        password = "Gr51tR703859711965RiEEbp"
        authorization = f"Query.API: {base64.b64encode(password.encode()).decode()}"
        date_header = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

        payload = {
            "queryRequest": {
                "table": "HABSOL",
                "fields": ["RESERVA", "FEC_LLEG", "DIAS_EST", "FEC_SALI", "STATUS", "TIPO_HAB", "CANTIDAD"],
                "conditions": [
                    # {
                    #     "field": "STATUS",
                    #     "oper": "!=",
                    #     "value": status,
                    # },
                    {
                        "field": "FEC_LLEG",
                        "oper": "<",
                        "value": startRangeValue,
                    },
                    {
                        "field": "SALIDA",
                        "oper": ">",
                        "value": endRangeValue
                    }
                ]
            },
            "control": {
                "uniqueId": "654315758",
                "timestamp": "2025-06-30T18:12:41+02:00"
            }
        }

        headers = {
            "CID": cid,
            "Authorization": authorization,
            "Date": date_header,
            "Content-Type": "application/json"
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload), verify=False)
        if response.status_code == 200:
            result = response.json()
            return result["queryResult"]
        else:
            print("Error:", response.status_code, response.text)
            return None

    def get_data_by_query_habits(self, tipo_hab):
        url = "https://83.48.12.213:1281/api/Query/Table/"
        cid = "b21b8d9c6eeec87d6bc5d71b39aab97df03ebbfe"
        password = "Gr51tR703859711965RiEEbp"
        authorization = f"Query.API: {base64.b64encode(password.encode()).decode()}"
        date_header = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

        payload = {
            "queryRequest": {
                "table": "HABITS",
                "fields": ["COD_HAB", "TIPO_HAB", "PLANTA", "SITU_HAB", "NRESERVA"],
                "conditions": [
                    {
                        "field": "TIPO_HAB",
                        "oper": "=",
                        "value": str(tipo_hab)
                    }
                ]
            },
            "control": {
                "uniqueId": "654315758",
                "timestamp": "2025-06-06T18:12:41+02:00"
            }
        }

        headers = {
            "CID": cid,
            "Authorization": authorization,
            "Date": date_header,
            "Content-Type": "application/json"
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload), verify=False)
        if response.status_code == 200:
            result = response.json()
            return result["queryResult"]
        else:
            print("Error:", response.status_code, response.text)
            return None

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
            return {"message": "Usuario logueado", "code": 200, "resp": str(resp)}
        elif "Redirecting to https://hotelsuitesferia.greenhotel.cloud/auth/login" in resp:
            return {"message": "Fallo el inicio de sesion.", "code": 400, "resp": "Redirecting to https://hotelsuitesferia.greenhotel.cloud/auth/login"}
        else:
            return {"message": "Fallo el inicio de sesion.", "code": 400, "resp": "Inicio de sesión" if "Inicio de sesión" in resp else "Verificar en logs.", "data": str(resp)}

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
            return {"message": "Fallo al obtener la disponibilidad.", "code": 400}

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
            return {"message": "Sesión cerrada correctamente.", "code": 200}
        else:
            return {"message": "Fallo el cierre de sesion.", "code": 400}

def filtrar_habsol_status(habsol):
    """
    Descarta todas las habitaciones de HABSOL con STATUS = 'PROCESADA'.
    """
    return [r for r in habsol if r[4].upper() != "PROCESADA"]

def filtrar_habsol_unicos(asg, habsol):
    """
    Devuelve un set de IDs de reserva únicos, combinando ASG y habsol (sin duplicados).
    """
    ids_habsol = set()
    reservas_habsol_filtradas = []
    for r in habsol:
        id_reserva = r[0]
        if id_reserva not in ids_habsol:
            ids_habsol.add(id_reserva)
            reservas_habsol_filtradas.append(r)
    ids_asg = set(r[0] for r in asg)
    ids_final = ids_asg.union(ids_habsol)
    return ids_final

if __name__ == "__main__":
    # suites_feria = SuitesFeria("", "")

    # start_date = "2025-08-02"
    # end_date = "2025-08-01"

    # # Convertir a objetos datetime
    # start = datetime.strptime(start_date, "%Y-%m-%d")
    # end = datetime.strptime(end_date, "%Y-%m-%d")

    # # Recorrer el rango día por día
    # # current = start
    # # while current <= end:
    # #     print(current.strftime("%Y-%m-%d"))  # Puedes usar directamente current si prefieres el objeto datetime
    # #     current += timedelta(days=1)

    # confirmadas_asg = suites_feria.get_data_by_query_asghab(start_date, end_date)
    # print(confirmadas_asg)
    # print(len(confirmadas_asg))
    # habsol_filtrado = suites_feria.get_data_by_query_habsol(start_date, end_date, "")
    # print(habsol_filtrado)

    # tipos = ["1"]

    # for t in tipos:
    #     print("---------------------------------------------")
    #     habitaciones_tipo = suites_feria.get_data_by_query_habits(t)
    #     ocupadas_asghab = [c for c in confirmadas_asg if c[5] == t]
    #     ocupadas_habsol = [c for c in habsol_filtrado if c[5] == t]

    #     print(f"Tipo: {t}")
    #     print(f"AsgHab: {len(ocupadas_asghab)} - {ocupadas_asghab}")
    #     print(f"Habsol filtrado: {len(ocupadas_habsol)} - {ocupadas_habsol}")

    #     habsol_unicos = filtrar_habsol_unicos(ocupadas_asghab, ocupadas_habsol)
    #     print(f"Reservas únicas ({len(habsol_unicos)}): {habsol_unicos}")
    #     print(f"Total habitaciones tipo {t}: {len(habitaciones_tipo)}")

    #     ocupadas_total = len(habsol_unicos)
    #     disponibles = len(habitaciones_tipo) - ocupadas_total

    #     print(f" Ocupadas: {ocupadas_total}")
    #     print(f" Disponibles: {disponibles}")


    suites_feria = SuitesFeria("", "")

    start_date = "2025-08-01"
    end_date = "2025-08-31"

    # Convertir a objetos datetime
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    # Recorrer el rango día por día
    tipos = ["1"]
    habitaciones_tipo = suites_feria.get_data_by_query_habits(tipos[0])
    
    current = start
    _time = time()
    while current <= end:
        print(current.strftime("%Y-%m-%d"))  # Puedes usar directamente current si prefieres el objeto datetime

        start_date = str(current.date())
        end_date = str((current - timedelta(days=1)).date())
        
        print(f"DATE: {start_date} - {end_date}")

        confirmadas_asg = suites_feria.get_data_by_query_asghab(start_date, end_date)
        print(confirmadas_asg)
        print(len(confirmadas_asg))
        habsol_filtrado = suites_feria.get_data_by_query_habsol(start_date, end_date, "")
        print(habsol_filtrado)

        for t in tipos:
            print("---------------------------------------------")
            #habitaciones_tipo = suites_feria.get_data_by_query_habits(t)
            ocupadas_asghab = [c for c in confirmadas_asg if c[5] == t]
            ocupadas_habsol = [c for c in habsol_filtrado if c[5] == t]

            print(f"Tipo: {t}")
            print(f"AsgHab: {len(ocupadas_asghab)} - {ocupadas_asghab}")
            print(f"Habsol filtrado: {len(ocupadas_habsol)} - {ocupadas_habsol}")

            habsol_unicos = filtrar_habsol_unicos(ocupadas_asghab, ocupadas_habsol)
            print(f"Reservas únicas ({len(habsol_unicos)}): {habsol_unicos}")
            print(f"Total habitaciones tipo {t}: {len(habitaciones_tipo)}")

            ocupadas_total = len(habsol_unicos)
            disponibles = len(habitaciones_tipo) - ocupadas_total

            print(f" Ocupadas: {ocupadas_total}")
            print(f" Disponibles: {disponibles}")


        #sleep(5)

        current += timedelta(days=1)
    
    print(time() - _time)