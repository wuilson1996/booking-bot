from datetime import datetime, timedelta
ttl_minutes = 0.5
current_time = datetime.now()
expires = current_time + timedelta(minutes=ttl_minutes)
print(expires)