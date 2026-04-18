from datetime import timedelta
from django.utils import timezone
from .models import WaterLevel, HourlyWaterConsumption, WaterEvent

TANK_CAPACITY = 1750  # liters


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
    prev = None

    for record in records:
        if prev is not None:
            diff = record.percentage - prev.percentage

            # 🚰 Pump ON
            if diff > 5:
                liters = (diff / 100) * TANK_CAPACITY

                create_event(
                    'pump_on',
                    record.created_at,
                    prev.percentage,
                    record.percentage,
                    diff,
                    liters
                )

            # 💧 Leak
            elif diff < -5:
                drop = abs(diff)
                liters = (drop / 100) * TANK_CAPACITY

                create_event(
                    'leak',
                    record.created_at,
                    prev.percentage,
                    record.percentage,
                    drop,
                    liters
                )

        prev = record


# 🔥 EMPTY TANK HANDLING (WITH COOLDOWN)
def handle_empty_tank(records):
    consecutive_zeros = 0

    for r in reversed(records):
        if r.percentage <= 1:
            consecutive_zeros += 1
        else:
            break

    if consecutive_zeros >= 5:
        print("⚠️ Tank Empty Detected")

        # ⛔ cooldown: avoid duplicate empty events
        last_empty = WaterEvent.objects.filter(
            event_type='empty'
        ).order_by('-start_time').first()

        if last_empty and (timezone.now() - last_empty.start_time < timedelta(minutes=30)):
            return True

        create_event(
            'empty',
            records[-1].created_at,
            0,
            0,
            0,
            0
        )

        # delete only processed records
        ids = [r.id for r in records]
        WaterLevel.objects.filter(id__in=ids).delete()

        return True

    return False


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
    total_percentage_drop = 0
    prev = None

    for record in records:
        if prev is not None:
            diff = prev.percentage - record.percentage

            # ignore noise
            if diff > 0.5:
                total_percentage_drop += diff

        prev = record

    if total_percentage_drop == 0:
        return

    usage_liters = (total_percentage_drop / 100) * TANK_CAPACITY

    # inside process_hourly_consumption()

    HourlyWaterConsumption.objects.update_or_create(
        date=now.date(),
        hour=now.hour,
        defaults={
            "start_level": records[0].percentage,
            "end_level": records[-1].percentage,
            "usage_percentage": total_percentage_drop,
            "usage_liters": usage_liters,
        }
    )

    # 🔥 DELETE ONLY PROCESSED RECORDS
    ids = [r.id for r in records]
    WaterLevel.objects.filter(id__in=ids).delete()

    # 🔥 CLEAN OLD DATA (> 2 hours)
    two_hours_ago = now - timedelta(hours=2)
    WaterLevel.objects.filter(created_at__lt=two_hours_ago).delete()