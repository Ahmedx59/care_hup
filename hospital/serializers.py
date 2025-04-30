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
    city = serializers.CharField(source='city.name')
    class Meta:
        model = Hospital
        fields = '__all__'


class HospitalMiniSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Hospital
        fields = ['name', 'address', 'image']

    def get_image(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.image.url) if obj.image else None

class DepartmentSerializer(serializers.ModelSerializer):
    hospital = HospitalMiniSerializer(read_only=True)

    class Meta:
        model = Department
        fields = ['id', 'name', 'opening_time', 'closing_time', 'hospital']
