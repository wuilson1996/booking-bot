# myapp/tasks.py

import threading
import time
from datetime import datetime, timedelta
from .models import *
from pathlib import Path
import logging
from django.db import transaction

def acquire_lock(name="ejecutar_funcion", ttl_minutes=90):
    try:
        with transaction.atomic():
            current_time = now()
            expires = current_time + timedelta(minutes=ttl_minutes)

            lock, created = TaskLock.objects.select_for_update().get_or_create(
                name=name,
                defaults={
                    "acquired_at": current_time,
                    "expires_at": expires,
                }
            )

            if not created:
                if lock.expires_at > current_time:
                    return False  # Ya existe y no ha expirado
                # Si expiró, actualizarlo
                lock.acquired_at = current_time
                lock.expires_at = expires
                lock.save()

            return True
    except Exception as e:
        generate_log(f"No se pudo adquirir el lock en base de datos: {datetime.now()}: {e}", BotLog.HISTORY)
        return False

def ejecutar_funcion():
    generate_log(f"¡init copy: {datetime.now()}", BotLog.HISTORY)
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
            #logging.info("[+] Copy price.")
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
            generate_log(f"Error copy price: {datetime.now()}. {e}", BotLog.HISTORY)
            
        try:
            #logging.info("[+] Copy price suites feria.")
            # copy price with suites feria.
            price_with_names = PriceWithNameHotel.objects.filter(title = "Hotel Suites Feria de Madrid", date_from = str(_date_from.date()))
            for price_with_name in price_with_names:
                CopyPriceWithNameFromDay.objects.create(
                    price = price_with_name.price,
                    created = str(datetime.now().date()),
                    avail = price_with_name
                )
        except Exception as e:
            generate_log(f"Error copy price suites feria: {datetime.now()}. {e}", BotLog.HISTORY)

        try:
            #logging.info("[+] Copy avail suites feria.")
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
                
                casf3 = CantAvailSuitesFeria.objects.filter(avail_suites_feria = asf, type_avail = 3).last()
                casf3_avail = 0
                if casf3:
                    casf3_avail = casf3.avail
                    
                casf4 = CantAvailSuitesFeria.objects.filter(avail_suites_feria = asf, type_avail = 4).last()
                casf4_avail = 0
                if casf4:
                    casf4_avail = casf4.avail
                CopyAvailWithDaySF.objects.create(
                    type_avail = "0",
                    avail_1 = str(casf1_avail),
                    avail_2 = str(casf2_avail),
                    avail_3 = str(casf3_avail),
                    avail_4 = str(casf4_avail),
                    created = str(datetime.now().date()),
                    avail_suites_feria = asf
                )
        except Exception as e:
            generate_log(f"Error copy avail suites feria: {datetime.now()}. {e}", BotLog.HISTORY)


        try:
            #logging.info("[+] Copy complement total search.")
            for c in Complement.objects.filter(date_from = str(_date_from.date()), start = 4):
                CopyComplementWithDay.objects.create(
                    total_search = c.total_search,
                    created = str(datetime.now().date()),
                    complement = c
                )
        except Exception as e:
            generate_log(f"Error complement total search: {datetime.now()}. {e}", BotLog.HISTORY)

        _date_from += timedelta(days=1)

    generate_log(f"[+] finish Copy: {datetime.now()}", BotLog.HISTORY)

def delete_old_logs(days=5):
    cutoff_date = datetime.now() - timedelta(days=days)
    deleted_count, _ = BotLog.objects.filter(created__lt=cutoff_date).delete()
    return deleted_count

def iniciar_tarea_diaria():
    def tarea_en_thread():
        time.sleep(5)

        # Solo un worker entra aquí gracias al lock de 30 segundos
        if not acquire_lock(name="espera_tarea_diaria", ttl_minutes=0.5):  # 30 segundos
            generate_log(f"Otro worker está encargado de la espera. Este se detiene: {datetime.now()}", BotLog.HISTORY)
            return

        while True:
            ahora = datetime.now()
            proxima_ejecucion = ahora.replace(hour=6, minute=34, second=0, microsecond=0)
            if ahora > proxima_ejecucion:
                proxima_ejecucion += timedelta(days=1)

            tiempo_espera = (proxima_ejecucion - ahora).total_seconds()
            generate_log(f"Esperando {tiempo_espera / 3600:.2f} horas hasta la próxima ejecución: {datetime.now()}", BotLog.HISTORY)
            deleted = delete_old_logs()
            generate_log(f"Se eliminaron {deleted} registros antiguos de logs: {datetime.now()}", BotLog.HISTORY)
            time.sleep(tiempo_espera)

            if not acquire_lock(name="ejecutar_funcion", ttl_minutes=90):
                generate_log(f"Otro worker ya está ejecutando la función principal: {datetime.now()}", BotLog.HISTORY)
                continue

            try:
                ejecutar_funcion()
            except Exception as e:
                generate_log(f"Error al ejecutar la función: {datetime.now()}: {e}", BotLog.HISTORY)

    generate_log(f"Worker ejecutado: {datetime.now()}", BotLog.HISTORY)
    thread = threading.Thread(target=tarea_en_thread)
    thread.daemon = True
    thread.start()