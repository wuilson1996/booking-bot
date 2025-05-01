#import datetime
#from django.utils.timezone import now as nw
from datetime import timedelta, datetime
from django.utils import timezone

def now():
    return timezone.localtime((datetime.now() + timedelta(hours=0)).astimezone())

def parse_created_to_localtime(created_str):
    naive_datetime = datetime.strptime(created_str, "%Y-%m-%d %H:%M:%S")  # Formato esperado: "2025-05-01 12:34:56"
    return timezone.make_aware(naive_datetime)