from datetime import timedelta
from django.utils import timezone
from .models import WaterLevel, HourlyWaterConsumption, WaterEvent

TANK_CAPACITY = 1750  # liters


# 🔥 EVENT DETECTION
def detect_events(records):
    prev = None

    for record in records:
        if prev is not None:
            diff = record.percentage - prev.percentage

            # 🚰 Pump ON
            if diff > 5:
                liters = (diff / 100) * TANK_CAPACITY

                WaterEvent.objects.create(
                    event_type='pump_on',
                    start_time=prev.created_at,
                    start_level=prev.percentage,
                    end_level=record.percentage,
                    change_percentage=diff,
                    change_liters=liters
                )

            # 💧 Leak
            elif diff < -5:
                drop = abs(diff)
                liters = (drop / 100) * TANK_CAPACITY

                WaterEvent.objects.create(
                    event_type='leak',
                    start_time=prev.created_at,
                    start_level=prev.percentage,
                    end_level=record.percentage,
                    change_percentage=drop,
                    change_liters=liters
                )

        prev = record


# 🔥 HOURLY CONSUMPTION
def process_hourly_consumption():
    now = timezone.now()
    one_hour_ago = now - timedelta(hours=1)

    records = list(
    WaterLevel.objects.filter(
        created_at__gte=one_hour_ago
    ).order_by("created_at")[:200]   # limit records
    )

    if len(records) < 2:
        return

    # 🔥 Detect pump/leak events
    detect_events(records)

    total_percentage_drop = 0
    prev = None

    for record in records:
        if prev is not None:
            diff = prev.percentage - record.percentage

            # ignore noise + refill
            if diff > 0.5:
                total_percentage_drop += diff

        prev = record

    if total_percentage_drop == 0:
        return

    usage_liters = (total_percentage_drop / 100) * TANK_CAPACITY

    HourlyWaterConsumption.objects.create(
        date=now.date(),
        hour=now.hour,
        start_level=records.first().percentage,
        end_level=records.last().percentage,
        usage_percentage=total_percentage_drop,
        usage_liters=usage_liters
    )

    # 🔥 Clean raw data
    records.delete()