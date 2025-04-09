from django.db import models
from django.contrib.auth.models import User
from .now_date import now
# Create your models here.

class Booking(models.Model):
    start = models.CharField(max_length=20)
    title = models.CharField(max_length=512)
    link = models.CharField(max_length=3000)
    address = models.CharField(max_length=512)
    distance = models.CharField(max_length=512)
    description = models.CharField(max_length=1024)
    img = models.CharField(max_length=3000)
    updated = models.DateTimeField()
    created = models.DateTimeField()
    
    def __str__(self) -> str:
        return str(self.pk)+" | "+str(self.title)+" | Start: "+str(self.start)

class Complement(models.Model):
    total_search = models.IntegerField(default=0)
    occupancy = models.IntegerField(default=4)
    start = models.CharField(max_length=20)
    date_from = models.CharField(max_length=30)
    date_to = models.CharField(max_length=30)
    updated = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return str(self.total_search)+" | Occupancy: "+str(self.occupancy)+" | Start: "+str(self.start)+" | From: "+str(self.date_from)+" | To: "+str(self.date_to)    

class AvailableBooking(models.Model):
    date_from = models.CharField(max_length=30)
    date_to = models.CharField(max_length=30)
    active = models.BooleanField(default=True)
    price = models.CharField(max_length=30)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    complement = models.ForeignKey(Complement, on_delete=models.CASCADE, null=True, blank=True)
    position = models.IntegerField(default=0)
    total_search = models.IntegerField(default=0)
    occupancy = models.IntegerField(default=4)
    start = models.CharField(max_length=20)
    updated = models.DateTimeField()
    created = models.DateTimeField()

    def __str__(self) -> str:
        return str(self.booking)+" | "+str(self.date_from)+" - "+str(self.date_to)+" | Price: "+str(self.price)+" | Occupancy: "+str(self.occupancy)+" | Start: "+str(self.start)

class AvailSuitesFeria(models.Model):
    date_avail = models.CharField(max_length=50)

    def __str__(self) -> str:
        return str(self.date_avail)

class CantAvailSuitesFeria(models.Model):
    type_avail = models.CharField(max_length=5)
    avail = models.IntegerField(default=0)
    avail_suites_feria = models.ForeignKey(AvailSuitesFeria, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.type_avail)+" | "+str(self.avail_suites_feria)+" | "+ str(self.avail)

class AvailWithDate(models.Model):
    date_from = models.CharField(max_length=30)
    avail = models.CharField(max_length=50)
    updated = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return str(self.avail)+" | "+str(self.date_from)

class Price(models.Model):
    date_from = models.CharField(max_length=30)
    OCCUPANCYS = (
        (1, "1 Personas"),
        (2, "2 Personas"),
        (3, "3 Personas"),
        (4, "4 Personas"),
        (5, "5 Personas"),
        (6, "6 Personas")
    )
    occupancy = models.IntegerField(choices=OCCUPANCYS, default=2)
    price = models.CharField(max_length=50)
    updated = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(null=True, blank=True)
    plataform_sync = models.BooleanField(default=False)

    def __str__(self) -> str:
        return str(self.price)+" - "+str(self.occupancy)

class MessageByDay(models.Model):
    date_from = models.CharField(max_length=30)
    OCCUPANCYS = (
        (2, "2 Personas"),
        (3, "3 Personas"),
        (5, "5 Personas")
    )
    occupancy = models.IntegerField(choices=OCCUPANCYS, default=2)
    text = models.CharField(max_length=512)
    updated = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return str(self.text)

class EventByDay(models.Model):
    date_from = models.CharField(max_length=30)
    OCCUPANCYS = (
        (2, "2 Personas"),
        (3, "3 Personas"),
        (5, "5 Personas")
    )
    occupancy = models.IntegerField(choices=OCCUPANCYS, default=2)
    text = models.CharField(max_length=512)
    updated = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return str(self.text)

