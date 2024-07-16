from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from .views import *

urlpatterns = [
    path('get/booking', get_booking, name="get_booking"),
    path("sign-in", login, name="sign-in"),
    path("log-out", logout, name="log-out"),
    path("", index, name="index"),
    path("booking", booking_view, name="booking"),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)