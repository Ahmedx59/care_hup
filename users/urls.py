from django.urls import path 
from rest_framework.routers import DefaultRouter

from users.api.views import AuthUser , UserProfile , DoctorsViewSet ,NurseViewSet , ProfileViewSet , SpecialtyDoctorViewSet

router = DefaultRouter()

router.register('Auth' , AuthUser , basename='Auth-user')
router.register('user' , UserProfile , basename='user')
router.register('doctor' , DoctorsViewSet , basename='doctor')
router.register('nurse' , NurseViewSet , basename='nurse')
router.register('profile' , ProfileViewSet , basename='profile')
router.register('specialty', SpecialtyDoctorViewSet , basename='specialty')



app_name = 'users'
urlpatterns = router.urls