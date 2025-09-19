from bs4 import BeautifulSoup
import requests
import json
import logging

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import os
import platform
from .models import *

import datetime
import time

class DEdge:
    URL = "https://extranet.availpro.com/Planning/Edition/Save"
    URL_GET = "https://extranet.availpro.com/Planning/Edition/Index/DATE/Room0/Rate585370"
    URL_LOGIN = "https://login.availpro.com/es?ReturnUrl=%2f"
    URL_TARGET = "https://extranet.availpro.com/"
    ROOM_TYPES = {
        "2": "113516",
        "0": "113522",
        "1": "113517",
        "3": "113705",
        "4": "113518",
        "5": "113519",
        "6": "113703"
    }
    RATE_ID = "585370"

    # atributos de clase para mantener sesión y datos
    session = requests.Session()
    username = None
    password = None

    @classmethod
    def initialize(cls, db_cookies: dict, username: str, password: str):
        cls.username = username
        cls.password = password

        if db_cookies:
            generate_log(f"[+] Update cookies", BotLog.ROOMPRICE)
            logging.info("[+] Update cookies")
            generate_log(f"{str(db_cookies)}", BotLog.ROOMPRICE)
            logging.info(db_cookies)
            cls.session.cookies.update(db_cookies)

        # Si se hizo login, retornar True para que el caller guarde cookies nuevas
        logged_in = cls.ensure_session()
        return logged_in

    @classmethod
    def get_new_cookies(cls):
        return cls.session.cookies.get_dict()

    @classmethod
    def get_type(cls, room_type):
        return cls.ROOM_TYPES.get(room_type, "113516")

    @classmethod
    def get_headers(cls, _date):
        return {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "es-ES,es;q=0.9",
            "cache-control": "max-age=0",
            "sec-ch-ua": "\"Chromium\";v=\"140\", \"Not=A?Brand\";v=\"24\", \"Google Chrome\";v=\"140\"",
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": "\"Android\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "referer": f"https://extranet.availpro.com/Planning/Edition/Index/{_date}/Room0/Rate585370",
            "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36"
        }

    @classmethod
    def get_cookies(cls):
        return {
            "__insp_wid": "554316038",
            "__insp_nv": "true",
            "__insp_targlpu": "aHR0cHM6Ly9leHRyYW5ldC5hdmFpbHByby5jb20vRGV2aWNlL1Vua25vd24%3D",
            "__insp_targlpt": "RC1FREdFIC0gwr9TZSBlc3TDoSBjb25lY3RhbmRvIGRlc2RlIHVuIGRpc3Bvc2l0aXZvIG51ZXZvPw==",
            "__insp_norec_sess": "true",
            "__insp_slim": "1756829720681",
            "_hjSessionUser_60265": "eyJpZCI6ImYxNzcwMTI3LTg3ZWQtNThkYy1iMDUxLWE5Y2U5NTE1NjVmZiIsImNyZWF0ZWQiOjE3NTY4Mjk3MzEyMzgsImV4aXN0aW5nIjp0cnVlfQ==",
            "_gid": "GA1.2.2074678862.1757635960",
            "ASP.NET_SessionId": "0nx1s0iktgllqim12xrqddzh",
            "_clsk": "1qdtvct%5E1757778635128%5E1%5E0%5Eq.clarity.ms%2Fcollect",
            "_ga": "GA1.1.1472735258.1756563538",
            "_clck": "1k68npn%5E2%5Efza%5E0%5E2082",
            "_ga_CQNZ2C0Y74": "GS2.1.s1757778633$o2$g1$t1757778635$j58$l0$h0",
            ".AVPAUTH": "9e11570bad6cf20931ded8bd040dfe05d438808783c1301dadda6afad111b86cd770c398bb55730c9592da1a5dfa841c937d02b42097217ee791e895e3741dabdad29be75a4f2c3f54f7d5e201c195e7f5e2511b8069c0b56ac518ffda93e63a68f6973d7bc643588e82dae5023aa35d42e24b65a44d0c4004238be1da8e095e",
            ".DEVICEID": "DzsFvvJYKoVyIaW2e+0fnZcthMap8hg4g/HO62QngboUvZVhWUzfUQshYmFDbsdm/KJJ7Jn6aeAJn2u80QCxqSuwjdEEXgjMUtmY/GHozAHoRSGpe3S1tyBGSJ9R5MrpLiLDPhcjt/f2tlZrV1lXvpB/9yY6hP2S/I9Kvuj/0L8="
        }

    @classmethod
    def is_login_required(cls, response_text):
        """Detecta si el HTML contiene el formulario de login."""
        return '<form method="post" id="login-form"' in response_text
    
    @classmethod
    def get_verification_token(cls, html):
        """Extrae __RequestVerificationToken del formulario de login."""
        soup = BeautifulSoup(html, "html.parser")
        token_input = soup.find("input", {"name": "__RequestVerificationToken"})
        return token_input["value"] if token_input else None

    @classmethod
    def update_cookies(cls, db_cookies):
        """Permite cargar cookies previas desde DB al iniciar."""
        cls.session.cookies.update(db_cookies)

    @classmethod
    def _driver_chrome(cls) -> None:
        options = webdriver.ChromeOptions()
        #options.add_argument("headless")
        #options.add_argument("disable-gpu")
        #options.add_argument("no-sandbox")

        return webdriver.Chrome(executable_path=os.path.abspath("chromedriver.exe"), options=options)

    @classmethod
    def _driver_firefox(cls) -> None:
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        #options.add_argument("-private")  # Modo incógnito
        options.set_preference("browser.privatebrowsing.autostart", True)

        return webdriver.Firefox(executable_path=os.path.abspath("geckodriver"), options=options)
    
    @classmethod
    def _driver(cls) -> None:
        if platform.system() == "Windows":
            return cls._driver_chrome()
        else:
            return cls._driver_firefox()

    @classmethod
    def handle_new_device_prompt(cls, driver):
        """Detecta si aparece la pantalla de 'dispositivo nuevo' y hace clic en 'Ingrese el código'."""
        try:
            wait = WebDriverWait(driver, 5)
            # Detectar si aparece el título de la página
            wait.until(EC.presence_of_element_located(
                (By.XPATH, "//h1[contains(., '¿Se está conectando desde un dispositivo nuevo?')]")
            ))
            logging.warning("⚠️ Se detectó el aviso de 'dispositivo nuevo'")

            try:
                btn_ingresar = driver.find_element(By.ID, "authorisation-link")
                driver.execute_script("arguments[0].click();", btn_ingresar)
                logging.info("✅ Link 'Ingrese el código' clickeado, esperando código...")
                return True
            except Exception:
                logging.error("⚠️ No se encontró el link con ID 'authorisation-link'")
                return False

        except TimeoutException:
            # No hay mensaje de nuevo dispositivo
            return False

    @classmethod
    def selenium_login(cls, db_cookies=None):
        generate_log(f"Iniciando navegador Selenium...", BotLog.ROOMPRICE)
        logging.info("🚀 Iniciando navegador Selenium...")
        driver = cls._driver()
        driver.get(cls.URL_LOGIN)

        # --- Si tenemos cookies previas, las agregamos ---
        if db_cookies:
            generate_log(f"Cargando cookies previas en Selenium...", BotLog.ROOMPRICE)
            logging.info("🍪 Cargando cookies previas en Selenium...")
            driver.delete_all_cookies()
            for name, value in db_cookies.items():
                driver.add_cookie({"name": name, "value": value, "domain": ".availpro.com"})
            driver.refresh()

        try:
            wait = WebDriverWait(driver, 15)

            try:
                cls.guardar_captura(driver, name=f"cap_LOGIN_DEdge_1_{now()}")
            except Exception:
                pass

            # Si ya estamos logueados, no hay login-form
            if not driver.find_elements(By.NAME, "login"):
                generate_log(f"Ya estábamos logueados (cookies válidas)", BotLog.ROOMPRICE)
                logging.info("✅ Ya estábamos logueados (cookies válidas)")
            else:
                generate_log(f"Escribiendo credenciales...", BotLog.ROOMPRICE)
                logging.info("✍️ Escribiendo credenciales...")
                input_user = wait.until(EC.presence_of_element_located((By.NAME, "login")))
                input_pass = wait.until(EC.presence_of_element_located((By.NAME, "password")))

                input_user.clear()
                input_user.send_keys(cls.username)
                input_pass.clear()
                input_pass.send_keys(cls.password)
                try:
                    cls.guardar_captura(driver, name=f"cap_LOGIN_DEdge_2_{now()}", descripcion="Credenciales escritas")
                except Exception:
                    pass
                input_pass.send_keys(Keys.RETURN)

                wait.until(lambda d: "login" not in d.current_url)
                generate_log(f"Login completado en Selenium", BotLog.ROOMPRICE)
                logging.info("✅ Login completado en Selenium")
                try:
                    cls.guardar_captura(driver, name=f"cap_LOGIN_DEdge_3_{now()}", descripcion="Login completado en Selenium")
                except Exception:
                    pass
                    
                # Si aparece el aviso de dispositivo nuevo
                if cls.handle_new_device_prompt(driver):
                    logging.info("⌛ Esperando que el usuario ingrese el código en la base de datos...")
                    generate_log(f"Esperando que el usuario ingrese el código en la base de datos...", BotLog.ROOMPRICE)
                    code = None
                    max_wait = 300  # espera máxima 60s
                    start_time = time.time()

                    while time.time() - start_time < max_wait:
                        last_code = DEdgeCode.objects.order_by("-created_at").first()
                        if last_code:
                            code = last_code.code
                            generate_log(f"Código detectado en DB: {code}", BotLog.ROOMPRICE)
                            break
                        time.sleep(3)

                    if not code:
                        logging.error("⏳ No se recibió el código dentro del tiempo límite")
                        generate_log(f"No se recibió el código dentro del tiempo límite", BotLog.ROOMPRICE)
                        return None

                    try:
                        cls.guardar_captura(driver, name=f"cap_LOGIN_DEdge_4_{now()}", descripcion="Validacion de codigo")
                    except Exception:
                        pass

                    cls.write_html(driver.page_source, "page_factor2_code.html")

                    # --- Paso 3: Escribir y enviar el código ---
                    input_code = wait.until(EC.presence_of_element_located((By.ID, "form-code")))
                    input_code.clear()
                    input_code.send_keys(code)

                    try:
                        cls.guardar_captura(driver, name=f"cap_LOGIN_DEdge_5_{now()}", descripcion="Código escrito en el input")
                    except Exception:
                        pass

                    # Click en el botón de confirmar
                    #submit_btn = driver.find_element(By.ID, "submit-button")
                    #driver.execute_script("arguments[0].click();", submit_btn)
                    input_code.send_keys(Keys.RETURN)

                    wait.until(lambda d: "login" not in d.current_url)
                    try:
                        cls.guardar_captura(driver, name=f"cap_LOGIN_DEdge_6_{now()}", descripcion="Validacion de codigo")
                    except Exception:
                        pass
                    logging.info("✅ Código verificado y login completado")
                    generate_log(f"Código verificado y login completado", BotLog.ROOMPRICE)

            # Obtener cookies finales
            selenium_cookies = driver.get_cookies()
            final_cookies = {c["name"]: c["value"] for c in selenium_cookies}
            generate_log(f"Cookies finales: {str(final_cookies)}", BotLog.ROOMPRICE)
            logging.info(f"📌 Cookies finales: {final_cookies}")

            # Pasar cookies a requests.Session
            cls.session.cookies.clear()
            for name, value in final_cookies.items():
                cls.session.cookies.set(name, value, domain=".availpro.com")

            return final_cookies

        except Exception as e:
            generate_log(f"Error en Selenium login: {str(e)}", BotLog.ROOMPRICE)
            logging.error(f"❌ Error en Selenium login: {e}")
            return None

        finally:
            driver.quit()

    @classmethod
    def ensure_session(cls):
        """Verifica si la sesión es válida. Si no, hace login con Selenium."""
        generate_log(f"Verificando sesión actual...", BotLog.ROOMPRICE)
        logging.info("🔎 Verificando sesión actual...")
        resp = cls.session.get(cls.URL_TARGET)

        if cls.is_login_required(resp.text):
            generate_log(f"Sesión inválida, iniciando login con Selenium...", BotLog.ROOMPRICE)
            logging.info("🔒 Sesión inválida, iniciando login con Selenium...")
            final_cookies = cls.selenium_login(cls.session.cookies.get_dict())
            if final_cookies:
                generate_log(f"Sesión restablecida con nuevas cookies", BotLog.ROOMPRICE)
                logging.info("✅ Sesión restablecida con nuevas cookies")
                return True
            generate_log(f"❌ No se pudo restablecer sesión", BotLog.ROOMPRICE)
            logging.error("❌ No se pudo restablecer sesión")
            return False

        generate_log(f"Sesión válida con cookies actuales", BotLog.ROOMPRICE)
        logging.info("✅ Sesión válida con cookies actuales")
        return True

    @classmethod
    def login(cls, resp):
        logging.info("🔑 Obteniendo token de login...")
        #resp = cls.session.get(cls.URL_LOGIN)
        token = cls.get_verification_token(resp.text)
        if not token:
            raise Exception("No se pudo obtener el __RequestVerificationToken")
        logging.info(f"🔑 Token login: {token}")
        payload = {
            "__RequestVerificationToken": token,
            "login": cls.username,
            "IsQueryLogin": "False",
            "password": cls.password
        }

        headers = { 
            "content-type": "application/x-www-form-urlencoded",
            "referer": cls.URL_LOGIN,
            "origin": "https://login.availpro.com",
            "user-agent": "Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36"
        }

        logging.info("🔄 Enviando login...")
        response = cls.session.post(cls.URL_LOGIN, headers=headers, data=payload, allow_redirects=False)

        logging.info(cls.session.cookies.get_dict())

        cls.write_html(response.text, "login_template.html")

        logging.info(f"Status Code login: {response.status_code}")

        if response.status_code == 302 and not cls.is_login_required(response.text):
            logging.info("✅ Login exitoso")

            # ------- 302 de https://extranet.availpro.com/?token=_____wiRqQMY_n0gmccBKhIJ-lPEy4C0PUARoTJRkWwSNWcyCwjW2LHDos26PhAF0 ---------
            redirect_url = response.headers.get("Location")
            logging.info(f"➡️ Redirigiendo a: {redirect_url}")
            # Ahora seguimos el redirect manualmente
            redirect_resp = cls.session.get(redirect_url, allow_redirects=False)
            logging.info(f"Status Code login: {response.status_code}")
            logging.info(f"Header: {response.headers}")
            logging.info(cls.session.cookies.get_dict())
            logging.info(redirect_resp.text)
            if redirect_resp.status_code != 302:
                logging.error(f"⚠️ Error en redirect. Status: {redirect_resp.status_code}")
                return False

            # Verificamos si el contenido ya no es la página de login
            soup = BeautifulSoup(redirect_resp.text, "html.parser")
            if soup.find("form", {"id": "login-form"}):
                logging.error("🔒 Aún estamos en el formulario de login -> fallo de autenticación")
                return False
            
            # ---------- 302 de https://extranet.availpro.com/ -------------
            redirect_url = "https://extranet.availpro.com"+redirect_resp.headers.get("Location")
            logging.info(f"➡️ Redirigiendo a: {redirect_url}")
            # Ahora seguimos el redirect manualmente
            redirect_resp2 = cls.session.get(redirect_url, allow_redirects=False)
            logging.info(f"Status Code login: {response.status_code}")
            logging.info(f"Header: {response.headers}")
            logging.info(cls.session.cookies.get_dict())
            logging.info(redirect_resp2.text)
            if redirect_resp2.status_code != 302:
                logging.error(f"⚠️ Error en redirect. Status: {redirect_resp2.status_code}")
                return False

            # Verificamos si el contenido ya no es la página de login
            soup = BeautifulSoup(redirect_resp2.text, "html.parser")
            if soup.find("form", {"id": "login-form"}):
                logging.error("🔒 Aún estamos en el formulario de login -> fallo de autenticación")
                return False

            # ----- 200 https://extranet.availpro.com/Home?language=es-ES&FromLoginPage=True --------
            redirect_url = redirect_resp2.headers.get("Location")
            redirect_url = "https://extranet.availpro.com"+redirect_url if '/Login.aspx?ReturnUrl=' in redirect_url else redirect_url
                
            logging.info(f"➡️ Redirigiendo a: {redirect_url}")
            # Ahora seguimos el redirect manualmente
            redirect_resp3 = cls.session.get(redirect_url)
            logging.info(f"Status Code login: {response.status_code}")
            logging.info(f"Header: {response.headers}")
            logging.info(cls.session.cookies.get_dict())
            logging.info(redirect_resp2.text)
            if redirect_resp3.status_code != 200:
                logging.error(f"⚠️ Error en redirect. Status: {redirect_resp3.status_code}")
                return False

            # Verificamos si el contenido ya no es la página de login
            soup = BeautifulSoup(redirect_resp3.text, "html.parser")
            if soup.find("form", {"id": "login-form"}):
                logging.error("🔒 Aún estamos en el formulario de login -> fallo de autenticación")
                return False
            
            return True

        logging.info("⚠️ Error en login: revisa credenciales")
        return None
    
    @classmethod
    def get_price_by_date(cls, url):
        import requests
        from bs4 import BeautifulSoup

        response = requests.get(url, headers=cls.get_headers(), cookies=cls.get_cookies())
        soup = BeautifulSoup(response.text, 'html.parser')
        
        price_element = soup.find('span', class_='price')
        if price_element:
            return price_element.text.strip()
        return None
    
    @classmethod
    def mock_response(cls):
        class MockResponse:
            status_code = 200
            text = json.dumps({"message":"Rango no necesita actualizacion."})
        return MockResponse()

    @classmethod
    def set_price_by_date(cls, _date, prices):
        changes, status = cls.generate_changes(prices, _date)
        if not changes or len(changes) == 0:
            response = cls.mock_response()
            response.status_code = status
            return response
        headers = cls.get_headers(_date)
        # Construir primero el payload como dict
        planning_changes = {
            "startDate": _date,
            "Room": "0",
            "Rate": cls.RATE_ID,
            "Items": 12,
            "changes": changes
        }
        data = {"planningChanges": json.dumps(planning_changes)}
        logging.info(f"set_price_by_date: {str(data)}")
        generate_log(f"set_price_by_date: {str(data)}", BotLog.ROOMPRICE)
        response = cls.session.post(cls.URL, headers=headers, data=data)
        #response = cls.mock_response()
        #response.text = json.dumps({"message":"Mock response success"})
        return response

    @classmethod
    def set_price_by_date_and_type(cls, _date, prev_price, next_price, room_type):
        room_id = cls.get_type(room_type)
        headers = cls.get_headers()
        # Construir primero el payload como dict
        planning_changes = {
            "startDate": _date,
            "Room": "0",
            "Rate": cls.RATE_ID,
            "Items": 12,
            "changes": [
                {"Day": 0, "ArticleId": "0", "RoomId": int(room_id), "LineType": "RatePrice", "RateId": int(cls.RATE_ID), "PropertyId": 0, "OriginValue": prev_price, "NewValue": next_price, "NewOverridingValue": next_price, "Target": "Price"}
            ]
        }
        data = {"planningChanges": json.dumps(planning_changes)}
        response = cls.session.post(cls.URL, headers=headers, data=data)
        return response
    
    @classmethod
    def generate_changes(cls, prices, _date):
        # ✅ Si no hay precios, no hacemos la consulta
        if not prices or all(not v for v in prices.values()):
            # Retornamos lista vacía y status 204 (sin contenido)
            return [], 204  
        response = cls.get_prev_price(_date) # sigue siendo igual..
        generate_log(f"generate_changes: Status Page: {response.status_code}", BotLog.ROOMPRICE)
        logging.info(f"generate_changes : Status Page: {response.status_code}")
        if response.status_code != 200:
            cls.write_html(response.text, "page_d-edge_error.html")
            return [], response.status_code
        cls.write_html(response.text, "page_d-edge.html")
        prev_prices = cls.get_prev_price_source(response.text) # cambio necesario para obtener los precios previos de todo el rango.
        generate_log(f"generate_changes : Status Page: {str(prev_prices)}", BotLog.ROOMPRICE)
        logging.info(f"generate_changes: {str(prev_prices)}")
        changes = []
        for key, value in prices.items():
            if value:
                for room_type, price in value.items():
                    room_id = cls.get_type(room_type)
                    changes.append(
                        {
                            "Day": int(price["day"]), 
                            "ArticleId": "0", 
                            "RoomId": int(room_id), 
                            "LineType": "RatePrice", 
                            "RateId": int(cls.RATE_ID), 
                            "PropertyId": 0, 
                            "OriginValue": prev_prices[str(price["day"])][room_id], 
                            "NewValue": price["next_price"], 
                            "NewOverridingValue": price["next_price"], 
                            "Target": "Price"
                        }
                    )
        return changes, response.status_code
    
    @classmethod
    def get_prev_price(cls, _date):
        headers = cls.get_headers(_date)
        response = cls.session.get(cls.URL_GET.replace("DATE", _date), headers=headers)
        return response
    
    @classmethod
    def get_prev_price_source(cls, content):
        soup = BeautifulSoup(content, "html.parser")
        result = {}
        # Buscar filas con type="RatePrice"
        rate_rows = soup.find_all("tr", {"type": "RatePrice"})
        for row in rate_rows:
            room_id = row.get("roomid")
            if not room_id:
                continue
            # Buscar solo <td> con isMealPlanRate="False"
            tds = row.find_all("td", {
                "day": True,
                "originvalue": True,
                "ismealplanrate": "False"  # filtro clave
            })
            for td in tds:
                day = td["day"]
                origin_value = td["originvalue"]
                # Filtrar solo valores numéricos válidos
                if not origin_value.isdigit():
                    continue  # Ignorar Undefined, texto o vacíos
                if day not in result:
                    result[day] = {}
                result[day][room_id] = origin_value  # Guardamos como string, lo puedes convertir si necesitas número
        return result
    
    @classmethod
    def write_html(cls, content, filename):
        """Guardar el contenido completo en un archivo HTML."""
        with open(filename, "w", encoding="utf-8") as file:
            file.write(content)
        
    @classmethod
    def guardar_captura(cls, driver, carpeta="media/capturas", name="", descripcion=""):
        # Crear carpeta si no existe
        if not os.path.exists(carpeta):
            os.makedirs(carpeta)

        # Generar nombre con timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"{name}_{timestamp}.png" if name else f"captura_{timestamp}.png"
        ruta_completa = os.path.join(carpeta, nombre_archivo)

        # Guardar captura
        driver.save_screenshot(ruta_completa)
        generate_log(f"[✓] Captura guardada en: {ruta_completa}", BotLog.BOOKING)

        try:
            ScreenshotLog.objects.create(
                descripcion = descripcion,
                created = now(),
                imagen = "capturas/"+nombre_archivo,
            )
        except Exception as e:
            logging.info(f"[-] Error create Screen: {e}")
            try:
                ScreenshotLog.objects.create(
                    descripcion = descripcion,
                    created = now(),
                    imagen = "capturas/"+nombre_archivo,
                )
            except Exception as e:
                logging.info(f"[-] Error create Screen: {e}")

if __name__ == "__main__":
    d_edge = DEdge()
    #d_edge.set_price_by_date_and_type("2026-02-01", "95", "94", "0")

    # test generate changes
    #prices = {"0": {"prev_price":"94", "next_price":"95"}}
    #changes = d_edge.generate_changes(prices)
    #logging.info(changes)
    response = d_edge.get_prev_price("2026-02-01")
    prices = d_edge.get_prev_price_source(response.text)
    logging.info(prices)
    #d_edge.write_html(response.text, "test.html")
    