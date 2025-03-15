from rest_framework import serializers
from .models import Governorate, City, Hospital, Department

class GovernorateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Governorate
        fields = '__all__'

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = '__all__'

class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = '__all__'

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'
