from rest_framework import serializers
from .models import AvailableSlot, Appointment, PatientProfile
from users.models import DoctorNurseProfile, SpecialtyDoctor

# ✅ تسلسل بيانات الطبيب
class DoctorSerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField()
    def get_doctor_name(self, obj):
        return obj.user.get_full_name()
    specialty = serializers.CharField(source='specialty.name', required=False, allow_null=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = DoctorNurseProfile
        fields = ['id', 'doctor_name', 'specialty', 'image']

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.user.image:
            return request.build_absolute_uri(obj.user.image.url)
        return None

# ✅ تسلسل بيانات المواعيد المتاحة
class AvailableSlotSerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField()
    def get_doctor_name(self, obj):
        return obj.doctor.user.get_full_name()
    specialty = serializers.CharField(source='doctor.specialty.name', required=False, allow_null=True)

    
    class Meta:
        model = AvailableSlot
        fields = ['id', 'date', 'time','doctor_name','specialty']

# ✅ تسلسل بيانات المواعيد
class AppointmentSerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField()

    def get_doctor_name(self, obj):
        return obj.doctor.user.get_full_name()  
     # specialty = serializers.CharField(source='doctor.specialty.name', required=False, allow_null=True)

    class Meta:
        model = Appointment
        fields = ['id', 'doctor', 'doctor_name',  'date', 'time']


# ✅ تسلسل بيانات المواعيد الخاصة بالمريض
class PatientAppointmentSerializer(serializers.ModelSerializer):
    patient_id = serializers.IntegerField(source='patient.user.id')
    patient_name = serializers.SerializerMethodField()

    def get_patient_name(self, obj):
        return obj.patient.user.get_full_name()
    phone_number = serializers.CharField(source='patient.user.phone_number')

    class Meta:
        model = Appointment
        fields = [
            'id',
            'doctor',
            'date',
            'time',
            'patient_id',
            'patient_name',
            'phone_number'
            
        ]

# ✅ تسلسل بيانات المواعيد السابقة للمريض
class PatientPastAppointmentsSerializer(serializers.ModelSerializer):
    doctor = serializers.SerializerMethodField()
    patient_id = serializers.IntegerField(source='patient.user.id')

    class Meta:
        model = Appointment
        fields = [
            'id',
            'patient_id',
            'date',
            'time',
            'doctor'
        ]
    
    def get_doctor(self, obj):
        request = self.context.get('request') 
        doctor = obj.doctor
        image_url = request.build_absolute_uri(doctor.user.image.url) if doctor.user.image else None
        return {

            "doctor_id": doctor.id,
            "doctor_name": doctor.user.get_full_name(),
            "specialty": doctor.specialty.name if doctor.specialty else "No specialty",
            "image": image_url 


        }

# ✅ تسلسل بيانات المواعيد القادمة مع معلومات الطبيب
class UpcomingAppointmentsSerializer(serializers.ModelSerializer):
    doctor = DoctorSerializer() 

    class Meta:
        model = Appointment
        fields = [
            'id',
            'date',
            'time',
            'doctor'
        ]
