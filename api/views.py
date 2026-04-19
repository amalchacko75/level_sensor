from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import WaterLevel
from .models import HourlyWaterConsumption
from django.utils import timezone
from django.db.models import Sum
from .models import WaterEvent
from .services import process_hourly_consumption
from django.shortcuts import render


@api_view(['POST'])
def save_water_level(request):
    percentage = request.data.get("percentage")
    distance = request.data.get("distance")
    wifi_ssid = request.data.get("wifi_ssid")
    signal_strength = request.data.get("signal_strength")

    WaterLevel.objects.create(
        percentage=percentage,
        distance=distance,
        wifi_ssid=wifi_ssid,
        signal_strength=signal_strength
    )

    # 🔥 Process logic
    # process_hourly_consumption()

    return Response({"status": "saved"})


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
        return Response({"level": 0})

    return Response({
        "level": latest.percentage,
        "distance": latest.distance,
        "time": latest.created_at
    })