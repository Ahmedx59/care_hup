from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAdminUser, AllowAny
from django.shortcuts import get_object_or_404
from .models import Governorate, City, Hospital, Department
from .serializers import GovernorateSerializer, CitySerializer, HospitalSerializer, DepartmentSerializer
from rest_framework.response import Response

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
    
    
    def retrieve(self, request, *args, **kwargs):
        city_id = kwargs.get('pk')  
        hospitals = Hospital.objects.filter(city_id=city_id)
        if not hospitals.exists():
            return Response({'detail': 'No hospitals found for this city.'}, status=404)
        serializer = self.get_serializer(hospitals, many=True)
        return Response(serializer.data)





# عرض تفاصيل والتخصصات المتاحه في المستشفي

class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [AllowAny]  

    def retrieve(self, request, *args, **kwargs):
        hospital_id = kwargs.get('pk')  
        departments = Department.objects.filter(hospital_id=hospital_id)
        
        if not departments.exists():
            return Response({'detail': 'No departments found for this hospital.'}, status=404)
        
        serializer = self.get_serializer(departments, many=True)
        return Response(serializer.data)