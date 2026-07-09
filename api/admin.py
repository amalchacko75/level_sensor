from django.contrib import admin
from .models import DeviceToken, NotificationSettings, WaterLevel, HourlyWaterConsumption, WaterEvent


@admin.register(WaterLevel)
class WaterLevelAdmin(admin.ModelAdmin):
    list_display = (
        'percentage', 
        'distance', 
        'wifi_ssid', 
        'signal_strength', 
        'battery_voltage',
        'battery_percentage',
        'created_at'
    )


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


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "device_type",
        "short_token",
        "created_at",
    )

    search_fields = (
        "token",
        "device_type",
    )

    list_filter = (
        "device_type",
    )

    ordering = ("-created_at",)

    def short_token(self, obj):
        return f"{obj.token[:30]}..."

    short_token.short_description = "Token"

@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):

    list_display = (
        "enabled",
        "report_interval",
        "last_sent"
    )