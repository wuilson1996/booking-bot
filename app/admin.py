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

class AvailWithDateAdmin(admin.ModelAdmin):
    search_fields = ["id"]

class CantAvailSuitesFeriaAdmin(admin.ModelAdmin):
    search_fields = ["id", "avail_suites_feria__date_avail", "type_avail", "avail"]

class PriceAdmin(admin.ModelAdmin):
    search_fields = ["id", "price", "date_from"]

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

class CopyPriceWithNameFromDayAdmin(admin.ModelAdmin):
    search_fields = ["id"]

class CopyAvailWithDaySFAdmin(admin.ModelAdmin):
    search_fields = ["id"]

class CopyComplementWithDayAdmin(admin.ModelAdmin):
    search_fields = ["id"]

class CredentialPlataformAdmin(admin.ModelAdmin):
    search_fields = ["id"]

class CronActiveAdmin(admin.ModelAdmin):
    search_fields = ["id"]

class BotLogAdmin(admin.ModelAdmin):
    search_fields = ["id", "description", "plataform_option", "created"]

admin.site.register(Booking, BookingAdmin)
admin.site.register(AvailableBooking, AvailableBookingAdmin)
admin.site.register(ProcessActive, ProcessActiveAdmin)
admin.site.register(GeneralSearch, GeneralSearchAdmin)
admin.site.register(AvailSuitesFeria, AvailSuitesFeriaAdmin)
admin.site.register(AvailWithDate, AvailWithDateAdmin)
admin.site.register(CantAvailSuitesFeria, CantAvailSuitesFeriaAdmin)
admin.site.register(Price, PriceAdmin)
admin.site.register(MessageByDay, MessageByDayAdmin)
admin.site.register(EventByDay, EventByDayAdmin)
admin.site.register(TemporadaByDay, TemporadaByDayAdmin)
admin.site.register(Complement, ComplementAdmin)
admin.site.register(CopyPriceWithDay, CopyPriceWithDayAdmin)
admin.site.register(PriceWithNameHotel, PriceWithNameHotelAdmin)
admin.site.register(CopyPriceWithNameFromDay, CopyPriceWithNameFromDayAdmin)
admin.site.register(CopyAvailWithDaySF, CopyAvailWithDaySFAdmin)
admin.site.register(CopyComplementWithDay, CopyComplementWithDayAdmin)
admin.site.register(CredentialPlataform, CredentialPlataformAdmin)
admin.site.register(CronActive, CronActiveAdmin)
admin.site.register(BotLog, BotLogAdmin)
admin.site.register(TaskLock)
admin.site.register(BotSetting)
admin.site.register(BotAutomatization)
admin.site.register(BotRange)
admin.site.register(TaskExecute)
admin.site.register(ScreenshotLog)
admin.site.register(HourRange)
admin.site.register(Day)
admin.site.register(MessageName)
admin.site.register(EmailSMTP)
admin.site.register(EmailSend)
admin.site.register(MessageEmail)