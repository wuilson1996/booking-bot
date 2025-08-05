from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import login as do_login
from django.contrib.auth import authenticate
from django.contrib.auth import logout as do_logout
from rest_framework.decorators import api_view
from rest_framework.response import Response
import locale
import threading
import time
import subprocess
from .booking import *
from .models import *
from .suitesferia import SuitesFeria
from .fee import FeeTask
from django.utils.timezone import localtime
from .serializer import *
from .generate_sample_date import *
from django.db.models import F
from itertools import groupby
from operator import attrgetter
from datetime import timedelta

from .green_correction import SuitesFeria as SuFe
from .green_correction import filtrar_habsol_unicos

def reset_task():
    logging.info("[+] Check cron active...")
    for t in CronActive.objects.filter(active=True):
        t.active = False
        t.save()
    logging.info("[+] Check cron active finish...")

    logging.info("[+] Reset data price status...")
    for t in Price.objects.all():
        #t.plataform_sync = True
        t.active_sync = False
        t.save()
    logging.info("[+] Reset data price status finish...")
    for t in TaskLock.objects.all():
        t.delete()

threading.Thread(target=reset_task).start()

def active_process_sf_v2():
    _credential = CredentialPlataform.objects.filter(plataform_option="suitesferia").last()
    if _credential:
        suites_feria = SuFe(_credential.username, _credential.password)

        tipos = ["1", "2", "3", "4"]
        habitaciones_tipo = suites_feria.get_data_by_query_habits(tipos[0])

        while True:
            try:
                generate_log("Entro en bucle", BotLog.SUITESFERIA)
                start_date = now().date()
                generate_log("Entro en bucle2", BotLog.SUITESFERIA)
                end_date = start_date + timedelta(days=62)
                generate_log("Entro en bucle3", BotLog.SUITESFERIA)
                current = start_date
                #_time = time()
                generate_log("Entro en bucle4", BotLog.SUITESFERIA)
                while current <= end_date:
                    generate_log("Entro en bucle5", BotLog.SUITESFERIA)
                    generate_log(str(current), BotLog.SUITESFERIA)

                    start_date_str = str(current)
                    end_date_str = str((current - timedelta(days=1)))

                    generate_log(f"DATE: {start_date_str} - {end_date_str}", BotLog.SUITESFERIA)

                    confirmadas_asg = suites_feria.get_data_by_query_asghab(start_date_str, end_date_str)
                    generate_log(str(confirmadas_asg), BotLog.SUITESFERIA)
                    generate_log(str(len(confirmadas_asg)), BotLog.SUITESFERIA)

                    habsol_filtrado = []  # opcional: suites_feria.get_data_by_query_habsol(start_date_str, end_date_str, "")
                    #generate_log(habsol_filtrado)

                    # Inicializar estructura para guardar los valores como si fuera _resp_sf
                    dsf = {
                        "date": start_date_str,
                        "avail": {}
                    }

                    for t in tipos:
                        generate_log("---------------------------------------------", BotLog.SUITESFERIA)
                        ocupadas_asghab = [c for c in confirmadas_asg if c[5] == t]
                        ocupadas_habsol = [c for c in habsol_filtrado if c[5] == t]

                        generate_log(f"Tipo: {t}", BotLog.SUITESFERIA)
                        generate_log(f"AsgHab: {len(ocupadas_asghab)} - {ocupadas_asghab}", BotLog.SUITESFERIA)
                        generate_log(f"Habsol filtrado: {len(ocupadas_habsol)} - {ocupadas_habsol}", BotLog.SUITESFERIA)

                        habsol_unicos = filtrar_habsol_unicos(ocupadas_asghab, ocupadas_habsol)
                        generate_log(f"Reservas únicas ({len(habsol_unicos)}): {habsol_unicos}", BotLog.SUITESFERIA)
                        generate_log(f"Total habitaciones tipo {t}: {len(habitaciones_tipo)}", BotLog.SUITESFERIA)

                        ocupadas_total = len(habsol_unicos)
                        disponibles = len(habitaciones_tipo) - ocupadas_total

                        generate_log(f" Ocupadas: {ocupadas_total}", BotLog.SUITESFERIA)
                        generate_log(f" Disponibles: {disponibles}", BotLog.SUITESFERIA)

                        # Agregamos al diccionario para guardar
                        dsf["avail"][t] = disponibles

                    # GUARDAR EN LA BASE DE DATOS
                    try:
                        avail_sf = AvailSuitesFeria.objects.filter(date_avail=dsf["date"]).first()
                        if not avail_sf:
                            avail_sf = AvailSuitesFeria.objects.create(date_avail=dsf["date"])

                        for key_sf, value_sf in dsf["avail"].items():
                            cant_asf = CantAvailSuitesFeria.objects.filter(
                                avail_suites_feria=avail_sf,
                                type_avail=key_sf
                            ).first()
                            if not cant_asf:
                                CantAvailSuitesFeria.objects.create(
                                    type_avail=key_sf,
                                    avail=value_sf,
                                    avail_suites_feria=avail_sf
                                )
                            else:
                                cant_asf.avail = value_sf
                                cant_asf.save()

                        generate_log(f"[+] Guardado disponibilidad v2 para {dsf['date']} correctamente", BotLog.SUITESFERIA)
                    except Exception as e:
                        logging.error(f"[!] Error guardando v2 en BD para {dsf['date']}: {str(e)}")

                    current += timedelta(days=1)

                #generate_log(f"Tiempo total: {time() - _time}", BotLog.SUITESFERIA)

                logging.info(f"[+] Suites feria v2 actualizado: {now()}")
                generate_log(f"[+] Dispo Suites feria v2 actualizado: {now()}", BotLog.SUITESFERIA)

                if not check_finish_process():
                    logging.info(f"[+] {now()} Finish process, proceso suites feria v2...")
                    generate_log(f"[+] Finalizando proceso, proceso suites feria v2...", BotLog.SUITESFERIA)
                    break
                
                time.sleep(300)

                if not check_finish_process():
                    logging.info(f"[+] {now()} Finish process, proceso suites feria v2...")
                    generate_log(f"[+] Finalizando proceso, proceso suites feria v2...", BotLog.SUITESFERIA)
                    break
            except Exception as er:
                logging.info(f"[+] {now()} Error Get Suites feria v2: "+str(er))
                generate_log("[+] Error Get Suites feria v2: "+str(er), BotLog.SUITESFERIA)
                if not check_finish_process():
                    logging.info(f"[+] {now()} Finish process, proceso suites feria v2...")
                    generate_log(f"[+] Finalizando proceso, proceso suites feria v2...", BotLog.SUITESFERIA)
                    break
                time.sleep(300)

def active_process_sf():
    _credential = CredentialPlataform.objects.filter(plataform_option = "suitesferia").first()
    if _credential:
        suites_feria = SuitesFeria(_credential.username, _credential.password)
        while True:
            # get data suitesferia.
            try:  
                resp = suites_feria.login()
                logging.info(f"[+] Actualizando suites feria: {now().date()} {resp}")
                generate_log(f"[+] Actualizando Dispo suites feria: {resp['message']}", BotLog.SUITESFERIA)
                if resp["code"] == 200:
                    time.sleep(60)
                    break
            except Exception as e:
                logging.info(f"[+] {now()} Error Get Suites feria: "+str(er))
                generate_log("[+] Error Get Suites feria", BotLog.SUITESFERIA)
                if not check_finish_process():
                    logging.info(f"[+] {now()} Finish process, proceso suites feria...")
                    generate_log(f"[+] Finalizando proceso, proceso suites feria...", BotLog.SUITESFERIA)
                    break
                time.sleep(600)
        while True:
            # get data suitesferia.
            try:
                resp_sf = suites_feria.disponibilidad(now().date())
                _resp_sf = suites_feria.format_avail(resp_sf)
                for dsf in _resp_sf:
                    avail_sf = AvailSuitesFeria.objects.filter(date_avail = dsf["date"]).first()
                    if not avail_sf:
                        avail_sf = AvailSuitesFeria.objects.create(date_avail = dsf["date"])
                    for key_sf, value_sf in dsf["avail"].items():
                        cant_asf = CantAvailSuitesFeria.objects.filter(avail_suites_feria = avail_sf, type_avail = key_sf).first()
                        if not cant_asf:
                            cant_asf = CantAvailSuitesFeria.objects.create(
                                type_avail = key_sf,
                                avail = value_sf,
                                avail_suites_feria = avail_sf
                            )
                        else:
                            cant_asf.avail = value_sf
                            cant_asf.save()
                
                logging.info(f"[+] Suites feria actualizado: {now()} {resp_sf}")
                generate_log(f"[+] Dispo Suites feria actualizado: {resp_sf['message']}", BotLog.SUITESFERIA)

                if not check_finish_process():
                    logging.info(f"[+] {now()} Finish process, proceso suites feria...")
                    generate_log(f"[+] Finalizando proceso, proceso suites feria...", BotLog.SUITESFERIA)
                    break
                
                time.sleep(1200)

                if not check_finish_process():
                    logging.info(f"[+] {now()} Finish process, proceso suites feria...")
                    generate_log(f"[+] Finalizando proceso, proceso suites feria...", BotLog.SUITESFERIA)
                    break
            except Exception as er:
                logging.info(f"[+] {now()} Error Get Suites feria: "+str(er))
                generate_log("[+] Error Get Suites feria", BotLog.SUITESFERIA)
                if not check_finish_process():
                    logging.info(f"[+] {now()} Finish process, proceso suites feria...")
                    generate_log(f"[+] Finalizando proceso, proceso suites feria...", BotLog.SUITESFERIA)
                    break
                time.sleep(600)

        resp_l = suites_feria.logout()       
        logging.info(f"[+] Suites feria actualizado: {now()} {resp_l}")
        generate_log(f"[+] Dispo Suites feria actualizado: {resp_l['message']}", BotLog.SUITESFERIA)

        logging.info(f"[+] {now()} Proceso suites feria Finalizando...")
        generate_log("[+] Proceso suites feria Finalizando...", BotLog.SUITESFERIA)

def get_current_bot_range(bot_setting):
    """
    Retorna el primer BotRange válido para el bot_setting actual,
    que coincida con el día actual y hora actual.
    """

    # Día y hora actuales
    current_time = now().time()
    current_day = now().weekday()

    # Mapeo de inglés a español si tus días están almacenados así
    dias_map = {
        0: 'lunes',
        1: 'martes',
        2: 'miércoles',
        3: 'jueves',
        4: 'viernes',
        5: 'sábado',
        6: 'domingo'
    }
    dia_actual = dias_map.get(current_day)

    # Buscar todos los rangos del bot
    bots_range = BotRange.objects.filter(bot_setting=bot_setting)

    for btr in bots_range:
        # Comprobar si el día aplica
        day_filter = btr.day_name.filter(name=dia_actual)
        #generate_log(f"[-] Day: {dia_actual} - {day_filter}", BotLog.BOOKING)
        if day_filter:
            # Comprobar si la hora está en algún rango válido
            for hr in btr.hour_range.all():
                if hr.hour_from and hr.hour_to:
                    #generate_log(f"[-] Day: {hr.hour_from} <= {current_time} <= {hr.hour_to} ", BotLog.BOOKING)
                    if hr.hour_from <= current_time <= hr.hour_to:
                        generate_log(f"[-] Day: {hr.hour_from} <= {current_time} <= {hr.hour_to} - Valido: {btr}", BotLog.BOOKING)
                        return btr, hr  # ✅ Retornar el primer válido encontrado

    return None, None  # ❌ Si no se encontró ningún rango válido

def check_change_range(hr, stop_event, stop_event_check):
    while True:
        try:
            if not check_finish_process():
                #logging.info(f"[+] {now()} Finish process, Check range...")
                generate_log(f"[+] Finalizando proceso, Check range | Rango: {hr.hour_from} - {hr.hour_to}...", BotLog.BOOKING)
                break
            if stop_event_check and stop_event_check.is_set():
                #logging.info(f"[+] {now()} Deteniendo ejecución de verificacion")
                generate_log(f"[+] {now()} Deteniendo ejecución de verificacion | Rango: {hr.hour_from} - {hr.hour_to}", BotLog.BOOKING)
                break
            if hr.hour_to:
                now_time = now().time()
                cutoff_time = (dt.combine(dt.today(), hr.hour_to) - datetime.timedelta(minutes=5)).time()
                #logging.info(f"[!] Verificando Horario, Fin {cutoff_time} - Ahora: {now_time} | Rango: {hr.hour_from} - {hr.hour_to}")
                generate_log(f"[!] Verificando Horario, Fin {cutoff_time} - Ahora: {now_time} | Rango: {hr.hour_from} - {hr.hour_to}", BotLog.BOOKING)
                if now_time >= cutoff_time:
                    #logging.info("[!] Finalizando hilos antes del cambio de rango horario.")
                    generate_log(f"[!] Finalizando hilos por cambio de rango horario | Rango: {hr.hour_from} - {hr.hour_to}.", BotLog.BOOKING)
                    stop_event.set()
                    #logging.info("[+] Reiniciando con siguiente rango tras esperar 5 minutos.")
                    generate_log(f"[+] Reiniciando con siguiente rango tras esperar 5 minutos | Rango: {hr.hour_from} - {hr.hour_to}.", BotLog.BOOKING)
        except Exception as e:
            generate_log(f"[+] Error Check change range: {e}...", BotLog.BOOKING)
        sleep(60)

