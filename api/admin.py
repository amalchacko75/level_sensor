from django.contrib import admin
from .models import WaterLevel, HourlyWaterConsumption, WaterEvent


@admin.register(WaterLevel)
class WaterLevelAdmin(admin.ModelAdmin):
    list_display = ('percentage', 'distance', 'wifi_ssid', 'signal_strength', 'created_at')


@admin.register(HourlyWaterConsumption)
class HourlyWaterConsumptionAdmin(admin.ModelAdmin):
    list_display = (
        'date',
        'hour',
        'start_level',
        'end_level',
        'usage_percentage',
        'usage_liters',
    )


@admin.register(WaterEvent)
class WaterEventAdmin(admin.ModelAdmin):
    list_display = (
        'event_type',
        'start_time',
        'start_level',
        'end_level',
        'change_percentage',
        'change_liters',
    )