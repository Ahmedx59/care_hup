# notifications/serializers.py
from rest_framework import serializers
from .models import FCMDevice

class FCMDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FCMDevice
        fields = ['registration_id', 'device_type']