def get_cookie_param(instances, general_search:GeneralSearch):
    while True:
        status_param = instances[0]["booking"].get_params(instances[0]["driver"], general_search.city_and_country)
        generate_log(f"[+] Configurando url base...", BotLog.BOOKING)
        #print(status_param)
        if status_param:
            generate_log(f"[+] Configurando url base... {status_param}", BotLog.BOOKING)
            cookie_url = CookieUrl.objects.create(
                name = general_search.city_and_country,
                label = status_param
            )
            break
        sleep(5)
    return cookie_url

def active_process(bot_setting:BotSetting):
    general_search = GeneralSearch.objects.filter(type_search = 1).last()
    general_search_to_name = GeneralSearch.objects.filter(type_search = 2)
    instances = []

    # active bot
    bot_auto = BotAutomatization.objects.last()
    bot_auto.active = True
    bot_auto.currenct = True
    bot_auto.save()

    for p in general_search.proces_active.all():
        booking = BookingSearch()
        instances.append({
            "booking": booking,
            "driver": booking._driver(general_search.url)
        })

    #logging.info(f"[+] {now()} Activando process...")
    generate_log("[+] Activando process...", BotLog.BOOKING)
    threading.Thread(target=active_process_sf_v2).start()

    while True:
        try:
            cookie_url = get_cookie_param(instances, general_search)
            stop_event = threading.Event()
            if not check_finish_process():
                #logging.info(f"[+] {now()} Finish process...")
                generate_log(f"[+] Finalizando proceso...", BotLog.BOOKING)
                break

            if bot_auto.automatic:
                bot_range, hr = get_current_bot_range(bot_setting)
            else:
                bot_range = BotRange.objects.filter(bot_setting=bot_setting, number=1).last()

            if not bot_range:
                generate_log(f"[-] No hay rango válido actualmente. {now()}", BotLog.BOOKING)
                #logging.info("[-] No hay rango válido actualmente.")
                time.sleep(60)
                continue

            if bot_auto.automatic:
                stop_event_check = threading.Event()
                bot_range.date_from = now().date() + datetime.timedelta(days=bot_range.days_from)
                bot_range.date_end = now().date() + datetime.timedelta(days=bot_range.days)
                generate_log(f"Buscar Datos Automaticos: {bot_range.date_from} - {bot_range.date_end} | {bot_range.days_from} - {bot_range.days} | {hr.hour_from} - {hr.hour_to}", BotLog.BOOKING)
                
                generate_log(f"[+] Iniciando verificacion de cambio de rango...", BotLog.BOOKING)
                threading.Thread(target=check_change_range, args=(hr, stop_event, stop_event_check)).start()

            threads = []
            cont = 0
            for p in ProcessActive.objects.filter(type_proces = 1):
                try:
                    #logging.info(f"[+] {now()} Process active in while. Search with city browser... {instances[cont]['booking']}")
                    generate_log("[+] Buscando posiciones...", BotLog.BOOKING)

                    process = threading.Thread(
                        target=instances[cont]["booking"].controller, 
                        args=(
                            instances[cont]["driver"],
                            p,
                            general_search.city_and_country,
                            general_search_to_name,
                            bot_range.date_from,
                            bot_range.date_end,
                            stop_event,
                            cookie_url.label
                        )
                    )
                    process.daemon = True
                    process.start()
                    threads.append(process)
                except Exception as ec:
                    logging.info(f"[-] {now()} Error in Execute controller positions... {ec}")
                    generate_log(f"[-] Error in Execute controller positions... {ec}", BotLog.BOOKING)
                cont += 1

            for t in threads:
                #logging.info(f"[+] {now()} Esperando finalizacion de thread...")
                generate_log("[+] Esperando finalizacion de thread...", BotLog.BOOKING)
                t.join()
            
            if not check_finish_process():
                #logging.info(f"[+] {now()} Finish process, despues de posiciones...")
                generate_log(f"[+] Finalizando proceso, despues de posiciones...", BotLog.BOOKING)
                break

            # add process name hotel.
            #logging.info(f"[+] {now()} Process active in while. Search with name browser... {instances[0]['booking']}")
            generate_log("[+] Buscando hoteles por nombre...", BotLog.BOOKING)
            for gs in general_search_to_name:
                #cookie_url = get_cookie_param(instances, gs)
                if not check_finish_process():
                    #logging.info(f"[+] {now()} Finish process de busqueda por nombre...")
                    generate_log(f"[+] {now()} Finish process de busqueda por nombre...", BotLog.BOOKING)
                    break
                for _pa in gs.proces_active.all():
                    if not check_finish_process():
                        #logging.info(f"[+] {now()} Finish process2 de busqueda por nombre...")
                        generate_log(f"[+] {now()} Finish process2 de busqueda por nombre...", BotLog.BOOKING)
                        break
                    try:
                        instances[0]["booking"].controller(
                            instances[0]["driver"],
                            _pa,
                            gs.city_and_country,
                            None,
                            bot_range.date_from,
                            bot_range.date_end,
                            stop_event,
                            cookie_url.label
                        )
                    except Exception as ec:
                        logging.info(f"[-] {now()} Error in Execute controller with name... {ec}")
                        generate_log(f"[-] Error in Execute controller with name... {ec}", BotLog.BOOKING)

            if not check_finish_process():
                #logging.info(f"[+] {now()} Finish process, despues de nombres...")
                generate_log(f"[+] Finalizando proceso, despues de nombres...", BotLog.BOOKING)
                break

            seconds = 60 * (general_search.time_sleep_minutes if general_search else 3)
            #logging.info(f"[+] {now()} Sleep {seconds} seconds...")
            generate_log(f"[+] Sleep {seconds} seconds...", BotLog.BOOKING)
            sleep(seconds)

            if not check_finish_process():
                #logging.info(f"[+] {now()} Finish process, proceso final...")
                generate_log(f"[+] Finalizando proceso, proceso final...", BotLog.BOOKING)
                break

            #logging.info(f"[+] {now()} Sleep {seconds} seconds finish...")
            generate_log(f"[+] Sleep {seconds} seconds finish...", BotLog.BOOKING)

            if bot_auto.automatic:
                try:
                    stop_event_check.set()
                    if check_finish_process():
                        sleep(300)
                except Exception as e:
                    generate_log(f"[+] Error Stop Event: {e}...", BotLog.BOOKING)
        except Exception as e:
            logging.info(f"[-] {now()} Error process general: {e}...")
            generate_log(f"[-] Error process general: {e}...", BotLog.BOOKING)

    for c in instances:
        try:
            c["booking"].close(c["driver"])
        except Exception as e:
            logging.info(f"[+] {now()} Error Finalizar Booking...")
            generate_log(f"[+] Error al Finalizar Bot Booking: {e}...", BotLog.BOOKING)

    #logging.info(f"[+] {now()} Process Booking Finalizando...")
    generate_log("[+] Process Bot Booking Finalizando...", BotLog.BOOKING)
    try:
        if bot_auto.automatic:
            stop_event_check.set()
    except Exception as e:
        generate_log(f"[+] Error Stop Event, General: {e}...", BotLog.BOOKING)
    #bot_auto = BotAutomatization.objects.last()
    #bot_auto.currenct = False
    #bot_auto.save()

@api_view(["POST"])
def get_booking(request):
    result = {"code": 400, "status": "Fail", "message":"User not authenticated."}
    if request.user.is_authenticated:
        bot_auto = BotAutomatization.objects.last()
        result = {"code": 200, "status": "OK", "message":"Proceso activado correctamente."}
        if not bot_auto.active:
            bot_auto.active = False
            bot_auto.automatic = True if request.data["automatic"] == "true" else False
            bot_auto.save()

            if bot_auto.automatic:
                # configuracion de bot automatico
                bot_setting = bot_auto.bot_auto
                #bot_ranges = BotRange.objects.filter(bot_setting = bot_setting)
                #_bot_range = BotRange.objects.filter(pk = request.data["bot_range"]).first()
                #bot_setting.number_from = _bot_range.number
                #bot_setting.number_end = len(bot_ranges)
                #bot_setting.save()
            else:
                # configuracion de bot default.
                bot_setting = bot_auto.bot_default
                bot_gange = BotRange.objects.filter(bot_setting = bot_setting).last()
                bot_gange.date_end = request.data["date"]
                bot_gange.date_from = request.data["dateFrom"]
                bot_gange.save()

            threading.Thread(target=active_process, args=(bot_setting,)).start()
        else:
            result["message"] = "Proceso ya se encuentra activado."
            result["code"] = 400
    return Response(result)

def reset_service_with_task():
    reset_service()
    generate_log(f"Reset process: {now()}", BotLog.HISTORY)
    threading.Thread(target=active_process).start()

def reset_service():
    try:
        subprocess.run('sudo sync; echo 1 | sudo tee /proc/sys/vm/drop_caches', shell=True)
        logging.info("Clear memory1.")
    except subprocess.CalledProcessError as e:
        logging.info(f"Error clear memory1: {e}")
    except Exception as ex:
        logging.info(f"Se produjo un error in cleal memory1: {ex}")
    
    try:
        subprocess.run('sudo sync; echo 2 | sudo tee /proc/sys/vm/drop_caches', shell=True)
        logging.info("Clear memory2.")
    except subprocess.CalledProcessError as e:
        logging.info(f"Error clear memory2: {e}")
    except Exception as ex:
        logging.info(f"Se produjo un error in cleal memory2: {ex}")

    try:
        subprocess.run('sudo sync; echo 3 | sudo tee /proc/sys/vm/drop_caches', shell=True)
        logging.info("Clear memory3.")
    except subprocess.CalledProcessError as e:
        logging.info(f"Error clear memory3: {e}")
    except Exception as ex:
        logging.info(f"Se produjo un error in cleal memory3: {ex}")

    bot_auto = BotAutomatization.objects.last()
    bot_auto.active = False
    bot_auto.save()

    # for _ in range(310):
    #     bot_auto = BotAutomatization.objects.last()
    #     if not bot_auto.currenct:
    #         break
    #     sleep(1)
    sleep(40)
    bot_auto.currenct = False
    bot_auto.save()
    sleep(1)
    try:
        subprocess.run(['sudo', 'systemctl', 'restart', "booking"], check=True)
        #subprocess.run(['sudo', 'systemctl', 'restart', "nginx"], check=True)
        logging.info("Servicio booking y nginx reiniciado correctamente.")
    except subprocess.CalledProcessError as e:
        logging.info(f"Error al reiniciar el servicio booking: {e}")
    except Exception as ex:
        logging.info(f"Se produjo un error: {ex}")

@api_view(["POST"])
def finish_get_booking(request):
    result = {"code": 400, "status": "Fail", "message":"User not authenticated."}
    if request.user.is_authenticated:
        threading.Thread(target=reset_service).start()
        #reset_service()
        result["code"] = 200
        result["status"] = "OK"
        result["message"] = "Proceso desactivado correctamente."
    return Response(result)

