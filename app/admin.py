from django.contrib import admin
from .models import *
# Register your models here.

class BookingAdmin(admin.ModelAdmin):
    search_fields = ["id", "title",  "start"]

class AvailableBookingAdmin(admin.ModelAdmin):
    search_fields = ["id", "date_from", "date_to", "active"]

class ProcessActiveAdmin(admin.ModelAdmin):
    search_fields = ["id", "date_end", "occupancy", "start"]

class GeneralSearchAdmin(admin.ModelAdmin):
    search_fields = ["id"]

class AvailSuitesFeriaAdmin(admin.ModelAdmin):
    search_fields = ["id"]

class CantAvailSuitesFeriaAdmin(admin.ModelAdmin):
    search_fields = ["id"]

class PriceAdmin(admin.ModelAdmin):
    search_fields = ["id"]

class MessageByDayAdmin(admin.ModelAdmin):
    search_fields = ["id"]

class EventByDayAdmin(admin.ModelAdmin):
    search_fields = ["id"]

class TemporadaByDayAdmin(admin.ModelAdmin):
    search_fields = ["id"]

class ComplementAdmin(admin.ModelAdmin):
    search_fields = ["id"]

class CopyPriceWithDayAdmin(admin.ModelAdmin):
    search_fields = ["id"]

class PriceWithNameHotelAdmin(admin.ModelAdmin):
    search_fields = ["id"]

admin.site.register(Booking, BookingAdmin)
admin.site.register(AvailableBooking, AvailableBookingAdmin)
admin.site.register(ProcessActive, ProcessActiveAdmin)
admin.site.register(GeneralSearch, GeneralSearchAdmin)
admin.site.register(AvailSuitesFeria, AvailSuitesFeriaAdmin)
admin.site.register(CantAvailSuitesFeria, CantAvailSuitesFeriaAdmin)
admin.site.register(Price, PriceAdmin)
admin.site.register(MessageByDay, MessageByDayAdmin)
admin.site.register(EventByDay, EventByDayAdmin)
admin.site.register(TemporadaByDay, TemporadaByDayAdmin)
admin.site.register(Complement, ComplementAdmin)
admin.site.register(CopyPriceWithDay, CopyPriceWithDayAdmin)
admin.site.register(PriceWithNameHotel, PriceWithNameHotelAdmin)