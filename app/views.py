from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import login as do_login
from django.contrib.auth import authenticate
from django.contrib.auth import logout as do_logout
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .booking import *
import threading
from datetime import datetime as dt
from .models import *
from .suitesferia import SuitesFeria
# Create your views here.

def active_process(request):
    for a in AvailableBooking.objects.all():
        _date = dt(
            year=int(a.date_from.split("-")[0]),
            month=int(a.date_from.split("-")[1]),
            day=int(a.date_from.split("-")[2]),
        )
        if _date < dt.now():
            a.delete()
        
    for p in ProcessActive.objects.all():
        p.currenct = True
        p.save()

    logging.info(f"[+] {dt.now()} Activando process...")
    while True:
        threads = []
        general_search = GeneralSearch.objects.all().last()
        for p in ProcessActive.objects.all():
            if not p.active:
                booking = BookingSearch()
                logging.info(f"[+] {dt.now()} Search driver...")
                _driver = booking._driver(general_search.url)
                p.active = True
                p.save()
                #process = threading.Thread(target=booking.controller, args=(_driver, dt.now(), request.data["date_end"].split("-"), request.data["occupancy"], request.data["start"]))"Madrid, Comunidad de Madrid, España"
                logging.info(f"[+] {dt.now()} Process active in while...")
                process = threading.Thread(target=booking.controller, args=(_driver, dt.now(), str(p.date_end).split("-"), int(p.occupancy), int(p.start), p, general_search.city_and_country))
                process.daemon = True
                process.start()
                threads.append(process)
        
        # get data suitesferia.
        suites_feria = SuitesFeria()
        resp = suites_feria.login()
        logging.info(f"[+] {dt.now()} {resp}")
        if resp["code"] == 200:
            resp_sf = suites_feria.disponibilidad()
            resp_sf = suites_feria.format_avail(resp_sf)
            for dsf in resp_sf:
                avail_sf = AvailSuitesFeria.objects.filter(date_avail = dsf["date"])
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
            logging.info(f"[+] {dt.now()} {resp_l}")

        for t in threads:
            logging.info(f"[+] {dt.now()} Esperando finalizacion de thread...")
            t.join()
        
        if general_search:
            seconds = 60 * general_search.time_sleep_minutes
            logging.info(f"[+] {dt.now()} Sleep defined {seconds} seconds...")
            sleep(seconds) # minutos definidos en proceso.
        else:
            seconds = 60 * 3
            logging.info(f"[+] {dt.now()} Sleep default {seconds} seconds...")
            sleep(seconds) # 3 minutos por default.
        logging.info(f"[+] {dt.now()} Sleep {seconds} seconds finish...")
        state = False
        for p in ProcessActive.objects.all():
            if p.currenct:
                state = True
                break
        if not state:
            break
    logging.info(f"[+] {dt.now()} Finalizando process...")

@api_view(["POST"])
def get_booking(request):
    state = False
    for p in ProcessActive.objects.all():
        if p.currenct:
            state = True
            break
    result = {"code": 200, "status": "OK", "message":"Proceso activado correctamente."}
    if not state:
        for p in ProcessActive.objects.all():
            p.active = False
            p.save()
        threading.Thread(target=active_process, args=(request,)).start()
    else:
        for p in ProcessActive.objects.all():
            p.currenct = False
            p.save()
        result["message"] = "Proceso desactivado correctamente."
    return Response(result)

def index(request):
    if request.user.is_authenticated:
        available_booking = AvailableBooking.objects.all().order_by("id")
        bookings = {}
        for b in available_booking:
            if b.date_from not in bookings:
                bookings[b.date_from] = {}
            bookings[b.date_from]["date_from"] = b.date_from
            bookings[b.date_from]["date_to"] = b.date_to
            if b.booking.occupancy not in bookings[b.date_from]:
                bookings[b.date_from][b.booking.occupancy] = {}

            bookings[b.date_from][b.booking.occupancy]["total_search"] = b.total_search

            if int(b.booking.start) != 0:
                if b.booking.start not in bookings[b.date_from][b.booking.occupancy]:
                    bookings[b.date_from][b.booking.occupancy][b.booking.start] = {}
                
                _price = b.price.replace("€ ", "")

                if "media_total" not in bookings[b.date_from][b.booking.occupancy]:
                    bookings[b.date_from][b.booking.occupancy]["media_total"] = 0
                    bookings[b.date_from][b.booking.occupancy]["media_cant"] = 0

                #if "2024-05-10" == b.date_from and 2 == b.booking.occupancy:
                #    print(_price, b.booking.start, b.position)

                if "COP" not in _price and b.position not in bookings[b.date_from][b.booking.occupancy][b.booking.start]:
                    bookings[b.date_from][b.booking.occupancy][b.booking.start][b.position] = {}
                    bookings[b.date_from][b.booking.occupancy][b.booking.start][b.position]["price"] = _price
                    bookings[b.date_from][b.booking.occupancy]["media_total"] += int(_price)
                    bookings[b.date_from][b.booking.occupancy]["media_cant"] += 1
                    bookings[b.date_from][b.booking.occupancy][b.booking.start][b.position]["name"] = b.booking.title
        #try:
        #    print(bookings["2024-05-10"])
        #except:
        #    pass
        return render(request, "app/index.html", {"bookings":bookings, "segment": "index"})
    else:
        return redirect("sign-in")
    
