from django.db import models
from django.contrib.auth.models import User
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
        return str(self.id)+" | "+str(self.title)+" | Start: "+str(self.start)

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
    
class ProcessActive(models.Model):
    date_end = models.DateField()
    occupancy = models.CharField(max_length=30, default=2)
    start = models.CharField(max_length=30, default=4)
    active = models.BooleanField(default=False)
    position = models.JSONField(default={})
    currenct = models.BooleanField(default=False)

    def __str__(self) -> str:
        return str(self.date_end)+" | Occupancy: "+str(self.occupancy)+" | Start: "+str(self.start)+" | Positions: "+str(self.position)+" | "+str(self.active)

class GeneralSearch(models.Model):
    url = models.TextField(default="https://www.booking.com")
    city_and_country = models.TextField(default="Madrid, Comunidad de Madrid, España")
    time_sleep_minutes = models.IntegerField(default=1)

    def __str__(self) -> str:
        return str(self.url)+" - "+str(self.city_and_country)+" - "+str(self.time_sleep_minutes)

class AvailSuitesFeria(models.Model):
    date_avail = models.CharField(max_length=50)

    def __str__(self) -> str:
        return str(self.date_avail)

class CantAvailSuitesFeria(models.Model):
    type_avail = models.CharField(max_length=5)
    avail = models.IntegerField(default=0)
    avail_suites_feria = models.ForeignKey(AvailSuitesFeria, on_delete=models.CASCADE)

class AvailWithDate(models.Model):
    date_from = models.CharField(max_length=30)
    avail = models.CharField(max_length=50)
    updated = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return str(self.avail)

class Price(models.Model):
    date_from = models.CharField(max_length=30)
    OCCUPANCYS = (
        (2, "2 Personas"),
        (3, "3 Personas"),
        (5, "5 Personas")
    )
    occupancy = models.IntegerField(choices=OCCUPANCYS, default=2)
    price = models.CharField(max_length=50)
    updated = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return str(self.price)

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
        ("bg-warning", "bg-warning"),
        ("bg-success", "bg-success"),
        ("bg-secondary", "bg-secondary"),
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