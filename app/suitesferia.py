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
    
    def get_data_by_query_asghab(self, startRangeValue, endRangeValue):
        # Datos
        url = ""  # o Custom/TableFields
        cid = ""
        password = ""
        authorization = f"Query.API: {base64.b64encode(password.encode()).decode()}"
        date_header = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

        # JSON de la consulta
        payload = {
            "queryRequest": {
                "table": "ASGHAB",
                "fields": ["NRESERVA", "FEC_LLEG", "DIAS_EST", "SALIDA", "CHEKOUT", "TIPO_HAB"],
                "conditions": [
                    {
                        "field": "FEC_LLEG",
                        "oper": "in",
                        "startRangeValue": startRangeValue,
                        "endRangeValue": endRangeValue
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
            result = response.json()
            return result["queryResult"]
        else:
            print("Error:", response.status_code, response.text)
            return None

    def get_data_by_query_habsol(self, startRangeValue, endRangeValue):
        # Datos
        url = ""  # o Custom/TableFields
        cid = ""
        password = ""
        authorization = f"Query.API: {base64.b64encode(password.encode()).decode()}"
        date_header = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

        # JSON de la consulta
        payload = {
            "queryRequest": {
                "table": "HABSOL",
                "fields": ["RESERVA", "FEC_LLEG", "DIAS_EST", "FEC_SALI", "STATUS", "TIPO_HAB", "CANTIDAD"],
                "conditions": [
                    # {
                    #     "field": "STATUS",
                    #     "oper": "!=",
                    #     "value": "PROCESADA"
                    # },
                    {
                        "field": "FEC_LLEG",
                        "oper": "in",
                        "startRangeValue": startRangeValue,
                        "endRangeValue": endRangeValue
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
            result = response.json()
            return result["queryResult"]
        else:
            print("Error:", response.status_code, response.text)
            return None

    def get_data_by_query_habits(self, n):
        # Datos
        url = ""  # o Custom/TableFields
        cid = ""
        password = ""
        authorization = f"Query.API: {base64.b64encode(password.encode()).decode()}"
        date_header = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

        # JSON de la consulta
        payload = {
            "queryRequest": {
                "table": "HABITS",
                "fields": ["COD_HAB", "TIPO_HAB", "PLANTA", "SITU_HAB", "NRESERVA"],
                # "conditions": [
                #     {
                #         "field": "NRESERVA",
                #         "oper": "=",
                #         "value": n
                #     }
                # ]
                "conditions": [
                    {
                        "field": "TIPO_HAB",
                        "oper": "=",
                        "value": str(n)
                    }
                ]
                # "conditions": [
                #     {
                #         "field": "SITU_HAB",
                #         "oper": "=",
                #         "value": "L"
                #     }
                # ]
            },
            "control": {
                "uniqueId": "654315758",
                "timestamp": "2025-06-06T18:12:41+02:00"
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
            result = response.json()
            return result["queryResult"]
        else:
            print("Error:", response.status_code, response.text)
            return None

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
                "table": "HABITS",
                "fields": ["COD_HAB", "TIPO_HAB", "PLANTA", "SITU_HAB", "NRESERVA", "FEC_LLEG"],
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

def filtrar_habsol_unicos(asg, habsol):
    """
    Devuelve un set de IDs de reserva únicos, combinando ASG y Habsol (sin duplicados).
    """
    # Filtrar duplicados dentro de Habsol
    ids_habsol = set()
    reservas_habsol_filtradas = []

    for r in habsol:
        id_reserva = r[0]
        if id_reserva not in ids_habsol:
            ids_habsol.add(id_reserva)
            reservas_habsol_filtradas.append(r)

    # Crear set con todos los IDs únicos: ASG + habsol (ya filtrado)
    ids_asg = set(r[0] for r in asg)
    ids_final = ids_asg.union(ids_habsol)

    return ids_final


if __name__ == "__main__":
    suites_feria = SuitesFeria("", "")
    confirmadas_asg = suites_feria.get_data_by_query_asghab("2025-06-21", "2025-06-21")
    procesadas_habsol = suites_feria.get_data_by_query_habsol("2025-06-21", "2025-06-21")

    #print(f"AsgHab: {confirmadas}")
    #print(f"Habsol: {procesadas}")
    tipos = ["1", "2", "3", "4"]

    for t in tipos:
        print("---------------------------------------------")
        habitaciones_tipo = suites_feria.get_data_by_query_habits(t)

        ocupadas_asghab = [c for c in confirmadas_asg if c[5] == t]
        ocupadas_habsol = [c for c in procesadas_habsol if c[5] == t]

        print(f"Tipo: {t}")
        print(f"AsgHab: {len(ocupadas_asghab)} - {ocupadas_asghab}")
        print(f"Habsol: {len(ocupadas_habsol)} - {ocupadas_habsol}")
        habsol_limpio = filtrar_habsol_unicos(ocupadas_asghab, ocupadas_habsol)
        print(f"Habsol filtrado ({len(habsol_limpio)}): {habsol_limpio}")
        print(f"habits: {habitaciones_tipo}")

        # Detectar duplicados por ID (índice 0)
        duplicadas = set()
        ids_asghab = set([c[0] for c in ocupadas_asghab])
        for c in ocupadas_habsol:
            if c[0] in ids_asghab:
                duplicadas.add(c[0])

        contador_duplicados = len(duplicadas)

        # Calcular ocupadas únicas
        ocupadas_total = len(habsol_limpio)#len(ocupadas_asghab) + len(ocupadas_habsol) - contador_duplicados
        disponibles = len(habitaciones_tipo) - ocupadas_total

        print(f"Contador duplicados: {contador_duplicados}")
        print(f"  Total habitaciones: {len(habitaciones_tipo)}")
        print(f"  Ocupadas: {ocupadas_total}")
        print(f"  Disponibles: {disponibles}")


    #suites_feria = SuitesFeria("", "")
    #confirmadas = suites_feria.get_data_by_query_asghab("2025-06-06", "2025-06-06")
    #procesadas = suites_feria.get_data_by_query_habsol("2025-06-06", "2025-06-06")

    # l = 0
    # confirmadas2 = confirmadas
    # for p in procesadas:
    #     for c in range(len(confirmadas2)):
    #         if p[0] == confirmadas2[c][0]:
    #             l += 1
    #             del confirmadas2[c]
    #             break
    # print(l)
    # print(len(procesadas))
    # print(confirmadas2)
    # IDs únicos de reservas activas
    #ids_confirmadas = {reserva[0] for reserva in confirmadas}
    #ids_procesadas = {reserva[0] for reserva in procesadas}
    #ids_ocupados = ids_confirmadas.union(ids_procesadas)

    #print(f"Reservas totales activas para el día: {len(confirmadas)}")
    #print(f"Confirmadas asghab: {len(confirmadas)} - {confirmadas}")
    #print(f"Procesadas habsol: {len(procesadas)} - {procesadas}")
    # tipos = {
    #     "1": 0,
    #     "2": 0,
    #     "3": 0,
    #     "4": 0
    # }
    #tipos = ["1", "2", "3", "4"]
    #for c in confirmadas:
    #for t in tipos:
        # Habitaciones actuales
    #    habitacion = suites_feria.get_data_by_query_habits(t)
    #    print(f"Tipo: {t} - {habitacion}")
    #    for c in confirmadas:
    #        pass
            #if t == c[]
        #break
        #tipos[habitacion[0][1]] += 1

    #print(tipos)

    # print(confirmadas)
    # #print("------------------------------------------------")
    # #print(procesadas)
    # print("------------------------------------------------")
    # print(habitaciones)
    # print("------------------------------------------------")

    # # Clasificar habitaciones libres y ocupadas
    # habitaciones_libres = [h for h in habitaciones if h[3] == 'L']
    # habitaciones_ocupadas = [h for h in habitaciones if h[3] == 'O']

    # print("\nHabitaciones libres:")
    # for hab in habitaciones_libres:
    #     print(hab)

    #suites_feria.get_fields_data_by_query()
    # resp = suites_feria.login()
    # print(resp)
    # if resp["code"] == 200:
    #     resp_sf = suites_feria.disponibilidad("2025-03-25")
    #     resp_sf = suites_feria.format_avail(resp_sf)
    #     print(resp_sf)
    #     resp_l = suites_feria.logout()
    #     print(resp_l)