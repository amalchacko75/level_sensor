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


def send_notification(token, title, body):

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        token=token
    )
    try:
        response = messaging.send(message)
        return response

    except messaging.UnregisteredError:
        DeviceToken.objects.filter(token=token).delete()
    except Exception as e:
        print(f"Failed to send notification: {e}")

        return None


def check_alerts(level, battery):

    if level >= 95:

        return (
            "Tank Full",
            "Water tank is almost full."
        )

    if level <= 65:

        return (
            "Tank Empty",
            "Water level is very low."
        )

    if battery <= 40:

        return (
            "Battery Low",
            "Battery is below 40%."
        )

    return None


def build_status_message():

    latest = WaterLevel.objects.order_by("-created_at").first()

    today = timezone.now().date()

    usage = HourlyWaterConsumption.objects.filter(
        date=today
    ).aggregate(
        total=Sum("usage_liters")
    )["total"] or 0

    settings = NotificationSettings.objects.first()

    lines = []

    if settings.include_water_level:
        lines.append(
            f"💧 Water Level : {latest.percentage:.0f}%"
        )

    if settings.include_daily_usage:
        lines.append(
            f"🚰 Today's Usage : {usage:.1f} L"
        )

    if settings.include_battery:
        lines.append(
            f"🔋 Battery : {latest.battery_percentage:.0f}%"
        )

    if settings.include_voltage:
        lines.append(
            f"⚡ Voltage : {latest.battery_voltage:.2f}V"
        )

    if settings.include_wifi:
        lines.append(
            f"📶 WiFi : {latest.signal_strength} dBm"
        )

    return "\n".join(lines)


def send_status_report():

    body = build_status_message()

    tokens = DeviceToken.objects.all()

    for device in tokens:

        send_notification(

            device.token,

            "💧 Water Tank Status",

            body

        )


def should_send_report():

    settings = NotificationSettings.objects.first()

    if not settings.enabled:
        return False

    if settings.last_sent is None:
        return True

    diff = timezone.now() - settings.last_sent

    return diff >= timedelta(
        minutes=settings.report_interval
    )