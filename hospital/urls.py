
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GovernorateViewSet, CityViewSet, HospitalViewSet, DepartmentViewSet


router = DefaultRouter()
router.register(r'governorates', GovernorateViewSet, basename='governorate')
router.register(r'cities', CityViewSet, basename='city')
router.register(r'hospitals', HospitalViewSet, basename='hospital')
router.register(r'departments', DepartmentViewSet, basename='department')

urlpatterns = [
    path('api/', include(router.urls)),  
]

