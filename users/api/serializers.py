from uuid import uuid4


from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.core.validators import MinLengthValidator
from django.conf import settings
from django.contrib.auth.hashers import  check_password
from django.utils import timezone

from rest_framework import serializers

from random import randint
from datetime import datetime , timedelta
   
from users.models import User , DoctorNurseProfile ,PatientProfile , City , Governorate , SpecialtyDoctor


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
    gender = serializers.CharField(required = True)
    phone_number = serializers.IntegerField(required = True)
    birth_date = serializers.DateTimeField(required = True)
    class Meta:
        model = PatientProfile
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
    phone_number = serializers.IntegerField()
    birth_date = serializers.DateTimeField()
    
    class Meta:
        model = DoctorNurseProfile
        exclude = ('user',)
             
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'error':'the passwords do not match'})
        email_user = User.objects.filter(email = attrs['email']).first()
        if email_user :
            raise serializers.ValidationError({'detail':'this email is existed'})
        return super().validate(attrs)

    def create(self, validated_data):
        
        validated_data.pop('confirm_password')
        validated_data['is_active'] = False
        validated_data['activation_code'] = randint(1000,9999)

        certificates = validated_data.pop('certificates')
        about = validated_data.pop('about')
        experience_year = validated_data.pop('experience_year')
        price = validated_data.pop('price')
        specialty = validated_data.pop('specialty')
        city = validated_data.pop('city')

        send_mail(
            f"Activation Code ",
            f"welcome {validated_data['username']}\n Here is the activation code : {validated_data['activation_code']}.",
            settings.EMAIL_HOST_USER,
            {validated_data['email']},
            fail_silently=False,
        )
        user = User.objects.create_user(**validated_data)
        user_profile = DoctorNurseProfile.objects.filter(user = user).first()
        user_profile.price = price
        user_profile.experience_year = experience_year
        user_profile.about = about
        user_profile.certificates = certificates
        user_profile.specialty = specialty
        user_profile.city = city
        user_profile.save()

        return {}

        
    


class UserActivateSerializers(serializers.Serializer):
    code = serializers.CharField(required=True , write_only=True )

    def create(self, validated_data):
        user_id = self.context['view'].kwargs['pk']
        user = User.objects.get(id=user_id)
        if user.activation_code != validated_data['code']:
            raise serializers.ValidationError({'detail':'invalid Code'})
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

    def create(self, validated_data):
        user = User.objects.filter(email = validated_data['email']).first()
        if not user:
            raise serializers.ValidationError({'detail':'not found'})
        
        user.reset_pass_token = get_random_string(10)
        user.reset_pass_expire_date = datetime.now() + timedelta(minutes=30)
        user.save()

        send_mail(
            f"Activation Code ",
            f"welcome {user.username}\n click this link to reset password : http://127.0.0.1:8000/api/user/confirm_reset_password/{user.reset_pass_token}.",
            settings.EMAIL_HOST_USER,
            {validated_data['email']},
            fail_silently=False,
        )
        return {}

class ConfirmResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(required = True , validators=[MinLengthValidator(8)])
    confirm_password = serializers.CharField(required = True)


    def create(self, validated_data):
        token = self.context['view'].kwargs['token']
        user = User.objects.filter(reset_pass_token = token).first()
        if not user: 
            raise serializers.ValidationError({'detail':'user not found'})
        
        if user.reset_pass_expire_date < timezone.now():
            raise serializers.ValidationError({'message':'token is expired'})
        
        if validated_data['password'] != validated_data['confirm_password']:
            raise serializers.ValidationError({'detail':'the passwords not confirm'}) 
        
        user.set_password(validated_data['password'])
        user.save()
        return {}
    
class UserRetSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "gender",
            "phone_number",
            "birth_date",
        )


class ProfileDoctorAndNurseSerializer(serializers.ModelSerializer):
    user = UserRetSerializer()

    class Meta:
        model = DoctorNurseProfile
        fields = (
            "user",
            "id",
            "price",
            "experience_year",
            "about",
            "certificates",
        )


class PatientProfileSerializer(serializers.ModelSerializer):
    user = UserRetSerializer()

    class Meta:
        model = PatientProfile
        fields = (
            "user",
            "id",
            "chronic_diseases",
        )
    

class ListDoctorSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = DoctorNurseProfile
        fields = ('user','price','specialty','city',)

class ListNurseSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = DoctorNurseProfile
        fields = ['user','price']


class UsersGovernorateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Governorate
        fields = '__all__'


class UsersCitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = '__all__'