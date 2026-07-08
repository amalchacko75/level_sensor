from django.urls import path
from .views import (
    current_level, daily_usage, dashboard, events_list, 
    hourly_usage, run_processing, save_device_token, 
    save_water_level, test_notification
)

urlpatterns = [
    path('water/', save_water_level),
    path('hourly/', hourly_usage),
    path('daily/', daily_usage),
    path('events/', events_list),
    path('process/', run_processing),
    path('dashboard/', dashboard),
    path('current-level/', current_level),
    path("save-token/", save_device_token),
    path("test-notification/", test_notification),
]