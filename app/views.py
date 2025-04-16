from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import login as do_login
from django.contrib.auth import authenticate
from django.contrib.auth import logout as do_logout
from rest_framework.decorators import api_view
from rest_framework.response import Response
import locale
import threading
from datetime import datetime as dt
import time
import subprocess
from .booking import *
from .models import *
from .suitesferia import SuitesFeria
from .fee import FeeTask
from django.utils.timezone import localtime

def reset_task():
    logging.info("[+] Check cron active...")
    for t in CronActive.objects.filter(active=True):
        t.active = False
        t.save()
    logging.info("[+] Check cron active finish...")

    logging.info("[+] Reset data price status...")
    #for t in Price.objects.all():
    #    t.plataform_sync = True
    #    t.save()
    logging.info("[+] Reset data price status finish...")
    for t in TaskLock.objects.all():
        t.delete()

threading.Thread(target=reset_task).start()

def generate_date_with_month(_date:str):
    ___date_from = dt(
        year=int(_date.split("-")[0]),
        month=int(_date.split("-")[1]),
        day=int(_date.split("-")[2])
    )
    return ___date_from.strftime('%d')+"-"+___date_from.strftime('%B')

def generate_date_with_month_time(_date:str):
    _time = _date.split(" ")[1].split(".")[0]
    _date = _date.split(" ")[0]
    meses = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]
    ___date_from = dt(
        year=int(_date.split("-")[0]),
        month=int(_date.split("-")[1]),
        day=int(_date.split("-")[2])
    )
    return f"{___date_from.day}-{meses[___date_from.month - 1]} {_time[:-3]}"
    
def active_process_sf():
    _credential = CredentialPlataform.objects.filter(plataform_option = "suitesferia").first()
    if _credential:
        while True:
            # get data suitesferia.
            try:
                suites_feria = SuitesFeria(_credential.username, _credential.password)
                resp = suites_feria.login()
                logging.info(f"[+] Actualizando suites feria: {now().date()} {resp}")
                generate_log(f"[+] Actualizando Dispo suites feria {now().date()}", BotLog.SUITESFERIA)
                if resp["code"] == 200:
                    resp_sf = suites_feria.disponibilidad(now().date())
                    resp_sf = suites_feria.format_avail(resp_sf)
                    for dsf in resp_sf:
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
                    resp_l = suites_feria.logout()
                    
                    if not check_finish_process():
                        logging.info(f"[+] {now()} Finish process, proceso suites feria...")
                        generate_log(f"[+] Finalizando proceso, proceso suites feria...", BotLog.SUITESFERIA)
                        break

                    logging.info(f"[+] Suites feria actualizado: {now()} {resp_l}")
                    generate_log("[+] Dispo Suites feria actualizado", BotLog.SUITESFERIA)
                
                time.sleep(60)

                if not check_finish_process():
                    logging.info(f"[+] {now()} Finish process, proceso suites feria...")
                    generate_log(f"[+] Finalizando proceso, proceso suites feria...", BotLog.SUITESFERIA)
                    break
            except Exception as er:
                logging.info(f"[+] {now()} Error Get Suites feria: "+str(er))
                generate_log("[+] Error Get Suites feria", BotLog.SUITESFERIA)
                time.sleep(60)

        logging.info(f"[+] {now()} Proceso suites feria Finalizando...")
        generate_log("[+] Proceso suites feria Finalizando...", BotLog.SUITESFERIA)

