from django.db import models


class WaterLevel(models.Model):
    percentage = models.FloatField()
    distance = models.FloatField(null=True, blank=True)
    wifi_ssid = models.CharField(max_length=100, null=True, blank=True)
    signal_strength = models.IntegerField(null=True, blank=True)
    battery_voltage = models.FloatField(null=True, blank=True)
    battery_percentage = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class HourlyWaterConsumption(models.Model):
    date = models.DateField()
    hour = models.IntegerField()

    start_level = models.FloatField()
    end_level = models.FloatField()

    usage_percentage = models.FloatField()
    usage_liters = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.date} - {self.hour}h"


class WaterEvent(models.Model):
    EVENT_TYPE_CHOICES = (
        ('pump_on', 'Pump ON'),
        ('leak', 'Leak'),
        ('empty', 'Empty'),  # ✅ added
    )

    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)

    start_level = models.FloatField()
    end_level = models.FloatField()

    change_percentage = models.FloatField()
    change_liters = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event_type', 'start_time')  # ✅ prevents duplicates

    def __str__(self):
        return f"{self.event_type} at {self.start_time}"


class DeviceToken(models.Model):
    token = models.TextField(unique=True)

    device_type = models.CharField(
        max_length=20,
        default="web"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.device_type
    
class NotificationSettings(models.Model):

    STATUS = [
        (1, "Every 1 Minutes"),
        (15, "Every 15 Minutes"),
        (30, "Every 30 Minutes"),
        (60, "Every Hour"),
        (120, "Every 2 Hours"),
        (360, "Every 6 Hours"),
        (720, "Every 12 Hours"),
        (1440, "Daily"),
    ]

    enabled = models.BooleanField(default=True)

    report_interval = models.IntegerField(
        choices=STATUS,
        default=60
    )

    include_water_level = models.BooleanField(default=True)

    include_daily_usage = models.BooleanField(default=True)

    include_battery = models.BooleanField(default=True)

    include_voltage = models.BooleanField(default=True)

    include_wifi = models.BooleanField(default=False)

    tank_full_notification = models.BooleanField(default=True)

    tank_full_percentage = models.IntegerField(default=90)

    tank_empty_notification = models.BooleanField(default=True)

    tank_empty_percentage = models.IntegerField(default=35)

    battery_low_notification = models.BooleanField(default=True)

    battery_low_percentage = models.IntegerField(default=40)

    wifi_offline_enabled = models.BooleanField(default=True)

    last_sent = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return "Notification Settings"