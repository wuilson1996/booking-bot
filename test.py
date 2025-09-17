# import datetime

# def generar_rangos_14_dias(fecha_inicio: datetime.date, cantidad_rangos: int = 1):
#     """
#     Genera cortes de 14 días a partir de fecha_inicio y devuelve
#     también la siguiente fecha para continuar generando rangos.

#     :param fecha_inicio: Fecha desde donde empiezan los cortes
#     :param cantidad_rangos: Cuántos cortes generar (por defecto 1)
#     :return: (rangos, siguiente_fecha)
#              rangos -> Lista de tuplas [(fecha_inicio_rango, fecha_fin_rango), ...]
#              siguiente_fecha -> Fecha del día siguiente al último rango
#     """
#     rangos = []
#     actual = fecha_inicio

#     for _ in range(cantidad_rangos):
#         inicio = actual
#         fin = actual + datetime.timedelta(days=13)
#         rangos.append((inicio, fin))
#         actual = fin + datetime.timedelta(days=1)

#     # La fecha siguiente para seguir generando después
#     siguiente_fecha = actual

#     return rangos, siguiente_fecha


# # Ejemplo de uso:
# hoy = datetime.date.today()
# rangos, siguiente = generar_rangos_14_dias(hoy, 27)

# for i, (inicio, fin) in enumerate(rangos, start=1):
#     print(f"Rango {i}: {inicio} -> {fin}")

# print(f"Fecha siguiente: {siguiente}")


import requests
from bs4 import BeautifulSoup

session = requests.Session()

# Headers base
BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "es-ES,es;q=0.9",
    "Connection": "keep-alive",
}

def print_cookies(msg):
    print(f"\n=== {msg} ===")
    for k, v in session.cookies.get_dict().items():
        print(f"{k} = {v}")

session.cookies.update({
    "__insp_wid": "554316038",
    "__insp_nv": "true",
    "__insp_targlpu": "aHR0cHM6Ly9leHRyYW5ldC5hdmFpbHByby5jb20vRGV2aWNlL1Vua25vd24%3D",
    "__insp_targlpt": "RC1FREdFIC0gwr9TZSBlc3TDoSBjb25lY3RhbmRvIGRlc2RlIHVuIGRpc3Bvc2l0aXZvIG51ZXZvPw==",
    "__insp_norec_sess": "true",
    "__insp_slim": "1756829720681",
    "_hjSessionUser_60265": "eyJpZCI6ImYxNzcwMTI3LTg3ZWQtNThkYy1iMDUxLWE5Y2U5NTE1NjVmZiIsImNyZWF0ZWQiOjE3NTY4Mjk3MzEyMzgsImV4aXN0aW5nIjp0cnVlfQ==",
    "_gid": "GA1.2.2074678862.1757635960",
    "ASP.NET_SessionId": "0nx1s0iktgllqim12xrqddzh",
    "_clsk": "1qdtvct%5E1757778635128%5E1%5E0%5Eq.clarity.ms%2Fcollect",
    "_ga": "GA1.1.1472735258.1756563538",
    "_clck": "1k68npn%5E2%5Efza%5E0%5E2082",
    "_ga_CQNZ2C0Y74": "GS2.1.s1757778633$o2$g1$t1757778635$j58$l0$h0",
    ".AVPAUTH": "9e11570bad6cf20931ded8bd040dfe05d438808783c1301dadda6afad111b86cd770c398bb55730c9592da1a5dfa841c937d02b42097217ee791e895e3741dabdad29be75a4f2c3f54f7d5e201c195e7f5e2511b8069c0b56ac518ffda93e63a68f6973d7bc643588e82dae5023aa35d42e24b65a44d0c4004238be1da8e095e",
    ".DEVICEID": "DzsFvvJYKoVyIaW2e+0fnZcthMap8hg4g/HO62QngboUvZVhWUzfUQshYmFDbsdm/KJJ7Jn6aeAJn2u80QCxqSuwjdEEXgjMUtmY/GHozAHoRSGpe3S1tyBGSJ9R5MrpLiLDPhcjt/f2tlZrV1lXvpB/9yY6hP2S/I9Kvuj/0L8="
})

def get_verification_token(html):
    """Extrae __RequestVerificationToken del formulario de login."""
    soup = BeautifulSoup(html, "html.parser")
    token_input = soup.find("input", {"name": "__RequestVerificationToken"})
    return token_input["value"] if token_input else None

def update_cookies(response):
    """Actualiza la sesión con las cookies devueltas en la respuesta."""
    for cookie in response.cookies:
        session.cookies.set_cookie(cookie)

headers_post = BASE_HEADERS.copy()
headers_post.update({
    "user-agent": "Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36",
    "origin": "https://login.availpro.com",
    "referer": "https://login.availpro.com/es?ReturnUrl=%2f",
    "content-type": "application/x-www-form-urlencoded",
})

resp_login_page = session.get("https://login.availpro.com/es?ReturnUrl=%2f", headers=headers_post)
update_cookies(resp_login_page)
token = get_verification_token(resp_login_page.text)
print(token)
payload = {
    "UserName": "rec1@hotelsuitesferiademadrid.com",
    "Password": "Megatron2024*",
    "IsQueryLogin": "False",
    "__RequestVerificationToken": token
}
resp1 = session.post(
    "https://login.availpro.com/es?ReturnUrl=%2f",
    data=payload,
    headers=headers_post,
    allow_redirects=False,  # seguimos manualmente para ver el token
)
update_cookies(resp1)
print(f"Paso 1 → Status: {resp1.status_code} Location: {resp1.headers.get('Location')}")
print_cookies("Cookies después del POST")

# Paso 2: GET al Location con el token
token_url = resp1.headers.get("Location")
headers_get = BASE_HEADERS.copy()
headers_get["Referer"] = "https://login.availpro.com/"

resp2 = session.get(token_url, headers=headers_get, allow_redirects=False)
print(f"Paso 2 → Status: {resp2.status_code} Location: {resp2.headers.get('Location')}")
print_cookies("Cookies después del GET con token")

# Paso 3: GET a "/" (redirige a /Home...)
resp3 = session.get("https://extranet.availpro.com/", headers=headers_get, allow_redirects=False)
print(f"Paso 3 → Status: {resp3.status_code} Location: {resp3.headers.get('Location')}")
print_cookies("Cookies después del GET /")

# Paso 4: GET a /Home?language=es-ES...
home_url = resp3.headers.get("Location")
resp4 = session.get(f"https://extranet.availpro.com{home_url}", headers=headers_get)
print(f"Paso 4 → Status: {resp4.status_code}")
print_cookies("Cookies finales (logueado)")

# Si quieres ver el HTML de la página logueada:
print("\nPrimeros 500 caracteres del HTML final:\n", resp4.text[:500])