from rest_framework import serializers
from .models import AvailableSlot, Appointment, PatientProfile
from users.models import DoctorNurseProfile, SpecialtyDoctor

# ✅ تسلسل بيانات الطبيب
class DoctorSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='user.username')
    specialty = serializers.CharField(source='specialty.name', required=False, allow_null=True)

    class Meta:
        model = DoctorNurseProfile
        fields = ['id', 'doctor_name', 'specialty']

# ✅ تسلسل بيانات المواعيد المتاحة
class AvailableSlotSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.user.username', read_only=True)
    specialty = serializers.CharField(source='doctor.specialty.name', required=False, allow_null=True)

    
    class Meta:
        model = AvailableSlot
        fields = ['id', 'date', 'time','doctor_name','specialty']

# ✅ تسلسل بيانات المواعيد
class AppointmentSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.user.username', read_only=True)
   # specialty = serializers.CharField(source='doctor.specialty.name', required=False, allow_null=True)

    class Meta:
        model = Appointment
        fields = ['id', 'doctor', 'doctor_name',  'date', 'time']


# ✅ تسلسل بيانات المواعيد الخاصة بالمريض
class PatientAppointmentSerializer(serializers.ModelSerializer):
    patient_id = serializers.IntegerField(source='patient.user.id')
    patient_name = serializers.CharField(source='patient.user.username')
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
        doctor = obj.doctor
        return {
            "doctor_id": doctor.id,
            "doctor_name": doctor.user.username,
            "specialty": doctor.specialty.name if doctor.specialty else "No specialty"
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