@api_view(["POST"])
def check_booking_process(request):
    result = {"code": 400, "status": "Fail", "message":"User not authenticated."}
    if request.user.is_authenticated:
        bot_auto = BotAutomatization.objects.last()
        
        bot_logs = {}
        bot_log = BotLog.objects.filter(plataform_option = BotLog.BOOKING).last()
        if bot_log:
            bot_log_range_vh = BotLog.objects.filter(plataform_option = BotLog.BOOKING, description__icontains="[!] Verificando Horario").last()
            bot_log_range = BotLog.objects.filter(plataform_option = BotLog.BOOKING, description__icontains="Buscar Datos Automaticos").last()
            ranges = list(bot_log_range.description.split("|")) if bot_log_range else []
            _date_task = dt(
                year=int(str(bot_log.created).split(" ")[0].split("-")[0]),
                month=int(str(bot_log.created).split(" ")[0].split("-")[1]),
                day=int(str(bot_log.created).split(" ")[0].split("-")[2]),
                hour=int(str(bot_log.created).split(" ")[1].split(":")[0]),
                minute=int(str(bot_log.created).split(" ")[1].split(":")[1]),
            )
            __current_now = now()
            _date_task_now = dt(
                year=int(str(__current_now).split(" ")[0].split("-")[0]),
                month=int(str(__current_now).split(" ")[0].split("-")[1]),
                day=int(str(__current_now).split(" ")[0].split("-")[2]),
                hour=int(str(__current_now).split(" ")[1].split(":")[0]),
                minute=int(str(__current_now).split(" ")[1].split(":")[1]),
            )
            _date_rest = (_date_task_now - _date_task).total_seconds() / 60
            #generate_log(f"[+] Test Get: {_date_rest} | {_date_task} | {_date_task_now}", BotLog.HISTORY)
            bot_logs[bot_log.plataform_option] = {
                "description": bot_log.description,
                "created": generate_date_with_month_time(str(bot_log.created)),
                "range_hour": ranges[2] if ranges else "No hay rango disponible",
                "range_days": ranges[1] if ranges else "No hay rango disponible",
                "range_date": ranges[0] if ranges else "No hay rango disponible",
                "log_range": bot_log_range.description if bot_log_range else "No hay rango disponible",
                "alarm": True if _date_rest > 10 else False,
                "minute": _date_rest
            }
        bot_log = BotLog.objects.filter(plataform_option = BotLog.ROOMPRICE).last()
        if bot_log:
            bot_logs[bot_log.plataform_option] = {
                "description": bot_log.description, 
                "created": generate_date_with_month_time(str(bot_log.created))
            }
        bot_log = BotLog.objects.filter(plataform_option = BotLog.SUITESFERIA).last()
        if bot_log:
            _date_task = dt(
                year=int(str(bot_log.created).split(" ")[0].split("-")[0]),
                month=int(str(bot_log.created).split(" ")[0].split("-")[1]),
                day=int(str(bot_log.created).split(" ")[0].split("-")[2]),
                hour=int(str(bot_log.created).split(" ")[1].split(":")[0]),
                minute=int(str(bot_log.created).split(" ")[1].split(":")[1]),
            )
            __current_now = now()
            _date_task_now = dt(
                year=int(str(__current_now).split(" ")[0].split("-")[0]),
                month=int(str(__current_now).split(" ")[0].split("-")[1]),
                day=int(str(__current_now).split(" ")[0].split("-")[2]),
                hour=int(str(__current_now).split(" ")[1].split(":")[0]),
                minute=int(str(__current_now).split(" ")[1].split(":")[1]),
            )
            _date_rest = (_date_task_now - _date_task).total_seconds() / 60
            #generate_log(f"[+] Test Get: {_date_rest} | {_date_task} | {_date_task_now}", BotLog.HISTORY)
            bot_logs[bot_log.plataform_option] = {
                "description": bot_log.description, 
                "created": generate_date_with_month_time(str(bot_log.created)),
                "alarm": True if _date_rest > 10 else False,
                "minute": _date_rest
            }
        
        _date_from = dt(
            year=int(request.POST["date"].split("-")[0]),
            month=int(request.POST["date"].split("-")[1]),
            day=int(request.POST["date"].split("-")[2])
        )
        __date_to = str(_date_from.date() + datetime.timedelta(days=int(request.POST["days"])))
        _date_to = dt(
            year=int(__date_to.split("-")[0]),
            month=int(__date_to.split("-")[1]),
            day=int(__date_to.split("-")[2])
        )
        status_price = []
        while _date_from.date() <= _date_to.date():
            prices = []
            for _price in Price.objects.filter(date_from = str(_date_from.date())):
                prices.append(
                    {
                        "price": _price.price, 
                        "pSync": _price.plataform_sync, 
                        "active": _price.active_sync, 
                        "date_from": _price.date_from, 
                        "occupancy": _price.occupancy
                    }
                )
            status_price.append(prices)
            _date_from += datetime.timedelta(days=1)

        # obtener horario de ejecucion
        task_execute = TaskExecute.objects.all().last()
        __now = now()
        current = __now.replace(hour=task_execute.hour, minute=task_execute.minute, second=task_execute.second, microsecond=0)
        _next = current + datetime.timedelta(days=1)

        # Calcula la ventana de 10 minutos antes y después
        inicio_ventana = current - datetime.timedelta(minutes=10)
        fin_ventana = current + datetime.timedelta(minutes=10)
        #print(inicio_ventana, current, fin_ventana, __now)

        # Verifica si el momento actual está dentro de esa ventana
        in_range = inicio_ventana <= __now <= fin_ventana
        _message = "Se ha generado la copia de hoy."
        if in_range:
            _message = "Generando copia de hoy."
        elif current > __now:
            _message = "No se ha generado aún la copia de hoy."

        result = {
            "code": 200, 
            "status": "OK", 
            "active":bot_auto.active, 
            "current":bot_auto.currenct, 
            "botLog": bot_logs, 
            "status_price": status_price, 
            "task": {
                "status": in_range, 
                "now": generate_date_with_month_time(str(__now)), 
                "current": generate_date_with_month_time(str(current)), 
                "next": generate_date_with_month_time(str(_next)),
                "from_task": generate_date_with_month_time(str(inicio_ventana)),
                "to_task": generate_date_with_month_time(str(fin_ventana)),
                "copy": _message
            }
        }
    return Response(result)

@api_view(["POST"])
def save_message(request):
    result = {"code": 400, "status": "Fail", "message":"User not authenticated."}
    if request.user.is_authenticated:
        #print(request.data)
        _message_by_day = MessageByDay.objects.filter(
            date_from = request.data["date"],
            occupancy = request.data["occupancy"]
        ).last()
        __message_name = MessageName.objects.filter(pk = request.data["text"]).first()
        if not _message_by_day:
            _message_by_day = MessageByDay.objects.create(
                date_from = request.data["date"],
                occupancy = request.data["occupancy"],
                text_name = __message_name,
                updated = now(),
                created = now()
            )
        else:
            if _message_by_day.text_name:
                if _message_by_day.text_name.pk != __message_name:
                    _message_by_day = MessageByDay.objects.create(
                        date_from = request.data["date"],
                        occupancy = request.data["occupancy"],
                        text_name = __message_name,
                        updated = now(),
                        created = now()
                    )
            else:
                _message_by_day = MessageByDay.objects.create(
                    date_from = request.data["date"],
                    occupancy = request.data["occupancy"],
                    text_name = __message_name,
                    updated = now(),
                    created = now()
                )
        result = {
            "code": 200,
            "status": "OK",
            "message":"Proceso activado correctamente.",
            "updated": generate_date_with_month_time(str(_message_by_day.updated)),
            "bg_color": __message_name.bg_color,
            "text_color": __message_name.text_color
        }
    return Response(result)

def task_save_fee_masive(cron:CronActive, _credential:CredentialPlataform, days):
    while cron.current_date > now():
        sleep(1)

    fee = FeeTask()
    _driver = fee._driver()
    _check = fee.sign_in(_driver, _credential.username, _credential.password)
    if _check:
        prices_list = []
        prices_list_not = []
        prices_all = Price.objects.all().order_by("-id")
        _prices = {}
        for price_obj in prices_all:
            if datetime.datetime(year=int(price_obj.date_from.split("-")[0]), month=int(price_obj.date_from.split("-")[1]), day=int(price_obj.date_from.split("-")[2])).date() >= now().date():
                if price_obj.date_from not in list(_prices.keys()):
                    #plataform_sync = False
                    _prices[price_obj.date_from] = {
                        "plataform_sync": False
                    }

                if price_obj.price != None and price_obj.price != "":
                    if not price_obj.plataform_sync:
                        _prices[price_obj.date_from]["plataform_sync"] = True

                    _prices[price_obj.date_from][str(price_obj.occupancy)] = price_obj
                    price_obj.active_sync = True
                    price_obj.save()

        #print(_prices)
        #logging.info(_prices)
        logging.info("----------------------------------------------")
        for _key, _value in _prices.items():
            _check = False
            if _value["plataform_sync"]:
                logging.info(_value)
                del _value["plataform_sync"]
                _check = fee.send_fee_masive(_driver, _value, _key)
                sleep(10)
            if _check:
                prices_list.append(_value)
            else:
                prices_list_not.append(_value)
            logging.info("----------------------------------------------")

        if prices_list:
            fee.update_with_range(_driver, "Masive instance", prices_list, False)

        sleep(5)
        fee.close(_driver)
        for price in prices_list + prices_list_not:
            for key, value in price.items():
                if key != "plataform_sync":
                    logging.info(f"{key} {value}")
                    _p = Price.objects.filter(pk = value.pk).first()
                    _p.active_sync = False
                    _p.save()

def task_save_fee(price, _date, cron:CronActive, _credential:CredentialPlataform):
    try:
        while cron.current_date > now():
            sleep(1)

        #cont = 0
        #while True:
        try:
            #for _ in range(2):
            fee = FeeTask()
            _driver = fee._driver()
            _check = fee.controller(_driver, price, _date, _credential.username, _credential.password)
            sleep(5)
            fee.close(_driver)
            for key, value in price.items():
                _p = Price.objects.filter(pk = value.pk).first()
                _p.active_sync = False
                _p.save()
            # if not _check:
            #     break
            #if _check or cont >= 3:
            #    break
            #cont += 1
        except Exception as e:
            logging.info(f"Error general Fee: {e}")
            generate_log(f"Error general Fee: {now()}: {e}", BotLog.ROOMPRICE)

        cron.active = False
        cron.save()
    except Exception as e:
        logging.info(f"Error task fee: {e}")
        generate_log(f"Error task fee: {now()}: {e}", BotLog.ROOMPRICE)

@api_view(["POST"])
def upgrade_fee(request):
    result = {"code": 400, "status": "Fail", "message":"User not authenticated."}
    if request.user.is_authenticated:
        try:
            _prices = {}
            __time = 90
            # if request.data["masive"] == "false":
            #     for p in Price.objects.filter(date_from = request.data["date"]):
            #         if p.price != None and p.price != "":
            #             _prices[str(p.occupancy)] = p
            #             p.active_sync = True
            #             p.save()

            message = "Proceso activado correctamente."
            # _credential = CredentialPlataform.objects.filter(plataform_option = "roomprice").first()
            # if _credential:
            #     cron_active = CronActive.objects.last()
            #     #print(cron_active)
            #     if cron_active:
            #         if cron_active.active:
            #             cron = CronActive.objects.create(
            #                 active = True,
            #                 current_date = cron_active.current_date + datetime.timedelta(minutes=1.5)
            #             )
            #         else:
            #             cron = CronActive.objects.create(
            #                 active = True,
            #                 current_date = now()
            #             )
            #     else:
            #         cron = CronActive.objects.create(
            #             active = True,
            #             current_date = now()
            #         )
            #     if request.data["masive"] == "false":
            #         threading.Thread(
            #             target=task_save_fee, 
            #             args=(
            #                 _prices,
            #                 request.data["date"],
            #                 cron,
            #                 _credential
            #             )
            #         ).start()
            #         __time += (cron.current_date - now()).total_seconds()
            #     else:
            #         threading.Thread(
            #             target=task_save_fee_masive, 
            #             args=(
            #                 cron,
            #                 _credential,
            #                 0
            #             )
            #         ).start()
            #         __time += (cron.current_date - now()).total_seconds()
            # else:
            #     message = "No se ha configurado credenciales"
        except Exception as e:
            logging.info(f"Error price: {e}")
            generate_log(f"Error price: {now()}: {e}", BotLog.ROOMPRICE)
            message = f"Error price: {e}"

        result = {"code": 200, "status": "OK", "message":message, "time": int(__time)}
    return Response(result)

@api_view(["POST"])
def save_price(request):
    result = {"code": 400, "status": "Fail", "message":"User not authenticated."}
    if request.user.is_authenticated:
        _price = Price.objects.filter(
            date_from = request.data["date"],
            occupancy = request.data["occupancy"]
        ).last()
        if not _price:
            _price = Price.objects.create(
                date_from = request.data["date"],
                occupancy = request.data["occupancy"],
                price = request.data["text"],
                updated = now(),
                created = now()
            )
        else:
            #if _price.price != request.data["text"]:
            _price.price = request.data["text"]
            _price.plataform_sync = False
            _price.active_sync = False
            _price.updated = now()
            _price.save()
        result = {
            "code": 200, 
            "status": "OK", 
            "message":"Proceso activado correctamente.", 
            "updated": generate_date_with_month_time(str(_price.updated)), 
            "pSync": _price.plataform_sync,
            "active": _price.active_sync,
            "pk_price": _price.pk,
        }
    return Response(result)

@api_view(["POST"])
def save_temp(request):
    result = {"code": 400, "status": "Fail", "message":"User not authenticated."}
    if request.user.is_authenticated:
        _temp_by_day = TemporadaByDay.objects.filter(
            date_from = request.data["date"]
        ).last()
        bg_color = "bg-success"
        if request.data["numTemp"]:
            if not _temp_by_day:
                _temp_by_day = TemporadaByDay.objects.create(
                    date_from = request.data["date"],
                    bg_color = TemporadaByDay.COLORS[int(request.data["numTemp"])][0],
                    text_color = "text-white",
                    number = request.data["numTemp"],
                    updated = now(),
                    created = now()
                )
            else:
                _temp_by_day.bg_color = TemporadaByDay.COLORS[int(request.data["numTemp"])][0]
                _temp_by_day.number = request.data["numTemp"]
                _temp_by_day.updated = now()
                _temp_by_day.save()
            bg_color = _temp_by_day.bg_color
        else:
            if _temp_by_day:
                _temp_by_day.delete()

        result = {"code": 200, "status": "OK", "message":"Proceso activado correctamente.", "bg_color": bg_color}
    return Response(result)

