from bs4 import BeautifulSoup
import random
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from time import sleep
import pandas as pd
import logging
import json
from datetime import datetime as dt
import datetime
import re
from .models import *
import os

_logging = logging.basicConfig(filename="logger.log", level=logging.INFO)

pattern = r"\b(19\d\d|20\d\d)[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])\b"
def search_date(text):
    return re.findall(pattern, text)

class BookingSearch:
    @classmethod
    def _driver2(cls) -> None:
        cls._url = "https://www.booking.com"
        options = webdriver.ChromeOptions()
        options.add_argument("headless")
        options.add_argument("disable-gpu")
        options.add_argument("no-sandbox")

        return webdriver.Chrome(executable_path=os.path.abspath("chromedriver"), options=options)

    @classmethod
    def _driver(cls) -> None:
        cls._url = "https://www.booking.com"
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        return webdriver.Firefox(executable_path=os.path.abspath("geckodriver"), options=options)
    
    @classmethod
    def controller(cls, driver, _now:dt.now=dt.now(), date_end=list(), occupancy=2, start=4, p:ProcessActive=None):
        driver.get(cls._url)
        driver.implicitly_wait(15)
        sleep(5)
        #logging.info(driver.current_url)
        try:
            _button = driver.find_element_by_xpath("//button[@id='onetrust-accept-btn-handler']")
            _button.click()
        except NoSuchElementException as e:
            logging.info(f"[-] {dt.now()} Error in button cookies, element not fount")
        except ElementClickInterceptedException as e:
            logging.info(f"[-] {dt.now()} Error in button cookies, element not clicked")
            
        # Search
        search = driver.find_element_by_xpath("//input[@name='ss']")
        search.send_keys("Madrid, Comunidad de Madrid, España")

        data = []
        _date_end = dt(int(date_end[0]), int(date_end[1]), int(date_end[2]))
        cont = 0
        item_list = {}
        try:
            while True:
                try:
                    b2 = driver.find_element_by_xpath("//button[@data-testid='occupancy-config']")
                    driver.execute_script("arguments[0].click();", b2)
                    #b2.click()
                    sleep(2)
                    _divs = driver.find_elements_by_xpath("//div[@data-testid='occupancy-popup']")
                    divs2 = _divs[0].find_element_by_tag_name("div").find_element_by_tag_name("div").find_elements_by_tag_name("div")[1]
                    #logging.info(divs2.get_attribute("innerHTML"))
                    logging.info(f"{dt.now()} - {divs2.text} - {occupancy}")
                    for i in range(occupancy - int(divs2.text)):
                        buttons2 = divs2.find_elements_by_tag_name("button")
                        buttons2[1].click()
                except NoSuchElementException as e:
                    logging.info(f"[-] {dt.now()} Error in button occupancy, element not fount")
                except ElementClickInterceptedException as e:
                    logging.info(f"[-] {dt.now()} Error in button occupancy, element not clicked")
                except Exception as e:
                    logging.info(f"[-] {dt.now()} Error in button occupancy general")

                try:
                    _error = None
                    _date = driver.find_element_by_xpath("//div[@data-testid='searchbox-dates-container']")
                    _date.click()
                    divs = driver.find_element_by_xpath("//div[@data-testid='searchbox-datepicker-calendar']").find_element_by_tag_name("div").find_element_by_tag_name("div")
                    divs = [divs, divs.find_element_by_xpath('following-sibling::div')]
                    #print(divs[1].get_attribute("innerHTML"))
                    tds = divs[0].find_elements_by_tag_name("td")
                    tds += divs[1].find_elements_by_tag_name("td")
                    for _td in tds:
                        _date_soup = BeautifulSoup(_td.get_attribute("innerHTML"), "html.parser")
                        if _date_soup:
                            #print("td soup: "+str(_date_soup))
                            try:
                                aux_date = search_date(str(_date_soup))
                                #print("Date aux: "+str(aux_date))
                                try:
                                    if len(aux_date) == 1:
                                        _date_elem = dt(int(aux_date[0][0]), int(aux_date[0][1]), int(aux_date[0][2]))
                                        if _date_elem.date() == _now.date():
                                            _td.click()
                                            _now += datetime.timedelta(days=1)
                                            logging.info(f"{dt.now()} - {str(_date_elem.date())} - {str(_now.date())}")
                                            break
                                except Exception as error2:
                                    #print("Error 74: "+str(error2))
                                    _error = "Error get date error2: "+str(error2)
                            except Exception as error3:
                                #print("Error 64: "+str(error3))
                                _error = "Error in get date error3: "+str(error3)
                            
                except Exception as error:
                    #print("Error 77: "+str(error))
                    _error = "Error in get date error1: "+str(error)
                
                if _error is None:
                    #logging.info(driver.current_url)
                    buttons = driver.find_elements_by_xpath("//button[@type='submit']")
                    sleep(2)

                    buttons = driver.find_elements_by_xpath("//button[@type='submit']")
                    sleep(2)
                    for b in buttons:
                        logging.info(f"[+] {dt.now()} Button Submit: {b.text}")
                        if "Buscar" or "Search" in b.text:
                            try:
                                b.click()
                            except Exception as e:
                                logging.info(f"[-] {dt.now()} Error in button submit general, element not clicked")
                                driver.execute_script("arguments[0].click();", b)
                                sleep(2)
                            break
                    
                    logging.info(driver.current_url)

                    try:
                        if cont <= 1:
                            _button = driver.find_element_by_xpath("//button[@aria-label='Ignorar información sobre el inicio de sesión.']")
                            _button.click()
                            logging.info(f"[+] {dt.now()} Click button modal success")
                    except NoSuchElementException as e:
                        logging.info(f"[-] {dt.now()} Error in button Modal")
                    except ElementClickInterceptedException as e:
                        logging.info(f"[-] {dt.now()} Error in button Modal, element not clicked")
                    except Exception as e:
                        logging.info(f"[-] {dt.now()} Error in button Modal general")
                    sleep(1)
                    try:
                        _soup_elements = BeautifulSoup(driver.page_source, "html.parser")
                        elements = _soup_elements.find_all("input", {"type": "checkbox"})
                        for s in elements:
                            logging.info(f"[+] {dt.now()} - {str(start)} stars - Input: {s.get('aria-label')}")
                            if str(start)+" stars" in str(s.get('aria-label')) or str(start)+" estrellas" in str(s.get('aria-label')):# or str(start)+" stars" 
                                check_start = driver.find_element_by_xpath("//input[@id='"+str(s.get("id"))+"']")
                                try:
                                    check_start.click()
                                except ElementClickInterceptedException:
                                    driver.execute_script("arguments[0].click();", check_start)
                                    sleep(2)
                                logging.info(f"[+] {dt.now()} Click button start success")
                                try:
                                    check_start = driver.find_element_by_xpath("//input[@id='"+str(s.get("id"))+"']")
                                    logging.info(f"[+] {dt.now()} {check_start.get_attribute('innerHTML')}")
                                except Exception as e0:
                                    logging.info(f"[-] {dt.now()} Error in start get input check state")
                                break
                                
                    except NoSuchElementException as e:
                        logging.info(f"[-] {dt.now()} Error in start button")
                        try:
                            _soup_elements = BeautifulSoup(driver.page_source, "html.parser")
                            elements = _soup_elements.find_all("input")
                            for s in elements:
                                logging.info(f"[+] {dt.now()} - {str(start)} stars - Input: {s.get('aria-label')}")
                                if str(start)+" stars" in str(s.get('aria-label')) or str(start)+" estrellas" in str(s.get('aria-label')):#or str(start)+" stars"
                                    driver.find_element_by_xpath("//input[@id='"+str(s.get("id"))+"']").click()
                                    logging.info(f"[+] {dt.now()} Click button start success")
                                    break
                                    
                        except NoSuchElementException as e:
                            logging.info(f"[-] {dt.now()} Error in start button - reintento 2")
                        except ElementClickInterceptedException as e:
                            logging.info(f"[-] {dt.now()} Error in start button, element not clicked2")
                        except Exception as e:
                            logging.info(f"[-] {dt.now()} Error in start button general, element not clicked")
                    except ElementClickInterceptedException as e:
                        logging.info(f"[-] {dt.now()} Error in start button, element not clicked1")
                    except Exception as e:
                        logging.info(f"[-] {dt.now()} Error in start button general")
                    sleep(1)
                    try:
                        _soup_elements = BeautifulSoup(driver.page_source, "html.parser")
                        elements = _soup_elements.find_all("input", {"type": "checkbox"})
                        for s in elements:
                            if "Hoteles" or "Hotels" in str(s):
                                check_hotel = driver.find_element_by_xpath("//input[@id='"+str(s.get("id"))+"']")
                                try:
                                    check_hotel.click()
                                except ElementClickInterceptedException as e2:
                                    driver.execute_script("arguments[0].click();", check_hotel)
                                    sleep(2)
                                logging.info(f"[+] {dt.now()} Click button hoteles success")
                                try:
                                    check_hotel = driver.find_element_by_xpath("//input[@id='"+str(s.get("id"))+"']")
                                    logging.info(f"[+] {dt.now()} {check_hotel}")
                                except Exception as e3:
                                    logging.info(f"[-] {dt.now()} Error in Hoteles get input check")
                                break
                    except NoSuchElementException as e:
                        logging.info(f"[-] {dt.now()} Error in Hoteles button")
                    except ElementClickInterceptedException as e:
                        logging.info(f"[-] {dt.now()} Error in Hoteles button, element not clicked")
                    except Exception as e:
                        logging.info(f"[-] {dt.now()} Error in Hoteles button general")

                    sleep(1)
                    try:
                        driver.find_element_by_xpath("//button[@data-testid='sorters-dropdown-trigger']").click()
                        sleep(1)
                        #driver.find_element_by_xpath("//div[@data-testid='sorters-dropdown']")
                        check_price = driver.find_element_by_xpath("//button[@data-id='price']")
                        try:
                            check_price.click()
                        except ElementClickInterceptedException as e2:
                            driver.execute_script("arguments[0].click();", check_price)
                            sleep(2)
                        logging.info(f"[+] {dt.now()} Click button price success")
                    except NoSuchElementException as e:
                        logging.info(f"[-] {dt.now()} Error in button price")
                    except ElementClickInterceptedException as e:
                        logging.info(f"[-] {dt.now()} Error in price button, element not clicked")
                    except Exception as e:
                        logging.info(f"[-] {dt.now()} Error in price button general")

                    sleep(2)
                    # Items booking search
                    items = driver.find_elements_by_xpath("//div[@data-testid='property-card']")
                    logging.info(f"[+] {dt.now()} Elementos encontrados: {len(items)}")
                    total_search = 0
                    try:
                        total_search = str(driver.find_element_by_xpath("//h1[@aria-live='assertive']").text).split(": ")[1].split(" ")[0].strip().replace(".", "")
                        logging.info(f"[+] {dt.now()} Total search success: {total_search}")
                        total_search = total_search.replace(",", "").replace(".", "")
                    except NoSuchElementException as e:
                        logging.info(f"[-] {dt.now()} Error in get total_search")
                    except ElementClickInterceptedException as e:
                        logging.info(f"[-] {dt.now()} Error in total_search, element not clicked1")
                    except Exception as e:
                        logging.info(f"[-] {dt.now()} Error in total_search general")

                    try:
                        for position in p.position:
                            aux_d = cls.get_data_to_text(items[position], _date_elem, _now, occupancy, position, total_search)
                            if aux_d["title"] not in list(item_list.keys()):
                                item_list[aux_d["title"]] = []
                            item_list[aux_d["title"]].append(aux_d)
                    except Exception as e:
                        logging.info(f"[-] {dt.now()} Error 170: "+str(e))
                    sleep(1)
                        
                    if _date_elem.date() >= _date_end.date():
                        break
                    cont += 1
        except Exception as e2:
            logging.info(f"[-] {dt.now()} Error 218: "+str(e2))

        driver.close()

        # for b in Booking.objects.filter(start = start, occupancy = occupancy):
        #     for a in AvailableBooking.objects.filter(booking = b):
        #         state = False
        #         try:
        #             for value in item_list[b.title]:
        #                 print("New value")
        #                 print(value["date_from"], value["date_to"])
        #                 print("Value DB")
        #                 print(a.date_from, a.date_to)
        #                 if a.date_from == value["date_from"] and a.date_to == value["date_to"]:
        #                     state = True
        #                     break
        #             if not state:
        #                 a.delete()
        #         except Exception as e:
        #             print("Error 237: "+str(e))
        
        p.active = False
        p.save()

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
    def get_data_to_text(cls, item, _date_elem, _now, occupancy, position, total_search):
        try:
            item_dict = {
                "start": 0,
                "title": "",
                "link": "",
                "address": "",
                "distance": "",
                "description": "",
                "img": "",
                "price": "",
                "date_from": str(_date_elem.date()),
                "date_to":  str(_now.date())
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

            bg = Booking.objects.filter(title=item_dict["title"], start=item_dict["start"], occupancy=occupancy).first()
            if not bg:
                bg = Booking.objects.create(
                    start = item_dict["start"],
                    title = item_dict["title"],
                    link = item_dict["link"],
                    address = item_dict["address"],
                    distance = item_dict["distance"],
                    description = item_dict["description"],
                    img = item_dict["img"],
                    occupancy = occupancy,
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
                bg.occupancy = occupancy
                bg.updated = dt.now()
                bg.save()

            _available = AvailableBooking.objects.filter(date_from=item_dict["date_from"], date_to=item_dict["date_to"], booking=bg).first()
            if not _available:
                _available = AvailableBooking.objects.create(
                    date_from = item_dict["date_from"],
                    date_to = item_dict["date_to"],
                    booking = bg,
                    position = position,
                    total_search = int(total_search),
                    price = item_dict["price"],
                    updated = dt.now(),
                    created = dt.now()
                )
            else:
                _available.date_from = item_dict["date_from"]
                _available.date_to = item_dict["date_to"]
                _available.position = position
                _available.total_search = int(total_search)
                _available.active = True
                _available.updated = dt.now()
                _available.price = item_dict["price"]
                _available.save()
            logging.info(item_dict)
        except Exception as e:
            logging.info(f"[-] {dt.now()} Error General data: "+str(e))
            logging.info(item_dict)
        
        return item_dict

if __name__ == "__main__":
    booking = BookingSearch()
    _driver = booking._driver()
    booking.controller(_driver, date_end=["2024", "12", "31"])