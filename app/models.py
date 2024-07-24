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
    occupancy = models.IntegerField(default=4)
    updated = models.DateTimeField()
    created = models.DateTimeField()

    
    def __str__(self) -> str:
        return str(self.id)+" | "+str(self.title)+" | Start: "+str(self.start)+" | Occupancy: "+str(self.occupancy)
    
class AvailableBooking(models.Model):
    date_from = models.CharField(max_length=30)
    date_to = models.CharField(max_length=30)
    active = models.BooleanField(default=True)
    price = models.CharField(max_length=30)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    position = models.IntegerField(default=0)
    total_search = models.IntegerField(default=0)
    updated = models.DateTimeField()
    created = models.DateTimeField()

    def __str__(self) -> str:
        return str(self.booking)+" | "+str(self.date_from)+" - "+str(self.date_to)+" | Price: "+str(self.price)
    
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