def booking_view(request):
    if request.user.is_authenticated:
        available_booking = AvailableBooking.objects.filter(date_from=request.GET["date"]).order_by("id")
        bookings = {}
        if int(request.GET["occupancy"]) in [2, 3]:
            if int(request.GET["occupancy"]) == 2:
                bookings = {"bookings":{"3":{"list":[], "list2": [], "title":"2P 3*", "min": 200000000000, "media": 0, "media_cant": 0}, "4":{"list":[], "list2": [], "title":"2P 4*", "min": 200000000000, "media": 0, "media_cant": 0}}}
            else:
                bookings = {"bookings":{"3":{"list":[],"list2": [],  "title":"3P 3*", "min": 200000000000, "media": 0, "media_cant": 0}, "4":{"list":[], "list2": [], "title":"3P 4*", "min": 200000000000, "media": 0, "media_cant": 0}}}
        else:
            bookings = {"bookings":{"3":{"list":[],"list2": [],  "title":"5P 3*", "min": 200000000000, "media": 0, "media_cant": 0}, "4":{"list":[],"list2": [],  "title":"5P 4*", "min": 200000000000, "media": 0, "media_cant": 0}}}

        if int(request.GET["occupancy"]) == 2:
            bookings["bookings"]["3"]["list"] = [
                "Travelodge Torrelaguna",
                "Compostela Suites",
                "ZLEEP Madrid",
                "Caballero Errante",
                "Anaco",
                "Porcel Torregarden",
            ]
            bookings["bookings"]["4"]["list"] = [
                "Zenit Conde de Orgaz",
                "Ilunion Alcala Norte",
                "Best Osuna",
                "DWO Colours Alcala",
                "Senator Barajas",
                "Hotel Nuevo Boston",
                "Sercotel Aeropuerto",
                "Sercotel Alcala 511",
                "Praga",
                "Axor Feria",
                "Silken Puerta Madrid",
                "Axor Barajas",
                "Ilunion Atrium",
                "Eco Alcala Suites",
                "Exe Convention Plaza Madrid",
                "Hotel Suites Feria de Madrid"
            ]
        elif int(request.GET["occupancy"]) == 3:
            bookings["bookings"]["3"]["list"] = [
                "Travelodge Torrelaguna",
                "Compostela Suites",
                "Porcel Torregarden",
                "H-A Aparthotel QUO",
                "Aparthotel Tribunal",
            ]
            bookings["bookings"]["4"]["list"] = [
                "Zenit Conde de Orgaz",
                "Ilunion Alcala Norte",
                "Best Osuna",
                "DWO Colours Alcala",
                "Senator Barajas",
                "Hotel Nuevo Boston",
                "Ilunion Pio XII",
                "EXE Madrid Norte",
                "Praga",
                "VillaMadrid",
                "Hotel Suites Feria de Madrid"
            ]
        elif int(request.GET["occupancy"]) == 5:
            bookings["bookings"]["4"]["list"] = [
                "ALIANZA SUITES",
                "Eco Alcalá Suites",
                "Ekilibrio Hotel",
                "Praga",
                "AP Hotel madrid airport",
                "Holiday Inn MADRID- Las Tablas",
                "Hotel Suites Feria de Madrid"
            ]
        for b in available_booking:
            if b.booking.occupancy == int(request.GET["occupancy"]):
                if int(b.booking.start) in [3, 4, 5]:
                    #print(b.booking.title, f"- Occupancy: {b.booking.occupancy}", f"- Stars: {b.booking.start}")
                    _price = b.price.replace("€ ", "")
                    bookings["bookings"][str(b.booking.start)]["list2"].append("*"+b.booking.title+" - € "+_price+" - "+str(b.position) if b.booking.title in bookings["bookings"][str(b.booking.start)]["list"] else ""+b.booking.title+" - € "+_price+" - "+str(b.position))
                    
                    #if b.booking.title in bookings["bookings"][str(b.booking.start)]["list"]:
                    print(bookings["bookings"][str(b.booking.start)]["min"], _price, bookings["bookings"][str(b.booking.start)]["min"] > int(_price))
                    if bookings["bookings"][str(b.booking.start)]["min"] > int(_price):
                        bookings["bookings"][str(b.booking.start)]["min"] = int(_price)

                    bookings["bookings"][str(b.booking.start)]["media"] += int(_price)
                    bookings["bookings"][str(b.booking.start)]["media_cant"] += 1

                # if b.date_from not in bookings:
                #     bookings[b.date_from] = {}
                # bookings[b.date_from]["date_from"] = b.date_from
                # bookings[b.date_from]["date_to"] = b.date_to
                # if b.booking.occupancy not in bookings[b.date_from]:
                #     bookings[b.date_from][b.booking.occupancy] = {}

                # bookings[b.date_from][b.booking.occupancy]["total_search"] = b.total_search

                # if int(b.booking.start) != 0:
                #     if b.booking.start not in bookings[b.date_from][b.booking.occupancy]:
                #         bookings[b.date_from][b.booking.occupancy][b.booking.start] = {}
                    
                #     _price = b.price.replace("€ ", "")

                #     if "media_total" not in bookings[b.date_from][b.booking.occupancy]:
                #         bookings[b.date_from][b.booking.occupancy]["media_total"] = 0
                #         bookings[b.date_from][b.booking.occupancy]["media_cant"] = 0

                #     #if "2024-05-10" == b.date_from and 2 == b.booking.occupancy:
                #     #    print(_price, b.booking.start, b.position)

                #     if "COP" not in _price and b.position not in bookings[b.date_from][b.booking.occupancy][b.booking.start]:
                #         bookings[b.date_from][b.booking.occupancy][b.booking.start][b.position] = "€ "+_price
                #         bookings[b.date_from][b.booking.occupancy]["media_total"] += int(_price)
                #         bookings[b.date_from][b.booking.occupancy]["media_cant"] += 1
        #try:
        #    print(bookings["2024-05-10"])
        #except:
        #    pass
        #print(list(bookings.values()))
        return render(request, "app/booking.html", {"bookings":bookings, "segment": "index"})
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