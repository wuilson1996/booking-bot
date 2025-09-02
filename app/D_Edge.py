from bs4 import BeautifulSoup
import requests
import json

class DEdge:
    URL = "https://extranet.availpro.com/Planning/Edition/Save"
    URL_GET = "https://extranet.availpro.com/Planning/Edition/Index/DATE/Room0/Rate585370"
    ROOM_TYPES = {
        "2": "113516",
        "0": "113522",
        "1": "113517",
        "3": "113705",
        "4": "113518",
        "5": "113519",
        "6": "113703"
    }
    RATE_ID = "585370"
    @classmethod
    def get_cookies(cls):
        return {
            "ASP.NET_SessionId": "eploevqhtyixzqblrtx05pmw",
            "_clck": "1lkhd7c^2^fyz^0^2068",
            "__insp_wid": "554316038",
            "__insp_nv": "true",
            "__insp_targlpu": "aHR0cHM6Ly9leHRyYW5ldC5hdmFpbHByby5jb20vRGV2aWNlL1Vua25vd24=",
            "__insp_targlpt": "RC1FREdFIC0gwr9TZSBlc3TDoSBjb25lY3RhbmRvIGRlc2RlIHVuIGRpc3Bvc2l0aXZvIG51ZXZvPw==",
            "__insp_norec_sess": "true",
            "__insp_slim": "1756829720681",
            "_gid": "GA1.2.1698557967.1756829731",
            "_hjSession_60265": "eyJpZCI6ImIzNTA2OTRlLTliOWUtNGExOS04MTNlLTQ5ZjIwMWZkZGE3ZiIsImMiOjE3NTY4Mjk3MzEyMzksInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjoxLCJzcCI6MH0=",
            "_hjSessionUser_60265": "eyJpZCI6ImYxNzcwMTI3LTg3ZWQtNThkYy1iMDUxLWE5Y2U5NTE1NjVmZiIsImNyZWF0ZWQiOjE3NTY4Mjk3MzEyMzgsImV4aXN0aW5nIjp0cnVlfQ==",
            "_ga": "GA1.1.1472735258.1756563538",
            "_ga_CQNZ2C0Y74": "GS2.1.s1756831462$o1$g0$t1756831463$j59$l0$h0",
            ".AVPAUTH": "5545217a44a4e4b87e041055bd1cea6ac0582421e4139e8464b8c65615e8cd45d1d08e2d44d4bc61aa109d016783fe46da139258dd290e4241f38702b32718ff628bd77ced95aadc65aa0f37b734f91a345fda118ee90b2f6815c21545ab988a06ee6119e7f657eff7d29b4e54ae35cac47a4794850db807b000a88556635d96",
            ".DEVICEID": "bHc44kG/p1emka9OKXyYL1FIxEbUVwT15COKe5ooUiul6IS7sdchkwDuQHAxQfPI/xCJ9n4pM56Cz3YVG342/wshbT1Q6hK3DeRokWRgeWySadBRnBn2sPOciItVA+8pvlXoGUTzCOJ4ZPbYEel+mxOa0wKFHlmNmYLvjZHVGZM=",
            "_clsk": "1wo2epm^1756834089179^1^1^q.clarity.ms/collect",
            "_gat": "1"
        }
    
    @classmethod
    def get_type(cls, room_type):
        return cls.ROOM_TYPES.get(room_type, "113516")

    @classmethod
    def get_headers(cls, _date):
        return {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "es-ES,es;q=0.9",
            "connection": "keep-alive",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "host": "extranet.availpro.com",
            "origin": "https://extranet.availpro.com",
            "referer": "https://extranet.availpro.com/Planning/Edition/Index/"+_date+"/Room0/Rate"+cls.RATE_ID,
            "sec-ch-ua": "\"Not;A=Brand\";v=\"99\", \"Google Chrome\";v=\"139\", \"Chromium\";v=\"139\"",
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": "\"Android\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
            "x-requested-with": "XMLHttpRequest"
        }
    
    @classmethod
    def get_price_by_date(cls, url):
        import requests
        from bs4 import BeautifulSoup

        response = requests.get(url, headers=cls.get_headers(), cookies=cls.get_cookies())
        soup = BeautifulSoup(response.text, 'html.parser')
        
        price_element = soup.find('span', class_='price')
        if price_element:
            return price_element.text.strip()
        return None

    @classmethod
    def set_price_by_date(cls, _date, prices):
        changes = cls.generate_changes(prices, _date)
        headers = cls.get_headers(_date)
        cookies = cls.get_cookies()
        # Construir primero el payload como dict
        planning_changes = {
            "startDate": _date,
            "Room": "0",
            "Rate": cls.RATE_ID,
            "Items": 12,
            "changes": changes
        }
        data = {"planningChanges": json.dumps(planning_changes)}
        response = requests.post(cls.URL, headers=headers, cookies=cookies, data=data)
        return response

    @classmethod
    def set_price_by_date_and_type(cls, _date, prev_price, next_price, room_type):
        room_id = cls.get_type(room_type)
        headers = cls.get_headers()
        cookies = cls.get_cookies()
        # Construir primero el payload como dict
        planning_changes = {
            "startDate": _date,
            "Room": "0",
            "Rate": cls.RATE_ID,
            "Items": 12,
            "changes": [
                {"Day": 0, "ArticleId": "0", "RoomId": int(room_id), "LineType": "RatePrice", "RateId": int(cls.RATE_ID), "PropertyId": 0, "OriginValue": prev_price, "NewValue": next_price, "NewOverridingValue": next_price, "Target": "Price"}
            ]
        }
        data = {"planningChanges": json.dumps(planning_changes)}
        response = requests.post(cls.URL, headers=headers, cookies=cookies, data=data)
        return response
    
    @classmethod
    def generate_changes(cls, prices, _date):
        response = cls.get_prev_price(_date)
        prev_prices = cls.get_prev_price_source(response.text)
        changes = []
        for room_type, price in prices.items():
            room_id = cls.get_type(room_type)
            changes.append(
                {
                    "Day": 0, 
                    "ArticleId": "0", 
                    "RoomId": int(room_id), 
                    "LineType": "RatePrice", 
                    "RateId": int(cls.RATE_ID), 
                    "PropertyId": 0, 
                    "OriginValue": prev_prices[room_type], 
                    "NewValue": price["next_price"], 
                    "NewOverridingValue": price["next_price"], 
                    "Target": "Price"
                }
            )
        return changes
    
    @classmethod
    def get_prev_price(cls, _date):
        headers = cls.get_headers(_date)
        cookies = cls.get_cookies()
        response = requests.get(cls.URL_GET.replace("DATE", _date), headers=headers, cookies=cookies)
        return response
    
    @classmethod
    def get_prev_price_source(cls, content):
        soup = BeautifulSoup(content, "html.parser")

        # Buscar todos los <td> con los atributos especificados
        tds = soup.find_all("td", {
            "day": "0",
            "request": "False"
        }, originvalue=True)
        
        result = {}

        # Llenar el diccionario solo si hay valores
        cont = 1
        aux = 0
        for td in tds:
            if cont % 2 == 0:
                origin_value = td["originvalue"]
                keys = list(cls.ROOM_TYPES.keys())
                result[keys[aux]] = origin_value
                aux += 1
            cont += 1
        return result
    
    @classmethod
    def write_html(cls, content, filename):
        """Guardar el contenido completo en un archivo HTML."""
        with open(filename, "w", encoding="utf-8") as file:
            file.write(content)

if __name__ == "__main__":
    d_edge = DEdge()
    #d_edge.set_price_by_date_and_type("2026-02-01", "95", "94", "0")

    # test generate changes
    #prices = {"0": {"prev_price":"94", "next_price":"95"}}
    #changes = d_edge.generate_changes(prices)
    #print(changes)
    response = d_edge.get_prev_price("2026-02-01")
    prices = d_edge.get_prev_price_source(response.text)
    print(prices)
    #d_edge.write_html(response.text, "test.html")
    