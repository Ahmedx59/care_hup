from rest_framework import serializers
from .models import FCMDevice

class FCMDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FCMDevice
        fields = ['registration_id', 'device_type']

    def validate_device_type(self, value):
        allowed_types = ['android', 'ios', 'web']
        if value.lower() not in allowed_types:
            raise serializers.ValidationError("Invalid device type. Must be one of: android, ios, web")
        return value.lower()

    def validate_registration_id(self, value):
        if not value or len(value) < 10:
            raise serializers.ValidationError("Invalid registration ID. Must be at least 10 characters long.")
        return value
