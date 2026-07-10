import os
from django.conf import settings
from django.http import FileResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import NotificationSettings, WaterLevel
from .models import HourlyWaterConsumption
from django.utils import timezone
from django.db.models import Sum
from .models import WaterEvent
from .services import process_hourly_consumption
from django.shortcuts import render
from .models import DeviceToken
from .notification_service import check_alerts, is_wifi_connected, send_notification, send_status_report, should_send_report
from django.views.decorators.csrf import csrf_exempt



@api_view(["POST"])
def save_water_level(request):

    percentage = request.data.get("percentage")
    distance = request.data.get("distance")

    battery_voltage = request.data.get("battery_voltage")
    battery_percentage = request.data.get("battery_percentage")

    wifi_ssid = request.data.get("wifi_ssid")
    signal_strength = request.data.get("signal_strength")

    # 1. Save latest reading first
    WaterLevel.objects.create(
        percentage=percentage,
        distance=distance,
        battery_voltage=battery_voltage,
        battery_percentage=battery_percentage,
        wifi_ssid=wifi_ssid,
        signal_strength=signal_strength
    )

    # 2. Send emergency alerts
    alert = check_alerts(
        float(percentage),
        int(battery_percentage)
    )

    if alert:

        title, body = alert

        tokens = DeviceToken.objects.all()

        for device in tokens:

            try:

                send_notification(
                    device.token,
                    title,
                    body
                )

            except Exception as e:

                print(e)

    # 3. Send periodic report
    if should_send_report():

        send_status_report()

        settings = NotificationSettings.objects.first()

        settings.last_sent = timezone.now()

        settings.save(update_fields=["last_sent"])

    return Response({
        "status": "saved"
    })


@api_view(['GET'])
def hourly_usage(request):
    today = timezone.now().date()

    data = HourlyWaterConsumption.objects.filter(
        date=today
    ).order_by('hour')

    result = []

    for item in data:
        result.append({
            "hour": item.hour,
            "start": item.start_level,
            "end": item.end_level,
            "usage_percentage": item.usage_percentage,
            "usage_liters": item.usage_liters
        })

    return Response(result)


@api_view(['GET'])
def daily_usage(request):
    today = timezone.now().date()

    total_usage = HourlyWaterConsumption.objects.filter(
        date=today
    ).aggregate(total=Sum('usage_liters'))['total'] or 0

    return Response({
        "date": str(today),
        "total_usage_liters": round(total_usage, 2)
    })



@api_view(['GET'])
def events_list(request):
    events = WaterEvent.objects.all().order_by('-start_time')[:50]

    result = []

    for e in events:
        result.append({
            "type": e.event_type,
            "time": e.start_time,
            "start_level": e.start_level,
            "end_level": e.end_level,
            "change_liters": e.change_liters
        })

    return Response(result)



@api_view(['GET'])
def run_processing(request):

    try:

        process_hourly_consumption()

        # ----------------------------
        # Wi-Fi Offline Check
        # ----------------------------

        alert = is_wifi_connected()

        if alert:

            settings = NotificationSettings.objects.first()

            if settings and settings.wifi_offline_enabled:

                title, body = alert

                for device in DeviceToken.objects.all():

                    try:
                        send_notification(
                            device.token,
                            title,
                            body
                        )
                    except Exception:
                        pass

        return Response({
            "status": "success",
            "message": "Hourly processing completed"
        })

    except Exception as e:

        return Response({
            "status": "error",
            "message": str(e)
        })
    


def dashboard(request):
    return render(request, "dashboard.html")



@api_view(['GET'])
def current_level(request):
    latest = WaterLevel.objects.order_by('-created_at').first()

    if not latest:
        return Response({
            "level": 0,
            "distance": 0,
            "battery_voltage": 0,
            "battery_percentage": 0,
            "time": None
        })

    return Response({
        "level": latest.percentage,
        "distance": latest.distance,
        "battery_voltage": latest.battery_voltage,
        "battery_percentage": latest.battery_percentage,
        "time": latest.created_at
    })


@csrf_exempt
@api_view(["POST"])
def save_device_token(request):

    token = request.data.get("token")
    device_type = request.data.get(
        "device_type",
        "web"
    )

    if not token:
        return Response(
            {"error": "Token required"},
            status=400
        )

    DeviceToken.objects.update_or_create(
        token=token,
        defaults={"device_type": device_type}
    )

    return Response({
        "status": "saved"
    })



@api_view(["GET", "POST"])
def test_notification(request):

    title = "Water Monitor"
    body = "Test Notification"

    results = []

    for device in DeviceToken.objects.all():

        try:

            response = send_notification(
                device.token,
                title,
                body
            )

            results.append({
                "token": device.token[:25] + "...",
                "status": "success",
                "firebase": response
            })

        except Exception as e:

            results.append({
                "token": device.token[:25] + "...",
                "status": "failed",
                "error": str(e)
            })

    return Response(results)


def service_worker(request):
    path = os.path.join(settings.BASE_DIR, "service-worker.js")
    return FileResponse(
        open(path, "rb"),
        content_type="application/javascript"
    )