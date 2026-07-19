import firebase_admin
from datetime import timedelta

from firebase_admin import credentials
from firebase_admin import messaging
from django.utils import timezone
from django.conf import settings
from django.db.models import Sum

import os

from api.models import DeviceToken, HourlyWaterConsumption, NotificationSettings, WaterLevel

if not firebase_admin._apps:

    # Render Secret File (production)
    firebase_credentials = os.environ.get(
        "FIREBASE_CREDENTIALS"
    )

    # Local development fallback
    if not firebase_credentials:
        firebase_credentials = os.path.join(
            settings.BASE_DIR,
            "firebase-admin.json"
        )

    cred = credentials.Certificate(firebase_credentials)

    firebase_admin.initialize_app(cred)


# ----------------------------------------------------------------------
#  Sender
# ----------------------------------------------------------------------
#  priority="high" makes urgent alerts break through:
#    - Web (your PWA):  require_interaction -> notification stays on screen
#                       until tapped, and Urgency:high asks for prompt push.
#    - Android:         high priority + a dedicated channel (heads-up).
#    - iOS:             time-sensitive -> shows through Focus / Do-Not-Disturb
#                       (needs the Time Sensitive entitlement in the app).
#  Default is "normal", so any old 3-argument calls still work unchanged.
# ----------------------------------------------------------------------
def send_notification(token, title, body, priority="normal"):

    is_high = priority == "high"

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        token=token,

        # --- Web push (your PWA / service worker) ---
        webpush=messaging.WebpushConfig(
            headers={
                "Urgency": "high" if is_high else "normal",
                "TTL": "3600",
            },
            notification=messaging.WebpushNotification(
                title=title,
                body=body,
                icon="/static/icons/apple-touch-icon.png",
                badge="/static/favicon.ico",
                require_interaction=is_high,
            ),
        ),

        # --- Android (if you ever ship a native app) ---
        android=messaging.AndroidConfig(
            priority="high" if is_high else "normal",
            notification=messaging.AndroidNotification(
                channel_id="alerts_high" if is_high else "alerts_default",
                sound="default",
            ),
        ),

        # --- iOS / APNs ---
        apns=messaging.APNSConfig(
            headers={"apns-priority": "10" if is_high else "5"},
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    sound="default",
                    custom_data={
                        "interruption-level":
                            "time-sensitive" if is_high else "active"
                    },
                ),
            ),
        ),
    )

    try:
        response = messaging.send(message)
        return response

    except messaging.UnregisteredError:
        DeviceToken.objects.filter(token=token).delete()
    except Exception as e:
        print(f"Failed to send notification: {e}")
        return None


def send_alert(alert):
    """Broadcast an (title, body, priority) tuple to every device.
    Does nothing if alert is None."""
    if not alert:
        return
    title, body, priority = alert
    for device in DeviceToken.objects.all():
        send_notification(device.token, title, body, priority)


# ----------------------------------------------------------------------
#  Situation-specific alerts
#  Each returns (title, body, priority) or None.
# ----------------------------------------------------------------------
def check_alerts(level, battery):

    conf = NotificationSettings.objects.first()
    if not conf:
        return None

    if level >= conf.tank_full_percentage and conf.tank_full_notification:
        return (
            f"✅ Tank full — {level:.0f}%",
            "Refill complete, pump switched off.",
            "normal",
        )

    if level <= conf.tank_empty_percentage and conf.tank_empty_notification:
        return (
            "🪣 Tank is empty",
            f"Level {level:.0f}% — refill soon, the pump may need a look.",
            "high",
        )

    if battery <= conf.battery_low_percentage:
        critical = battery <= max(10, conf.battery_low_percentage / 2)
        label = "critical" if critical else "low"
        return (
            f"🔋 Sensor battery {label} — {battery:.0f}%",
            "Charge the sensor soon to keep monitoring.",
            "high" if critical else "normal",
        )

    return None


