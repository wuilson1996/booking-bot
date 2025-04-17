from datetime import datetime, timedelta
# ttl_minutes = 0.5
# current_time = datetime.now()
# expires = current_time + timedelta(minutes=ttl_minutes)
# print(expires)
from datetime import timedelta, datetime
#from django.utils.timezone import localtime

def now():
    return (datetime.now() + timedelta(hours=7)).astimezone()
now = now().time()
print(now)