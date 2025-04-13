from bs4 import BeautifulSoup
import random
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
                        generate_log(f"[+] Buscando fecha en calendario: {_date} | {str(b.get_attribute('data-testid'))}", BotLog.ROOMPRICE)
                        if _date == str(b.get_attribute("data-testid")):
                            logging.info(f"[+] Fecha encontrada: {str(b.get_attribute('data-testid'))}...")
                            generate_log(f"[+] Fecha encontrada: {str(b.get_attribute('data-testid'))}... {_date} | {str(cls.organice_price(price))}", BotLog.ROOMPRICE)
                            driver.execute_script("arguments[0].scrollIntoView();", b)
                            sleep(1)
                            #b.click()
                            driver.execute_script("arguments[0].click();", b) # Upgrade change button for javascript.
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
                            if "Sending Prices. Waiting for the Channel Manager to confirm" in driver.page_source:
                                logging.info(f"[+] Check message Sending Prices....")
                            if "Prices Uploaded Successfully" in driver.page_source:
                                logging.info(f"[+] Check message Prices Uploaded....")
                            if "Data Updated Successfully" in driver.page_source:
                                logging.info(f"[+] Check message Data Updated....")

                            for b2 in driver.find_elements_by_xpath("//div[@class='m_69686b9b mantine-SegmentedControl-control']"):
                                if b2.text == "Precios fijos":
                                    #driver.execute_script("arguments[0].scrollIntoView();", b2)
                                    sleep(1)
                                    b2.click()
                                    logging.info(f"[+] Precios fijos click success...")
                                    generate_log(f"[+] Edicion de precios fijos... {_date} | {str(cls.organice_price(price))}", BotLog.ROOMPRICE)
                                    sleep(2)

                                    # cambiar boton por cambios en plataforma roomprice. -------- solucionado -----------
                                    bs = driver.find_element_by_xpath("//input[@role='switch']")
                                    logging.info(f"[+] Button switch check... {bs}")
                                    if bs.get_attribute("checked"):
                                        bs_div = driver.find_element_by_xpath("//input[@role='switch']/following-sibling::div")
                                        logging.info(f"[+] Button switch success... {bs_div}")
                                        driver.execute_script("arguments[0].click();", bs_div)
                                        
                                    sleep(2)
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
                                    
                                    start_time2 = time()  # Guarda el tiempo de inicio
                                    timeout2 = 180  # Tiempo máximo en segundos
                                    while True:
                                        sleep(2)
                                        cls.guardar_captura(driver, descripcion="pagina_cargada")
                                        for btn_update in driver.find_elements_by_xpath("//button[@type='button']"):
                                            generate_log(f"[+] Button: {btn_update.text} - {_date} | {btn_update.get_attribute('innerHTML')}", BotLog.ROOMPRICE)
                                            if btn_update.text == "Actualizar tarifas" and "currentColor" not in str(btn_update.get_attribute("innerHTML")):
                                                generate_log(f"[+] Button Encontrado: {btn_update.text} - {_date} | {btn_update.get_attribute('innerHTML')}", BotLog.ROOMPRICE)
                                                #b.click()
                                                driver.execute_script("arguments[0].click();", btn_update)
                                                break
                                        
                                        if time() - start_time2 > timeout2:  # Verifica si han pasado 120 segundos
                                            logging.error("[!] Button Actualizar tarifa: Tiempo de espera agotado. No se detectó el boton.")
                                            generate_log(f"[!] Button Actualizar tarifa: Tiempo de espera agotado. No se detectó el boton... {_date}", BotLog.ROOMPRICE)
                                            break
                                    # wait = WebDriverWait(driver, 120)  # espera hasta 20 segundos
                                    # button = wait.until(EC.presence_of_element_located(
                                    #     (By.XPATH, "//button[@data-userflow-id='price-drawer-upload-prices-button']")
                                    # ))
                                    # button.click()
                                    #btn_update = driver.find_element_by_xpath("//button[@data-userflow-id='price-drawer-upload-prices-button']")
                                    #driver.execute_script("arguments[0].scrollIntoView();", btn_update)
                                    sleep(1)
                                    #driver.execute_script("arguments[0].click();", btn_update)
                                    #btn_update.click()
                                    status = True
                                    break
                            break
                if status:
                    logging.info("[+] Abrir modal, actualizar channels manager...")
                    generate_log(f"[+] Abrir modal, Actualizar channels manager... {_date} | {str(cls.organice_price(price))}", BotLog.ROOMPRICE)
                    sleep(3)
                    try:
                        start_time1 = time()  # Guarda el tiempo de inicio
                        timeout1 = 180  # Tiempo máximo en segundos
                        while True:
                            generate_log(f"[+] Buscando boton: Confirmar y Enviar al Channel Manager... {_date} | {str(cls.organice_price(price))}", BotLog.ROOMPRICE)
                            logging.info("[+] Buscando boton: Confirmar y Enviar al Channel Manager...")
                            if time() - start_time1 > timeout1:  # Verifica si han pasado 120 segundos
                                logging.error("[!] Channel Manager: Tiempo de espera agotado. No se detectó la actualización de tarifas.")
                                generate_log(f"[!] Channel Manager: Tiempo de espera agotado. No se detectó la actualización de tarifas... {_date} | {str(cls.organice_price(price))}", BotLog.ROOMPRICE)
                                break
                            status_button = False
                            for button_update in driver.find_elements_by_xpath("//button[@type='button']"):
                                if "Confirmar y Enviar al Channel Manager" in button_update.text:
                                    status_button = True
                                    generate_log(f"[+] Enviando a Channels Manager... {_date} | {str(cls.organice_price(price))}", BotLog.ROOMPRICE)
                                    logging.info(button_update.text)
                                    logging.info(button_update.get_attribute("innerHTML"))
                                    #button_update.click()
                                    driver.execute_script("arguments[0].click();", button_update)
                                    #driver.execute_script("arguments[0].scrollIntoView();", button_update)
                                    
                                    start_time = time()  # Guarda el tiempo de inicio
                                    timeout = 120  # Tiempo máximo en segundos
                                    status1 = False
                                    status2 = False
                                    status3 = False
                                    status = False
                                    while True:
                                        if "Sending Prices. Waiting for the Channel Manager to confirm" in driver.page_source:
                                            status1 = True
                                            logging.info("[+] Channel Manager: Sending Prices. Waiting for the Channel Manager to confirm")
                                            generate_log(f"[+] Channel Manager: Sending Prices. Waiting for the Channel Manager to confirm... {_date} | {str(cls.organice_price(price))} | Sending Prices:{status1} | Prices Uploaded:{status2}", BotLog.ROOMPRICE)
                                        if "Prices Uploaded Successfully" in driver.page_source:
                                            status2 = True
                                            logging.info("[+] Channel Manager: Prices Uploaded Successfully.")
                                            generate_log(f"[+] Channel Manager: Prices Uploaded Successfully... {_date} | {str(cls.organice_price(price))} | Sending Prices:{status1} | Prices Uploaded:{status2}", BotLog.ROOMPRICE)
                                        if "Data Updated Successfully" in driver.page_source:
                                            status3 = True
                                            logging.info("[+] Channel Manager: Data Updated Successfully.")
                                            generate_log(f"[+] Channel Manager: Data Updated Successfully... {_date} | {str(cls.organice_price(price))} | Sending Prices:{status1} | Prices Uploaded:{status2}", BotLog.ROOMPRICE)
                                        
                                        if status1 and status2 and status3:
                                            status = True
                                            break

                                        if time() - start_time > timeout:  # Verifica si han pasado 120 segundos
                                            logging.error("[!] Channel Manager: Tiempo de espera agotado. No se detectó la actualización de tarifas.")
                                            generate_log(f"[!] Channel Manager: Tiempo de espera agotado. No se detectó la actualización de tarifas... {_date} | {str(cls.organice_price(price))} | Sending Prices:{status1} | Prices Uploaded:{status2}", BotLog.ROOMPRICE)
                                            status = False
                                            break
                                        sleep(1)

                                    if status:
                                        check = True
                                        generate_log(f"[+] Tarifa actualizada... {_date} | {str(cls.organice_price(price))} | Sending Prices:{status1} | Prices Uploaded:{status2}", BotLog.ROOMPRICE)
                                        cls.change_status_price(price, True)
                                        sleep(10)
                                        break

                                    break
                            if status_button:
                                break
                            sleep(1)
                    except Exception as e1:
                        logging.info(f"Error button update: {e1}")
                        generate_log(f"[+] Error button update {e1}... {_date} | {str(cls.organice_price(price))}", BotLog.ROOMPRICE)
                    break
                else:
                    logging.info("[+] Buscando calendario...")
                    generate_log(f"[+] Buscando calendario... {_date} | {str(cls.organice_price(price))}", BotLog.ROOMPRICE)
                    bt_next = driver.find_element_by_xpath("//button[@data-testid='toNextMonthButton']")
                    driver.execute_script("arguments[0].scrollIntoView();", bt_next)
                    driver.execute_script("arguments[0].click();", bt_next)
                    sleep(1)
                    #bt_next.click()
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

    @classmethod
    def guardar_captura(cls, driver, carpeta="media/capturas", descripcion=""):
        # Crear carpeta si no existe
        if not os.path.exists(carpeta):
            os.makedirs(carpeta)

        # Generar nombre con timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"{descripcion}_{timestamp}.png" if descripcion else f"captura_{timestamp}.png"
        ruta_completa = os.path.join(carpeta, nombre_archivo)

        # Guardar captura
        driver.save_screenshot(ruta_completa)
        generate_log(f"[✓] Captura guardada en: {ruta_completa}", BotLog.ROOMPRICE)