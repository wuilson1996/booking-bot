import datetime
from django.utils.timezone import now as nw

def now():
    return nw() + datetime.timedelta(hours=1)