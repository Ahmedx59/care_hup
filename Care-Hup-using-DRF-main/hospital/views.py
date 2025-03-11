from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAdminUser, AllowAny
from django.shortcuts import get_object_or_404
from .models import Governorate, City, Hospital, Department
from .serializers import GovernorateSerializer, CitySerializer, HospitalSerializer, DepartmentSerializer

#اختيار المحافظه

class GovernorateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Governorate.objects.all()
    serializer_class = GovernorateSerializer
    permission_classes = [AllowAny] 


# اختيار المدينة

class CityViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CitySerializer
    permission_classes = [AllowAny]  

    def get_queryset(self):
        queryset = City.objects.all()
        governorate_id = self.request.query_params.get('governorate_id')
        if governorate_id:
            queryset = queryset.filter(governorate_id=governorate_id)
        return queryset


# عرض المستشفيات 

class HospitalViewSet(viewsets.ModelViewSet):
    queryset = Hospital.objects.all()
    serializer_class = HospitalSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]


# عرض تفاصيل والتخصصات المتاحه في المستشفي

class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [AllowAny]  
