from uuid import uuid4

from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.core.validators import MinLengthValidator
from django.conf import settings
from django.contrib.auth.hashers import  check_password
from django.utils import timezone
from django.contrib.auth import get_user_model


from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


from random import randint
from datetime import datetime , timedelta

from users.models import User , DoctorNurseProfile ,PatientProfile ,SpecialtyDoctor
from hospital.models import City
from hospital.serializers import CitySerializer

class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecialtyDoctor
        fields = '__all__'

class SingUpSerializer(serializers.ModelSerializer):
    username=serializers.CharField(required = True)
    email = serializers.CharField(required = True)
    password = serializers.CharField(write_only = True , validators=[MinLengthValidator(8)] , required = True)
    confirm_password = serializers.CharField(required = True , write_only = True)
    user_type = serializers.ChoiceField(choices=User.User_Type.choices , required = True)
    gender = serializers.ChoiceField(choices=User.GenderType.choices , required = True)
    phone_number = serializers.IntegerField(required = True)
    birth_date = serializers.DateTimeField(required = True)
    class Meta:
        model = PatientProfile
        exclude = ('user',)

        # fields = ('chronic_diseases','user_type')

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'detail':'the passwords do not match'})
        email_user = User.objects.filter(email = attrs['email']).first()
        if email_user :
            raise serializers.ValidationError({'detail':'this email is existed'})
        return super().validate(attrs)
    
    def create(self, validated_data):
        
        validated_data.pop('confirm_password')
        validated_data['is_active'] = False
        validated_data['activation_code'] = randint(1000,9999)

        chronic_diseases= validated_data.pop('chronic_diseases')

        send_mail(
            f"Activation Code ",
            f"welcome {validated_data['username']}\n Here is the activation code : {validated_data['activation_code']}.",
            settings.EMAIL_HOST_USER,
            {validated_data['email']},
            fail_silently=False,
        )
        user = User.objects.create_user(**validated_data)
        user_profile = PatientProfile.objects.filter(user = user).first()
        user_profile.chronic_diseases = chronic_diseases
        
        return {}
    
class SignUpDoctorNurseSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required = True)
    email = serializers.CharField(required = True)
    password = serializers.CharField(write_only = True , validators=[MinLengthValidator(8)] , required = True)
    confirm_password = serializers.CharField(required = True , write_only = True)
    user_type = serializers.ChoiceField(choices=User.User_Type.choices , required = True)
    gender = serializers.ChoiceField(choices=User.GenderType.choices ,required = True)
    phone_number = serializers.CharField(allow_blank=True , required = False)
    birth_date = serializers.DateTimeField()
    image = serializers.ImageField()
    
    class Meta:
        model = DoctorNurseProfile
        exclude = ('user','offer',)
             
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'error':'the passwords do not match'})
        email_user = User.objects.filter(email = attrs['email']).first()
        if email_user :
            raise serializers.ValidationError({'detail':'this email is existed'})
        return super().validate(attrs)
    
    def generate_unique_activation_code(self):
        while True:
            code = randint(1000, 9999)
            if not User.objects.filter(activation_code=code).exists():
                return code
        
    def create(self, validated_data):
        
        
        validated_data.pop('confirm_password')
        validated_data['is_active'] = False

        activation_code = self.generate_unique_activation_code()
        validated_data['activation_code'] = activation_code 

        certificates = validated_data.pop('certificates')
        about = validated_data.pop('about')
        experience_year = validated_data.pop('experience_year')
        price = validated_data.pop('price')
        specialty = validated_data.pop('specialty')
        city = validated_data.pop('city')
        card = validated_data.pop('card')
        services = validated_data.pop('services')
        governorate = validated_data.pop('governorate')

        user = User.objects.create_user(**validated_data)
        user_profile = DoctorNurseProfile.objects.filter(user = user).first()
        user_profile.price = price
        user_profile.experience_year = experience_year
        user_profile.about = about
        user_profile.certificates = certificates
        user_profile.specialty = specialty
        user_profile.city = city
        user_profile.card = card
        user_profile.services = services
        user_profile.governorate = governorate

        user_profile.save()

        return {}

        
    


class UserActivateSerializers(serializers.Serializer):
    code = serializers.CharField(required=True , write_only=True )

    def create(self, validated_data):
        code = validated_data['code']
        user = User.objects.filter(activation_code=code).first()

        if not user:
            raise serializers.ValidationError({'detail': 'Invalid activation code'})

        user.is_active = True
        user.activation_code = ''
        user.save()
        return {}
    
class ChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField(required = True)
    new_password = serializers.CharField(required = True , write_only = True , validators=[MinLengthValidator(8)])
    confirm_new_password = serializers.CharField(required = True , write_only = True)

    def create(self, validated_data):
        user = self.context['request'].user

        if not check_password(validated_data['password'] , user.password ):
            raise serializers.ValidationError({'detail':'old password not equal password'})
        
        if validated_data['new_password'] != validated_data['confirm_new_password']:
            raise serializers.ValidationError({'message':'The New Passwords do not match.'})
        
        user.set_password(validated_data['new_password'])
        user.save()

        return {}


    def to_representation(self, instance):
        return {'message': 'Password change process completed.'}


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.CharField(required = True)

    def generate_unique_activation_code(self):        
        while True:
            code = randint(1000,9999)
            if not User.objects.filter(reset_pass_token = code).exists():
                return code


    def create(self, validated_data):
        user = User.objects.filter(email = validated_data['email']).first()
        if not user:
            raise serializers.ValidationError({'detail':'not found'})

        user.reset_pass_token = self.generate_unique_activation_code()
        user.reset_pass_expire_date = datetime.now() + timedelta(minutes=30)
        user.is_reset_verified = False
        user.save()

        send_mail(
            f"Activation Code ",
            f"welcome {user.username}\n use this code to reset your password :{user.reset_pass_token}.",
            settings.EMAIL_HOST_USER,
            [validated_data['email']],
            fail_silently=False,
        )
        return {}
    
class ActivateResetPasswordSerializer(serializers.Serializer):
    code = serializers.CharField(required=True)

    def create(self, validated_data):
        request = self.context.get('request')

        user = User.objects.filter(reset_pass_token=validated_data["code"]).first()

        if not user:
            raise serializers.ValidationError({'detail': 'User not found'})

        if user.reset_pass_expire_date < timezone.now():
            raise serializers.ValidationError({'message': 'Token is expired'})

        user.is_reset_verified = True 
        
        user.save()
        request.session['reset_user_id'] = user.id

        return {}
    

User = get_user_model()

class ConfirmResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(required=True, validators=[MinLengthValidator(8)])
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({'detail': 'Passwords do not match'})
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        user_id = request.session.get('reset_user_id')

        if not user_id:
            raise serializers.ValidationError({'detail': 'Session expired or invalid. Please restart the reset process.'})

        user = User.objects.filter(id=user_id).first()

        if not user:
            raise serializers.ValidationError({'detail': 'User not found'})

        user.set_password(validated_data['password'])
        user.reset_pass_token = ""
        user.reset_pass_expire_date = None
        user.save()

        # Clear session
        del request.session['reset_user_id']

        return {}
    
#==================================================================================



class UserRetSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "username",
            "gender",
            "phone_number",
            "birth_date",
            "image",



        )

class ProfileDoctorAndNurseSerializer(serializers.ModelSerializer):
    user = UserRetSerializer(read_only=True)

    class Meta:
        model = DoctorNurseProfile
        fields = (
            "user",
            "id",
            "price",
            "experience_year",
            "about",
            "certificates",
            "offer",
            "services"
        )

class UpdateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "username",
            "gender",
            "phone_number",
            "birth_date",
            "image",
        ) 

class UpdateProfileDoctorAndNurseSerializer(serializers.ModelSerializer):
    user = UpdateUserSerializer()

    class Meta:
        model = DoctorNurseProfile
        fields = (
            "user",
            "id",
            "price",
            "experience_year",
            "about",
            "certificates",
            "offer",
            "services"
        )

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", None)  # Extract user data from request

        if user_data:
            # Update the related user fields
            for attr, value in user_data.items():
                setattr(instance.user, attr, value)
            instance.user.save()

        return super().update(instance, validated_data)

    # def update(self, instance, validated_data):
    #     print("="*100)
    #     print(instance)
    #     print(instance.user)

    #     print(validated_data["user"]["username"])
    #     instance.user.username = validated_data.get("username", instance.user.username)
    #     instance.user.email = validated_data.get("email", instance.user.email)
    #     instance.user.phone_number = validated_data.get("phone_number", instance.user.phone_number)
    #     instance.user.gender = validated_data.get("gender", instance.user.gender)
    #     instance.user.image = validated_data.get("image", instance.user.image)
    #     instance.user.birth_date = validated_data.get("birth_date", instance.user.birth_date)
    #     instance.user.save()

    #     print(instance.user.email)
    #     return instance


class PatientProfileSerializer(serializers.ModelSerializer):
    user = UpdateUserSerializer()

    class Meta:
        model = PatientProfile
        fields = (
            "user",
            "id",
            "chronic_diseases",
        )

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", None)  # Extract user data from request

        if user_data:
            # Update the related user fields
            for attr, value in user_data.items():
                setattr(instance.user, attr, value)
            instance.user.save()

        return super().update(instance, validated_data)
    

class ListDoctorSerializer(serializers.ModelSerializer):
    user = UserRetSerializer()
    specialty = serializers.CharField()
    city = serializers.CharField()


    class Meta:
        model = DoctorNurseProfile
        fields = ('id','user','price','specialty','city','governorate','offer','about',)

class ListNurseSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    image = serializers.SerializerMethodField()
    city = serializers.CharField()

    

    class Meta:
        model = DoctorNurseProfile
        fields = ['user','price','id','about','image','city','governorate',]

    def get_image(self, obj):
        request = self.context.get('request')
        image_url = obj.user.image.url if obj.user.image else None
        if image_url and request:
            return request.build_absolute_uri(image_url)
        return image_url
    
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        data['user_id'] = user.id
        data['user_type'] = user.user_type

        if user.user_type == User.User_Type.PATIENT:
            data['profile_id'] = user.patient_profile.id
        elif user.user_type in [User.User_Type.DOCTOR, User.User_Type.NURSE]:
            data['profile_id'] = user.doctor_profile.id
        else:
            data['profile_id'] = None 

        return data