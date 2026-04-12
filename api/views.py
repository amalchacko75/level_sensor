from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import WaterLevel
from .serializers import WaterLevelSerializer
from django.contrib.auth.models import User


@api_view(['POST'])
def save_water_level(request):
    percentage = request.data.get("percentage")
    distance = request.data.get("distance")
    wifi_ssid = request.data.get("wifi_ssid")
    signal_strength = request.data.get("signal_strength")

    obj = WaterLevel.objects.create(
        percentage=percentage,
        distance=distance,
        wifi_ssid=wifi_ssid,
        signal_strength=signal_strength
    )

    # 🔔 Alerts
    if percentage >= 90:
        print("🚰 ALERT: Tank FULL")

    elif percentage <= 20:
        print("⚠️ ALERT: Tank LOW")

    return Response({"status": "saved"})


@api_view(['GET'])
def latest_water_level(request):
    obj = WaterLevel.objects.last()

    if not obj:
        return Response({"message": "No data"})

    serializer = WaterLevelSerializer(obj)
    return Response(serializer.data)


def create_admin_user():
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='your_email@gmail.com',
            password='admin123'
        )