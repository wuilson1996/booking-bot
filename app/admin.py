from django.contrib import admin
from .models import *
# Register your models here.

class BookingAdmin(admin.ModelAdmin):
    search_fields = ["id", "title",  "start"]

class AvailableBookingAdmin(admin.ModelAdmin):
    search_fields = ["id", "date_from", "date_to", "active"]

class ProcessActiveAdmin(admin.ModelAdmin):
    search_fields = ["id", "date_end", "occupancy", "start"]

admin.site.register(Booking, BookingAdmin)
admin.site.register(AvailableBooking, AvailableBookingAdmin)
admin.site.register(ProcessActive, ProcessActiveAdmin)