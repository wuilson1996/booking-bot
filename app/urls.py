from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from .views import *

urlpatterns = [
    path('get/booking', get_booking, name="get_booking"),
    path('finish/get/booking', finish_get_booking, name="finish_get_booking"),
    path("sign-in", login, name="sign-in"),
    path("log-out", logout, name="log-out"),
    path("", index, name="index"),
    path("booking", booking_view, name="booking"),
    path('save/price', save_price, name="save_price"),
    path('save/message', save_message, name="save_message"),
    path('save/temp', save_temp, name="save_temp"),
    path('save/event', save_event, name="save_event"),
    path("check/booking/process", check_booking_process, name="check_booking_process"),
    path("save/avail/with/date", save_avail_with_date, name="save_avail_with_date"),
    path('upgrade/fee', upgrade_fee, name="upgrade_fee"),
    path('reception', reception, name="reception"),
    path('reception/price', reception_price, name="reception_price"),
    path('price/export/', export_price_from_excel, name="price_export"),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)