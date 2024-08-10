from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import login as do_login
from django.contrib.auth import authenticate
from django.contrib.auth import logout as do_logout
from rest_framework.decorators import api_view
from rest_framework.response import Response
import locale
import threading
from datetime import datetime as dt
from .booking import *
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
        try:
            suites_feria = SuitesFeria()
            resp = suites_feria.login()
            logging.info(f"[+] {dt.now()} {resp}")
            if resp["code"] == 200:
                resp_sf = suites_feria.disponibilidad()
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
                logging.info(f"[+] {dt.now()} {resp_l}")
        except Exception as er:
            logging.info(f"[+] {dt.now()} Error: "+str(er))

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
                updated = dt.now(),
                created = dt.now()
            )
        else:
            if _message_by_day.text != request.data["text"]:
                _message_by_day = MessageByDay.objects.create(
                    date_from = request.data["date"],
                    occupancy = request.data["occupancy"],
                    text = request.data["text"],
                    updated = dt.now(),
                    created = dt.now()
                )
        result = {"code": 200, "status": "OK", "message":"Proceso activado correctamente.", "updated": str(_message_by_day.updated).split(".")[0]}
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
                updated = dt.now(),
                created = dt.now()
            )
        else:
            _price.price = request.data["text"]
            _price.updated = dt.now()
            _price.save()
        result = {"code": 200, "status": "OK", "message":"Proceso activado correctamente.", "updated": str(_price.updated).split(".")[0]}
    return Response(result)

def index(request):
    if request.user.is_authenticated:
        __date_from = str(dt.now().date())
        __date_to = str(dt.now().date() + datetime.timedelta(days=1))
        if "date_from" in request.POST:
            __date_from = str(request.POST["date_from"])
        if "date_to" in request.POST:
            __date_to = str(request.POST["date_to"])

        _date_from = dt(
            year=int(__date_from.split("-")[0]),
            month=int(__date_from.split("-")[1]),
            day=int(__date_from.split("-")[2])
        )
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
                bookings[str(_date_from.date())] = {}
            
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
                    bookings[str(_date_from.date())][int(ocp)]["tarifa"] = {"price":__price.price, "updated": str(__price.updated).split(".")[0]}

                # get message
                __message_by_day = MessageByDay.objects.filter(date_from = str(_date_from.date()), occupancy=int(ocp)).last()
                if __message_by_day:
                    bookings[str(_date_from.date())][int(ocp)]["messageDay"] = {"text":__message_by_day.text, "updated":str(__message_by_day.updated).split(".")[0]}

                # get event by day
                __event_by_day = EventByDay.objects.filter(date_from = str(_date_from.date()), occupancy=int(ocp)).last()
                if __event_by_day:
                    bookings[str(_date_from.date())][int(ocp)]["eventByDay"] = {"text":__event_by_day.text, "updated":str(__event_by_day.updated).split(".")[0]}

                avail_sf = AvailSuitesFeria.objects.filter(date_avail = str(_date_from.date())).last()
                avail_sf_cant = CantAvailSuitesFeria.objects.filter(
                    type_avail = int(ocp),
                    avail_suites_feria = avail_sf
                ).last()

                if avail_sf_cant:
                    bookings[str(_date_from.date())][int(ocp)]["suiteFeria"] = avail_sf_cant.avail
                    if int(ocp) == 2:
                        avail_sf_cant = CantAvailSuitesFeria.objects.filter(
                            type_avail = 1,
                            avail_suites_feria = avail_sf
                        ).last()
                        bookings[str(_date_from.date())][int(ocp)]["suiteFeria1"] = avail_sf_cant.avail
                else:
                    if int(ocp) == 5:
                        avail_sf_cant = CantAvailSuitesFeria.objects.filter(
                            type_avail = 4,
                            avail_suites_feria = avail_sf
                        ).last()
                        bookings[str(_date_from.date())][int(ocp)]["suiteFeria"] = avail_sf_cant.avail
                        
                available_booking = AvailableBooking.objects.filter(date_from=str(_date_from.date()), occupancy=int(ocp))
                for avail_book in available_booking:
                    bookings[avail_book.date_from]["updated"] = str(avail_book.updated).split(".")[0]
                    bookings[avail_book.date_from]["date_from"] = avail_book.date_from
                    bookings[avail_book.date_from]["date_to"] = avail_book.date_to
                    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
                    fecha_especifica = dt.strptime(avail_book.date_from, '%Y-%m-%d')
                    bookings[avail_book.date_from]["day"] = fecha_especifica.strftime('%A')
                    
                    bookings[avail_book.date_from][avail_book.occupancy]["total_search"] = avail_book.total_search
                    bookings[avail_book.date_from][avail_book.occupancy]["total_search_192"] = "{:.2f}".format(avail_book.total_search / 192 * 100)

                    if int(avail_book.booking.start) != 0:
                        if avail_book.booking.start not in bookings[avail_book.date_from][avail_book.occupancy]:
                            bookings[avail_book.date_from][avail_book.occupancy][avail_book.booking.start] = {}
                        
                        _price = avail_book.price.replace("€ ", "")
                        
                        if "Hotel Suites Feria de Madrid" == avail_book.booking.title:
                            bookings[avail_book.date_from][avail_book.occupancy]["priceSuitesFeria"] = _price

                        if "media_total" not in bookings[avail_book.date_from][avail_book.occupancy]:
                            bookings[avail_book.date_from][avail_book.occupancy]["media_total"] = 0
                            bookings[avail_book.date_from][avail_book.occupancy]["media_cant"] = 0

                        #if "2024-05-10" == b.date_from and 2 == b.booking.occupancy:
                        #    print(_price, b.booking.start, b.position)

                        if "COP" not in _price and avail_book.position not in bookings[avail_book.date_from][avail_book.occupancy][avail_book.booking.start]:
                            #print(b.booking.occupancy, b.booking.start, b.position, _price)
                            bookings[avail_book.date_from][avail_book.occupancy][avail_book.booking.start][avail_book.position] = {}
                            bookings[avail_book.date_from][avail_book.occupancy][avail_book.booking.start][avail_book.position]["price"] = _price
                            if int(avail_book.booking.start) == 4 and avail_book.position in [0,1,2,3,4,9]:
                                bookings[avail_book.date_from][avail_book.occupancy]["media_total"] += int(_price)
                                bookings[avail_book.date_from][avail_book.occupancy]["media_cant"] += 1
                            bookings[avail_book.date_from][avail_book.occupancy][avail_book.booking.start][avail_book.position]["name"] = avail_book.booking.title
            
            _date_from += datetime.timedelta(days=1)

        return render(request, "app/index.html", {"bookings":bookings, "segment": "index", "date_from": __date_from, "date_to": __date_to})
    else:
        return redirect("sign-in")
    
