from django.db import models

class WaterLevel(models.Model):
    percentage = models.FloatField()
    distance = models.FloatField(null=True, blank=True)
    wifi_ssid = models.CharField(max_length=100, null=True, blank=True)
    signal_strength = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.percentage}%"