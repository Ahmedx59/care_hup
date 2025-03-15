from rest_framework import serializers
from .models import AvailableSlot, Appointment
from users.models import DoctorNurseProfile, PatientProfile

class AvailableSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailableSlot
        fields = ['id', 'doctor', 'date', 'time']

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['id','doctor', 'patient', 'date', 'time']
