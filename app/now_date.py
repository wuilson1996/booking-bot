#import datetime
#from django.utils.timezone import now as nw
from datetime import timedelta, datetime
from django.utils.timezone import localtime

def now():
    return localtime((datetime.now() + timedelta(hours=0)).astimezone())