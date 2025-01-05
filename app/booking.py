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
import datetime
import re
from .models import *
import os
import platform

_logging = logging.basicConfig(filename="logger.log", level=logging.INFO)

pattern = r"\b(19\d\d|20\d\d)[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])\b"
def search_date(text):
    return re.findall(pattern, text)

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

        options.set_preference("browser.privatebrowsing.autostart", True)

        return webdriver.Firefox(executable_path=os.path.abspath("geckodriver"), options=options)
    
    @classmethod
    def _driver(cls, url) -> None:
        if platform.system() == "Windows":
            return cls._driver_chrome(url)
        else:
            return cls._driver_firefox(url)

    @classmethod
    def controller(cls, driver, _now:dt.now=dt.now(), process:ProcessActive=None, search_name=""):
        try:
            driver.get(cls._url)
            driver.implicitly_wait(15)
            driver.delete_all_cookies()
            sleep(5)
            #logging.info(driver.current_url)
            #if process.type_proces == 1:
            try:
                _button = driver.find_element_by_xpath("//button[@id='onetrust-accept-btn-handler']")
                _button.click()
            except NoSuchElementException as e:
                logging.info(f"[-] {dt.now()} Error in button cookies, element not fount")
            except ElementClickInterceptedException as e:
                logging.info(f"[-] {dt.now()} Error in button cookies, element not clicked")
                
            # Search
            sleep(2)
            search = driver.find_element_by_xpath("//input[@name='ss']")
            search.send_keys(Keys.CONTROL + "a")  # Selecciona todo el texto
            search.send_keys(Keys.DELETE)  # Elimina el texto seleccionado
            sleep(1)
            # Escribe el texto en el campo de búsqueda
            logging.info(f"Search name or city: {search_name} {_now}")
            search.send_keys(search_name)
            sleep(1)
            # Confirma con ENTER
            search.send_keys(Keys.RETURN)
            sleep(1)
            
            _date_end = dt(int(str(process.date_end).split("-")[0]), int(str(process.date_end).split("-")[1]), int(str(process.date_end).split("-")[2]))
            cont = 0

            _date_elem = _now
            _now += datetime.timedelta(days=1)

            try:
                _current_url = driver.current_url
                while True:
                    process = ProcessActive.objects.filter(pk = process.pk).first()
                    if not process.currenct:
                        break
                    
                    if "ss" not in _current_url:
                        _url_performance = _url_performance + f"ss={search_name}"

                    if "group_adults" in _current_url:
                        #logging.info("[+] group_adults encontrado dentro de la url...")
                        _url_performance = _current_url.replace("group_adults=2", "group_adults="+str(process.occupancy))#.replace(f"checkin={str(_date_elem.date())}", f"checkin={str(_date_elem.date())}").replace(f"checkout={_now.date()}", f"checkout={_now.date()}")
                    else:
                        _url_performance = _url_performance + f"&group_adults={str(process.occupancy)}"

                    # Reemplazar las fechas en la URL usando expresiones regulares
                    if "checkin" in _current_url:
                        _url_performance = re.sub(r"checkin=\d{4}-\d{2}-\d{2}", f"checkin={str(_date_elem.date())}", _url_performance)
                    else:
                        _url_performance = _url_performance + f"&checkin={str(_date_elem.date())}"

                    if "checkout" in _current_url:
                        _url_performance = re.sub(r"checkout=\d{4}-\d{2}-\d{2}", f"checkout={_now.date()}", _url_performance)
                    else:
                        _url_performance = _url_performance + f"&checkout={_now.date()}"
                    #else:
                    #    logging.info("[+] group_adults no encontrado dentro de la url...")
                    #    _url_performance = cls._url + f"ss={search_name}&checkin={str(_date_elem.date())}&checkout={str(_now.date())}&group_adults={str(process.occupancy)}&no_rooms=1&group_children=0"
                    driver.get(_url_performance)
                    driver.implicitly_wait(15)
                    #logging.info(f"[-] {dt.now()} - {search_name} - {_date_elem.date()} - {_now.date()} - S:{process.start} - O:{process.occupancy} - {driver.current_url}")

                    #if process.type_proces == 1:
                    try:
                        if cont <= 2:
                            _button = driver.find_element_by_xpath("//button[@aria-label='Ignorar información sobre el inicio de sesión.']")
                            _button.click()
                            #logging.info(f"[+] {dt.now()} Click button modal success: {_date_elem.date()} - {_now.date()} - S:{process.start} - O:{process.occupancy}")
                    except NoSuchElementException as e:
                        logging.info(f"[-] {dt.now()} Error in button Modal, not fount")
                    except ElementClickInterceptedException as e:
                        logging.info(f"[-] {dt.now()} Error in button Modal, element not clicked")
                    except Exception as e:
                        logging.info(f"[-] {dt.now()} Error in button Modal general: "+str(e))
                    sleep(3)
                    if process.type_proces == 1:
                        try:
                            _soup_elements = BeautifulSoup(driver.page_source, "html.parser")
                            elements = _soup_elements.find_all("input", {"type": "checkbox"})
                            for s in elements:
                                #logging.info(f"[+] {dt.now()} - {str(process.start)} stars - Input: {s.get('aria-label')}")
                                if str(process.start)+" stars" == str(s.get('aria-label')).split(":")[0].strip() or str(process.start)+" stars" == str(s.get('aria-label')).split("/")[0].strip() or str(process.start)+" estrellas" == str(s.get('aria-label')).split(":")[0].strip():# or str(process.start)+" stars" 
                                    #logging.info(f"[+] {dt.now()} - Stars - {_date_elem.date()} - {_now.date()} - O:{process.occupancy} - S:{str(process.start)} stars - Input: {s}")
                                    check_start = driver.find_element_by_xpath("//input[@id='"+str(s.get("id"))+"']")
                                    try:
                                        driver.execute_script("arguments[0].scrollIntoView(true);", check_start)
                                        check_start.click()
                                    except ElementClickInterceptedException:
                                        driver.execute_script("arguments[0].click();", check_start)
                                        sleep(2)
                                    #logging.info(f"[+] {dt.now()} Click button start success - {_date_elem.date()} - {_now.date()} - S:{process.start} - O:{process.occupancy}")
                                    break
                                    
                        except NoSuchElementException as e:
                            logging.info(f"[-] {dt.now()} Error in start button, not fount")
                            try:
                                _soup_elements = BeautifulSoup(driver.page_source, "html.parser")
                                elements = _soup_elements.find_all("input")
                                for s in elements:
                                    #logging.info(f"[+] {dt.now()} - Log2 - {str(start)} stars - Input: {s.get('aria-label')}")
                                    if str(process.start)+" stars" == str(s.get('aria-label')).split(":")[0].strip() or str(process.start)+" stars" == str(s.get('aria-label')).split("/")[0].strip() or str(process.start)+" estrellas" == str(s.get('aria-label')).split(":")[0].strip():#or str(process.start)+" stars"
                                        #logging.info(f"[+] {dt.now()} - Stars - O:{process.occupancy} - S:{str(process.start)} stars - Input: {s}")
                                        check_start = driver.find_element_by_xpath("//input[@id='"+str(s.get("id"))+"']")
                                        try:
                                            driver.execute_script("arguments[0].scrollIntoView(true);", check_start)
                                            check_start.click()
                                        except ElementClickInterceptedException:
                                            driver.execute_script("arguments[0].click();", check_start)
                                            sleep(2)
                                        #logging.info(f"[+] {dt.now()} Click button start success - {_date_elem.date()} - {_now.date()}  - S:{process.start} - O:{process.occupancy}")
                                        break
                                        
                            except NoSuchElementException as e:
                                logging.info(f"[-] {dt.now()} Error in start button - reintento 2, not fount")
                            except ElementClickInterceptedException as e:
                                logging.info(f"[-] {dt.now()} Error in start button, element not clicked2")
                            except Exception as e:
                                logging.info(f"[-] {dt.now()} Error in start button general: "+str(e))
                        except ElementClickInterceptedException as e:
                            logging.info(f"[-] {dt.now()} Error in start button, element not clicked1")
                        except Exception as e:
                            logging.info(f"[-] {dt.now()} Error in start button general: "+str(e))
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
                                        logging.info(f"[-] {dt.now()} Error durante el scroll: {e}")
                                    try:
                                        check_hotel.click()
                                    except Exception as e:
                                        logging.info(f"[-] {dt.now()} Error al hacer click, intentando con JavaScript: {e}")
                                        driver.execute_script("arguments[0].click();", check_hotel)
                                        sleep(2)
                                        
                                    #logging.info(f"[+] {dt.now()} Click button hoteles success: {_date_elem.date()} - {_now.date()}  - S:{process.start} - O:{process.occupancy}")
                                    break
                        except Exception as e:
                            logging.info(f"[-] {dt.now()} Error in Hoteles button general: "+str(e))

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
                            #logging.info(f"[+] {dt.now()} Click button dropdown success: - {_date_elem.date()} - {_now.date()}  - S:{process.start} - O:{process.occupancy}")
                            #driver.find_element_by_xpath("//div[@data-testid='sorters-dropdown']")

                            # div_li = driver.find_elements_by_xpath("//div[@data-testid='sorters-dropdown']")
                            # for dl in div_li:
                            #     logging.info(f"[+] {dt.now()} Element: {dl.text}")
                            check_price = driver.find_element_by_xpath("//button[@data-id='price']")
                            try:
                                driver.execute_script("arguments[0].scrollIntoView(true);", check_price)
                                check_price.click()
                            except ElementClickInterceptedException as e2:
                                driver.execute_script("arguments[0].click();", check_price)
                                sleep(2)
                            #logging.info(f"[+] {dt.now()} Click button price success: - {_date_elem.date()} - {_now.date()}  - S:{process.start} - O:{process.occupancy}")
                        except NoSuchElementException as e:
                            logging.info(f"[-] {dt.now()} Error in button price, not fount")
                        except ElementClickInterceptedException as e:
                            logging.info(f"[-] {dt.now()} Error in price button, element not clicked")
                        except Exception as e:
                            logging.info(f"[-] {dt.now()} Error in price button general: "+str(e))

                    sleep(3)
                    # Items booking search
                    items = driver.find_elements_by_xpath("//div[@data-testid='property-card']")
                    #logging.info(f"[+] {dt.now()} Elementos encontrados: {len(items)} - {_date_elem.date()} - {_now.date()}  - S:{process.start} - O:{process.occupancy}")
                    total_search = 0
                    try:
                        total_search = str(driver.find_element_by_xpath("//h1[@aria-live='assertive']").text).split(": ")[1].split(" ")[0].strip().replace(".", "")
                        #logging.info(f"[+] {dt.now()} Total search success: {total_search} - {_date_elem.date()} - {_now.date()}  - S:{process.start} - O:{process.occupancy}")
                        total_search = total_search.replace(",", "").replace(".", "")
                    except NoSuchElementException as e:
                        logging.info(f"[-] {dt.now()} Error in get total_search, not fount")
                    except ElementClickInterceptedException as e:
                        logging.info(f"[-] {dt.now()} Error in total_search, element not clicked1")
                    except Exception as e:
                        logging.info(f"[-] {dt.now()} Error in total_search general: "+str(e))

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
                                    updated = dt.now(),
                                    created = dt.now()
                                )
                            else:
                                comp.total_search = total_search
                                comp.updated = dt.now()
                                comp.created = dt.now()
                                comp.save()
                        except Exception as er2:
                            logging.info(f"[-] {dt.now()} Error 228: "+str(er2))

                    try:
                        #logging.info(f"[-] {dt.now()} - {search_name} - {_date_elem.date()} - {_now.date()} - S:{process.start} - O:{process.occupancy} - {driver.current_url} - {_url_performance}")
                        for position in process.position:
                            cls.get_data_to_text(items[position], _date_elem, _now, process.occupancy, position, total_search, process)
                    except Exception as e:
                        logging.info(f"[-] {dt.now()} Error 170: "+str(e))
                    sleep(1)
                        
                    if _date_elem.date() >= _date_end.date():
                        break
                    cont += 1

                    #if int(total_search) > 0:
                    _date_elem = _now
                    _now += datetime.timedelta(days=1)
            except Exception as e2:
                logging.info(f"[-] {dt.now()} Error 262: "+str(e2))
        except Exception as e02:
            logging.info(f"[-] {dt.now()} Error General 264: "+str(e02))

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
    def get_data_to_text(cls, item, _date_elem, _now, occupancy, position, total_search, process:ProcessActive):
        try:
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
                logging.info(f"[-] {dt.now()} Error in Get start")
            try:
                item_dict["title"], item_dict["link"] = cls.search_title(html)
            except Exception as e3:
                logging.info(f"[-] {dt.now()} Error in Get title and link")
            try:
                item_dict["address"], item_dict["distance"] = cls.search_address(html)
            except Exception as e4:
                logging.info(f"[-] {dt.now()} Error in Get address")
            try:
                item_dict["description"] = cls.search_description(html)
            except Exception as _e2:
                logging.info(f"[-] {dt.now()} Error in Get description")
            try:
                item_dict["img"] = cls.search_img(html)
            except Exception as e5:
                logging.info(f"[-] {dt.now()} Error in Get img")
            try:
                item_dict["price"] = cls.search_price(html)
            except Exception as e6:
                logging.info(f"[-] {dt.now()} Error in Get price")

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
                            updated = dt.now(),
                            created = dt.now()
                        )
                    else:
                        bg.start = item_dict["start"]
                        bg.title = item_dict["title"]
                        bg.link = item_dict["link"]
                        bg.address = item_dict["address"]
                        bg.distance = item_dict["distance"]
                        bg.description = item_dict["description"]
                        bg.img = item_dict["img"]
                        bg.updated = dt.now()
                        bg.save()

                    # _complement = Complement.objects.filter(
                    #     date_from=item_dict["date_from"], 
                    #     date_to=item_dict["date_to"], 
                    #     occupancy=occupancy, 
                    #     start=item_dict["start"]
                    # ).first()
                    # if not _complement:
                    #     _complement = Complement.objects.create(
                    #         total_search=total_search,
                    #         date_from=item_dict["date_from"], 
                    #         date_to=item_dict["date_to"], 
                    #         occupancy=occupancy, 
                    #         start=item_dict["start"]
                    #     )
                    # else:
                    #     _complement.total_search = total_search
                    #     _complement.save()
                        
                    # _available = AvailableBooking.objects.filter(
                    #     position=position,
                    #     complement=_complement
                    # ).first()

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
                            updated = dt.now(),
                            created = dt.now(),
                            occupancy = occupancy,
                            start = item_dict["start"]
                        )
                    else:
                        #_available.date_from = item_dict["date_from"]
                        #_available.date_to = item_dict["date_to"]
                        #_available.position = position
                        _available.total_search = int(total_search)
                        _available.active = True
                        _available.updated = dt.now()
                        _available.price = item_dict["price"]
                        #_available.occupancy = occupancy
                        _available.booking = bg
                        _available.save()
                    #logging.info(item_dict)
                else:
                    logging.info(f"Data Error Start {item_dict['start']} - O: {occupancy}: {item_dict}")
            else:
                price_with_name_hotel = PriceWithNameHotel.objects.filter(title = item_dict["title"], date_from = item_dict["date_from"], occupancy = occupancy).first()
                if not price_with_name_hotel:
                    price_with_name_hotel = PriceWithNameHotel.objects.create(
                        start = item_dict["start"],
                        title = item_dict["title"],
                        link = item_dict["link"],
                        address = item_dict["address"],
                        distance = item_dict["distance"],
                        description = item_dict["description"],
                        img = item_dict["img"],
                        updated = dt.now(),
                        created = dt.now(),
                        date_from = item_dict["date_from"],
                        date_to = item_dict["date_to"],
                        price = item_dict["price"],
                        occupancy = occupancy
                    )
                else:
                    price_with_name_hotel.price = item_dict["price"]
                    price_with_name_hotel.save()
                
                #logging.info(f"[+] Data Start success: {item_dict}")

        except Exception as e:
            logging.info(f"[-] {dt.now()} Error General data: "+str(e))
            logging.info(item_dict)
        
        return item_dict

if __name__ == "__main__":
    booking = BookingSearch()
    _driver = booking._driver()
    booking.controller(_driver, date_end=["2024", "12", "31"])