class TemporadaByDay(models.Model):
    date_from = models.CharField(max_length=30)
    COLORS = (
        ("bg-danger", "bg-danger"),
        ("bg-danger", "bg-danger"),
        ("bg-warning", "bg-warning"),
        ("bg-success", "bg-success"),
        ("bg-info", "bg-info"),
        ("bg-dark", "bg-dark"),
    )
    TEXT_COLORS = (
        ("text-success", "text-success"),
        ("text-warning", "text-warning"),
        ("text-info", "text-info"),
        ("text-secondary", "text-secondary"),
        ("text-dark", "text-dark"),
        ("text-white", "text-white"),
        ("text-black", "text-black"),
        ("text-primary", "text-primary"),
    )
    bg_color = models.TextField(choices=COLORS, default="bg-success")
    text_color = models.TextField(choices=TEXT_COLORS, default="text-success")
    number = models.CharField(max_length=3)
    updated = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return str(self.number)+" - "+str(self.date_from)

class CopyPriceWithDay(models.Model):
    """
        related to object with.
        date_from
        position
        occupancy
        start
    """
    price = models.CharField(max_length=30)
    created = models.DateField(null=True, blank=True)
    avail_booking = models.ForeignKey(AvailableBooking, on_delete=models.CASCADE)

    def __str__(self):
        return self.price

class CopyComplementWithDay(models.Model):
    total_search = models.CharField(max_length=30)
    created = models.DateField(null=True, blank=True)
    complement = models.ForeignKey(Complement, on_delete=models.CASCADE)

    def __str__(self):
        return self.total_search

# agregar ocupacion de cada nombre de precio.
class PriceWithNameHotel(models.Model):
    start = models.CharField(max_length=20)
    title = models.CharField(max_length=512)
    link = models.CharField(max_length=3000)
    address = models.CharField(max_length=512)
    distance = models.CharField(max_length=512)
    description = models.CharField(max_length=1024)
    img = models.CharField(max_length=3000)
    updated = models.DateTimeField()
    created = models.DateTimeField()
    date_from = models.CharField(max_length=30)
    date_to = models.CharField(max_length=30)
    price = models.CharField(max_length=30)
    occupancy = models.IntegerField(default=2)

    def __str__(self) -> str:
        return str(self.id)+" | "+str(self.title)+" | Start: "+str(self.start)+" | "+str(self.date_from)+" | Occupancy: "+str(self.occupancy)
    
class CopyPriceWithNameFromDay(models.Model):
    price = models.CharField(max_length=30)
    created = models.DateField(null=True, blank=True)
    avail = models.ForeignKey(PriceWithNameHotel, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.price)+" | "+str(self.avail)
    
class CopyAvailWithDaySF(models.Model):
    type_avail = models.CharField(max_length=5)
    avail_1 = models.IntegerField(default=0)
    avail_2 = models.IntegerField(default=0)
    avail_3 = models.IntegerField(default=0)
    avail_4 = models.IntegerField(default=0)
    created = models.DateField(null=True, blank=True)
    avail_suites_feria = models.ForeignKey(AvailSuitesFeria, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.avail_suites_feria)+" | "+ str(self.avail_1)+" | "+ str(self.avail_2)+" | "+ str(self.avail_4)
    
class CredentialPlataform(models.Model):
    TEXT_PLATAFORM = (
        ("suitesferia", "suitesferia"),
        ("roomprice", "roomprice"),
    )
    plataform_option = models.TextField(choices=TEXT_PLATAFORM, default="suitesferia")
    username = models.CharField(max_length=256)
    password = models.CharField(max_length=256)
    updated = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return str(self.plataform_option)
    
class CronActive(models.Model):
    active = models.BooleanField(default=False)
    current_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.active)+" | "+str(self.current_date)
    