def get_current_bot_range(bot_setting):
    """
    Retorna el primer BotRange válido para el bot_setting actual,
    que coincida con el día actual y hora actual.
    """

    # Día y hora actuales
    current_time = now().time()
    current_day = now().strftime('%A').lower()

    # Mapeo de inglés a español si tus días están almacenados así
    dias_map = {
        'monday': 'lunes',
        'tuesday': 'martes',
        'wednesday': 'miércoles',
        'thursday': 'jueves',
        'friday': 'viernes',
        'saturday': 'sábado',
        'sunday': 'domingo'
    }
    dia_actual = dias_map.get(current_day)

    # Buscar todos los rangos del bot
    bots_range = BotRange.objects.filter(bot_setting=bot_setting)

    for btr in bots_range:
        # Comprobar si el día aplica
        if btr.day_name.filter(name__iexact=dia_actual).exists():
            # Comprobar si la hora está en algún rango válido
            for hr in btr.hour_range.all():
                if hr.hour_from and hr.hour_to:
                    if hr.hour_from <= current_time <= hr.hour_to:
                        return btr  # ✅ Retornar el primer válido encontrado

    return None  # ❌ Si no se encontró ningún rango válido

def active_process(bot_setting:BotSetting):
    general_search = GeneralSearch.objects.filter(type_search = 1).last()
    general_search_to_name = GeneralSearch.objects.filter(type_search = 2)
    instances = []

    # active bot
    bot_auto = BotAutomatization.objects.last()
    bot_auto.active = True
    bot_auto.save()

    for p in general_search.proces_active.all():
        booking = BookingSearch()
        instances.append({
            "booking": booking,
            "driver": booking._driver(general_search.url)
        })

    logging.info(f"[+] {now()} Activando process...")
    generate_log("[+] Activando process...", BotLog.BOOKING)
    threading.Thread(target=active_process_sf).start()

    stop_event = threading.Event()

    while True:
        try:
            if bot_auto.automatic:
                bot_range = get_current_bot_range(bot_setting)
            else:
                bot_range = BotRange.objects.filter(bot_setting=bot_setting, number=1).last()

            if not bot_range:
                generate_log("[-] No hay rango válido actualmente.", BotLog.BOOKING)
                logging.info("[-] No hay rango válido actualmente.")
                time.sleep(60)
                continue

            if bot_auto.automatic:
                bot_range.date_from = now().date() + datetime.timedelta(days=bot_range.days_from)
                bot_range.date_end = now().date() + datetime.timedelta(days=bot_range.days)
                generate_log(f"Buscar Datos Automaticos: {bot_range.date_from} - {bot_range.date_end} - {bot_range.days}", BotLog.BOOKING)

            threads = []
            cont = 0
            if not check_finish_process():
                logging.info(f"[+] {now()} Finish process...")
                generate_log(f"[+] Finalizando proceso...", BotLog.BOOKING)
                break
            for p in ProcessActive.objects.filter(type_proces = 1):
                try:
                    logging.info(f"[+] {now()} Process active in while. Search with city browser... {instances[cont]['booking']}")
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
                            stop_event
                        )
                    )
                    process.daemon = True
                    process.start()
                    threads.append(process)
                except Exception as ec:
                    logging.info(f"[-] {now()} Error in Execute controller positions... {ec}")
                    generate_log(f"[-] Error in Execute controller positions... {ec}", BotLog.BOOKING)
                cont += 1

            if bot_auto.automatic:
                # Verificar si faltan 5 minutos para el fin de rango
                for hr in bot_range.hour_range.all():
                    if hr.hour_to:
                        now_time = now().time()
                        cutoff_time = (dt.combine(dt.today(), hr.hour_to) - datetime.timedelta(minutes=5)).time()
                        logging.info(f"[!] Check hours: {cutoff_time} - Now: {now_time}")
                        generate_log(f"[!] Check hours: {cutoff_time} - Now: {now_time}", BotLog.BOOKING)
                        if now_time >= cutoff_time:
                            logging.info("[!] Finalizando hilos antes del cambio de rango horario.")
                            generate_log("[!] Finalizando hilos por cambio de rango horario.", BotLog.BOOKING)
                            stop_event.set()
                            logging.info("[+] Reiniciando con siguiente rango tras esperar 5 minutos.")
                            generate_log("[+] Reiniciando con siguiente rango tras esperar 5 minutos.", BotLog.BOOKING)
                            sleep(300)
                            break

            for t in threads:
                logging.info(f"[+] {now()} Esperando finalizacion de thread...")
                generate_log("[+] Esperando finalizacion de thread...", BotLog.BOOKING)
                t.join()
            
            if not check_finish_process():
                logging.info(f"[+] {now()} Finish process, despues de posiciones...")
                generate_log(f"[+] Finalizando proceso, despues de posiciones...", BotLog.BOOKING)
                break

            # add process name hotel.
            logging.info(f"[+] {now()} Process active in while. Search with name browser... {instances[0]['booking']}")
            generate_log("[+] Buscando hoteles por nombre...", BotLog.BOOKING)
            for gs in general_search_to_name:
                for _pa in gs.proces_active.all():
                    #if gs.proces_active.last().active:
                    try:
                        instances[0]["booking"].controller(
                            instances[0]["driver"],
                            _pa,
                            gs.city_and_country,
                            None,
                            bot_range.date_from,
                            bot_range.date_end,
                            stop_event
                        )
                    except Exception as ec:
                        logging.info(f"[-] {now()} Error in Execute controller with name... {ec}")
                        generate_log(f"[-] Error in Execute controller with name... {ec}", BotLog.BOOKING)

            if not check_finish_process():
                logging.info(f"[+] {now()} Finish process, despues de nombres...")
                generate_log(f"[+] Finalizando proceso, despues de nombres...", BotLog.BOOKING)
                break

            seconds = 60 * (general_search.time_sleep_minutes if general_search else 3)
            logging.info(f"[+] {now()} Sleep {seconds} seconds...")
            generate_log(f"[+] Sleep {seconds} seconds...", BotLog.BOOKING)
            sleep(seconds)

            if not check_finish_process():
                logging.info(f"[+] {now()} Finish process, proceso final...")
                generate_log(f"[+] Finalizando proceso, proceso final...", BotLog.BOOKING)
                break

            logging.info(f"[+] {now()} Sleep {seconds} seconds finish...")
            generate_log(f"[+] Sleep {seconds} seconds finish...", BotLog.BOOKING)

        except Exception as e:
            logging.info(f"[-] {now()} Error process general: {e}...")
            generate_log(f"[-] Error process general: {e}...", BotLog.BOOKING)

    logging.info(f"[+] {now()} Process Booking Finalizando...")
    generate_log("[+] Process Booking Finalizando...", BotLog.BOOKING)

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
    # try:
    #     subprocess.run(['sudo', 'systemctl', 'restart', "booking"], check=True)
    #     subprocess.run(['sudo', 'systemctl', 'restart', "nginx"], check=True)
    #     logging.info("Servicio booking y nginx reiniciado correctamente.")
    # except subprocess.CalledProcessError as e:
    #     logging.info(f"Error al reiniciar el servicio booking: {e}")
    # except Exception as ex:
    #     logging.info(f"Se produjo un error: {ex}")
    
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

