from datetime import datetime as dt

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