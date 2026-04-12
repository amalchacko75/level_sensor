from django.urls import path
from .views import save_water_level, latest_water_level

urlpatterns = [
    path('water/', save_water_level),
    path('water/latest/', latest_water_level),
]