class BotLog(models.Model):
    SUITESFERIA = "suitesferia"
    ROOMPRICE = "roomprice"
    BOOKING = "booking"
    HISTORY = "history"
    TEXT_PLATAFORM = (
        (SUITESFERIA, SUITESFERIA),
        (ROOMPRICE, ROOMPRICE),
        (BOOKING, BOOKING),
        (HISTORY, HISTORY),
    )
    plataform_option = models.TextField(choices=TEXT_PLATAFORM, default=BOOKING)
    description = models.TextField()
    updated = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.description)

class TaskLock(models.Model):
    name = models.CharField(max_length=255, unique=True)
    acquired_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return now() > self.expires_at

class TaskExecute(models.Model):
    hour = models.IntegerField(default=22)
    minute = models.IntegerField(default=0)
    second = models.IntegerField(default=0)
    time_sleep = models.FloatField(default=0.5)
    time_execute = models.FloatField(default=90)

    def __str__(self):
        return str(self.hour)+" "+str(self.minute)+" "+str(self.second)

class ProcessActive(models.Model):
    occupancy = models.CharField(max_length=30, default=2)
    start = models.CharField(max_length=30, default=4)
    position = models.JSONField(default={})

    TYPE_PROCES = (
        (1, "City"),
        (2, "Name")
    )
    type_proces = models.IntegerField(choices=TYPE_PROCES, default=1)

    def __str__(self) -> str:
        return "Occupancy: "+str(self.occupancy)+" | Start: "+str(self.start)+" | Positions: "+str(self.position)+" | tipo: "+str(self.type_proces)

class GeneralSearch(models.Model):
    url = models.TextField(default="https://www.booking.com/searchresults.es.html?")
    city_and_country = models.TextField(default="Madrid, España")
    time_sleep_minutes = models.IntegerField(default=1)
    TYPE_SEARCH = (
        (1, "City"),
        (2, "Name")
    )
    type_search = models.IntegerField(choices=TYPE_SEARCH, default=1)
    proces_active = models.ManyToManyField(ProcessActive, null=True, blank=True)

    def __str__(self) -> str:
        return str(self.url)+" | "+str(self.city_and_country)+" | "+str(self.time_sleep_minutes)+" | "+str(self.type_search)

class BotSetting(models.Model): # Configurations bots default and automatics.
    BOT_AUTO = "bot_auto"
    BOT_DEFAULT = "bot_default"
    TEXT_NAME = (
        (BOT_AUTO, BOT_AUTO),
        (BOT_DEFAULT, BOT_DEFAULT),
    )
    name = models.TextField(choices=TEXT_NAME, default=BOT_DEFAULT)
    number_from = models.IntegerField(default=1)
    number_end = models.IntegerField(default=1)
    def __str__(self):
        return "Nombre: "+str(self.name)
    
class BotAutomatization(models.Model):
    active = models.BooleanField(default=False)
    currenct = models.BooleanField(default=False)
    automatic = models.BooleanField(default=False)
    bot_auto = models.ForeignKey(BotSetting, related_name="bot_auto", on_delete=models.SET_NULL, null=True) # bot automatizado en horarios
    bot_default = models.ForeignKey(BotSetting, related_name="bot_default", on_delete=models.SET_NULL, null=True) # bot default en fecha configurada.

    def __str__(self):
        bot = getattr(self, "bot_default", "N/A")
        if getattr(self, "automatic", False):
            bot = getattr(self, "bot_auto", "N/A")
        return f"{self.automatic} | {bot}"

class BotRange(models.Model):
    number = models.IntegerField(default=1)
    days = models.IntegerField(default=30)
    date_from = models.DateField(null=True, blank=True)
    date_end = models.DateField(null=True, blank=True)
    bot_setting = models.ForeignKey(BotSetting, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return str(self.number)+" | "+str(self.days)+" | Desde: "+str(self.date_from)+" | Hasta: "+str(self.date_end)+" | "+str(self.bot_setting)

def generate_log(description, option):
    BotLog.objects.create(
        plataform_option = option,
        description = description,
        updated = now(),
        created = now()
    )