def is_wifi_connected():

    conf = NotificationSettings.objects.first()

    if not conf or not conf.wifi_offline_enabled:
        return None

    latest = WaterLevel.objects.order_by("-created_at").first()

    if latest is None:
        return None

    elapsed = timezone.now() - latest.created_at
    minutes = int(elapsed.total_seconds() / 60)

    if minutes >= 5:
        return (
            "📶 Sensor offline",
            f"No data for {minutes} min — check the sensor's power or Wi-Fi.",
            "high",
        )

    return None


# ----------------------------------------------------------------------
#  Routine status report
# ----------------------------------------------------------------------
def get_status_headline(latest):
    """Title + priority for the routine report: lead with what matters."""
    if latest.battery_percentage <= 10:
        return f"🔋 Battery critical — {latest.battery_percentage:.0f}%", "high"
    return f"💧 Tank at {latest.percentage:.0f}%", "normal"


def build_status_message(latest=None, usage=None, conf=None):
    """Body for the routine report. Honors the NotificationSettings
    toggles. All args optional -> callable with no arguments as before."""

    if latest is None:
        latest = WaterLevel.objects.order_by("-created_at").first()
    if latest is None:
        return ""

    if conf is None:
        conf = NotificationSettings.objects.first()
    if conf is None:
        return ""

    if usage is None:
        today = timezone.now().date()
        usage = HourlyWaterConsumption.objects.filter(
            date=today
        ).aggregate(total=Sum("usage_liters"))["total"] or 0

    parts = []

    if conf.include_water_level:
        parts.append(f"{latest.percentage:.0f}% full")
    if conf.include_daily_usage:
        parts.append(f"{usage:.1f} L used today")

    # battery + voltage read better together than as two separate items
    if conf.include_battery and conf.include_voltage:
        parts.append(
            f"battery {latest.battery_percentage:.0f}% "
            f"({latest.battery_voltage:.2f} V)"
        )
    elif conf.include_battery:
        parts.append(f"battery {latest.battery_percentage:.0f}%")
    elif conf.include_voltage:
        parts.append(f"{latest.battery_voltage:.2f} V")

    if conf.include_wifi:
        parts.append(f"Wi-Fi {latest.signal_strength} dBm")

    # one flowing line instead of a congested stack.
    # swap " · " for ", " if you prefer a sentence feel.
    return " · ".join(parts)


def send_status_report():

    latest = WaterLevel.objects.order_by("-created_at").first()
    if latest is None:
        return

    title, priority = get_status_headline(latest)
    body = build_status_message(latest=latest)

    if not body:
        return

    for device in DeviceToken.objects.all():
        send_notification(device.token, title, body, priority)


def should_send_report():

    conf = NotificationSettings.objects.first()

    if not conf or not conf.enabled:
        return False

    if conf.last_sent is None:
        return True

    diff = timezone.now() - conf.last_sent

    return diff >= timedelta(minutes=conf.report_interval)


# ----------------------------------------------------------------------
#  Orchestrator — call this from your scheduler / task.
# ----------------------------------------------------------------------
def run_notifications(level=None, battery=None):
    """One entry point that fires the right things at the right priority:
      1. sensor-offline alert (event-driven)
      2. tank full / empty / battery alerts (event-driven)
      3. the routine status report, but only on its interval
    """
    latest = WaterLevel.objects.order_by("-created_at").first()
    if latest is None:
        return

    if level is None:
        level = latest.percentage
    if battery is None:
        battery = latest.battery_percentage

    # 1 + 2: urgent, event-driven alerts
    send_alert(is_wifi_connected())
    send_alert(check_alerts(level, battery))

    # 3: routine report on schedule
    if should_send_report():
        send_status_report()
        conf = NotificationSettings.objects.first()
        if conf:
            conf.last_sent = timezone.now()
            conf.save(update_fields=["last_sent"])
