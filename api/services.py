from datetime import timedelta
from statistics import mean
from django.utils import timezone
from .models import WaterLevel, HourlyWaterConsumption, WaterEvent

TANK_CAPACITY = 1750  # liters

EVENT_THRESHOLD = 10  # %

NOISE_THRESHOLD = 0.5  # Ignore sensor fluctuation below 0.5%


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


def _moving_average(values, window=5):
    """Trailing moving average to suppress sensor jitter."""
    if window <= 1 or len(values) <= window:
        return list(values)
    out = []
    for i in range(len(values)):
        lo = max(0, i - window + 1)
        chunk = values[lo:i + 1]
        out.append(sum(chunk) / len(chunk))
    return out


# -------------------------------------------------------
# PROCESS PREVIOUS HOUR
# -------------------------------------------------------

def process_hourly_consumption():

    now = timezone.now()
    current_hour = now.replace(minute=0, second=0, microsecond=0)
    previous_hour = current_hour - timedelta(hours=1)

    # Prevent duplicate processing
    if HourlyWaterConsumption.objects.filter(
        date=previous_hour.date(),
        hour=previous_hour.hour,
    ).exists():
        return

    records = list(
        WaterLevel.objects.filter(
            created_at__gte=previous_hour,
            created_at__lt=current_hour,
        ).order_by("created_at")
    )

    if len(records) < 2:
        return

    # Empty tank detection
    if handle_empty_tank(records):
        return

    # Event detection
    detect_events(records)

    # Smooth raw readings first — cancels symmetric sensor jitter
    levels = [r.percentage for r in records]
    smoothed = _moving_average(levels, window=5)

    start_level = smoothed[0]
    end_level = smoothed[-1]

    # Did the level ever rise past the deadband? -> a refill occurred
    refill_happened = any(
        b - a > NOISE_THRESHOLD for a, b in zip(smoothed, smoothed[1:])
    )

    if not refill_happened:
        # No refill: consumption is simply the net drop. No loop, no leak.
        usage_percentage = max(0.0, start_level - end_level)
    else:
        # Refill(s) occurred: accumulate only the downward segments.
        usage_percentage = 0.0
        reference = smoothed[0]
        for current in smoothed[1:]:
            diff = reference - current
            if abs(diff) < NOISE_THRESHOLD:
                continue
            if diff > 0:                 # level fell -> water consumed
                usage_percentage += diff
            # level rose -> refill/pump, not consumption
            reference = current          # always advance the reference

    usage_liters = (usage_percentage / 100.0) * TANK_CAPACITY

    HourlyWaterConsumption.objects.create(
        date=previous_hour.date(),
        hour=previous_hour.hour,
        start_level=round(start_level, 2),
        end_level=round(end_level, 2),
        usage_percentage=round(usage_percentage, 2),
        usage_liters=round(usage_liters, 2),
    )

    # Keep raw data for 2 days
    WaterLevel.objects.filter(
        created_at__lt=now - timedelta(days=2)
    ).delete()

    # Keep events for 30 days
    WaterEvent.objects.filter(
        created_at__lt=now - timedelta(days=1)
    ).delete()
