#import datetime
#from django.utils.timezone import now as nw
from datetime import timedelta, datetime

def now():
    return (datetime.now() + timedelta(hours=0)).astimezone()