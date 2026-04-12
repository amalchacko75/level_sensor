from django.urls import path
from .views import daily_usage, events_list, hourly_usage, save_water_level

urlpatterns = [
    path('water/', save_water_level),
    path('hourly/', hourly_usage),
    path('daily/', daily_usage),
    path('events/', events_list),
]