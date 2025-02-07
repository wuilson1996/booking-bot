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
from .models import *

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

        #options.set_preference("browser.privatebrowsing.autostart", True)

        return webdriver.Firefox(executable_path=os.path.abspath("geckodriver"), options=options)
    
    @classmethod
    def _driver(cls) -> None:
        if platform.system() == "Windows":
            return cls._driver_chrome()
        else:
            return cls._driver_firefox()

    @classmethod
    def organice_price(cls, prices):
        _prices = {}
        for key, value in prices.items():
            _prices[key] = value.price
        return _prices

    @classmethod
    def controller(cls, driver, price, _date, username, password):
        try:
            check = False
            driver.get(cls._url)
            driver.maximize_window()
            driver.implicitly_wait(15)
            driver.delete_all_cookies()
            generate_log(f"[+] Iniciando sesion... {_date} | {cls.organice_price(price)}", BotLog.ROOMPRICE)
            driver.find_element_by_xpath("//input[@type='email']").send_keys(username)
            #logging.info(f"[+] Add username success...")
            #generate_log(f"[+] Add username success... {_date} | {str(price)}", BotLog.ROOMPRICE)
            driver.find_element_by_xpath("//input[@type='password']").send_keys(password)
            #logging.info(f"[+] Add username password...")
            #generate_log(f"[+] Add username password... {_date} | {str(price)}", BotLog.ROOMPRICE)
            driver.find_element_by_xpath("//button[@type='submit']").click()
            #logging.info(f"[+] click button login success...")
            #generate_log(f"[+] click button login success... {_date} | {str(price)}", BotLog.ROOMPRICE)
            sleep(5)
            if "Ajustes de la cuenta" in driver.page_source:
                logging.info(f"[+] Inicio sesion correctamente... {_date} | {str(price)}")
                generate_log(f"[+] Inicio sesion correctamente... {_date} | {str(cls.organice_price(price))}", BotLog.ROOMPRICE)
            __time = time()
            while True:
                logging.info(f"[+] verificando inicio de sesion...")
                generate_log(f"[+] verificando inicio de sesion... {_date} | {str(cls.organice_price(price))}", BotLog.ROOMPRICE)
                if "Optimizando..." not in driver.page_source or (time() - __time >= 180):
                    break
                sleep(1)

            #logging.info(f"[+] Login success...")
            #generate_log(f"[+] Login success... {_date} | {str(price)}", BotLog.ROOMPRICE)
            # try:
            #     for button_update in driver.find_elements_by_xpath("//button[@type='button']"):
            #         logging.info(button_update.text)
            # except Exception as e1:
            #     logging.info(f"Error button update: {e1}")
            while True:
                status = False
                logging.info(f"[+] search buttons calendar...")
                generate_log(f"[+] Buscando fecha en calendario... {_date} | {str(cls.organice_price(price))}", BotLog.ROOMPRICE)
                for b in driver.find_elements_by_xpath("//button[@data-state='closed']"):
                    if b.get_attribute("data-testid") != "" and b.get_attribute("data-testid") != None:
                        #logging.info(f"[+] Fecha: {_date} {str(b.get_attribute('data-testid'))}...")
                        if _date == str(b.get_attribute("data-testid")):
                            logging.info(f"[+] Fecha encontrada: {str(b.get_attribute('data-testid'))}...")
                            generate_log(f"[+] Fecha encontrada: {str(b.get_attribute('data-testid'))}... {_date} | {str(cls.organice_price(price))}", BotLog.ROOMPRICE)
                            status = True
                            driver.execute_script("arguments[0].scrollIntoView();", b)
                            sleep(1)
                            b.click()
                            logging.info(f"[+] Click fecha success...")
                            generate_log(f"[+] Abriendo fecha... {_date} | {str(cls.organice_price(price))}", BotLog.ROOMPRICE)
                            sleep(3)
                            bt_edit_price = driver.find_element_by_xpath("//button[@data-testid='editPricesTab']")
                            driver.execute_script("arguments[0].scrollIntoView();", bt_edit_price)
                            sleep(1)
                            bt_edit_price.click()
                            logging.info(f"[+] Click button edit price tab success...")
                            generate_log(f"[+] Abriendo edicion de precios... {_date} | {str(cls.organice_price(price))}", BotLog.ROOMPRICE)
                            sleep(2)
                            for b2 in driver.find_elements_by_xpath("//div[@class='m_69686b9b mantine-SegmentedControl-control']"):
                                if b2.text == "Precios fijos":
                                    #driver.execute_script("arguments[0].scrollIntoView();", b2)
                                    sleep(1)
                                    b2.click()
                                    logging.info(f"[+] Precios fijos click success...")
                                    generate_log(f"[+] Edicion de precios fijos... {_date} | {str(cls.organice_price(price))}", BotLog.ROOMPRICE)
                                    sleep(2)
                                    bs = driver.find_element_by_xpath("//button[@role='switch']")
                                    if str(bs.get_attribute("data-headlessui-state")) == "checked":
                                        #driver.execute_script("arguments[0].scrollIntoView();", bs)
                                        sleep(1)
                                        bs.click()
                                    sleep(2)
                                    logging.info(f"[+] Button switch success...")
                                    generate_log(f"[+] Cambiando precios... {_date} | {str(cls.organice_price(price))}", BotLog.ROOMPRICE)

                                    input_price = driver.find_element_by_xpath("//input[@id='fixPricesAdjustment.3.id']")
                                    input_price.clear()
                                    input_price2 = driver.find_element_by_xpath("//input[@id='fixPricesAdjustment.4.id']")
                                    input_price2.clear()
                                    if "1" in price.keys():
                                        input_price.send_keys(str(price["1"].price))
                                        input_price2.send_keys(str(price["1"].price))
                                    
                                    input_price = driver.find_element_by_xpath("//input[@id='fixPricesAdjustment.0.id']")
                                    input_price.clear()
                                    if "2" in price.keys():
                                        input_price.send_keys(str(price["2"].price))

                                    input_price = driver.find_element_by_xpath("//input[@id='fixPricesAdjustment.1.id']")
                                    input_price.clear()
                                    if "3" in price.keys():
                                        input_price.send_keys(str(price["3"].price))
                                    
                                    input_price = driver.find_element_by_xpath("//input[@id='fixPricesAdjustment.2.id']")
                                    input_price.clear()
                                    if "4" in price.keys():
                                        input_price.send_keys(str(price["4"].price))
                                    
                                    input_price = driver.find_element_by_xpath("//input[@id='fixPricesAdjustment.5.id']")
                                    input_price.clear()
                                    if "5" in price.keys():
                                        input_price.send_keys(str(price["5"].price))
                                    
                                    input_price = driver.find_element_by_xpath("//input[@id='fixPricesAdjustment.6.id']")
                                    input_price.clear()
                                    if "6" in price.keys():
                                        input_price.send_keys(str(price["6"].price))

                                    sleep(2)
                                    btn_update = driver.find_element_by_xpath("//button[@data-userflow-id='price-drawer-save-prices-button']")
                                    #driver.execute_script("arguments[0].scrollIntoView();", btn_update)
                                    sleep(1)
                                    btn_update.click()
                                    logging.info(f"[+] Tarifa actualizado correctamente....")
                                    generate_log(f"[+] Tarifa actualizado correctamente.... {_date} | {str(cls.organice_price(price))}", BotLog.ROOMPRICE)
                                    break
                            break
                if status:
                    logging.info("[+] Encontrada...")
                    generate_log(f"[+] Actualizacion general... {_date} | {str(cls.organice_price(price))}", BotLog.ROOMPRICE)
                    sleep(3)
                    try:
                        for button_update in driver.find_elements_by_xpath("//button[@type='button']"):
                            if "Actualizar tarifas" in button_update.text:
                                generate_log(f"[+] Actualizando tarifa... {_date} | {str(cls.organice_price(price))}", BotLog.ROOMPRICE)
                                logging.info(button_update.text)
                                #button_update.click()
                                #driver.execute_script("arguments[0].scrollIntoView();", button_update)
                                sleep(1)
                                driver.execute_script("arguments[0].click();", button_update)
                                sleep(2)
                                for b in driver.find_elements_by_xpath("//div[@role='radio']"):
                                    if "Próximos 3 meses" in b.text:
                                        logging.info(b.text)
                                        #driver.execute_script("arguments[0].scrollIntoView();", b)
                                        sleep(1)
                                        driver.execute_script("arguments[0].click();", b)
                                        sleep(4)
                                        for btt in driver.find_elements_by_xpath("//button[@type='button']"):
                                            if "Actualizar tarifas" in btt.text and "currentColor" not in btt.get_attribute("innerHTML"):
                                                logging.info(btt.text)
                                                #logging.info(btt.get_attribute("innerHTML"))
                                                #driver.execute_script("arguments[0].scrollIntoView();", btt)
                                                sleep(1)
                                                btt.click()
                                                check = True
                                                generate_log(f"[+] Tarifa actualizada... {_date} | {str(cls.organice_price(price))}", BotLog.ROOMPRICE)
                                                cls.change_status_price(price, True)
                                                sleep(10)
                                                break
                                        break
                                break
                    except Exception as e1:
                        logging.info(f"Error button update: {e1}")
                        generate_log(f"[+] Error button update {e1}... {_date} | {str(cls.organice_price(price))}", BotLog.ROOMPRICE)
                    break
                else:
                    logging.info("[+] Buscando calendario...")
                    generate_log(f"[+] Buscando calendario... {_date} | {str(cls.organice_price(price))}", BotLog.ROOMPRICE)
                    bt_next = driver.find_element_by_xpath("//button[@data-testid='toNextMonthButton']")
                    #driver.execute_script("arguments[0].scrollIntoView();", bt_next)
                    sleep(1)
                    bt_next.click()
                    sleep(3)
                    logging.info(f"[+] Click button next calendar success...")
                    generate_log(f"[+] Siguiente calendario... {_date} | {str(cls.organice_price(price))}", BotLog.ROOMPRICE)
        
        except Exception as e:
            logging.info("Error Fee: "+str(e))
            generate_log(f"[+] Error Fee {e}... {_date} | {str(cls.organice_price(price))}", BotLog.ROOMPRICE)

        return check
    
    @classmethod
    def close(cls, driver):
        driver.close()
    
    @classmethod
    def change_status_price(cls, price, status):
        for key, value in price.items():
            value.plataform_sync = status
            value.save()