def booking_view(request):
    if request.user.is_authenticated:
        _date_from = dt(
            year=int(request.GET["date"].split("-")[0]),
            month=int(request.GET["date"].split("-")[1]),
            day=int(request.GET["date"].split("-")[2])
        )
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
        for i in range(0, 8, 1):
            if i == 0:
                available_booking = AvailableBooking.objects.filter(date_from=request.GET["date"], occupancy=int(request.GET["occupancy"])).order_by("id")
            else:
                available_booking = AvailableBooking.objects.filter(date_from=str(_date_from.date() - datetime.timedelta(days=i)), occupancy=int(request.GET["occupancy"])).order_by("id")

            #if not available_booking:
            for s in stars:
                # get message
                __message_by_day = MessageByDay.objects.filter(date_from = str(_date_from.date()), occupancy=int(request.GET["occupancy"])).all()
                if __message_by_day:
                    bookings["bookings"][str(s)]["messageDay"] = ""
                    for m in __message_by_day:
                        bookings["bookings"][str(s)]["messageDay"] += f"{m.text} - {str(m.updated).split('.')[0]} | "

                if i not in list(bookings["bookings"][str(s)].keys()):
                    bookings["bookings"][str(s)][i] = {"min": 100000, "media": 0, "media_cant": 0, "prices":[], "suitesFeriaPrice": 0, "suitesFeria1": 0, "suitesFeria2": 0}
                    if not available_booking:
                        if int(request.GET["occupancy"]) == 2:
                            if s == 3:
                                bookings["bookings"][str(s)][i]["prices"] = [0,0,0,0,0]
                            else:
                                bookings["bookings"][str(s)][i]["prices"] = [0,0,0,0,0,0,0,0,0]
                        elif int(request.GET["occupancy"]) in [3, 5]:
                            if s == 3:
                                bookings["bookings"][str(s)][i]["prices"] = [0,0,0,0,0]
                            else:
                                bookings["bookings"][str(s)][i]["prices"] = [0,0,0,0,0,0]
            
                #print(str(_date_from.date() - datetime.timedelta(days=i)))
                avail_sf = AvailSuitesFeria.objects.filter(date_avail = str(_date_from.date() - datetime.timedelta(days=i))).last()
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
                        bookings["bookings"][str(s)][i]["suitesFeria2"] = avail_sf_cant.avail
                else:
                    if int(request.GET["occupancy"]) == 5:
                        avail_sf_cant = CantAvailSuitesFeria.objects.filter(
                            type_avail = 4,
                            avail_suites_feria = avail_sf
                        ).last()
                        if avail_sf_cant:
                            bookings["bookings"][str(s)][i]["suitesFeria1"] = avail_sf_cant.avail

            for b in available_booking:
                if int(b.booking.start) in stars:
                    _price = b.price.replace("€ ", "")
                    if i == 0:
                        bookings["bookings"][str(b.booking.start)]["list2"].append("*"+b.booking.title+" - € "+_price+" - "+str(b.position) if b.booking.title in bookings["bookings"][str(b.booking.start)]["list"] else ""+b.booking.title)#+" - € "+_price+" - "+str(b.position)

                    if bookings["bookings"][str(b.booking.start)][i]["min"] > int(_price):
                        bookings["bookings"][str(b.booking.start)][i]["min"] = int(_price)

                    bookings["bookings"][str(b.booking.start)][i]["media"] += int(_price)
                    bookings["bookings"][str(b.booking.start)][i]["media_cant"] += 1

                    bookings["bookings"][str(b.booking.start)][i]["prices"].append(int(_price))
                    if "Hotel Suites Feria de Madrid" == b.booking.title:
                        bookings["bookings"][str(b.booking.start)][i]["suitesFeriaPrice"] = _price
        
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
        fecha_especifica = dt.strptime(request.GET["date"], '%Y-%m-%d')
        return render(request, "app/booking.html", {"bookings":bookings, "segment": "index", "day": fecha_especifica.strftime('%A')})
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