@api_view(["POST"])
def save_event(request):
    result = {"code": 400, "status": "Fail", "message":"User not authenticated."}
    if request.user.is_authenticated:
        _event_by_day = EventByDay.objects.filter(
            date_from = request.data["date"],
            occupancy = request.data["occupancy"]
        ).last()
        if not _event_by_day:
            _event_by_day = EventByDay.objects.create(
                date_from = request.data["date"],
                occupancy = request.data["occupancy"],
                text = str(request.data["text"]).strip().replace("\n", ". "),
                updated = now(),
                created = now()
            )
        else:
            _event_by_day.date_from = request.data["date"]
            _event_by_day.occupancy = request.data["occupancy"]
            _event_by_day.text = request.data["text"]
            _event_by_day.updated = now()
            _event_by_day.save()

        result = {"code": 200, "status": "OK", "message":"Proceso activado correctamente."}
    return Response(result)

@api_view(["POST"])
def save_avail_with_date(request):
    result = {"code": 400, "status": "Fail", "message":"User not authenticated."}
    if request.user.is_authenticated:
        _event_by_day = AvailWithDate.objects.filter(
            date_from = request.data["date"],
        ).last()
        if not _event_by_day:
            _event_by_day = AvailWithDate.objects.create(
                date_from = request.data["date"],
                avail = request.data["avail"],
                updated = now(),
                created = now()
            )
        else:
            _event_by_day.avail = request.data["avail"]
            _event_by_day.updated = now()
            _event_by_day.save()

        result = {"code": 200, "status": "OK", "message":"Proceso activado correctamente."}
    return Response(result)

@api_view(["POST"])
def export_price_from_excel(request):
    result = {"code": 400, "status": "Fail", "message": "User not authenticated."}

    if request.user.is_authenticated:
        generate_log(f"[+] Exportando precios...", BotLog.BOOKING)
        try:
            prices_all = Price.objects.all().order_by("-id")
            _prices = {}

            for price_obj in prices_all:
                date_str = price_obj.date_from
                date_parts = [int(part) for part in date_str.split("-")]
                date_obj = datetime.date(*date_parts)

                if date_obj >= now().date():
                    if date_str not in _prices:
                        _prices[date_str] = {"date": date_str}

                    if price_obj.price not in [None, ""]:
                        _prices[date_str][str(price_obj.occupancy)] = price_obj.price

            # Convert dict to list of rows
            data_rows = list(_prices.values())

            # Crear DataFrame
            df = pd.DataFrame(data_rows)

            # Columnas esperadas del 0 al 6 más la fecha
            columnas = ["date"] + [str(i) for i in range(7)]
            for col in columnas:
                if col not in df.columns:
                    df[col] = None

            df = df[columnas]

            # Convertir columna 'date' a datetime y ordenar
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")

            # Renombrar columnas
            df.rename(columns={
                "0": "individual",
                "1": "matrimonial",
                "2": "doble",
                "3": "triple",
                "5": "suites"
            }, inplace=True)

            # Crear carpeta si no existe
            export_dir = f"media/proces/"
            os.makedirs(export_dir, exist_ok=True)

            file_path = os.path.join(export_dir, f"{request.user.username}.xlsx")
        
            df.to_excel(file_path, index=False)
            message = "Procesado correctamente"
            result = {
                "code": 200,
                "status": "OK",
                "message": message,
                "file": f"{request.user.username}.xlsx",
                "path": file_path
            }
            generate_log(f"[+] Exportacion de precio con exito.", BotLog.BOOKING)
        except Exception as e:
            print("Error: " + str(e))
            result["message"] = "Error: " + str(e)
            generate_log(f"[-] Error export: {str(e)}", BotLog.BOOKING)

    return Response(result)

def get_filtered_available_bookings(_date_from, ocp):
    ocp = int(ocp)
    date_str = str(_date_from.date())

    # Límites máximos por ocupación y estrellas
    limits = {
        2: {'3': 5, '4': 9},
        3: {'3': 5, '4': 6},
        5: {'3': 5, '4': 6},
    }

    max_3 = limits.get(ocp, {}).get('3', 0)
    max_4 = limits.get(ocp, {}).get('4', 0)

    def get_unique_by_position(qs, max_items):
        unique = {}
        result = []
        for item in qs:
            key = item.position
            if key not in unique:
                unique[key] = item
                result.append(item)
            if len(result) >= max_items:
                break
        return result

    # Consulta para 3 estrellas
    qs_3 = (
        AvailableBooking.objects
        .filter(date_from=date_str, occupancy=ocp, booking__start="3")
        .select_related('booking')
        .order_by('position', '-updated')  # más actualizado por posición
    )

    results_3 = get_unique_by_position(qs_3, max_3)

    # Consulta para 4 estrellas
    qs_4 = (
        AvailableBooking.objects
        .filter(date_from=date_str, occupancy=ocp, booking__start="4")
        .select_related('booking')
        .order_by('position', '-updated')
    )

    results_4 = get_unique_by_position(qs_4, max_4)

    # Unir resultados
    final_results = results_3 + results_4

    return final_results

