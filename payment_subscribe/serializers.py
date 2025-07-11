from rest_framework import serializers
from api.models import AvailableSlot, Appointment, PatientProfile
from users.models import DoctorNurseProfile, SpecialtyDoctor


class AppointmentSerializer(serializers.ModelSerializer):
    payment_method = serializers.ChoiceField(
        choices=[('cash', 'Cash at Clinic'), ('paypal', 'PayPal')],
        write_only=True  # علشان يظهر فقط في الإدخال، مش في الإخراج (اختياري)
    )

    class Meta:
        model = Appointment
        fields = ['id', 'doctor', 'patient', 'date', 'time', 'payment_method', 'payment_status']
        read_only_fields = ['patient', 'payment_status']  # عشان يتحكم فيه الـ View مش المستخدم

class SubscriptionStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorNurseProfile
        fields = ['subscription_status', 'paypal_order_id']
