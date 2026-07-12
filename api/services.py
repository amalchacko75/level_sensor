from datetime import timedelta
from statistics import mean
from django.utils import timezone
from .models import WaterLevel, HourlyWaterConsumption, WaterEvent

TANK_CAPACITY = 1750  # liters

EVENT_THRESHOLD = 10  # %


# 🔥 SAFE EVENT CREATION (NO DUPLICATES)
def create_event(event_type, time, start, end, change_pct, change_liters):
    exists = WaterEvent.objects.filter(
        event_type=event_type,
        start_time=time
    ).exists()

    if exists:
        return

    WaterEvent.objects.create(
        event_type=event_type,
        start_time=time,
        end_time=time,
        start_level=start,
        end_level=end,
        change_percentage=change_pct,
        change_liters=change_liters
    )


# 🔥 EVENT DETECTION (FIXED)
def detect_events(records):

    if len(records) < 6:
        return

    for i in range(3, len(records) - 2):

        previous_avg = mean(
            r.percentage
            for r in records[i-3:i]
        )

        current_avg = mean(
            r.percentage
            for r in records[i:i+3]
        )

        diff = current_avg - previous_avg

        # ----------------------------------
        # Pump Filling
        # ----------------------------------

        if diff >= EVENT_THRESHOLD:

            liters = (diff / 100) * TANK_CAPACITY

            create_event(
                "pump_on",
                records[i].created_at,
                round(previous_avg, 2),
                round(current_avg, 2),
                round(diff, 2),
                round(liters, 2)
            )

        # ----------------------------------
        # Water Consumption / Leak
        # ----------------------------------

        elif diff <= -EVENT_THRESHOLD:

            drop = abs(diff)

            liters = (drop / 100) * TANK_CAPACITY

            create_event(
                "leak",
                records[i].created_at,
                round(previous_avg, 2),
                round(current_avg, 2),
                round(drop, 2),
                round(liters, 2)
            )


# 🔥 EMPTY TANK HANDLING (WITH COOLDOWN)
def handle_empty_tank(records):

    if not records:
        return False

    consecutive_zeros = 0

    for record in reversed(records):

        if record.percentage <= 1:

            consecutive_zeros += 1

        else:

            break

    if consecutive_zeros < 5:
        return False

    print("⚠ Tank Empty")

    last_empty = WaterEvent.objects.filter(
        event_type="empty"
    ).order_by("-start_time").first()

    if last_empty:

        elapsed = timezone.now() - last_empty.start_time

        if elapsed < timedelta(minutes=30):
            return True

    create_event(
        "empty",
        records[-1].created_at,
        0,
        0,
        0,
        0
    )

    WaterLevel.objects.filter(
        id__in=[r.id for r in records]
    ).delete()

    return True


# 🔥 HOURLY / 10-MIN PROCESSING
def process_hourly_consumption():
    now = timezone.now()
    ten_minutes_ago = now - timedelta(minutes=60)

    queryset = WaterLevel.objects.filter(
        created_at__gte=ten_minutes_ago
    ).order_by("created_at")[:200]

    records = list(queryset)

    # 🔥 CHECK EMPTY FIRST
    if handle_empty_tank(records):
        return

    if len(records) < 2:
        return

    # 🔥 EVENT DETECTION
    detect_events(records)

    # 🔥 USAGE CALCULATION
    # Average first 3 readings
    start_level = mean(
        r.percentage
        for r in records[:3]
    )

    # Average last 3 readings
    end_level = mean(
        r.percentage
        for r in records[-3:]
    )

    percentage_drop = start_level - end_level

    # Ignore sensor fluctuations
    if abs(percentage_drop) < 2:
        percentage_drop = 0

    # Ignore refill (pump running)
    if percentage_drop < 0:
        percentage_drop = 0

    usage_liters = (
        percentage_drop / 100
    ) * TANK_CAPACITY

    usage_liters = (percentage_drop / 100) * TANK_CAPACITY

    # inside process_hourly_consumption()

    HourlyWaterConsumption.objects.update_or_create(
        date=now.date(),
        hour=now.hour,
        defaults={
            "start_level": round(start_level, 2),
            "end_level": round(end_level, 2),
            "usage_percentage": round(percentage_drop, 2),
            "usage_liters": round(usage_liters, 2),
        }
    )

    # 🔥 DELETE ONLY PROCESSED RECORDS
    if len(records) > 3:

        ids = [
            r.id
            for r in records[:-3]
        ]

        WaterLevel.objects.filter(
            id__in=ids
        ).delete()

    # 🔥 CLEAN OLD DATA (> 2 hours)
    two_hours_ago = now - timedelta(hours=2)
    WaterLevel.objects.filter(created_at__lt=two_hours_ago).delete()

    # CLEAN WATER EVENTS
    one_day_ago = now-timedelta(days=1)
    WaterEvent.objects.filter(created_at__lt=one_day_ago).delete()