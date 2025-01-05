from bs4 import BeautifulSoup
import random
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.keys import Keys
from time import sleep, time
import pandas as pd
import logging
import json
from datetime import datetime as dt
import datetime
import re
import os
import platform

class FeeTask:
    _url = "https://app.roompricegenie.com/client/calendar"
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

        options.set_preference("browser.privatebrowsing.autostart", True)

        return webdriver.Firefox(executable_path=os.path.abspath("geckodriver"), options=options)
    
    @classmethod
    def _driver(cls) -> None:
        if platform.system() == "Windows":
            return cls._driver_chrome()
        else:
            return cls._driver_firefox()

    @classmethod
    def controller(cls, driver, price, tipo, _date:str, username, password):
        try:
            driver.get(cls._url)
            driver.implicitly_wait(15)
            driver.delete_all_cookies()

            driver.find_element_by_xpath("//input[@type='email']").send_keys(username)
            logging.info(f"[+] Add username success...")
            driver.find_element_by_xpath("//input[@type='password']").send_keys(password)
            logging.info(f"[+] Add username password...")
            driver.find_element_by_xpath("//button[@type='submit']").click()
            logging.info(f"[+] click button login success...")
            sleep(5)
            if "Ajustes de la cuenta" in driver.page_source:
                logging.info(f"[+] Inicio sesion correctamente...")
            __time = time()
            while True:
                logging.info(f"[+] verificando inicio de sesion...")
                if "Optimizando..." not in driver.page_source or (time() - __time >= 180):
                    break
                sleep(1)

            while True:
                status = False
                logging.info(f"[+] search buttons calendar...")
                for b in driver.find_elements_by_xpath("//button[@data-state='closed']"):
                    if b.get_attribute("data-testid") != "" and b.get_attribute("data-testid") != None:
                        logging.info(f"[+] Fecha: {str(b.get_attribute('data-testid'))}...")
                        if _date == str(b.get_attribute("data-testid")):
                            logging.info(f"[+] Fecha encontrada: {str(b.get_attribute('data-testid'))}...")
                            status = True
                            b.click()
                            sleep(3)
                            driver.find_element_by_xpath("//button[@data-testid='editPricesTab']").click()
                            sleep(1)
                            for b2 in driver.find_elements_by_xpath("//div[@class='m_69686b9b mantine-SegmentedControl-control']"):
                                if b2.text == "Precios fijos":
                                    b2.click()
                                    sleep(2)
                                    bs = driver.find_element_by_xpath("//button[@role='switch']")
                                    if str(bs.get_attribute("data-headlessui-state")) == "checked":
                                        bs.click()

                                    if tipo == 1:
                                        input_price = driver.find_element_by_xpath("//input[@id='fixPricesAdjustment.3.id']")
                                        input_price.clear()
                                        input_price.send_keys(str(price))
                                        input_price = driver.find_element_by_xpath("//input[@id='fixPricesAdjustment.4.id']")
                                    elif tipo == 2:
                                        input_price = driver.find_element_by_xpath("//input[@id='fixPricesAdjustment.0.id']")
                                    elif tipo == 3:
                                        input_price = driver.find_element_by_xpath("//input[@id='fixPricesAdjustment.1.id']")
                                    elif tipo == 4:
                                        input_price = driver.find_element_by_xpath("//input[@id='fixPricesAdjustment.2.id']")
                                    elif tipo == 5:
                                        input_price = driver.find_element_by_xpath("//input[@id='fixPricesAdjustment.5.id']")
                                    elif tipo == 6:
                                        input_price = driver.find_element_by_xpath("//input[@id='fixPricesAdjustment.6.id']")
                                    input_price.clear()
                                    input_price.send_keys(str(price))

                                    sleep(1)
                                    driver.find_element_by_xpath("//button[@data-userflow-id='price-drawer-save-prices-button']").click()
                                    logging.info(f"[+] Tarifa actualizado correctamente....")
                                    break
                            break
                if status:
                    logging.info("[+] Encontrada...")
                    break
                else:
                    logging.info("[+] Aumenta calendario...")
                    driver.find_element_by_xpath("//button[@data-testid='toNextMonthButton']").click()
                    sleep(3)
                    logging.info(f"[+] Click button next calendar success...")
        
        except Exception as e:
            logging.info("Error: "+str(e))
    
    @classmethod
    def close(cls, driver):
        driver.close()