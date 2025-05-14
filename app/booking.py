from bs4 import BeautifulSoup
import random
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.keys import Keys
from time import sleep
import pandas as pd
import logging
import json
from datetime import datetime as dt
from .now_date import now
import datetime
import re
from .models import *
import os
import platform
from urllib.parse import urlencode

_logging = logging.basicConfig(filename="logger.log", level=logging.INFO)

pattern = r"\b(19\d\d|20\d\d)[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])\b"
def search_date(text):
    return re.findall(pattern, text)

def check_finish_process()-> bool:
    status = False
    try:
        status = BotAutomatization.objects.last().active
    except Exception as e:
        try:
            status = BotAutomatization.objects.last().active
        except Exception as e:
            pass
    return status

class BookingSearch:
    @classmethod
    def _driver_chrome(cls, url) -> None:
        cls._url = url
        options = webdriver.ChromeOptions()
        #options.add_argument("headless")
        #options.add_argument("disable-gpu")
        #options.add_argument("no-sandbox")

        return webdriver.Chrome(executable_path=os.path.abspath("chromedriver.exe"), options=options)

    @classmethod
    def _driver_firefox(cls, url) -> None:
        cls._url = url
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        #options.add_argument("-private")  # Modo incógnito
        options.set_preference("browser.privatebrowsing.autostart", True)

        return webdriver.Firefox(executable_path=os.path.abspath("geckodriver"), options=options)
    
    @classmethod
    def _driver(cls, url) -> None:
        if platform.system() == "Windows":
            return cls._driver_chrome(url)
        else:
            return cls._driver_firefox(url)

    @classmethod
    def controller(cls, driver, process:ProcessActive=None, search_name="", general_search_to_name=None, date_from="", date_end="", stop_event=None):
        try:#https://www.booking.com/searchresults.es.html?ss=Madrid, España&label=gen173nr-1FCAQoggI49ANIClgEaEaIAQGYAQq4ARjIAQ_YAQHoAQH4AQKIAgGoAgS4AsCnk8EGwAIB0gIkMjhkMzU1ODQtZWJkMS00OTliLWEzNjQtYzNiYWYwY2UxOGRk2AIF4AIB&aid=304142&lang=es&sb=1&src_elem=sb&src=searchresults&dest_id=-390625&dest_type=city&ac_position=0&ac_click_type=b&ac_langcode=es&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=befc7b60a9b1024c&ac_meta=GhBiZWZjN2I2MGE5YjEwMjRjIAAoATICZXM6D01hZHJpZCwgRXNwYcOxYUAASgBQAA%3D%3D&checkin=2025-05-28&checkout=2025-05-29&group_adults=5&no_rooms=1&group_children=0
            def check_params(url, clave):
                # Usa expresión regular para encontrar el valor exacto del parámetro sin decodificar
                match = re.search(rf"[?&]{clave}=([^&]+)", url)
                if match:
                    return match.group(1)
                return None

            for i in range(3):
                _date_end = dt(int(str(date_end).split("-")[0]), int(str(date_end).split("-")[1]), int(str(date_end).split("-")[2]))
                _now = dt(int(str(date_from).split("-")[0]), int(str(date_from).split("-")[1]), int(str(date_from).split("-")[2]))

                driver.get(cls._url)
                driver.implicitly_wait(15)
                driver.delete_all_cookies()
                sleep(5)
                #logging.info(driver.current_url)
                generate_log(f"[+] {str(process.occupancy)} | {str(process.start)} | Url inicial: {driver.current_url} {_now}", BotLog.BOOKING)
                #if process.type_proces == 1:
                try:
                    _button = driver.find_element_by_xpath("//button[@id='onetrust-accept-btn-handler']")
                    _button.click()
                except NoSuchElementException as e:
                    logging.info(f"[-] {now()} Error in button cookies, element not fount")
                except ElementClickInterceptedException as e:
                    logging.info(f"[-] {now()} Error in button cookies, element not clicked")
                    
                # Search
                sleep(2)
                search = driver.find_element_by_xpath("//input[@name='ss']")
                search.send_keys(Keys.CONTROL + "a")  # Selecciona todo el texto
                search.send_keys(Keys.DELETE)  # Elimina el texto seleccionado
                sleep(1)
                # Escribe el texto en el campo de búsqueda
                #logging.info(f"Search name or city: {search_name} {_now}")
                generate_log(f"[+] {str(process.occupancy)} | {str(process.start)} |  Actualizando Datos: {search_name} {_now}", BotLog.BOOKING)
                search.send_keys(search_name)
                sleep(1)
                # Confirma con ENTER
                search.send_keys(Keys.RETURN)
                sleep(1)
                cont = 0

                _date_elem = _now
                _now += datetime.timedelta(days=1)

                _url_performance = driver.current_url  # Inicialización
                if check_params(_url_performance, "label"):
                    generate_log(f"[✓] Parámetro 'label' detectado en intento {i+1} | {str(process.occupancy)} | {str(process.start)}", BotLog.BOOKING)
                    break
                else:
                    generate_log(f"[-] Parámetro 'label' no presente en intento {i+1} | {str(process.occupancy)} | {str(process.start)}", BotLog.BOOKING)
            try:
                generate_log(f"[+] {str(process.occupancy)} | {str(process.start)} | Url inicial2: {_url_performance} {_now}", BotLog.BOOKING)
                while True:
                    generate_log(f"[+] {str(process.occupancy)} | {str(process.start)} | Actualizando Datos: {search_name} - Date: {_now}", BotLog.BOOKING)
                    if not check_finish_process() or (stop_event and stop_event.is_set()):
                        generate_log(f"[+] {now()} | {str(process.occupancy)} | {str(process.start)} | Deteniendo ejecución. Search: {search_name} - Date: {_now}...", BotLog.BOOKING)
                        break
                    
                    # Reemplazar o agregar los parámetros manualmente
                    if "ss=" in _url_performance:
                        _url_performance = re.sub(r"ss=[^&]*", f"ss={search_name}", _url_performance)
                    else:
                        _url_performance += f"&ss={search_name}"

                    if "group_adults=" in _url_performance:
                        _url_performance = re.sub(r"group_adults=\d+", f"group_adults={process.occupancy}", _url_performance)
                    else:
                        _url_performance += f"&group_adults={process.occupancy}"

                    if "checkin=" in _url_performance:
                        _url_performance = re.sub(r"checkin=\d{4}-\d{2}-\d{2}", f"checkin={_date_elem.date()}", _url_performance)
                    else:
                        _url_performance += f"&checkin={_date_elem.date()}"

                    if "checkout=" in _url_performance:
                        _url_performance = re.sub(r"checkout=\d{4}-\d{2}-\d{2}", f"checkout={_now.date()}", _url_performance)
                    else:
                        _url_performance += f"&checkout={_now.date()}"
                    driver.get(_url_performance)
                    driver.implicitly_wait(15)
                    generate_log(f"[+] {str(process.occupancy)} | {str(process.start)} | Url Performance: {_url_performance} {_now}", BotLog.BOOKING)
                    #logging.info(f"[-] {now()} - {search_name} - {_date_elem.date()} - {_now.date()} - S:{process.start} - O:{process.occupancy} - {driver.current_url}")

                    #if process.type_proces == 1:
                    try:
                        if cont <= 2:
                            _button = driver.find_element_by_xpath("//button[@aria-label='Ignorar información sobre el inicio de sesión.']")
                            _button.click()
                            #logging.info(f"[+] {now()} Click button modal success: {_date_elem.date()} - {_now.date()} - S:{process.start} - O:{process.occupancy}")
                    except NoSuchElementException as e:
                        logging.info(f"[-] {now()} Error in button Modal, not fount")
                    except ElementClickInterceptedException as e:
                        logging.info(f"[-] {now()} Error in button Modal, element not clicked")
                    except Exception as e:
                        logging.info(f"[-] {now()} Error in button Modal general: "+str(e))
                    sleep(3)
                    if process.type_proces == 1:
                        #try:
                        #    cls.guardar_captura(driver, descripcion=f"cap_booking_{str(process.start)}_{_now.date()}")
                        #except Exception as e:
                        #    pass
                        try:
                            _soup_elements = BeautifulSoup(driver.page_source, "html.parser")
                            elements = _soup_elements.find_all("input", {"type": "checkbox"})
                            for s in elements:
                                #logging.info(f"[+] {now()} - {str(process.start)} stars - Input: {s.get('aria-label')}")
                                if str(process.start)+" stars" == str(s.get('aria-label')).split(":")[0].strip() or str(process.start)+" stars" == str(s.get('aria-label')).split("/")[0].strip() or str(process.start)+" estrellas" == str(s.get('aria-label')).split(":")[0].strip():# or str(process.start)+" stars" 
                                    #logging.info(f"[+] {now()} - Stars - {_date_elem.date()} - {_now.date()} - O:{process.occupancy} - S:{str(process.start)} stars - Input: {s}")
                                    check_start = driver.find_element_by_xpath("//input[@id='"+str(s.get("id"))+"']")
                                    try:
                                        driver.execute_script("arguments[0].scrollIntoView(true);", check_start)
                                        check_start.click()
                                    except ElementClickInterceptedException:
                                        driver.execute_script("arguments[0].click();", check_start)
                                        sleep(2)
                                    generate_log(f"[+] {now()} Click button start success: {_date_elem.date()} | {_now.date()} | S:{process.start} | O:{process.occupancy}", BotLog.HISTORY)
                                    #logging.info(f"[+] {now()} Click button start success - {_date_elem.date()} - {_now.date()} - S:{process.start} - O:{process.occupancy}")
                                    break
                                    
                        except NoSuchElementException as e:
                            logging.info(f"[-] {now()} Error in start button, not fount")
                            generate_log(f"[-] {now()} Error in start button, not fount", BotLog.HISTORY)
                            try:
                                _soup_elements = BeautifulSoup(driver.page_source, "html.parser")
                                elements = _soup_elements.find_all("input")
                                for s in elements:
                                    #logging.info(f"[+] {now()} - Log2 - {str(start)} stars - Input: {s.get('aria-label')}")
                                    if str(process.start)+" stars" == str(s.get('aria-label')).split(":")[0].strip() or str(process.start)+" stars" == str(s.get('aria-label')).split("/")[0].strip() or str(process.start)+" estrellas" == str(s.get('aria-label')).split(":")[0].strip():#or str(process.start)+" stars"
                                        #logging.info(f"[+] {now()} - Stars - O:{process.occupancy} - S:{str(process.start)} stars - Input: {s}")
                                        check_start = driver.find_element_by_xpath("//input[@id='"+str(s.get("id"))+"']")
                                        try:
                                            driver.execute_script("arguments[0].scrollIntoView(true);", check_start)
                                            check_start.click()
                                        except ElementClickInterceptedException:
                                            driver.execute_script("arguments[0].click();", check_start)
                                            sleep(2)
                                        generate_log(f"[+] {now()} Click button start success: {_date_elem.date()} | {_now.date()} | S:{process.start} | O:{process.occupancy}", BotLog.HISTORY)
                                        #logging.info(f"[+] {now()} Click button start success - {_date_elem.date()} - {_now.date()}  - S:{process.start} - O:{process.occupancy}")
                                        break
                                        
                            except NoSuchElementException as e:
                                logging.info(f"[-] {now()} Error in start button - reintento 2, not fount")
                            except ElementClickInterceptedException as e:
                                logging.info(f"[-] {now()} Error in start button, element not clicked2")
                            except Exception as e:
                                logging.info(f"[-] {now()} Error in start button general: "+str(e))
                        except ElementClickInterceptedException as e:
                            logging.info(f"[-] {now()} Error in start button, element not clicked1")
                        except Exception as e:
                            logging.info(f"[-] {now()} Error in start button general: "+str(e))
                        sleep(3)
                        try:
                            _soup_elements = BeautifulSoup(driver.page_source, "html.parser")
                            elements = _soup_elements.find_all("input", {"type": "checkbox"})
                            for s in elements:
                                #logging.info(f"{s}")
                                if "Hoteles" == str(s.get('aria-label')).split(":")[0].strip() or "Hotels" == str(s.get('aria-label')).split(":")[0].strip():
                                    #logging.info(f"{s}")
                                    check_hotel = driver.find_element_by_xpath("//input[@id='"+str(s.get("id"))+"']")
                                    try:
                                        driver.execute_script("arguments[0].scrollIntoView(true);", check_hotel)
                                        sleep(2)  # Permitir que el desplazamiento se complete
                                    except Exception as e:
                                        logging.info(f"[-] {now()} Error durante el scroll: {e}")
                                    try:
                                        check_hotel.click()
                                    except Exception as e:
                                        logging.info(f"[-] {now()} Error al hacer click, intentando con JavaScript: {e}")
                                        driver.execute_script("arguments[0].click();", check_hotel)
                                        sleep(2)
                                    generate_log(f"[+] {now()} Click button hoteles success: {_date_elem.date()} | {_now.date()} | S:{process.start} | O:{process.occupancy}", BotLog.HISTORY)   
                                    #logging.info(f"[+] {now()} Click button hoteles success: {_date_elem.date()} - {_now.date()}  - S:{process.start} - O:{process.occupancy}")
                                    break
                        except Exception as e:
                            logging.info(f"[-] {now()} Error in Hoteles button general: "+str(e))

                        sleep(3)
                        try:
                            dropdown_price = driver.find_element_by_xpath("//button[@data-testid='sorters-dropdown-trigger']")
                            try:
                                driver.execute_script("arguments[0].scrollIntoView(true);", dropdown_price)
                                dropdown_price.click()
                                sleep(1)
                            except ElementClickInterceptedException as e02:
                                driver.execute_script("arguments[0].click();", dropdown_price)
                                sleep(2)
                            #logging.info(f"[+] {now()} Click button dropdown success: - {_date_elem.date()} - {_now.date()}  - S:{process.start} - O:{process.occupancy}")
                            #driver.find_element_by_xpath("//div[@data-testid='sorters-dropdown']")

                            # div_li = driver.find_elements_by_xpath("//div[@data-testid='sorters-dropdown']")
                            # for dl in div_li:
                            #     logging.info(f"[+] {now()} Element: {dl.text}")
                            check_price = driver.find_element_by_xpath("//button[@data-id='price']")
                            try:
                                driver.execute_script("arguments[0].scrollIntoView(true);", check_price)
                                check_price.click()
                            except ElementClickInterceptedException as e2:
                                driver.execute_script("arguments[0].click();", check_price)
                                sleep(2)
                            generate_log(f"[+] {now()} Click button price success: {_date_elem.date()} | {_now.date()} | S:{process.start} | O:{process.occupancy}", BotLog.HISTORY)   
                            #logging.info(f"[+] {now()} Click button price success: - {_date_elem.date()} - {_now.date()}  - S:{process.start} - O:{process.occupancy}")
                        except NoSuchElementException as e:
                            logging.info(f"[-] {now()} Error in button price, not fount")
                        except ElementClickInterceptedException as e:
                            logging.info(f"[-] {now()} Error in price button, element not clicked")
                        except Exception as e:
                            logging.info(f"[-] {now()} Error in price button general: "+str(e))

                    sleep(3)
                    #try:
                    #    cls.guardar_captura(driver, descripcion=f"cap_booking_{str(process.start)}_{_now.date()}")
                    #except Exception as e:
                    #    pass
                    # Items booking search
                    items = driver.find_elements_by_xpath("//div[@data-testid='property-card']")
                    #logging.info(f"[+] {now()} Elementos encontrados: {len(items)} - {_date_elem.date()} - {_now.date()}  - S:{process.start} - O:{process.occupancy}")
                    total_search = 0
                    try:
                        total_search = str(driver.find_element_by_xpath("//h1[@aria-live='assertive']").text).split(": ")[1].split(" ")[0].strip().replace(".", "")
                        #logging.info(f"[+] {now()} Total search success: {total_search} - {_date_elem.date()} - {_now.date()}  - S:{process.start} - O:{process.occupancy}")
                        generate_log(f"[+] {now()} Total search success: {total_search} - {_date_elem.date()} - {_now.date()}  - S:{process.start} - O:{process.occupancy}", BotLog.HISTORY)   
                        total_search = total_search.replace(",", "").replace(".", "")
                    except NoSuchElementException as e:
                        logging.info(f"[-] {now()} Error in get total_search, not fount")
                    except ElementClickInterceptedException as e:
                        logging.info(f"[-] {now()} Error in total_search, element not clicked1")
                    except Exception as e:
                        logging.info(f"[-] {now()} Error in total_search general: "+str(e))

                    if process.type_proces == 1:
                        try:
                            comp = Complement.objects.filter(date_from=str(_date_elem.date()), occupancy=process.occupancy, start=process.start).first()
                            if not comp:
                                Complement.objects.create(
                                    total_search = total_search,
                                    occupancy = process.occupancy,
                                    start = process.start,
                                    date_from = str(_date_elem.date()),
                                    date_to = str(_now.date()),
                                    updated = now(),
                                    created = now()
                                )
                            else:
                                comp.total_search = total_search
                                comp.updated = now()
                                comp.created = now()
                                comp.save()
                            
                            if total_search == 0:
                                try:
                                    cls.guardar_captura(driver, name=f"cap_booking_{str(process.occupancy)}_{str(process.start)}_{_now.date()}", descripcion=_url_performance+f" | {total_search} | {str(process.occupancy)} | {str(process.start)}")
                                except Exception as e:
                                    pass
                        except Exception as er2:
                            logging.info(f"[-] {now()} Error 228: "+str(er2))

                    try:
                        #logging.info(f"[-] {now()} - {search_name} - {_date_elem.date()} - {_now.date()} - S:{process.start} - O:{process.occupancy} - {driver.current_url} - {_url_performance}")
                        generate_log(f"[-] {now()} | {search_name} | {_date_elem.date()} | {_now.date()} | S:{process.start} | O:{process.occupancy} | {driver.current_url} | {_url_performance}", BotLog.HISTORY)   
                        for position in process.position:
                            cls.get_data_to_text(items[position], _date_elem, _now, process.occupancy, position, total_search, process, search_name)
                    except Exception as e:
                        logging.info(f"[-] {now()} Error 170: "+str(e))
                    sleep(1)

                    if process.type_proces == 1:
                        for __item in items:
                            try:
                                cls.check_name_calling(__item, _date_elem, _now, process.occupancy, general_search_to_name)
                            except Exception as e:
                                logging.info(f"[-] {now()} Error 295: "+str(e))
                    if _date_elem.date() >= _date_end.date():
                        break
                    cont += 1

                    #if int(total_search) > 0:
                    _date_elem = _now
                    _now += datetime.timedelta(days=1)
                    generate_log(f"[+] Actualizado: {search_name} - Date: {_now}", BotLog.BOOKING)
            except Exception as e2:
                logging.info(f"[-] {now()} Error 262: "+str(e2))
                generate_log(f"[-] Error 262: "+str(e2), BotLog.BOOKING)
        except Exception as e02:
            logging.info(f"[-] {now()} Error General 264: "+str(e02))
            generate_log(f"[-] Error General 264: "+str(e02), BotLog.BOOKING)

    @classmethod
    def filter_data(cls, data):
        data2 = []
        for d in data:
            if d["start"] == 4:
                data2.append(d)

        return data2

    @classmethod
    def search_price(cls, html):
        soup = BeautifulSoup(html, "html.parser")
        price = soup.find("span", {"data-testid":"price-and-discounted-price"})
        #print(price.text)
        return price.text

    @classmethod
    def search_start(cls, html):
        soup = BeautifulSoup(html, "html.parser")
        container_start = soup.find("div", {"data-testid":"rating-stars"})
        result = 0
        if not container_start:
            container_start = soup.find("div", {"data-testid":"rating-squares"})
        if container_start:
            starts = container_start.find_all("span", {"aria-hidden":"true"})
            result = len(starts)

        return result
    
    @classmethod
    def search_title(cls, html):
        soup = BeautifulSoup(html, "html.parser")
        title_and_link = soup.find("h3")
        title = title_and_link.find("div", {"data-testid":"title"}).text
        link = title_and_link.find("a", {"data-testid":"title-link"}).get("href")
        return title, link
    
    @classmethod
    def search_address(cls, html):
        soup = BeautifulSoup(html, "html.parser")
        address = soup.find("span", {"data-testid":"address"})
        if address:
            address = address.text
        distance = soup.find("span", {"data-testid":"distance"})
        if distance:
            distance = distance.text
        return address if address else "", distance if distance else ""
    
    @classmethod
    def search_description(cls, html):
        soup = BeautifulSoup(html, "html.parser")
        items = soup.find_all("div", {"class":"abf093bdfe"})
        result = ""
        for item in items:
            #print(item.get("class"))
            if len(item.get("class")) == 1:
                if item.get("class")[0] == "abf093bdfe":
                    #print(item)
                    result = item.text
                    break
        return result

    @classmethod
    def search_img(cls, html):
        soup = BeautifulSoup(html, "html.parser")
        img = soup.find("img", {"data-testid":"image"})
        #print(img)
        return img.get("src")
    
    @classmethod
    def pagination(cls, html, i):
        soup = BeautifulSoup(html, "html.parser")
        pg = soup.find("div", {"data-testid":"pagination"})
        buttons = pg.find_all("button")
        result = ""
        _pg = ""
        for b in buttons[1:]:
            if int(str(b.text).strip()) == i:
                result = b.get("class")
                break
        return result, int(str(buttons[-2].text).strip())
    
    @classmethod
    def write_file(cls, data, name):
        json_object = json.dumps(data, indent=4)
        # Writing to sample.json
        with open("media/json/"+name+".json", "w") as outfile:
            outfile.write(json_object)

    @classmethod
    def visit_page(cls, url, driver:webdriver.Chrome):
        driver.get(url)
        driver.implicitly_wait(15)

    @classmethod
    def convert_to_json(cls, occupancy, item, _date_elem, _now):
        item_dict = {
            "start": 0,
            "price": "0",
            "occupancy": occupancy,
            "date_from": str(_date_elem.date()),
            "date_to":  str(_now.date()),
            "title": "",
            "address": "",
            "distance": "",
            "description": "",
            "img": "",
            "link": ""
        }
        html = item.get_attribute("innerHTML")
        try:
            item_dict["start"] = cls.search_start(html)
        except Exception as e0:
            logging.info(f"[-] {now()} Error in Get start")
        try:
            item_dict["title"], item_dict["link"] = cls.search_title(html)
        except Exception as e3:
            logging.info(f"[-] {now()} Error in Get title and link")
        try:
            item_dict["address"], item_dict["distance"] = cls.search_address(html)
        except Exception as e4:
            logging.info(f"[-] {now()} Error in Get address")
        try:
            item_dict["description"] = cls.search_description(html)
        except Exception as _e2:
            logging.info(f"[-] {now()} Error in Get description")
        try:
            item_dict["img"] = cls.search_img(html)
        except Exception as e5:
            logging.info(f"[-] {now()} Error in Get img")
        try:
            item_dict["price"] = cls.search_price(html)
        except Exception as e6:
            logging.info(f"[-] {now()} Error in Get price")
        return item_dict

    @classmethod
    def get_data_to_text(cls, item, _date_elem, _now, occupancy, position, total_search, process:ProcessActive, search_name):
        try:
            item_dict = cls.convert_to_json(occupancy, item, _date_elem, _now)
            if process.type_proces == 1:
                if item_dict["start"] != 0:
                    bg = Booking.objects.filter(
                        title=item_dict["title"], 
                        start=item_dict["start"]
                    ).first()
                    if not bg:
                        bg = Booking.objects.create(
                            start = item_dict["start"],
                            title = item_dict["title"],
                            link = item_dict["link"],
                            address = item_dict["address"],
                            distance = item_dict["distance"],
                            description = item_dict["description"],
                            img = item_dict["img"],
                            updated = now(),
                            created = now()
                        )
                    else:
                        bg.start = item_dict["start"]
                        bg.title = item_dict["title"]
                        bg.link = item_dict["link"]
                        bg.address = item_dict["address"]
                        bg.distance = item_dict["distance"]
                        bg.description = item_dict["description"]
                        bg.img = item_dict["img"]
                        bg.updated = now()
                        bg.save()

                    _available = AvailableBooking.objects.filter(
                        date_from=item_dict["date_from"], 
                        date_to=item_dict["date_to"], 
                        position=position, 
                        occupancy=occupancy, 
                        start=item_dict["start"]
                    ).first()
                    if not _available:
                        _available = AvailableBooking.objects.create(
                            date_from = item_dict["date_from"],
                            date_to = item_dict["date_to"],
                            booking = bg,
                            position = position,
                            total_search = int(total_search),
                            price = item_dict["price"],
                            updated = now(),
                            created = now(),
                            occupancy = occupancy,
                            start = item_dict["start"]
                        )
                    else:
                        _available.total_search = int(total_search)
                        _available.active = True
                        _available.updated = now()
                        _available.price = item_dict["price"]
                        _available.booking = bg
                        _available.save()
                    #logging.info(item_dict)
                else:
                    logging.info(f"Data Error Start {item_dict['start']} - O: {occupancy}: {item_dict}")
            else:
                cls.save_name_hotel(item_dict, occupancy, search_name)
                
                #logging.info(f"[+] Data Start success: {item_dict}")

        except Exception as e:
            logging.info(f"[-] {now()} Error General data 537: {str(e)} | {item_dict}")
            generate_log(f"[-] Error General data 539: "+str(e), BotLog.BOOKING)
        
        return item_dict

    @classmethod
    def check_name_calling(cls, item, _date_elem, _now, occupancy, general_search_to_name):
        try:
            if general_search_to_name:
                item_dict = cls.convert_to_json(occupancy, item, _date_elem, _now)
                #logging.info(f"[+] Check |{item_dict['title']}| in positions. O: {occupancy} | {item_dict['date_from']}")
                #generate_log(f"[+] Check |{item_dict['title']}| in positions. O: {occupancy} | {item_dict['date_from']}", BotLog.BOOKING)
                cls.check_name_in_position(general_search_to_name, item_dict, occupancy)
        except Exception as e:
            logging.info(f"[-] {now()} Error check name General data 528: "+str(e))
            generate_log(f"[-] Error check name General data 528: "+str(e), BotLog.BOOKING)

    @classmethod
    def check_name_in_position(cls, general_search_to_name, item_dict, occupancy):
        try:
            for gs in general_search_to_name:
                if item_dict["title"] == gs.city_and_country:
                    status = False
                    for p in gs.proces_active.all():
                        if occupancy == p.occupancy:
                            status = True
                            break
                    if status:
                        #logging.info(f"[+] Save |{item_dict['title']}| in positions. O: {occupancy} | {item_dict['date_from']} from Name hotel")
                        generate_log(f"[+] Guardado |{item_dict['title']}| in positions. O: {occupancy} | {item_dict['date_from']} - para nombre de hotel", BotLog.BOOKING)
                        cls.save_name_hotel(item_dict, occupancy, gs.city_and_country)
                    break
        except Exception as e:
            logging.info(f"[-] {now()} Error General data Check name 557: "+str(e))
            generate_log(f"[-] {now()} Error General data Check name 557: "+str(e), BotLog.BOOKING)

    @classmethod
    def save_name_hotel(cls, item_dict, occupancy, search_name):
        price_with_name_hotel = PriceWithNameHotel.objects.filter(title = search_name, date_from = item_dict["date_from"], occupancy = occupancy).first()
        if search_name == item_dict["title"]:
            if not price_with_name_hotel:
                price_with_name_hotel = PriceWithNameHotel.objects.create(
                    start = item_dict["start"],
                    title = item_dict["title"],
                    link = item_dict["link"],
                    address = item_dict["address"],
                    distance = item_dict["distance"],
                    description = item_dict["description"],
                    img = item_dict["img"],
                    updated = now(),
                    created = now(),
                    date_from = item_dict["date_from"],
                    date_to = item_dict["date_to"],
                    price = item_dict["price"],
                    occupancy = occupancy
                )
            else:
                price_with_name_hotel.price = item_dict["price"]
                price_with_name_hotel.save()
        else:
            price_with_name_hotel.price = 0
            price_with_name_hotel.save()

    @classmethod
    def close(cls, driver):
        driver.close()

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
    booking = BookingSearch()
    _driver = booking._driver()
    booking.controller(_driver, date_end=["2024", "12", "31"])