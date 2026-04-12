from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import WaterLevel
from .services import process_hourly_consumption


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

from .models import HourlyWaterConsumption
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response


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

from django.db.models import Sum

@api_view(['GET'])
def daily_usage(request):
    today = timezone.now().date()

    total = HourlyWaterConsumption.objects.filter(
        date=today
    ).aggregate(total=Sum('usage_liters'))

    return Response({
        "date": today,
        "total_usage_liters": total['total'] or 0
    })

from .models import WaterEvent

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