@api_view(["POST"])
def finish_get_booking(request):
    result = {"code": 400, "status": "Fail", "message":"User not authenticated."}
    if request.user.is_authenticated:
        reset_service()
        result["code"] = 200
        result["status"] = "OK"
        result["message"] = "Proceso desactivado correctamente."
    return Response(result)

@api_view(["POST"])
def check_booking_process(request):
    result = {"code": 400, "status": "Fail", "message":"User not authenticated."}
    if request.user.is_authenticated:
        state = BotAutomatization.objects.last().active
        
        bot_logs = {}
        bot_log = BotLog.objects.filter(plataform_option = BotLog.BOOKING).last()
        if bot_log:
            bot_logs[bot_log.plataform_option] = {"description": bot_log.description, "created": generate_date_with_month_time(str(bot_log.created))}
        bot_log = BotLog.objects.filter(plataform_option = BotLog.ROOMPRICE).last()
        if bot_log:
            bot_logs[bot_log.plataform_option] = {"description": bot_log.description, "created": generate_date_with_month_time(str(bot_log.created))}
        bot_log = BotLog.objects.filter(plataform_option = BotLog.SUITESFERIA).last()
        if bot_log:
            bot_logs[bot_log.plataform_option] = {"description": bot_log.description, "created": generate_date_with_month_time(str(bot_log.created))}
        
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
                prices.append({"price": _price.price, "pSync": _price.plataform_sync, "date_from": _price.date_from, "occupancy": _price.occupancy})
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
            "active":state, 
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
        _message_by_day = MessageByDay.objects.filter(
            date_from = request.data["date"],
            occupancy = request.data["occupancy"]
        ).last()
        if not _message_by_day:
            _message_by_day = MessageByDay.objects.create(
                date_from = request.data["date"],
                occupancy = request.data["occupancy"],
                text = request.data["text"],
                updated = now(),
                created = now()
            )
        else:
            if _message_by_day.text != request.data["text"]:
                _message_by_day = MessageByDay.objects.create(
                    date_from = request.data["date"],
                    occupancy = request.data["occupancy"],
                    text = request.data["text"],
                    updated = now(),
                    created = now()
                )
        result = {"code": 200, "status": "OK", "message":"Proceso activado correctamente.", "updated": generate_date_with_month_time(str(_message_by_day.updated))}
    return Response(result)

