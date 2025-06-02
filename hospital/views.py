from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAdminUser, AllowAny
from django.shortcuts import get_object_or_404
from .models import Governorate, City, Hospital, Department
from .serializers import GovernorateSerializer, CitySerializer, HospitalSerializer, DepartmentSerializer
from rest_framework.response import Response
from rest_framework.decorators import action

#اختيار المحافظه

class GovernorateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Governorate.objects.all()
    serializer_class = GovernorateSerializer
    permission_classes = [AllowAny] 


# اختيار المدينة


class CityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [AllowAny]

    def retrieve(self, request, *args, **kwargs):
        governorate_id = kwargs.get('pk')  

        cities = City.objects.filter(governorate_id=governorate_id)
        if not cities.exists():
            return Response({'detail': 'No cities found for this governorate.'}, status=404)

        serializer = self.get_serializer(cities, many=True)
        return Response(serializer.data)


# عرض المستشفيات 

class HospitalViewSet(viewsets.ModelViewSet):
    queryset = Hospital.objects.all()
    serializer_class = HospitalSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]
    
    @action(detail=False, methods=['get'], url_path='by-city/(?P<city_name>[^/.]+)')
    def by_city(self, request, city_name=None):
        hospitals = Hospital.objects.filter(city__name__iexact=city_name)
        if not hospitals.exists():
            return Response({'detail': 'No hospitals found for this city.'}, status=404)
        
        serializer = self.get_serializer(hospitals, many=True)
        return Response(serializer.data)


# عرض تفاصيل والتخصصات المتاحه في المستشفي

class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [AllowAny]  

 

    @action(detail=False, methods=['get'], url_path='by-hospital/(?P<hospital_name>[^/.]+)')
    def by_hospital(self, request, hospital_name=None):
        departments = Department.objects.filter(hospital__name__iexact=hospital_name)
        
        if not departments.exists():
            return Response({'detail': 'No departments found for this hospital.'}, status=404)

        serializer = self.get_serializer(departments, many=True, context = {'request':request})
        return Response(serializer.data)
    
