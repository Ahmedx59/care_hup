from django.shortcuts import render , get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import mixins , viewsets , status , serializers ,filters
from rest_framework.decorators import action
from rest_framework.response import Response 
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import CustomTokenObtainPairSerializer
from .serializers import (
    SingUpPatientSerializer , 
    UserActivateSerializers , 
    ChangePasswordSerializer , 
    ResetPasswordSerializer , 
    ConfirmResetPasswordSerializer , 
    ProfileDoctorAndNurseSerializer ,
    PatientProfileSerializer,
    EditPatientProfileSerializer , 
    ListDoctorSerializer ,
    ListNurseSerializer ,
    SignUpDoctorNurseSerializer ,
    SpecialtySerializer,
    UpdateProfileDoctorAndNurseSerializer,
    ActivateResetPasswordSerializer
)

from users.models import User , DoctorNurseProfile ,PatientProfile, SpecialtyDoctor
from users.filter import DoctorFilter

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    # permission_classes = [AllowAny()]
    permission_classes = [AllowAny]

class AuthUser(
    viewsets.GenericViewSet):

    queryset = User.objects.all()
    serializer_class = SingUpPatientSerializer


    def get_permissions(self):
        if self.action in ("create","activate","sign_up_patient","sign_up_doctor_nurse","reset_password","active_reset_password","confirm_reset_password"):
            return [AllowAny()]
        return super().get_permissions()


    @action(detail=False , methods=['post'])
    def sign_up_patient(self,*args, **kwargs):
        data = self.request.data
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception = True)
        serializer.save()
        return Response({"detail": "check your email."})
    
    @action(detail=False , methods= ['post'],serializer_class = SignUpDoctorNurseSerializer)
    def sign_up_doctor_nurse(self,*args, **kwargs):
        data = self.request.data
        serializer = self.get_serializer(data = data)
        serializer.is_valid(raise_exception = True)
        serializer.save()
        return Response({'detail':'Waiting for a response from the admin.'})

        
    @action(detail=False , methods=['post'] , serializer_class=UserActivateSerializers)
    def activate(self, *args, **kwargs):
        data = self.request.data
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception =True)
        serializer.save()
        return Response ({'detail':'your account created successfully'},status=status.HTTP_200_OK)
    
    @action(detail=False , methods=['post'] , serializer_class= ChangePasswordSerializer)
    def change_password(self,*args, **kwargs):
        data = self.request.data
        serializer = self.get_serializer(data = data)
        serializer.is_valid(raise_exception = True)
        serializer.save()
        return Response({'detail':'your password change successfully'})
    
    @action(detail=False , methods=['post'] , serializer_class = ResetPasswordSerializer)
    def reset_password(self,*args, **kwargs):
        data = self.request.data
        serializer = self.get_serializer(data = data)
        serializer.is_valid(raise_exception = True)
        serializer.save()
        return Response({'detail':'check code on mail'})
    
    @action(detail=False ,methods=["post"] ,serializer_class = ActivateResetPasswordSerializer)
    def active_reset_password(self,request , pk=None):
        data = self.request.data
        serializer = self.get_serializer(data = data ,  context={'request': request})
        serializer.is_valid(raise_exception = True)
        serializer.save()
        return Response({'detail':'Code verified'})

    @action(detail=False ,methods=['post'] ,serializer_class = ConfirmResetPasswordSerializer)
    def confirm_reset_password(self,request):
        data = self.request.data
        serializer = self.get_serializer(data = data ,  context={'request': request})
        serializer.is_valid(raise_exception = True)
        serializer.save()
        return Response({'detail':'password change successfully'})
    