def task_save_fee(price, _date, cron:CronActive, _credential:CredentialPlataform):
    try:
        while cron.current_date > now():
            sleep(1)

        cont = 0
        while True:
            try:
                #for _ in range(2):
                fee = FeeTask()
                _driver = fee._driver()
                _check = fee.controller(_driver, price, _date, _credential.username, _credential.password)
                sleep(5)
                fee.close(_driver)
                # if not _check:
                #     break
                if _check or cont >= 3:
                    break
                cont += 1
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
            for p in Price.objects.filter(date_from = request.data["date"]):
                if p.price != None and p.price != "":
                    _prices[str(p.occupancy)] = p

            message = "Proceso activado correctamente."
            _credential = CredentialPlataform.objects.filter(plataform_option = "roomprice").first()
            if _credential:
                cron_active = CronActive.objects.last()
                #print(cron_active)
                if cron_active:
                    if cron_active.active:
                        cron = CronActive.objects.create(
                            active = True,
                            current_date = cron_active.current_date + datetime.timedelta(minutes=1.5)
                        )
                    else:
                        cron = CronActive.objects.create(
                            active = True,
                            current_date = now()
                        )
                else:
                    cron = CronActive.objects.create(
                        active = True,
                        current_date = now()
                    )
                threading.Thread(
                    target=task_save_fee, 
                    args=(
                        _prices,
                        request.data["date"],
                        cron,
                        _credential
                    )
                ).start()
                __time += (cron.current_date - now()).total_seconds()
            else:
                message = "No se ha configurado credenciales"
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
            _price.updated = now()
            _price.save()
        result = {"code": 200, "status": "OK", "message":"Proceso activado correctamente.", "updated": generate_date_with_month_time(str(_price.updated)), "pSync": _price.plataform_sync}
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
                text = request.data["text"],
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
        
            for ocp in occupancys:
                if int(ocp) not in list(bookings[str(_date_from.date())].keys()):
                    bookings[str(_date_from.date())][int(ocp)] = {}
                
                # get price tarifa
                __price = Price.objects.filter(date_from = str(_date_from.date()), occupancy=int(ocp)).last()
                if __price:
                    bookings[str(_date_from.date())][int(ocp)]["tarifa"] = {
                        "price":__price.price, 
                        "updated": generate_date_with_month_time(str(__price.updated)),
                        "pSync": __price.plataform_sync
                    }
                    if int(ocp) == 2:
                        __price = Price.objects.filter(date_from = str(_date_from.date()), occupancy=1).last()
                        if __price:
                            bookings[str(_date_from.date())][int(ocp)]["tarifa1"] = {
                                "price":__price.price, 
                                "updated": generate_date_with_month_time(str(__price.updated)),
                                "pSync": __price.plataform_sync
                            }
                    if int(ocp) == 3:
                        __price = Price.objects.filter(date_from = str(_date_from.date()), occupancy=4).last()
                        if __price:
                            bookings[str(_date_from.date())][int(ocp)]["tarifa1"] = {
                                "price":__price.price, 
                                "updated": generate_date_with_month_time(str(__price.updated)),
                                "pSync": __price.plataform_sync
                            }
                    if int(ocp) == 5:
                        __price = Price.objects.filter(date_from = str(_date_from.date()), occupancy=6).last()
                        if __price:
                            bookings[str(_date_from.date())][int(ocp)]["tarifa1"] = {
                                "price":__price.price, 
                                "updated": generate_date_with_month_time(str(__price.updated)),
                                "pSync": __price.plataform_sync
                            }
                # get message
                __message_by_day = MessageByDay.objects.filter(date_from = str(_date_from.date()), occupancy=int(ocp)).last()
                if __message_by_day:
                    bookings[str(_date_from.date())][int(ocp)]["messageDay"] = {"text":__message_by_day.text, "updated":generate_date_with_month_time(str(__message_by_day.updated))}

                # get event by day
                __event_by_day = EventByDay.objects.filter(date_from = str(_date_from.date()), occupancy=int(ocp)).last()
                if __event_by_day:
                    bookings[str(_date_from.date())][int(ocp)]["eventByDay"] = {"text":__event_by_day.text, "updated":generate_date_with_month_time(str(__event_by_day.updated))}

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
                available_booking = AvailableBooking.objects.filter(date_from=str(_date_from.date()), occupancy=int(ocp))
                for avail_book in available_booking:
                    if int(avail_book.booking.start) != 0:
                        #----------------------------------
                        #available_booking2 = AvailableBooking.objects.filter(date_from=str(_date_from_current.date() - datetime.timedelta(days=1)), occupancy=int(ocp))
                        try:
                            copy_prices1 = CopyPriceWithDay.objects.filter(avail_booking = avail_book).order_by("-id")[0]
                        except Exception as e:
                            copy_prices1 = CopyPriceWithDay()
                            copy_prices1.price = "0"
                        if "media_total1" not in bookings[str(_date_from.date())][avail_book.occupancy]:
                            bookings[str(_date_from.date())][avail_book.occupancy]["media_total1"] = 0
                            bookings[str(_date_from.date())][avail_book.occupancy]["media_cant1"] = 0

                        _price3 = copy_prices1.price.replace("€ ", "").replace(".", "").replace(",", "")
                        if _price3 != "":
                            if int(avail_book.booking.start) == 4 and avail_book.position in [0,1,2,3,4,9,14,19,24]:
                                bookings[str(_date_from.date())][avail_book.occupancy]["media_total1"] += int(_price3)
                                bookings[str(_date_from.date())][avail_book.occupancy]["media_cant1"] += 1  

                        #available_booking3 = AvailableBooking.objects.filter(date_from=str(_date_from_current.date() - datetime.timedelta(days=7)), occupancy=int(ocp))
                        try:
                            copy_prices1 = CopyPriceWithDay.objects.filter(avail_booking = avail_book).order_by("-id")[6]
                        except Exception as e:
                            copy_prices1 = CopyPriceWithDay()
                            copy_prices1.price = "0"
                        if "media_total7" not in bookings[str(_date_from.date())][avail_book.occupancy]:
                            bookings[str(_date_from.date())][avail_book.occupancy]["media_total7"] = 0
                            bookings[str(_date_from.date())][avail_book.occupancy]["media_cant7"] = 0
                        
                        _price4 = copy_prices1.price.replace("€ ", "").replace(".", "").replace(",", "")
                        if _price4 != "":
                            if int(avail_book.booking.start) == 4 and avail_book.position in [0,1,2,3,4,9,14,19,24]:
                                bookings[str(_date_from.date())][avail_book.occupancy]["media_total7"] += int(_price4)
                                bookings[str(_date_from.date())][avail_book.occupancy]["media_cant7"] += 1
                        #---------------------------------

                        if avail_book.booking.start not in bookings[avail_book.date_from][avail_book.occupancy]:
                            bookings[avail_book.date_from][avail_book.occupancy][avail_book.booking.start] = {}
                        
                        _price = avail_book.price.replace("€ ", "").replace(".", "").replace(",", "")
                        if _price != "":
                            if "media_total" not in bookings[avail_book.date_from][avail_book.occupancy]:
                                bookings[avail_book.date_from][avail_book.occupancy]["media_total"] = 0
                                bookings[avail_book.date_from][avail_book.occupancy]["media_cant"] = 0

                            #if "2024-05-10" == b.date_from and 2 == b.booking.occupancy:
                            #    print(_price, b.booking.start, b.position)

                            if "COP" not in _price and avail_book.position not in bookings[avail_book.date_from][avail_book.occupancy][avail_book.booking.start]:
                                #print(b.booking.occupancy, b.booking.start, b.position, _price)
                                try:
                                    if _price:
                                        bookings[avail_book.date_from][avail_book.occupancy][avail_book.booking.start][avail_book.position] = {}
                                        bookings[avail_book.date_from][avail_book.occupancy][avail_book.booking.start][avail_book.position]["price"] = _price
                                        if int(avail_book.booking.start) == 4 and avail_book.position in [0,1,2,3,4,9,14,19,24]:
                                            bookings[avail_book.date_from][avail_book.occupancy]["media_total"] += int(_price)
                                            bookings[avail_book.date_from][avail_book.occupancy]["media_cant"] += 1
                                        bookings[avail_book.date_from][avail_book.occupancy][avail_book.booking.start][avail_book.position]["name"] = avail_book.booking.title
                                except Exception as e:
                                    logging.info(f"[-] Error price: {e}")
                        
                # change price with nameprice hotel.
                price_with_name_hotel = PriceWithNameHotel.objects.filter(title = "Hotel Suites Feria de Madrid", date_from = str(_date_from.date()), occupancy = int(ocp)).first()
                if price_with_name_hotel:
                    bookings[price_with_name_hotel.date_from][int(ocp)]["priceSuitesFeria"] = price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")
                    
                    try:
                        available_booking1 = CopyPriceWithNameFromDay.objects.filter(avail = price_with_name_hotel).order_by("-id")[0]
                    except Exception as e:
                        available_booking1 = CopyPriceWithNameFromDay()
                        available_booking1.price = "0"

                    if available_booking1:
                        _price1 = available_booking1.price.replace("€ ", "").replace(".", "").replace(",", "")
                        bookings[price_with_name_hotel.date_from][int(ocp)]["priceSuitesFeria1"] = int(_price1)
                        bookings[price_with_name_hotel.date_from][int(ocp)]["priceSuitesFeriaRest1"] = int(_price1) - int(_price) if "priceSuitesFeria" in bookings[price_with_name_hotel.date_from][int(ocp)] else 0
                    
                    try:
                        available_booking7 = CopyPriceWithNameFromDay.objects.filter(avail = price_with_name_hotel).order_by("-id")[6]
                    except Exception as e:
                        available_booking7 = CopyPriceWithNameFromDay()
                        available_booking7.price = "0"

                    if available_booking7:
                        _price7 = available_booking7.price.replace("€ ", "").replace(".", "").replace(",", "")
                        bookings[price_with_name_hotel.date_from][int(ocp)]["priceSuitesFeria7"] = int(_price7)
                        bookings[price_with_name_hotel.date_from][int(ocp)]["priceSuitesFeriaRest7"] = int(_price7) - int(_price) if "priceSuitesFeria" in bookings[price_with_name_hotel.date_from][int(ocp)] else 0
                
            # change price with nameprice hotel.
            if "media_name_hotel" not in bookings[avail_book.date_from][2].keys():
                bookings[avail_book.date_from][2]["media_name_hotel"] = 0
                bookings[avail_book.date_from][2]["media_cant_name_hotel"] = 0

            price_with_name_hotel = PriceWithNameHotel.objects.filter(title = "Hotel Suites Feria de Madrid", date_from = str(_date_from.date()), occupancy = 2).first()
            if price_with_name_hotel:
                bookings[price_with_name_hotel.date_from][2]["priceSF"] = price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")
                #bookings[avail_book.date_from][2]["media_name_hotel"] += int(price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", ""))
                #bookings[avail_book.date_from][2]["media_cant_name_hotel"] += 1

            price_with_name_hotel = PriceWithNameHotel.objects.filter(title = "Zenit Conde de Orgaz", date_from = str(_date_from.date()), occupancy = 2).first()
            if price_with_name_hotel:
                bookings[price_with_name_hotel.date_from][2]["priceZEN"] = price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")
                if int(price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")) > 0:
                    bookings[avail_book.date_from][2]["media_name_hotel"] += int(price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", ""))
                    bookings[avail_book.date_from][2]["media_cant_name_hotel"] += 1
            
            price_with_name_hotel = PriceWithNameHotel.objects.filter(title = "Hotel Best Osuna", date_from = str(_date_from.date()), occupancy = 2).first()
            if price_with_name_hotel:
                bookings[price_with_name_hotel.date_from][2]["priceOSU"] = price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")
                if int(price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")) > 0:
                    bookings[avail_book.date_from][2]["media_name_hotel"] += int(price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", ""))
                    bookings[avail_book.date_from][2]["media_cant_name_hotel"] += 1

            price_with_name_hotel = PriceWithNameHotel.objects.filter(title = "Ilunion Alcala Norte", date_from = str(_date_from.date()), occupancy = 2).first()
            if price_with_name_hotel:
                bookings[price_with_name_hotel.date_from][2]["priceILU"] = price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")
                if int(price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")) > 0:
                    bookings[avail_book.date_from][2]["media_name_hotel"] += int(price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", ""))
                    bookings[avail_book.date_from][2]["media_cant_name_hotel"] += 1
            
            price_with_name_hotel = PriceWithNameHotel.objects.filter(title = "Eco Alcala Suites", date_from = str(_date_from.date()), occupancy = 2).first()
            if price_with_name_hotel:
                bookings[price_with_name_hotel.date_from][2]["priceECO"] = price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")
                if int(price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")) > 0:
                    bookings[avail_book.date_from][2]["media_name_hotel"] += int(price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", ""))
                    bookings[avail_book.date_from][2]["media_cant_name_hotel"] += 1
            
            price_with_name_hotel = PriceWithNameHotel.objects.filter(title = "Silken Puerta Madrid", date_from = str(_date_from.date()), occupancy = 2).first()
            if price_with_name_hotel:
                bookings[price_with_name_hotel.date_from][2]["priceSIL"] = price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")
                if int(price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")) > 0:
                    bookings[avail_book.date_from][2]["media_name_hotel"] += int(price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", ""))
                    bookings[avail_book.date_from][2]["media_cant_name_hotel"] += 1
            
            price_with_name_hotel = PriceWithNameHotel.objects.filter(title = "Exe Madrid Norte", date_from = str(_date_from.date()), occupancy = 2).first()
            if price_with_name_hotel:
                bookings[price_with_name_hotel.date_from][2]["priceEXE"] = price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")
                if int(price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")) > 0:
                    bookings[avail_book.date_from][2]["media_name_hotel"] += int(price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", ""))
                    bookings[avail_book.date_from][2]["media_cant_name_hotel"] += 1
            
            price_with_name_hotel = PriceWithNameHotel.objects.filter(title = "Sercotel Alcala 611", date_from = str(_date_from.date()), occupancy = 2).first()
            if price_with_name_hotel:
                bookings[price_with_name_hotel.date_from][2]["priceSER"] = price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")
                if int(price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")) > 0:
                    bookings[avail_book.date_from][2]["media_name_hotel"] += int(price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", ""))
                    bookings[avail_book.date_from][2]["media_cant_name_hotel"] += 1
            
            price_with_name_hotel = PriceWithNameHotel.objects.filter(title = "Axor Feria", date_from = str(_date_from.date()), occupancy = 2).first()
            if price_with_name_hotel:
                bookings[price_with_name_hotel.date_from][2]["priceAXO"] = price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")
                if int(price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")) > 0:
                    bookings[avail_book.date_from][2]["media_name_hotel"] += int(price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", ""))
                    bookings[avail_book.date_from][2]["media_cant_name_hotel"] += 1
            
            price_with_name_hotel = PriceWithNameHotel.objects.filter(title = "DWO Colours Alcala", date_from = str(_date_from.date()), occupancy = 2).first()
            if price_with_name_hotel:
                bookings[price_with_name_hotel.date_from][2]["priceDWO"] = price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")
                if int(price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")) > 0:
                    bookings[avail_book.date_from][2]["media_name_hotel"] += int(price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", ""))
                    bookings[avail_book.date_from][2]["media_cant_name_hotel"] += 1
            
            price_with_name_hotel = PriceWithNameHotel.objects.filter(title = "Hotel Nuevo Boston", date_from = str(_date_from.date()), occupancy = 2).first()
            if price_with_name_hotel:
                bookings[price_with_name_hotel.date_from][2]["priceBOS"] = price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")
                if int(price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")) > 0:
                    bookings[avail_book.date_from][2]["media_name_hotel"] += int(price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", ""))
                    bookings[avail_book.date_from][2]["media_cant_name_hotel"] += 1
            
            price_with_name_hotel = PriceWithNameHotel.objects.filter(title = "Senator Barajas", date_from = str(_date_from.date()), occupancy = 2).first()
            if price_with_name_hotel:
                bookings[price_with_name_hotel.date_from][2]["priceSEN"] = price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")
                if int(price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")) > 0:
                    bookings[avail_book.date_from][2]["media_name_hotel"] += int(price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", ""))
                    bookings[avail_book.date_from][2]["media_cant_name_hotel"] += 1
            
            price_with_name_hotel = PriceWithNameHotel.objects.filter(title = "Travelodge Torrelaguna", date_from = str(_date_from.date()), occupancy = 2).first()
            if price_with_name_hotel:
                bookings[price_with_name_hotel.date_from][2]["priceTOR2"] = price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")
                if int(price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", "")) > 0:
                    bookings[avail_book.date_from][2]["media_name_hotel"] += int(price_with_name_hotel.price.replace("€ ", "").replace(".", "").replace(",", ""))
                    bookings[avail_book.date_from][2]["media_cant_name_hotel"] += 1
            
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
            
            avail_with_date = AvailWithDate.objects.filter(date_from=str(_date_from.date())).first()
            bookings[str(_date_from.date())]["availWithDate"] = 0
            if avail_with_date:
                bookings[str(_date_from.date())]["availWithDate"] = int(avail_with_date.avail)
            valueRest = bookings[str(_date_from.date())]["totalFeria"] - bookings[str(_date_from.date())]["availWithDate"]
            bookings[str(_date_from.date())]["availWithDateRest"] = {"value":valueRest, "color": "text-white" if valueRest >= 0 else "text-danger"}
            if "range_bt" in request.POST:
                if request.POST["range_bt"] == "2":
                    if valueRest != 0:
                        del bookings[str(_date_from.date())]
                elif request.POST["range_bt"] == "3":
                    if valueRest == 0:
                        del bookings[str(_date_from.date())]

            _date_from += datetime.timedelta(days=1)

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
        #print(time.time() - __time)
        return render(
            request, 
            "app/index.html", 
            {
                "bookings":bookings,
                "segment": "index",
                "date_from": __date_from,
                "date_to": __date_to,
                "date_process_from": str(_date_process.date_from),
                "date_process": str(_date_process.date_end),
                "range_bt":range_bt,
                "range_pg": range_pg,
                "bot_auto": bot_auto,
                "bot_range": bot_range,
                "bot_setting": _bot_setting
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
                    bookings["bookings"][str(s)]["messageDay"].append(f"{m.text} ----- {generate_date_with_month_time(str(m.updated))}")
            
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