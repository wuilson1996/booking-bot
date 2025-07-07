# myapp/tasks.py

import time
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from .models import *
from django.db import transaction
import logging
from .notification import *

scheduler = BackgroundScheduler()

def acquire_lock(name="ejecutar_funcion", ttl_minutes=90):
    try:
        with transaction.atomic():
            current_time = now()
            expires = current_time + timedelta(minutes=ttl_minutes)

            lock, created = TaskLock.objects.get_or_create(
                name=name,
                defaults={
                    "acquired_at": current_time,
                    "expires_at": expires,
                }
            )

            if not created:
                if lock.expires_at > current_time:
                    generate_log(f"No ha expirado el lock: {now()}", BotLog.HISTORY)
                    return False  # Ya existe y no ha expirado
                # Si expiró, actualizarlo
                lock.acquired_at = current_time
                lock.expires_at = expires
                lock.save()
                generate_log(f"Se ha actualizado el lock: {now()}", BotLog.HISTORY)
            else:
                generate_log(f"Se ha creado el lock: {now()}", BotLog.HISTORY)
            return True
    except Exception as e:
        generate_log(f"No se pudo adquirir el lock en base de datos: {now()}: {e}", BotLog.HISTORY)
        return False

def ejecutar_funcion():
    generate_log(f"¡init copy: {now()}", BotLog.HISTORY)
    # 60 dias
    __date_from = str(now().date())
    __date_to = str(now().date() + timedelta(days=365))
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
                            created = str(now().date()),
                            avail_booking = avail_book
                        )
        except Exception as e:
            generate_log(f"Error copy price: {now()}. {e}", BotLog.HISTORY)
            
        
            #logging.info("[+] Copy price suites feria.")
            # copy price with suites feria.
        try:
            general_search_to_name = GeneralSearch.objects.filter(type_search=2).values_list('city_and_country', flat=True).distinct()
            generate_log(f"Name hotel by copy: {now()} - {str(general_search_to_name)}", BotLog.HISTORY)
            for g in general_search_to_name:
                try:
                    price_with_names = PriceWithNameHotel.objects.filter(title = g, date_from = str(_date_from.date()))
                    for price_with_name in price_with_names:
                        CopyPriceWithNameFromDay.objects.create(
                            price = price_with_name.price,
                            created = str(now().date()),
                            avail = price_with_name
                        )
                except Exception as e:
                    generate_log(f"Error copy price name hotel: {g} {now()}. {e}", BotLog.HISTORY)
        except Exception as e:
            generate_log(f"Error copy price suites feria: {now()}. {e}", BotLog.HISTORY)

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
                    created = str(now().date()),
                    avail_suites_feria = asf
                )
        except Exception as e:
            generate_log(f"Error copy avail suites feria: {now()}. {e}", BotLog.HISTORY)

        try:
            #logging.info("[+] Copy complement total search.")
            for c in Complement.objects.filter(date_from = str(_date_from.date()), start = 4):
                CopyComplementWithDay.objects.create(
                    total_search = c.total_search,
                    created = str(now().date()),
                    complement = c
                )
        except Exception as e:
            generate_log(f"Error complement total search: {now()}. {e}", BotLog.HISTORY)

        _date_from += timedelta(days=1)

    generate_log(f"[+] finish Copy: {now()}", BotLog.HISTORY)

def delete_old_logs(days=5):
    __now = now()
    cutoff_date = __now - timedelta(days=days)
    deleted_count, _ = BotLog.objects.filter(created__lt=cutoff_date).delete()

    count_avail = 0
    for a in AvailableBooking.objects.all():
        _date = datetime(
            year=int(a.date_from.split("-")[0]),
            month=int(a.date_from.split("-")[1]),
            day=int(a.date_from.split("-")[2]),
        )
        if _date.date() < (__now.date() - timedelta(days=16)):
            a.delete()
            count_avail += 1

    return deleted_count, count_avail

def tarea_diaria():
    generate_log(f"[+] Copia diaria iniciado: {now()}", BotLog.HISTORY)
    task_execute = TaskExecute.objects.last()
    if not task_execute:
        generate_log(f"No hay configuración de ejecución", BotLog.HISTORY)
        return

    try:
        deleted = delete_old_logs()
        generate_log(f"Logs eliminados: {deleted[0]} | Avails: {deleted[1]}", BotLog.HISTORY)
    except Exception as e:
        generate_log(f"Error en tarea diaria, delete: {e} - {now()}", BotLog.HISTORY)

    try:
        generate_log(f"Ejecutando tarea de copia: {now()}", BotLog.HISTORY)
        logging.info(f"¡Ejecutando tarea de copia: {now()}")
        ejecutar_funcion()
        generate_log(f"¡Tarea diaria completada! {now()}", BotLog.HISTORY)
        logging.info(f"¡Tarea diaria completada!: {now()}")
    except Exception as e:
        generate_log(f"Error al ejecutar la función: {now()}: {e}", BotLog.HISTORY)
        logging.info(f"Error al ejecutar la función: {now()}: {e}")

def iniciar_scheduler():
    #time.sleep(5)
    if not scheduler.running:
        scheduler.start()
        generate_log(f"[+]Scheduler iniciado: {now()}", BotLog.HISTORY)

    task_execute = TaskExecute.objects.last()
    if not task_execute:
        generate_log(f"[-]No hay configuración de ejecución para el scheduler", BotLog.HISTORY)
        return

    if not acquire_lock(name="espera_tarea_diaria", ttl_minutes=task_execute.time_sleep):
       generate_log(f"[-]Otro worker ya está ejecutando la tarea programada. Este no la agenda. {now()}", BotLog.HISTORY)
       return

    scheduler.add_job(
        tarea_diaria,
        'cron',
        hour=task_execute.hour,
        minute=task_execute.minute,
        second=task_execute.second,
        id='tarea_diaria_programada',
        replace_existing=True
    )
    generate_log(f"[+]Tarea programada diaria a las {task_execute.hour}:{task_execute.minute}:{task_execute.second}", BotLog.HISTORY)

    # ────────────────────── 3. NUEVA tarea cada 30 min ─────────────────────
    #   Ejecutará send_notification inmediatamente y luego cada 30 minutos.
    scheduler.add_job(
        notification_programer,
        trigger=IntervalTrigger(minutes=task_execute.minute_notify, start_date=datetime.now()),
        id='notificacion_30min',
        replace_existing=True,
        max_instances=1          # evita solapamientos
    )
    generate_log("[+] Tarea 'send_notification' programada cada 30 minutos", BotLog.HISTORY)