def index(request):
    if request.user.is_authenticated:
        cant_default = 30
        __time = time.time()
        __date_from = str(now().date())
        __date_to = str(now().date() + datetime.timedelta(days=cant_default))
            
        if "date_from" in request.POST:
            __date_from = str(request.POST["date_from"])
        if "date_to" in request.POST:
            __date_to = str(request.POST["date_to"])

        _date_from = dt(
            year=int(__date_from.split("-")[0]),
            month=int(__date_from.split("-")[1]),
            day=int(__date_from.split("-")[2])
        )

        if "range_pg" in request.POST:
            __date_to = str(_date_from.date() + datetime.timedelta(days=int(request.POST["range_pg"])))

        _date_from_current = _date_from
        _date_to = dt(
            year=int(__date_to.split("-")[0]),
            month=int(__date_to.split("-")[1]),
            day=int(__date_to.split("-")[2])
        )
        bookings = {}
        occupancys = []
        for p in ProcessActive.objects.all():
            if p.occupancy not in occupancys:
                occupancys.append(p.occupancy)
        
        #print(occupancys)
        while _date_from.date() <= _date_to.date():
            if str(_date_from.date()) not in bookings:
                bookings[str(_date_from.date())] = {"totalFeria": 0}

            # ----------------
            bookings[str(_date_from.date())]["date_from"] = generate_date_with_month(str(_date_from.date()))
            bookings[str(_date_from.date())]["date_to"] = generate_date_with_month(str(_date_from.date() + datetime.timedelta(days=1)))
            locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
            fecha_especifica = dt.strptime(str(_date_from.date()), '%Y-%m-%d')
            bookings[str(_date_from.date())]["day"] = fecha_especifica.strftime('%A')
            # ----------------------------

            # get event by day
            __temporada_by_day = TemporadaByDay.objects.filter(date_from = str(_date_from.date())).last()
            if __temporada_by_day:
                bookings[str(_date_from.date())]["temporadaByDay"] = {"number":__temporada_by_day.number, "bgColor":str(__temporada_by_day.bg_color), "textColor":str(__temporada_by_day.text_color)}

            #print(occupancys)
            for ocp in occupancys:
                if int(ocp) not in list(bookings[str(_date_from.date())].keys()):
                    bookings[str(_date_from.date())][int(ocp)] = {}
                
                # get price tarifa
                __price = Price.objects.filter(date_from = str(_date_from.date()), occupancy=int(ocp)).last()
                if __price:
                    bookings[str(_date_from.date())][int(ocp)]["tarifa"] = {
                        "price":__price.price, 
                        "updated": generate_date_with_month_time(str(__price.updated)),
                        "pSync": __price.plataform_sync,
                        "active": __price.active_sync
                    }
                    if int(ocp) == 2:
                        __price = Price.objects.filter(date_from = str(_date_from.date()), occupancy=1).last()
                        if __price:
                            bookings[str(_date_from.date())][int(ocp)]["tarifa1"] = {
                                "price":__price.price, 
                                "updated": generate_date_with_month_time(str(__price.updated)),
                                "pSync": __price.plataform_sync,
                                "active": __price.active_sync
                            }

                        __price = Price.objects.filter(date_from = str(_date_from.date()), occupancy=0).last()
                        if __price:
                            bookings[str(_date_from.date())][int(ocp)]["tarifa0"] = {
                                "price":__price.price, 
                                "updated": generate_date_with_month_time(str(__price.updated)),
                                "pSync": __price.plataform_sync,
                                "active": __price.active_sync
                            }

                    if int(ocp) == 3:
                        __price = Price.objects.filter(date_from = str(_date_from.date()), occupancy=4).last()
                        if __price:
                            bookings[str(_date_from.date())][int(ocp)]["tarifa1"] = {
                                "price":__price.price, 
                                "updated": generate_date_with_month_time(str(__price.updated)),
                                "pSync": __price.plataform_sync,
                                "active": __price.active_sync
                            }
                    if int(ocp) == 5:
                        __price = Price.objects.filter(date_from = str(_date_from.date()), occupancy=6).last()
                        if __price:
                            bookings[str(_date_from.date())][int(ocp)]["tarifa1"] = {
                                "price":__price.price, 
                                "updated": generate_date_with_month_time(str(__price.updated)),
                                "pSync": __price.plataform_sync,
                                "active": __price.active_sync
                            }
                # get message
                __message_by_day = MessageByDay.objects.filter(date_from = str(_date_from.date()), occupancy=int(ocp)).last()
                if __message_by_day:
                    bookings[str(_date_from.date())][int(ocp)]["messageDay"] = {
                        "pk":__message_by_day.text_name.pk if __message_by_day.text_name else 0,
                        "text":__message_by_day.text_name.name if __message_by_day.text_name else '',
                        "bg_color": __message_by_day.text_name.bg_color if __message_by_day.text_name else '',
                        "text_color": __message_by_day.text_name.text_color if __message_by_day.text_name else '',
                        "updated":generate_date_with_month_time(str(__message_by_day.updated))
                    }

                # get event by day
                __event_by_day = EventByDay.objects.filter(date_from = str(_date_from.date()), occupancy=int(ocp)).last()
                if __event_by_day:
                    bookings[str(_date_from.date())][int(ocp)]["eventByDay"] = {"text":__event_by_day.text.strip().replace("\n", ". "), "updated":generate_date_with_month_time(str(__event_by_day.updated))}

                # Disponiblidad actual
                avail_sf = AvailSuitesFeria.objects.filter(date_avail = str(_date_from.date())).last()
                avail_sf_cant = CantAvailSuitesFeria.objects.filter(
                    type_avail = int(ocp),
                    avail_suites_feria = avail_sf
                ).last()
                bookings[str(_date_from.date())][int(ocp)]["totalFeria"] = 0
                if avail_sf_cant:
                    bookings[str(_date_from.date())][int(ocp)]["suiteFeria"] = avail_sf_cant.avail
                    bookings[str(_date_from.date())][int(ocp)]["totalFeria"] += avail_sf_cant.avail
                    bookings[str(_date_from.date())]["totalFeria"] += avail_sf_cant.avail
                    if int(ocp) == 2:
                        avail_sf_cant = CantAvailSuitesFeria.objects.filter(
                            type_avail = 1,
                            avail_suites_feria = avail_sf
                        ).last()
                        bookings[str(_date_from.date())][int(ocp)]["suiteFeria1"] = avail_sf_cant.avail
                        bookings[str(_date_from.date())][int(ocp)]["totalFeria"] += avail_sf_cant.avail
                        bookings[str(_date_from.date())]["totalFeria"] += avail_sf_cant.avail
                else:
                    if int(ocp) == 5:
                        avail_sf_cant = CantAvailSuitesFeria.objects.filter(
                            type_avail = 4,
                            avail_suites_feria = avail_sf
                        ).last()
                        bookings[str(_date_from.date())][int(ocp)]["suiteFeria"] = avail_sf_cant.avail if avail_sf_cant else 0
                        bookings[str(_date_from.date())][int(ocp)]["totalFeria"] += avail_sf_cant.avail if avail_sf_cant else 0
                        bookings[str(_date_from.date())]["totalFeria"] += avail_sf_cant.avail if avail_sf_cant else 0
                
                #Disponibilidad 1 dia atras
                copy_avail_with_name = CopyAvailWithDaySF.objects.filter(avail_suites_feria = avail_sf).order_by("-id")[:7]
                try:
                    cpwd = copy_avail_with_name[0]
                except Exception as ecpwd:
                    cpwd = CopyAvailWithDaySF()
                    cpwd.avail_1 = 0
                    cpwd.avail_2 = 0
                    cpwd.avail_3 = 0
                    cpwd.avail_4 = 0
                    cpwd.created = str(now())

                if "totalFeria1" not in bookings[str(_date_from.date())][int(ocp)].keys():
                    bookings[str(_date_from.date())][int(ocp)]["totalFeria1"] = 0
                if int(ocp) == 2:
                    bookings[str(_date_from.date())][int(ocp)]["totalFeria1"] += cpwd.avail_1
                    bookings[str(_date_from.date())][int(ocp)]["totalFeriaM1"] = cpwd.avail_1

                    bookings[str(_date_from.date())][int(ocp)]["totalFeria1"] += cpwd.avail_2
                    bookings[str(_date_from.date())][int(ocp)]["totalFeriaD1"] = cpwd.avail_2

                elif int(ocp) == 3:
                    bookings[str(_date_from.date())][int(ocp)]["totalFeria1"] += cpwd.avail_3

                elif int(ocp) == 5:
                    bookings[str(_date_from.date())][int(ocp)]["totalFeria1"] += cpwd.avail_4

                #Disponibilidad 4 dias atras
                copy_avail_with_name = CopyAvailWithDaySF.objects.filter(avail_suites_feria = avail_sf).order_by("-id")[:7]
                try:
                    cpwd = copy_avail_with_name[3]
                except Exception as ecpwd:
                    cpwd = CopyAvailWithDaySF()
                    cpwd.avail_1 = 0
                    cpwd.avail_2 = 0
                    cpwd.avail_3 = 0
                    cpwd.avail_4 = 0
                    cpwd.created = str(now())

                if "totalFeria4" not in bookings[str(_date_from.date())][int(ocp)].keys():
                    bookings[str(_date_from.date())][int(ocp)]["totalFeria4"] = 0

                if int(ocp) == 2:
                    bookings[str(_date_from.date())][int(ocp)]["totalFeria4"] += cpwd.avail_1
                    bookings[str(_date_from.date())][int(ocp)]["totalFeriaM4"] = cpwd.avail_1

                    bookings[str(_date_from.date())][int(ocp)]["totalFeria4"] += cpwd.avail_2
                    bookings[str(_date_from.date())][int(ocp)]["totalFeriaD4"] = cpwd.avail_2

                elif int(ocp) == 3:
                    bookings[str(_date_from.date())][int(ocp)]["totalFeria4"] += cpwd.avail_3

                elif int(ocp) == 5:
                    bookings[str(_date_from.date())][int(ocp)]["totalFeria4"] += cpwd.avail_4

                #Disponibilidad 7 dias atras
                copy_avail_with_name = CopyAvailWithDaySF.objects.filter(avail_suites_feria = avail_sf).order_by("-id")[:7]
                try:
                    cpwd = copy_avail_with_name[6]
                except Exception as ecpwd:
                    cpwd = CopyAvailWithDaySF()
                    cpwd.avail_1 = 0
                    cpwd.avail_2 = 0
                    cpwd.avail_3 = 0
                    cpwd.avail_4 = 0
                    cpwd.created = str(now())

                if "totalFeria7" not in bookings[str(_date_from.date())][int(ocp)].keys():
                    bookings[str(_date_from.date())][int(ocp)]["totalFeria7"] = 0

                if int(ocp) == 2:
                    bookings[str(_date_from.date())][int(ocp)]["totalFeria7"] += cpwd.avail_1
                    bookings[str(_date_from.date())][int(ocp)]["totalFeriaM7"] = cpwd.avail_1

                    bookings[str(_date_from.date())][int(ocp)]["totalFeria7"] += cpwd.avail_2
                    bookings[str(_date_from.date())][int(ocp)]["totalFeriaD7"] = cpwd.avail_2

                elif int(ocp) == 3:
                    bookings[str(_date_from.date())][int(ocp)]["totalFeria7"] += cpwd.avail_3

                elif int(ocp) == 5:
                    bookings[str(_date_from.date())][int(ocp)]["totalFeria7"] += cpwd.avail_4

                #--------------
                for comp in Complement.objects.filter(date_from=str(_date_from.date()), occupancy=int(ocp), start=4):
                    if int(comp.start) in [4]:
                        bookings[str(_date_from.date())]["updated"] = generate_date_with_month_time(str(comp.updated))
                        bookings[str(_date_from.date())][int(ocp)]["total_search"] = comp.total_search
                        bookings[str(_date_from.date())][int(ocp)]["total_search_192"] = "{:.2f}".format(comp.total_search / 192 * 100)
                
                        __com_ht = CopyComplementWithDay.objects.filter(complement = comp).order_by("-id")[:7]
                        try:
                            __com2 = __com_ht[0]
                        except Exception as ecom:
                            __com2 = CopyComplementWithDay()
                            __com2.total_search = 0
                            __com2.created = str(now())
                        bookings[str(_date_from.date())][int(ocp)]["total_search1"] = __com2.total_search
                        try:
                            __com2 = __com_ht[6]
                        except Exception as ecom:
                            __com2 = CopyComplementWithDay()
                            __com2.total_search = 0
                            __com2.created = str(now())
                        bookings[str(_date_from.date())][int(ocp)]["total_search7"] = __com2.total_search

                #----------------
                #available_booking = AvailableBooking.objects.filter(date_from=str(_date_from.date()), occupancy=int(ocp))
                available_booking = get_filtered_available_bookings(_date_from, ocp)
                #print(f"Len: {len(available_booking)}")
                for avail_book in available_booking:
                    if int(float(avail_book.booking.start)) in [3,4]:

                        #if int(float(avail_book.booking.start)) == 4 and int(ocp) == 2:
                        #    print(avail_book.price)

                        if int(float(avail_book.booking.start)) not in list(bookings[str(_date_from.date())][int(ocp)].keys()):
                            bookings[str(_date_from.date())][int(ocp)][int(float(avail_book.booking.start))] = {}
                        #----------------------------------
                        try:
                            copy_prices1 = CopyPriceWithDay.objects.filter(avail_booking = avail_book).order_by("-id")[0]
                        except Exception as e:
                            copy_prices1 = CopyPriceWithDay()
                            copy_prices1.price = "0"
                        if "media_total1" not in bookings[str(_date_from.date())][int(ocp)][int(float(avail_book.booking.start))]:
                            bookings[str(_date_from.date())][int(ocp)][int(float(avail_book.booking.start))]["media_total1"] = 0
                            bookings[str(_date_from.date())][int(ocp)][int(float(avail_book.booking.start))]["media_cant1"] = 0

                        _price3 = copy_prices1.price.replace("€ ", "").replace(".", "").replace(",", "")
                        if _price3 != "":
                            if int(float(avail_book.booking.start)) in [3,4] and avail_book.position in [0,1,2,3,4,9,14,19,24]:
                                bookings[str(_date_from.date())][int(ocp)][int(float(avail_book.booking.start))]["media_total1"] += int(_price3)
                                bookings[str(_date_from.date())][int(ocp)][int(float(avail_book.booking.start))]["media_cant1"] += 1  

                        try:
                            copy_prices4 = CopyPriceWithDay.objects.filter(avail_booking = avail_book).order_by("-id")[3]
                        except Exception as e:
                            copy_prices4 = CopyPriceWithDay()
                            copy_prices4.price = "0"
                        if "media_total4" not in bookings[str(_date_from.date())][int(ocp)][int(float(avail_book.booking.start))]:
                            bookings[str(_date_from.date())][int(ocp)][int(float(avail_book.booking.start))]["media_total4"] = 0
                            bookings[str(_date_from.date())][int(ocp)][int(float(avail_book.booking.start))]["media_cant4"] = 0
                        
                        _price4 = copy_prices4.price.replace("€ ", "").replace(".", "").replace(",", "")
                        if _price4 != "":
                            if int(float(avail_book.booking.start)) in [3,4] and avail_book.position in [0,1,2,3,4,9,14,19,24]:
                                bookings[str(_date_from.date())][int(ocp)][int(float(avail_book.booking.start))]["media_total4"] += int(_price4)
                                bookings[str(_date_from.date())][int(ocp)][int(float(avail_book.booking.start))]["media_cant4"] += 1

                        try:
                            copy_prices7 = CopyPriceWithDay.objects.filter(avail_booking = avail_book).order_by("-id")[6]
                        except Exception as e:
                            copy_prices7 = CopyPriceWithDay()
                            copy_prices7.price = "0"
                        if "media_total7" not in bookings[str(_date_from.date())][int(ocp)][int(float(avail_book.booking.start))]:
                            bookings[str(_date_from.date())][int(ocp)][int(float(avail_book.booking.start))]["media_total7"] = 0
                            bookings[str(_date_from.date())][int(ocp)][int(float(avail_book.booking.start))]["media_cant7"] = 0
                        
                        _price4 = copy_prices7.price.replace("€ ", "").replace(".", "").replace(",", "")
                        if _price4 != "":
                            if int(float(avail_book.booking.start)) in [3,4] and avail_book.position in [0,1,2,3,4,9,14,19,24]:
                                bookings[str(_date_from.date())][int(ocp)][int(float(avail_book.booking.start))]["media_total7"] += int(_price4)
                                bookings[str(_date_from.date())][int(ocp)][int(float(avail_book.booking.start))]["media_cant7"] += 1
                        #---------------------------------

                        #if int(ocp) == 2 and int(float(avail_book.booking.start)) == 3:
                        #    print(_price4)
                        
                        
                        _price = avail_book.price.replace("€ ", "").replace(".", "").replace(",", "")
                        if _price != "":
                            if "media_total" not in bookings[avail_book.date_from][int(ocp)][int(float(avail_book.booking.start))]:
                                bookings[avail_book.date_from][int(ocp)][int(float(avail_book.booking.start))]["media_total"] = 0
                                bookings[avail_book.date_from][int(ocp)][int(float(avail_book.booking.start))]["media_cant"] = 0
                            if "media_total03" not in bookings[avail_book.date_from][int(ocp)][int(float(avail_book.booking.start))]:
                                bookings[avail_book.date_from][int(ocp)][int(float(avail_book.booking.start))]["media_total03"] = 0
                                bookings[avail_book.date_from][int(ocp)][int(float(avail_book.booking.start))]["media_cant03"] = 0

                            #print(avail_book.date_from)
                            #if "2025-07-03" == avail_book.date_from and 2 == int(ocp):
                            #    print(_price, int(float(avail_book.booking.start)), avail_book.position, bookings[avail_book.date_from][int(ocp)][int(float(avail_book.booking.start))])

                            if "COP" not in _price and avail_book.position not in bookings[avail_book.date_from][int(ocp)][int(float(avail_book.booking.start))]:
                                #print(ocp, int(float(avail_book.booking.start)), avail_book.position, _price)
                                try:
                                    if _price:
                                        bookings[avail_book.date_from][int(ocp)][int(float(avail_book.booking.start))][avail_book.position] = {}
                                        bookings[avail_book.date_from][int(ocp)][int(float(avail_book.booking.start))][avail_book.position]["price"] = _price

                                        if int(float(avail_book.booking.start)) == 4 and avail_book.position in [0,1,2,3,4,9,14,19,24]:
                                            bookings[avail_book.date_from][int(ocp)][int(float(avail_book.booking.start))]["media_total"] += int(_price)
                                            bookings[avail_book.date_from][int(ocp)][int(float(avail_book.booking.start))]["media_cant"] += 1

                                        elif int(float(avail_book.booking.start)) == 3 and avail_book.position in [0,1,2,3,4]:
                                            bookings[avail_book.date_from][int(ocp)][int(float(avail_book.booking.start))]["media_total03"] += int(_price)
                                            bookings[avail_book.date_from][int(ocp)][int(float(avail_book.booking.start))]["media_cant03"] += 1

                                        bookings[avail_book.date_from][int(ocp)][int(float(avail_book.booking.start))][avail_book.position]["name"] = avail_book.booking.title
                                except Exception as e:
                                    logging.info(f"[-] Error price: {e}")
                        
                # change price with nameprice hotel.
                price_with_name_hotel = PriceWithNameHotel.objects.filter(title = "Hotel Suites Feria de Madrid", date_from = str(_date_from.date()), occupancy = int(ocp)).first()
                if price_with_name_hotel:
                    bookings[str(_date_from.date())][int(ocp)]["priceSuitesFeria"] = price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")
                    
                    for inj in [0,3,6]:
                        try:
                            available_booking1 = CopyPriceWithNameFromDay.objects.filter(avail = price_with_name_hotel).order_by("-id")[inj]
                        except Exception as e:
                            available_booking1 = CopyPriceWithNameFromDay()
                            available_booking1.price = "0"

                        if available_booking1:
                            _price1 = available_booking1.price.replace("€ ", "").replace(".", "").replace(",", "")
                            bookings[str(_date_from.date())][int(ocp)][f"priceSuitesFeria{inj+1}"] = int(_price1)
                            bookings[str(_date_from.date())][int(ocp)][f"priceSuitesFeriaRest{inj+1}"] = int(bookings[str(_date_from.date())][int(ocp)]["priceSuitesFeria"]) - int(_price1) if "priceSuitesFeria" in bookings[str(_date_from.date())][int(ocp)] else 0

            # change price with nameprice hotel.
            if "media_name_hotel" not in bookings[str(_date_from.date())][2].keys():
                bookings[str(_date_from.date())][2]["media_name_hotel"] = 0
                bookings[str(_date_from.date())][2]["media_cant_name_hotel"] = 0

            price_with_name_hotel = PriceWithNameHotel.objects.filter(title = "Hotel Suites Feria de Madrid", date_from = str(_date_from.date()), occupancy = 2).first()
            if price_with_name_hotel:
                bookings[price_with_name_hotel.date_from][2]["priceSF"] = price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")
                #bookings[str(_date_from.date())][2]["media_name_hotel"] += int(price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", ""))
                #bookings[str(_date_from.date())][2]["media_cant_name_hotel"] += 1

            __general_search_to_name = GeneralSearch.objects.filter(type_search=2, proces_active__occupancy=2).order_by('city_and_country', 'id')  # importante ordenar
            for _name_hotel in __general_search_to_name:
                if _name_hotel.city_and_country != "Hotel Suites Feria de Madrid":
                    #logging.info(_name_hotel)
                    price_with_name_hotel = PriceWithNameHotel.objects.filter(title=_name_hotel.city_and_country, date_from = str(_date_from.date()), occupancy = 2).first()
                    if price_with_name_hotel:
                        bookings[str(_date_from.date())][2][f"price{_name_hotel.code}"] = price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")
                        if int(price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")) > 0:
                            bookings[str(_date_from.date())][2]["media_name_hotel"] += int(price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", ""))
                            bookings[str(_date_from.date())][2]["media_cant_name_hotel"] += 1

                        for i in [0,3,6]:
                            try:
                                copy_price_with_name = CopyPriceWithNameFromDay.objects.filter(avail = price_with_name_hotel).order_by("-id")[i]
                            except Exception as e:
                                copy_price_with_name = CopyPriceWithNameFromDay()
                                copy_price_with_name.price = "0"
                            #logging.info(f"{i+1} - {copy_price_with_name.price}")
                            if copy_price_with_name:
                                _price1 = copy_price_with_name.price.replace("€ ", "").replace(".", "").replace(",", "")
                                bookings[str(_date_from.date())][2][f"price{_name_hotel.code}{i+1}"] = int(_price1)
                                bookings[str(_date_from.date())][2][f"price{_name_hotel.code}Rest{i+1}"] = int(bookings[str(_date_from.date())][2][f"price{_name_hotel.code}"]) - int(_price1) if f"price{_name_hotel.code}" in bookings[str(_date_from.date())][2] else 0
                                
                                if f"media_name_hotel{i+1}" not in bookings[str(_date_from.date())][2].keys():
                                    bookings[str(_date_from.date())][2][f"media_name_hotel{i+1}"] = 0
                                    bookings[str(_date_from.date())][2][f"media_cant_name_hotel{i+1}"] = 0

                                if int(_price1) > 0:
                                    bookings[str(_date_from.date())][2][f"media_name_hotel{i+1}"] += int(_price1)
                                    bookings[str(_date_from.date())][2][f"media_cant_name_hotel{i+1}"] += 1
            
            for i in [0,3,6]:
                try:
                    bookings[str(_date_from.date())][2][f"media_name_hotel_general{i+1}"] = round((round((bookings[str(_date_from.date())][2][f"media_name_hotel{i+1}"] / bookings[str(_date_from.date())][2][f"media_cant_name_hotel{i+1}"])) + round((bookings[str(_date_from.date())][2][4][f"media_total{i+1}"] / bookings[str(_date_from.date())][2][4][f"media_cant{i+1}"]))) / 2)
                except Exception as e:
                    bookings[str(_date_from.date())][2][f"media_name_hotel_general{i+1}"] = 0
                    generate_log(f"[X] Error view data media_name_hotel_general{i+1}: {e} {str(_date_from.date())}", BotLog.BOOKING)
            
            try:
                try:
                    __media_name_hotel_aux = round((bookings[str(_date_from.date())][2]["media_name_hotel"] / bookings[str(_date_from.date())][2]["media_cant_name_hotel"]))
                except Exception as e001:
                    __media_name_hotel_aux = 0
                
                try:
                    __media_name_hotel_aux7 = round((bookings[str(_date_from.date())][2]["media_name_hotel7"] / bookings[str(_date_from.date())][2]["media_cant_name_hotel7"]))
                except Exception as e001:
                    __media_name_hotel_aux7 = 0

                bookings[str(_date_from.date())][2][f"media_name_hotelRest"] = round((__media_name_hotel_aux  -  __media_name_hotel_aux7))
            except Exception as e:
                bookings[str(_date_from.date())][2][f"media_name_hotelRest"] = 0
                generate_log(f"[X] Error view data media_name_hotel_generalRest: {e} {str(_date_from.date())}", BotLog.BOOKING)
            
            # prices triples y suites
            price_with_name_hotel = PriceWithNameHotel.objects.filter(title = "Travelodge Torrelaguna", date_from = str(_date_from.date()), occupancy = 3).first()
            if price_with_name_hotel:
                bookings[price_with_name_hotel.date_from][3]["priceTOR"] = price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")
            
            price_with_name_hotel = PriceWithNameHotel.objects.filter(title = "Senator Barajas", date_from = str(_date_from.date()), occupancy = 3).first()
            if price_with_name_hotel:
                bookings[price_with_name_hotel.date_from][3]["priceBAR"] = price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")
            
            price_with_name_hotel = PriceWithNameHotel.objects.filter(title = "Alianza Suites", date_from = str(_date_from.date()), occupancy = 5).first()
            if price_with_name_hotel:
                bookings[price_with_name_hotel.date_from][5]["priceAZA"] = price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")
            
            price_with_name_hotel = PriceWithNameHotel.objects.filter(title = "Eco Alcalá Suites", date_from = str(_date_from.date()), occupancy = 5).first()
            if price_with_name_hotel:
                bookings[price_with_name_hotel.date_from][5]["priceECO"] = price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")
            
            # media + %
            if bookings[str(_date_from.date())][2]["media_cant_name_hotel"] > 0:
                if "media_name_50" not in bookings[str(_date_from.date())][2].keys():
                    bookings[str(_date_from.date())][2]["media_name_50"] = round((bookings[str(_date_from.date())][2]["media_name_hotel"] / bookings[str(_date_from.date())][2]["media_cant_name_hotel"]) * 1.5)
                if "media_name_40" not in bookings[str(_date_from.date())][2].keys():
                    bookings[str(_date_from.date())][2]["media_name_40"] = round((bookings[str(_date_from.date())][2]["media_name_hotel"] / bookings[str(_date_from.date())][2]["media_cant_name_hotel"]) * 1.4)
                if "media_name_30" not in bookings[str(_date_from.date())][2].keys():
                    bookings[str(_date_from.date())][2]["media_name_30"] = round((bookings[str(_date_from.date())][2]["media_name_hotel"] / bookings[str(_date_from.date())][2]["media_cant_name_hotel"]) * 1.3)
                if "media_name_20" not in bookings[str(_date_from.date())][2].keys():
                    bookings[str(_date_from.date())][2]["media_name_20"] = round((bookings[str(_date_from.date())][2]["media_name_hotel"] / bookings[str(_date_from.date())][2]["media_cant_name_hotel"]) * 1.2)
                if "media_name_10" not in bookings[str(_date_from.date())][2].keys():
                    bookings[str(_date_from.date())][2]["media_name_10"] = round((bookings[str(_date_from.date())][2]["media_name_hotel"] / bookings[str(_date_from.date())][2]["media_cant_name_hotel"]) * 1.1)

            # media + % 4*
            if bookings[str(_date_from.date())][2][4]["media_total"] > 0:
                ___media_total = round(bookings[str(_date_from.date())][2][4]["media_total"] / bookings[str(_date_from.date())][2][4]["media_cant"])
                bookings[str(_date_from.date())][2][4]["media_total01"] = ___media_total
                if bookings[str(_date_from.date())][2][4]["media_total7"] > 0:
                    ___media_total7 = round(bookings[str(_date_from.date())][2][4]["media_total7"] / bookings[str(_date_from.date())][2][4]["media_cant7"])
                    valueRest = ___media_total - ___media_total7
                    bookings[str(_date_from.date())][2][4]["media_totalRest"] = {"value":valueRest, "color": "text-white" if valueRest >= 0 else "text-danger"}
            
            # media + % 3*
            if bookings[str(_date_from.date())][2][3]["media_total03"] > 0:
                ___media_total = round(bookings[str(_date_from.date())][2][3]["media_total03"] / bookings[str(_date_from.date())][2][3]["media_cant03"])
                if bookings[str(_date_from.date())][2][3]["media_total7"] > 0:
                    ___media_total7 = round(bookings[str(_date_from.date())][2][3]["media_total7"] / bookings[str(_date_from.date())][2][3]["media_cant7"])
                    valueRest = ___media_total - ___media_total7
                    bookings[str(_date_from.date())][2][3]["media_totalRest"] = {"value":valueRest, "color": "text-white" if valueRest >= 0 else "text-danger"}

            # media + % triples 4*
            if bookings[str(_date_from.date())][3][4]["media_total"] > 0:
                try:
                    ___media_total = round(bookings[str(_date_from.date())][3][4]["media_total"] / bookings[str(_date_from.date())][3][4]["media_cant"])
                    if "media_name_50" not in bookings[str(_date_from.date())][3].keys():
                        bookings[str(_date_from.date())][3]["media_name_50"] = round(___media_total * 1.5)
                    if "media_name_40" not in bookings[str(_date_from.date())][3].keys():
                        bookings[str(_date_from.date())][3]["media_name_40"] = round(___media_total * 1.4)
                    if "media_name_30" not in bookings[str(_date_from.date())][3].keys():
                        bookings[str(_date_from.date())][3]["media_name_30"] = round(___media_total * 1.3)
                    
                    if bookings[str(_date_from.date())][3][4]["media_total7"] > 0:
                        ___media_total7 = round(bookings[str(_date_from.date())][3][4]["media_total7"] / bookings[str(_date_from.date())][3][4]["media_cant7"])
                        valueRest = ___media_total - ___media_total7
                        bookings[str(_date_from.date())][3][4]["media_totalRest"] = {"value":valueRest, "color": "text-white" if valueRest >= 0 else "text-danger"}
                except Exception as e001:
                    generate_log(f"[X] Error view data: {e001} {str(_date_from.date())}", BotLog.BOOKING)
            
            # media + % triples 3*
            if bookings[str(_date_from.date())][3][3]["media_total03"] > 0:
                try:
                    ___media_total = round(bookings[str(_date_from.date())][3][3]["media_total03"] / bookings[str(_date_from.date())][3][3]["media_cant03"])
                    
                    if bookings[str(_date_from.date())][3][3]["media_total7"] > 0:
                        ___media_total7 = round(bookings[str(_date_from.date())][3][3]["media_total7"] / bookings[str(_date_from.date())][3][3]["media_cant7"])
                        valueRest = ___media_total - ___media_total7
                        bookings[str(_date_from.date())][3][3]["media_totalRest"] = {"value":valueRest, "color": "text-white" if valueRest >= 0 else "text-danger"}
                except Exception as e001:
                    generate_log(f"[X] Error view data: {e001} {str(_date_from.date())}", BotLog.BOOKING)
            # media + % suites 4*
            if bookings[str(_date_from.date())][5][4]["media_total"] > 0:
                ___media_total = round(bookings[str(_date_from.date())][5][4]["media_total"] / bookings[str(_date_from.date())][5][4]["media_cant"])
                if "media_name_60" not in bookings[str(_date_from.date())][5].keys():
                    bookings[str(_date_from.date())][5]["media_name_60"] = round(___media_total * 1.6)
                if "media_name_50" not in bookings[str(_date_from.date())][5].keys():
                    bookings[str(_date_from.date())][5]["media_name_50"] = round(___media_total * 1.5)
                if "media_name_40" not in bookings[str(_date_from.date())][5].keys():
                    bookings[str(_date_from.date())][5]["media_name_40"] = round(___media_total * 1.4)
                if "media_name_30" not in bookings[str(_date_from.date())][5].keys():
                    bookings[str(_date_from.date())][5]["media_name_30"] = round(___media_total * 1.3)

                if bookings[str(_date_from.date())][5][4]["media_total7"] > 0:
                    ___media_total7 = round(bookings[str(_date_from.date())][5][4]["media_total7"] / bookings[str(_date_from.date())][5][4]["media_cant7"])
                    valueRest = ___media_total - ___media_total7
                    bookings[str(_date_from.date())][5][4]["media_totalRest"] = {"value":valueRest, "color": "text-white" if valueRest >= 0 else "text-danger"}

            # media + % suites 4*
            if bookings[str(_date_from.date())][5][3]["media_total03"] > 0:
                ___media_total = round(bookings[str(_date_from.date())][5][3]["media_total03"] / bookings[str(_date_from.date())][5][3]["media_cant03"])

                if bookings[str(_date_from.date())][5][3]["media_total7"] > 0:
                    ___media_total7 = round(bookings[str(_date_from.date())][5][3]["media_total7"] / bookings[str(_date_from.date())][5][3]["media_cant7"])
                    valueRest = ___media_total - ___media_total7
                    bookings[str(_date_from.date())][5][3]["media_totalRest"] = {"value":valueRest, "color": "text-white" if valueRest >= 0 else "text-danger"}

            # media entre la zona y actual.
            if "media_name_hotel" in bookings[str(_date_from.date())][2].keys() and "media_total" in bookings[str(_date_from.date())][2][4].keys():
                if "media_general" not in bookings[str(_date_from.date())][2].keys():
                    try:
                        bookings[str(_date_from.date())][2]["media_general"] = round((round((bookings[str(_date_from.date())][2]["media_name_hotel"] / bookings[str(_date_from.date())][2]["media_cant_name_hotel"])) + round((bookings[str(_date_from.date())][2][4]["media_total"] / bookings[str(_date_from.date())][2][4]["media_cant"]))) / 2)
                    except Exception as e:
                        bookings[str(_date_from.date())][2]["media_general"] = 0
                        generate_log(f"[X] Error view data: {e} {str(_date_from.date())}", BotLog.BOOKING)
            
            try:
                bookings[str(_date_from.date())][2][f"media_name_hotel_generalRest"] = round(bookings[str(_date_from.date())][2][f"media_general"]) - round(bookings[str(_date_from.date())][2][f"media_name_hotel_general7"])
            except Exception as e:
                bookings[str(_date_from.date())][2]["media_name_hotel_generalRest"] = 0
                generate_log(f"[X] Error view data: {e} {str(_date_from.date())}", BotLog.BOOKING)

            # calculo de precio 5 y 10 posicion de triples y suites
            if 4 in bookings[str(_date_from.date())][3].keys() and 4 in bookings[str(_date_from.date())][5].keys():
                bookings[str(_date_from.date())][3][4]["5_10"] = round((float(bookings[str(_date_from.date())][3][4][4]["price"]) + float(bookings[str(_date_from.date())][3][4][9]["price"])) / 2)
                bookings[str(_date_from.date())][5][4]["5_10"] = round((float(bookings[str(_date_from.date())][5][4][4]["price"]) + float(bookings[str(_date_from.date())][5][4][9]["price"])) / 2)

            if "total_search" in bookings[str(_date_from.date())][2].keys() and "total_search7" in bookings[str(_date_from.date())][2].keys():
                bookings[str(_date_from.date())][2]["total_search_rest"] = int(float(bookings[str(_date_from.date())][2]["total_search"]) - float(bookings[str(_date_from.date())][2]["total_search7"]))

            # disponibilidad suites feria. resta de dia actual y 7 dias. 
            # tambien dia actual y disponiblidad manual.
            avail_with_date = AvailWithDate.objects.filter(date_from=str(_date_from.date())).first()
            bookings[str(_date_from.date())]["availWithDate"] = 0
            if avail_with_date:
                bookings[str(_date_from.date())]["availWithDate"] = int(avail_with_date.avail)
            
            # dia actual y disponibilidad manual.
            current_valueRest = bookings[str(_date_from.date())]["totalFeria"] - bookings[str(_date_from.date())]["availWithDate"]
            bookings[str(_date_from.date())]["availWithDateRest"] = {"value":current_valueRest, "color": "text-white" if current_valueRest >= 0 else "text-danger"}

            # disponibilidad suites feria actual y 7 dias.
            valueRest = bookings[str(_date_from.date())][2]["totalFeria"] - bookings[str(_date_from.date())][2]["totalFeria7"]
            bookings[str(_date_from.date())][2]["totalFeriaRest"] = {"value":valueRest, "color": "text-white" if valueRest >= 0 else "text-danger"}

            valueRest = bookings[str(_date_from.date())][2]["suiteFeria"] - bookings[str(_date_from.date())][2]["totalFeriaD7"]
            bookings[str(_date_from.date())][2]["totalFeriaDRest"] = {"value":valueRest, "color": "text-white" if valueRest >= 0 else "text-danger"}

            valueRest = bookings[str(_date_from.date())][2]["suiteFeria1"] - bookings[str(_date_from.date())][2]["totalFeriaM7"]
            bookings[str(_date_from.date())][2]["totalFeriaMRest"] = {"value":valueRest, "color": "text-white" if valueRest >= 0 else "text-danger"}

            valueRest = bookings[str(_date_from.date())][3]["totalFeria"] - bookings[str(_date_from.date())][3]["totalFeria7"]
            bookings[str(_date_from.date())][3]["totalFeriaRest"] = {"value":valueRest, "color": "text-white" if valueRest >= 0 else "text-danger"}

            valueRest = bookings[str(_date_from.date())][5]["totalFeria"] - bookings[str(_date_from.date())][5]["totalFeria7"]
            bookings[str(_date_from.date())][5]["totalFeriaRest"] = {"value":valueRest, "color": "text-white" if valueRest >= 0 else "text-danger"}

            # precio de suites feria, dia actual menos hace 7 dias.
            valueRest = int(bookings[str(_date_from.date())][2]["priceSuitesFeria"]) - bookings[str(_date_from.date())][2]["priceSuitesFeria7"]
            bookings[str(_date_from.date())][2]["priceSuitesFeriaRest"] = {"value":valueRest, "color": "text-white" if valueRest >= 0 else "text-danger"}

            valueRest = int(bookings[str(_date_from.date())][3]["priceSuitesFeria"]) - bookings[str(_date_from.date())][3]["priceSuitesFeria7"]
            bookings[str(_date_from.date())][3]["priceSuitesFeriaRest"] = {"value":valueRest, "color": "text-white" if valueRest >= 0 else "text-danger"}

            valueRest = int(bookings[str(_date_from.date())][5]["priceSuitesFeria"]) - bookings[str(_date_from.date())][5]["priceSuitesFeria7"]
            bookings[str(_date_from.date())][5]["priceSuitesFeriaRest"] = {"value":valueRest, "color": "text-white" if valueRest >= 0 else "text-danger"}

            if "range_bt" in request.POST:
                if request.POST["range_bt"] == "2":
                    if current_valueRest != 0:
                        del bookings[str(_date_from.date())]
                elif request.POST["range_bt"] == "3":
                    if current_valueRest == 0:
                        del bookings[str(_date_from.date())]

            _date_from += datetime.timedelta(days=1)

            #break
        
        _date_process =  BotRange.objects.filter(bot_setting=BotSetting.objects.filter(name = BotSetting.BOT_DEFAULT).last()).first()
        bot_auto = BotAutomatization.objects.last()
        _bot_setting = BotSetting.objects.filter(name = BotSetting.BOT_AUTO).last()
        bot_range = BotRange.objects.filter(bot_setting=_bot_setting)
        range_bt = "1"
        range_pg = str(cant_default)
        if "range_bt" in request.POST:
            range_bt = request.POST["range_bt"]
        if "range_pg" in request.POST:
            range_pg = request.POST["range_pg"]

        __message_name2 = MessageName.objects.filter(occupancy=2).order_by("number")
        __message_name3 = MessageName.objects.filter(occupancy=3).order_by("number")
        __message_name5 = MessageName.objects.filter(occupancy=5).order_by("number")

        message_name2_serializer = MessageNameSerializer(__message_name2, many=True)
        __message_name2_serializer = message_name2_serializer.data

        message_name3_serializer = MessageNameSerializer(__message_name3, many=True)
        __message_name3_serializer = message_name3_serializer.data

        message_name5_serializer = MessageNameSerializer(__message_name5, many=True)
        __message_name5_serializer = message_name5_serializer.data
        #print(bookings)
        #print(time.time() - __time)
        return render(
            request, 
            "app/index.html", 
            {
                "bookings":bookings,
                "bookings_text": json.dumps(bookings),
                "segment": "index",
                "date_from": __date_from,
                "date_to": __date_to,
                "date_process_from": str(_date_process.date_from),
                "date_process": str(_date_process.date_end),
                "range_bt":range_bt,
                "range_pg": range_pg,
                "bot_auto": bot_auto,
                "bot_range": bot_range,
                "bot_setting": _bot_setting,
                "message_name2": __message_name2,
                "message_name3": __message_name3,
                "message_name5": __message_name5,
                "message_name2_text": json.dumps(__message_name2_serializer),
                "message_name3_text": json.dumps(__message_name3_serializer),
                "message_name5_text": json.dumps(__message_name5_serializer)
            }
        )
    else:
        return redirect("sign-in")
    
def booking_view(request):
    if request.user.is_authenticated:
        data_aux = {
            "2": {#occupancy
                "4":[#stars
                    {"price": 0, "bg": "bg-danger", "color": "text-white"},
                    {"price": 0, "bg": "bg-warning", "color": "text-white"},
                    {"price": 0, "bg": "bg-primary", "color": "text-white"},
                    {"price": 0, "bg": "bg-white", "color": "text-black"},
                    {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                    {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                    {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                    {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                    {"price": 0, "bg": "bg-success", "color": "text-black"}
                ],
                "3":[
                    {"price": 0, "bg": "bg-white", "color": "text-black"},
                    {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                    {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                    {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                    {"price": 0, "bg": "bg-success", "color": "text-black"}
                ]
            },
            "3":{
                "4":[
                    {"price": 0, "bg": "bg-white", "color": "text-black"},
                    {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                    {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                    {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                    {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                    {"price": 0, "bg": "bg-success", "color": "text-black"}
                ],
                "3": [
                    {"price": 0, "bg": "bg-white", "color": "text-black"},
                    {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                    {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                    {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                    {"price": 0, "bg": "bg-success", "color": "text-black"}
                ]
            },
            "5":{
                "4":[
                    {"price": 0, "bg": "bg-white", "color": "text-black"},
                    {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                    {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                    {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                    {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                    {"price": 0, "bg": "bg-success", "color": "text-black"}
                ],
                "3": [
                    {"price": 0, "bg": "bg-white", "color": "text-black"},
                    {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                    {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                    {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                    {"price": 0, "bg": "bg-success", "color": "text-black"}
                ]
            }
        }

        _date_from = dt(
            year=int(request.GET["date"].split("-")[0]),
            month=int(request.GET["date"].split("-")[1]),
            day=int(request.GET["date"].split("-")[2])
        )
        _date_from_current = now()
        bookings = {}
        if int(request.GET["occupancy"]) in [2, 3]:
            if int(request.GET["occupancy"]) == 2:
                bookings = {"bookings":{"3":{"list":[], "list2": [], "title":"2P 3*"}, "4":{"list":[], "list2": [], "title":"2P 4*"}}}
            else:
                bookings = {"bookings":{"3":{"list":[],"list2": [],  "title":"3P 3*"}, "4":{"list":[], "list2": [], "title":"3P 4*"}}}
        else:
            bookings = {"bookings":{"3":{"list":[],"list2": [],  "title":"5P 3*"}, "4":{"list":[],"list2": [],  "title":"5P 4*"}}}

        stars = []
        for p in ProcessActive.objects.all():
            if int(p.start) not in stars:
                stars.append(int(p.start))

        #if not available_booking:
        for s in stars:
            # Get booking data
            available_booking = AvailableBooking.objects.filter(date_from=request.GET["date"], occupancy=int(request.GET["occupancy"]), start=str(s)).order_by("-updated")
            # get message
            __message_by_day = MessageByDay.objects.filter(date_from = str(_date_from.date()), occupancy=int(request.GET["occupancy"])).all()
            if __message_by_day:
                bookings["bookings"][str(s)]["messageDay"] = []
                for m in __message_by_day:
                    bookings["bookings"][str(s)]["messageDay"].append(f"{m.text_name.name if m.text_name else ''} ----- {generate_date_with_month_time(str(m.updated))}")
            
            __com = None
            avail_sf = None
            if s == 4:
                __com = Complement.objects.filter(date_from = request.GET["date"], occupancy = int(request.GET["occupancy"]), start = s).first()
                bookings["bookings"][str(s)]["dispTotal"] = __com.total_search

                avail_sf = AvailSuitesFeria.objects.filter(date_avail = str(_date_from.date())).last()

            for i in range(0, 8, 1):
                #if i not in list(bookings["bookings"][str(s)].keys()):
                bookings["bookings"][str(s)][i] = {"min": 100000, "media": 0, "media_cant": 0, "prices":[], "suitesFeriaPrice": 0, "suitesFeria1": 0, "suitesFeria2": 0}
                if not available_booking:
                    if int(request.GET["occupancy"]) == 2:
                        if s == 3:
                            bookings["bookings"][str(s)][i]["prices"] = [
                                {"price": 0, "bg": "bg-success", "color": "text-black"},
                                {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                                {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                                {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                                {"price": 0, "bg": "bg-white", "color": "text-black"}
                            ]
                        else:
                            bookings["bookings"][str(s)][i]["prices"] = [
                                {"price": 0, "bg": "bg-success", "color": "text-black"},
                                {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                                {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                                {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                                {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                                {"price": 0, "bg": "bg-white", "color": "text-black"},
                                {"price": 0, "bg": "bg-primary", "color": "text-white"},
                                {"price": 0, "bg": "bg-warning", "color": "text-white"},
                                {"price": 0, "bg": "bg-danger", "color": "text-white"}
                            ]
                    elif int(request.GET["occupancy"]) in [3, 5]:
                        if s == 3:
                            bookings["bookings"][str(s)][i]["prices"] = [
                                {"price": 0, "bg": "bg-success", "color": "text-black"},
                                {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                                {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                                {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                                {"price": 0, "bg": "bg-white", "color": "text-black"}
                            ]
                        else:
                            bookings["bookings"][str(s)][i]["prices"] = [
                                {"price": 0, "bg": "bg-success", "color": "text-black"},
                                {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                                {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                                {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                                {"price": 0, "bg": "bg-secondary", "color": "text-white"},
                                {"price": 0, "bg": "bg-white", "color": "text-black"}
                            ]

                if s == 4 and avail_sf:
                    if i == 0:
                        avail_sf_cant = CantAvailSuitesFeria.objects.filter(
                            type_avail = int(request.GET["occupancy"]),
                            avail_suites_feria = avail_sf
                        ).last()

                        if avail_sf_cant:
                            bookings["bookings"][str(s)][i]["suitesFeria1"] = avail_sf_cant.avail
                            if int(request.GET["occupancy"]) == 2:
                                avail_sf_cant = CantAvailSuitesFeria.objects.filter(
                                    type_avail = 1,
                                    avail_suites_feria = avail_sf
                                ).last()
                                bookings["bookings"][str(s)][i]["suitesFeria2"] += avail_sf_cant.avail
                        else:
                            if int(request.GET["occupancy"]) == 5:
                                avail_sf_cant = CantAvailSuitesFeria.objects.filter(
                                    type_avail = 4,
                                    avail_suites_feria = avail_sf
                                ).last()
                                if avail_sf_cant:
                                    bookings["bookings"][str(s)][i]["suitesFeria1"] = avail_sf_cant.avail
                    else:
                        copy_avail_with_name = CopyAvailWithDaySF.objects.filter(avail_suites_feria = avail_sf).order_by("-id")[:7]
                        try:
                            cpwd = copy_avail_with_name[i - 1]
                        except Exception as ecpwd:
                            cpwd = CopyAvailWithDaySF()
                            cpwd.avail_1 = 0
                            cpwd.avail_2 = 0
                            cpwd.avail_4 = 0
                            cpwd.created = str(now())
                        
                        if int(request.GET["occupancy"]) == 2:
                            bookings["bookings"][str(s)][i]["suitesFeria2"] = cpwd.avail_1
                            bookings["bookings"][str(s)][i]["suitesFeria1"] = cpwd.avail_2
                        elif int(request.GET["occupancy"]) == 3:
                            bookings["bookings"][str(s)][i]["suitesFeria1"] += cpwd.avail_3
                        elif int(request.GET["occupancy"]) == 5:
                            bookings["bookings"][str(s)][i]["suitesFeria1"] += cpwd.avail_4

                        if __com:
                            __com_ht = CopyComplementWithDay.objects.filter(complement = __com).order_by("-id")[:7]

                            try:
                                __com2 = __com_ht[i - 1]
                            except Exception as ecom:
                                __com2 = CopyComplementWithDay()
                                __com2.total_search = 0
                                __com2.created = str(now())

                            bookings["bookings"][str(s)][i]["dispTotal"] = __com2.total_search

                    bookings["bookings"][str(s)][i]["suitesFeriaTotal"] = bookings["bookings"][str(s)][i]["suitesFeria2"] + bookings["bookings"][str(s)][i]["suitesFeria1"]
                    
            price_with_name_hotel = PriceWithNameHotel.objects.filter(title = "Hotel Suites Feria de Madrid", date_from = str(_date_from.date()), occupancy = int(request.GET["occupancy"])).first()
            if price_with_name_hotel:
                price_w_name = price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")
                bookings["bookings"][str(s)][0]["suitesFeriaPrice"] = price_w_name
                # change price with name hotel.
                try:
                    cont = 1
                    copy_price_with_name = CopyPriceWithNameFromDay.objects.filter(avail = price_with_name_hotel).order_by("-id")[:7]
                    for index_cpwd in range(7):
                        try:
                            cpwd = copy_price_with_name[index_cpwd]
                        except Exception as ecpwd:
                            cpwd = CopyPriceWithNameFromDay()
                            cpwd.price = "0"
                            cpwd.created = str(now())
                        
                        cp_price = cpwd.price.replace("€ ", "").replace(".", "").replace(",", "")
                        bookings["bookings"][str(s)][cont]["suitesFeriaPrice"] = cp_price
                        cont += 1
                except Exception as e:
                    pass

            acum1 = 0
            acum2 = 0
            for b in available_booking:
                if int(b.booking.start) in stars:
                    #print(int(b.booking.start), stars, int(b.booking.start) in stars, i)
                    if int(b.booking.start) == 3:
                        acum = acum1
                    if int(b.booking.start) == 4:
                        acum = acum2
                    try:
                        _text_price = {
                            "price": data_aux[request.GET["occupancy"]][str(b.booking.start)][acum]["price"], 
                            "bg": data_aux[request.GET["occupancy"]][str(b.booking.start)][acum]["bg"], 
                            "color": data_aux[request.GET["occupancy"]][str(b.booking.start)][acum]["color"],
                            "position": b.position
                        }

                        _price = b.price.replace("€ ", "").replace(".", "").replace(",", "")
                        bookings["bookings"][str(b.booking.start)]["list2"].append(
                            {
                                "title": b.booking.title,
                                "price": _price,
                                "position": str(b.position)
                            }
                        )
                        if bookings["bookings"][str(b.booking.start)][0]["min"] > int(_price):
                            bookings["bookings"][str(b.booking.start)][0]["min"] = int(_price)

                        if int(b.booking.start) == 4:
                            if b.position in [0,1,2,3,4,9,14,19,24]:
                                bookings["bookings"][str(b.booking.start)][0]["media"] += int(_price)
                                bookings["bookings"][str(b.booking.start)][0]["media_cant"] += 1
                        elif int(b.booking.start) == 3:
                            bookings["bookings"][str(b.booking.start)][0]["media"] += int(_price)
                            bookings["bookings"][str(b.booking.start)][0]["media_cant"] += 1
                        #print(request.GET["occupancy"], b.booking.start, acum, b.updated)
                        #print(acum)

                        _text_price["price"] = int(_price)
                        bookings["bookings"][str(b.booking.start)][0]["prices"].append(_text_price)
                            
                    except Exception as eIndex:
                        pass#print(f"Error index: {i} - {str(b.booking.start)} - "+str(eIndex))

                    try:
                        cont = 1
                        #print("--------------------------------------------------")
                        copy_prices = CopyPriceWithDay.objects.filter(avail_booking = b).order_by("-id")[:7]
                        for index_cpwd in range(7):
                            try:
                                cpwd = copy_prices[index_cpwd]
                            except Exception as ecpwd:
                                cpwd = CopyPriceWithDay()
                                cpwd.price = "0"
                                cpwd.created = str(now())

                            #print(_price, cpwd.price, b.booking.start, cont, cpwd.created)

                            _text_price = {
                                "price": data_aux[request.GET["occupancy"]][str(b.booking.start)][acum]["price"], 
                                "bg": data_aux[request.GET["occupancy"]][str(b.booking.start)][acum]["bg"], 
                                "color": data_aux[request.GET["occupancy"]][str(b.booking.start)][acum]["color"],
                                "position": b.position
                            }

                            cp_price = cpwd.price.replace("€ ", "").replace(".", "").replace(",", "")

                            if bookings["bookings"][str(b.booking.start)][cont]["min"] > int(cp_price):
                                bookings["bookings"][str(b.booking.start)][cont]["min"] = int(cp_price)

                            if int(b.booking.start) == 4:
                                if b.position in [0,1,2,3,4,9,14,19,24]:
                                    bookings["bookings"][str(b.booking.start)][cont]["media"] += int(cp_price)
                                    bookings["bookings"][str(b.booking.start)][cont]["media_cant"] += 1
                            elif int(b.booking.start) == 3:
                                bookings["bookings"][str(b.booking.start)][cont]["media"] += int(cp_price)
                                bookings["bookings"][str(b.booking.start)][cont]["media_cant"] += 1

                            _text_price["price"] = int(cp_price)
                            bookings["bookings"][str(b.booking.start)][cont]["prices"].append(_text_price)
                            
                            cont += 1
                    except Exception as e001:
                        pass#print(f"Error copy price. {e001}")
                    
                    if int(b.booking.start) == 3:
                        acum1 += 1
                    if int(b.booking.start) == 4:
                        acum2 += 1

        try:
            for st,v in bookings["bookings"].items():#3,4
                #print(st)
                for k,v2 in v.items():#0,1,2,3,4,5,...,8
                    #print(k)
                    if "list" not in str(k) and "title" not in str(k) and "messageDay" not in str(k) and "dispTotal" not in str(k):
                        #print(k)
                        v2["prices"] = sorted(v2["prices"], key=lambda x: int(x["position"]))
                    elif "list2" == str(k):
                        v["list2"] = sorted(v2, key=lambda x: int(x["position"]))
        except Exception as eSort:
            generate_log(f"Error in Sorted: {eSort}", BotLog.HISTORY)

        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
        fecha_especifica = dt.strptime(request.GET["date"], '%Y-%m-%d')
        ___date = generate_date_with_month(request.GET["date"])
        if int(request.GET["occupancy"]) == 2:
            bg_color = "bg-info"
        elif int(request.GET["occupancy"]) == 3:
            bg_color = "bg-success"
        else:
            bg_color = "bg-danger"
        return render(request, "app/booking.html", {"bookings":bookings, "segment": "index", "day": fecha_especifica.strftime('%A'), "date": ___date, "bg_color": bg_color})
    else:
        return redirect("sign-in")

def history_hotel(request):
    if request.user.is_authenticated:
        _date_from = dt(
            year=int(request.GET["date"].split("-")[0]),
            month=int(request.GET["date"].split("-")[1]),
            day=int(request.GET["date"].split("-")[2])
        )
        bookings_name = []

        __general_search_to_name = GeneralSearch.objects.filter(type_search=2, proces_active__occupancy=2).order_by('city_and_country', 'id')  # importante ordenar
        for _name_hotel in __general_search_to_name:
            #logging.info(_name_hotel)
            history_name = {}
            price_with_name_hotel = PriceWithNameHotel.objects.filter(title=_name_hotel.city_and_country, date_from = str(_date_from.date()), occupancy = 2).first()
            if price_with_name_hotel:
                price_w_name = price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")
                history_name["code"] = _name_hotel.code
                history_name["name"] = _name_hotel.city_and_country
                history_name["price"] = []
                history_name["price"].append(price_w_name)
                # change price with name hotel.
                try:
                    cont = 1
                    copy_price_with_name = CopyPriceWithNameFromDay.objects.filter(avail = price_with_name_hotel).order_by("-id")[:7]
                    for index_cpwd in range(7):
                        try:
                            cpwd = copy_price_with_name[index_cpwd]
                        except Exception as ecpwd:
                            cpwd = CopyPriceWithNameFromDay()
                            cpwd.price = "0"
                            cpwd.created = str(now())
                        
                        cp_price = cpwd.price.replace("€ ", "").replace(".", "").replace(",", "")
                        history_name["price"].append(cp_price)
                        cont += 1
                except Exception as e:
                    pass

            bookings_name.append(history_name)

        fecha_especifica = dt.strptime(request.GET["date"], '%Y-%m-%d')
        ___date = generate_date_with_month(request.GET["date"])
        #if int(request.GET["occupancy"]) == 2:
        #bg_color = "bg-info"
        #elif int(request.GET["occupancy"]) == 3:
        #    bg_color = "bg-success"
        #else:
        #    bg_color = "bg-danger"

        context={
            "segment": "index",
            "history_hotel": bookings_name,
            "history_hotel_text": json.dumps(bookings_name),
            "day": fecha_especifica.strftime('%A'), "date": ___date, #"bg_color": bg_color
        }
        return render(request, "app/history-hotel.html", context)
    else:
        return redirect("sign-in")
    
def reception(request):
    if request.user.is_authenticated:
        context={
            "segment": "reception",
        }
        return render(request, "app/reception.html", context)
    else:
        return redirect("sign-in")
    
@api_view(["GET"])
def reception_price(request):
    try:
        ocuppancies = {
            0:"individual",
            1:"matrimonial",
            2:"double",
            3:"triple",
            4:"doubleExtra",
            5:"suite4",
            6:"suite6",
        }
        date_from = request.GET["date_from"]
        date_to = request.GET["date_to"]
        prices = Price.objects.filter(
            date_from__gte=date_from,
            date_from__lt=date_to
        ).values( "price", "date_from", "occupancy").distinct().order_by("date_from")
        data = {}
        for occcupancy in ocuppancies.values():
            data[occcupancy] = []
        for price in prices:
            occupancy = ocuppancies[price["occupancy"]]
            data[occupancy].append(price)
        result = {
            "code": 200,
            "status": "OK",
            "data": data,
            "message": "Success"
        }
        return Response(result)
    except Exception as e:
        print(e)
        result = {"code": 500, "status": "Fail", "message":"Error in reception_price."}
        return Response(result)



# Inicio de sesion para todos los usuarios.
def login(request):
    if request.method == "POST":
        user = request.POST["username"]
        passw = request.POST["password"]
        Users = authenticate(username=user, password=passw)
        message = "Usuario o password incorrecto"
        if Users is not None:
            _user = User.objects.filter(username=user).first()
            #user_info = UserInfo.objects.filter(user = _user).first()
            message = "Su usuario se encuentra desactivado"
            #if user_info.active:
            do_login(request, Users)
            return redirect('/')

        return render(request, "auth/sign-in.html", {"valid": message})

    return render(request, "auth/sign-in.html", {"valid": ""})

# Deslogeo
def logout(request):
    # Creacion de historial de logueo
    if request.user.is_authenticated:
        try:
            pass
            
        except Exception as e:
            print("Error: "+str(e))

        do_logout(request)
        return redirect('sign-in')
    return redirect('/')