# myapp/tasks.py

import threading
import time
from datetime import datetime, timedelta
from .models import *
from pathlib import Path
import logging

LOCK_FILE_PATH = "/tmp/ejecutar_funcion.lock"

def ejecutar_funcion():
    logging.info("¡init copy 10:00 p.m!")
    # 60 dias
    __date_from = str(datetime.now().date())
    __date_to = str(datetime.now().date() + timedelta(days=365))
    _date_from = datetime(
        year=int(__date_from.split("-")[0]),
        month=int(__date_from.split("-")[1]),
        day=int(__date_from.split("-")[2])
    )
    _date_from_current = _date_from
    _date_to = datetime(
        year=int(__date_to.split("-")[0]),
        month=int(__date_to.split("-")[1]),
        day=int(__date_to.split("-")[2])
    )
    occupancys = []
    for p in ProcessActive.objects.all():
        if p.occupancy not in occupancys:
            occupancys.append(p.occupancy)
    
    while _date_from.date() <= _date_to.date():
        try:
            logging.info("[+] Copy price.")
            # copy price with booking
            for ocp in occupancys:
                available_booking = AvailableBooking.objects.filter(date_from=str(_date_from.date()), occupancy=int(ocp))
                for avail_book in available_booking:
                    if int(avail_book.booking.start) != 0:
                        #print(f"Price: {avail_book.price}, Ocupancy:{ocp}, Position:{avail_book.position} Start: {avail_book.start}")
                        CopyPriceWithDay.objects.create(
                            price = avail_book.price,
                            created = str(datetime.now().date()),
                            avail_booking = avail_book
                        )
        except Exception as e:
            logging.info(f"Error copy price. {e}")
            
        try:
            logging.info("[+] Copy price suites feria.")
            # copy price with suites feria.
            price_with_name = PriceWithNameHotel.objects.filter(title = "Hotel Suites Feria de Madrid", date_from = str(_date_from.date())).first()
            if price_with_name:
                CopyPriceWithNameFromDay.objects.create(
                    price = price_with_name.price,
                    created = str(datetime.now().date()),
                    avail = price_with_name
                )
        except Exception as e:
            logging.info(f"Error copy price suites feria. {e}")

        try:
            logging.info("[+] Copy avail suites feria.")
            # copy avail with suites feria.
            asf = AvailSuitesFeria.objects.filter(date_avail = str(_date_from.date())).first()
            if asf:
                casf1 = CantAvailSuitesFeria.objects.filter(avail_suites_feria = asf, type_avail = 1).last()
                casf1_avail = 0
                if casf1:
                    casf1_avail = casf1.avail

                casf2 = CantAvailSuitesFeria.objects.filter(avail_suites_feria = asf, type_avail = 2).last()
                casf2_avail = 0
                if casf2:
                    casf2_avail = casf2.avail
                    
                casf4 = CantAvailSuitesFeria.objects.filter(avail_suites_feria = asf, type_avail = 4).last()
                casf4_avail = 0
                if casf4:
                    casf4_avail = casf4.avail
                CopyAvailWithDaySF.objects.create(
                    type_avail = "0",
                    avail_1 = str(casf1_avail),
                    avail_2 = str(casf2_avail),
                    avail_4 = str(casf4_avail),
                    created = str(datetime.now().date()),
                    avail_suites_feria = asf
                )
        except Exception as e:
            logging.info(f"Error copy avail suites feria. {e}")
        _date_from += timedelta(days=1)

    logging.info("[+] finish Copy")

def iniciar_tarea_diaria():
    def tarea_en_thread():
        time.sleep(5)
        while True:
            # Hora actual
            ahora = datetime.now()
            
            # Próxima ejecución a las 10:00 p.m. de hoy o mañana
            proxima_ejecucion = ahora.replace(hour=22, minute=0, second=0, microsecond=0)
            if ahora > proxima_ejecucion:
                proxima_ejecucion += timedelta(days=1)
            
            # Calcula el tiempo hasta la próxima ejecución
            tiempo_espera = (proxima_ejecucion - ahora).total_seconds()
            logging.info(f"Esperando {tiempo_espera / 3600:.2f} horas hasta la próxima ejecución")

            # Espera hasta las 10:00 p.m.
            time.sleep(tiempo_espera)
            
            # Revisa si el archivo de bloqueo existe
            lock_file = Path(LOCK_FILE_PATH)
            if lock_file.exists():
                logging.info("Otro worker ya está ejecutando la tarea.")
                continue
            
            try:
                # Crea el archivo de bloqueo
                lock_file.touch()

                # Ejecuta la función
                ejecutar_funcion()
            
            finally:
                # Elimina el archivo de bloqueo
                if lock_file.exists():
                    lock_file.unlink()

    # Iniciar el thread
    thread = threading.Thread(target=tarea_en_thread)
    thread.daemon = True  # El hilo se cerrará cuando el proceso principal se detenga
    thread.start()
