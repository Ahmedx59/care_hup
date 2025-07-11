from django.db import models
from users.models import DoctorNurseProfile, PatientProfile

# Model for Available Slots
class AvailableSlot(models.Model):
    doctor = models.ForeignKey(DoctorNurseProfile, on_delete=models.CASCADE, related_name="available_slots")
    date = models.DateField()
    time = models.TimeField()
    max_bookings = models.IntegerField(default=3)  
    def __str__(self):
        return f"{self.doctor.user.username} - {self.date} at {self.time}"

# Model for Appointment
class Appointment(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', 'قيد الانتظار'
        PAID = 'PAID', 'تم الدفع'
        CANCELLED = 'CANCELLED', 'تم الإلغاء'
        FAILED = 'FAILED', 'فشل الدفع'

    paypal_order_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    payment_status = models.CharField(max_length=20,choices=PaymentStatus.choices,default=PaymentStatus.PENDING)
    PAYMENT_METHODS = (
        ('paypal', 'PayPal'),
        ('cash', 'كاش في العيادة'),
    )
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='paypal')

    doctor = models.ForeignKey(DoctorNurseProfile, on_delete=models.CASCADE)
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    reminder_sent = models.BooleanField(default=False)  

    def __str__(self):
        return f"{self.patient.user.username} with {self.doctor.user.username} on {self.date} at {self.time}"
