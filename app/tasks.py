# myapp/tasks.py

import threading
import time
from datetime import datetime, timedelta
from .models import *
from pathlib import Path

LOCK_FILE_PATH = "/tmp/ejecutar_funcion.lock"

def ejecutar_funcion():
    print("¡Función ejecutada a las 10:00 p.m!")
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
        #print("--------------------------------------------------------------------------------")
        #print(_date_from, _date_to)
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

        _date_from += timedelta(days=1)

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
            print(f"Esperando {tiempo_espera / 3600:.2f} horas hasta la próxima ejecución")

            # Espera hasta las 10:00 p.m.
            time.sleep(tiempo_espera)
            
            # Revisa si el archivo de bloqueo existe
            lock_file = Path(LOCK_FILE_PATH)
            if lock_file.exists():
                print("Otro worker ya está ejecutando la tarea.")
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