class UserProfile(viewsets.GenericViewSet):
    queryset = DoctorNurseProfile.objects.all()
    serializer_class = ProfileDoctorAndNurseSerializer

    # @action(detail=True , methods=['get'])
    # def doctor(self,*args, **kwargs):
    #     pk = self.kwargs['pk']
    #     doctor_or_nurse = DoctorNurseProfile.objects.filter(id = pk).first()

    #     if not doctor_or_nurse:
    #         raise serializers.ValidationError({'error':'doctor not found'})
        
    #     serializer = self.get_serializer(doctor_or_nurse)
    #     return Response(serializer.data)
    
    @action(detail = True , methods=['get'] , serializer_class = EditPatientProfileSerializer)
    def Patient(self ,*args, **kwargs):
        pk = self.kwargs['pk']
        Patient = get_object_or_404(PatientProfile , id =pk)

        # Patient = PatientProfile.objects.filter(id = pk).first()

        # if not Patient:
        #     raise serializers.ValidationError({'error':'Patient not found'})
        
        serializer = EditPatientProfileSerializer(Patient)
        return Response(serializer.data)


    @action(detail=False , methods=['get'])
    def my_profile(self,request,*args, **kwargs):
        user = self.request.user
        
        if user.user_type in [User.User_Type.DOCTOR , User.User_Type.NURSE]:
            serializer = ProfileDoctorAndNurseSerializer(user.doctor_profile)
        
        if user.user_type == User.User_Type.PATIENT:
            serializer = PatientProfileSerializer(user.patient_profile)

        if not user.user_type:
            raise serializers.ValidationError({'error':'the user dont have user type'})
        return Response(serializer.data)
    
    @action(detail=False , methods=['put'], serializer_class=UpdateProfileDoctorAndNurseSerializer)
    def edit_Doctor_nurse_profile(self , request , *args, **kwargs):
        user = request.user
        data = request.data
        
        if user.user_type in [User.User_Type.DOCTOR , User.User_Type.NURSE]:
            serializer = self.get_serializer(user.doctor_profile, data = data)
            
            serializer.is_valid(raise_exception = True)
            serializer.save()

        return Response(serializer.data)
    
    @action(detail=False, methods=["put"], serializer_class=EditPatientProfileSerializer)
    def edit_patient_profile(self, request , *args, **kwargs):
        user = request.user
        data = request.data

        if user.user_type == User.User_Type.PATIENT:
            serializer = self.get_serializer(user.patient_profile,data = data)

            serializer.is_valid(raise_exception = True)
            serializer.save()

        return Response(serializer.data)


    # @action(detail=False , methods=['get'] , serializer_class = ListDoctorSerializer)
    # def list_doctor(self,request,*args, **kwargs):
    #     doctors = DoctorNurseProfile.objects.filter(user__user_type = User.User_Type.DOCTOR)

    #     serializer = self.get_serializer(doctors, many =True)
    #     return Response(serializer.data)

class DoctorsViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet):

    queryset = DoctorNurseProfile.objects.all()
    serializer_class = ListDoctorSerializer
    filter_backends = [DjangoFilterBackend]
    # filterset_fields = ["city", "specialty","governorate","offer"]
    filterset_class = DoctorFilter
    

    def get_serializer_class(self):
        if self.action == 'retrieve':            
            return ProfileDoctorAndNurseSerializer
        return super().get_serializer_class()
    
    def get_queryset(self):
        return super().get_queryset().filter(user__user_type = User.User_Type.DOCTOR)
    
class NurseViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet):

    queryset = DoctorNurseProfile.objects.all()
    serializer_class = ListNurseSerializer
    filter_backends = [DjangoFilterBackend]
    # filterset_fields = ["city","governorate"]
    filterset_class = DoctorFilter


    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProfileDoctorAndNurseSerializer
        return super().get_serializer_class()
    
    def get_queryset(self):
        return super().get_queryset().filter(user__user_type = User.User_Type.NURSE)
    
class ProfileViewSet(
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet):

    queryset = PatientProfile.objects.all()
    serializer_class = EditPatientProfileSerializer

    def get_serializer(self, *args, **kwargs):

        return super().get_serializer(*args, **kwargs)
        
class SpecialtyDoctorViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet
    ):
    queryset = SpecialtyDoctor.objects.all()
    serializer_class = SpecialtySerializer