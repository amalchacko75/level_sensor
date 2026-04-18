from django.db import models


class WaterLevel(models.Model):
    percentage = models.FloatField()
    distance = models.FloatField(null=True, blank=True)
    wifi_ssid = models.CharField(max_length=100, null=True, blank=True)
    signal_strength = models.IntegerField(null=True, blank=True)
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