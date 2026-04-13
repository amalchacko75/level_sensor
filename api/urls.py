from django.urls import path
from .views import (
    daily_usage, events_list, 
    hourly_usage, run_processing, 
    save_water_level
)

urlpatterns = [
    path('water/', save_water_level),
    path('hourly/', hourly_usage),
    path('daily/', daily_usage),
    path('events/', events_list),
    path('process/', run_processing),
]