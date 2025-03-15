from django.db import models
from users.models import DoctorNurseProfile, PatientProfile

# Model for Available Slots
class AvailableSlot(models.Model):
    doctor = models.ForeignKey(DoctorNurseProfile, on_delete=models.CASCADE, related_name="available_slots")
    date = models.DateField()
    time = models.TimeField()

    def __str__(self):
        return f"{self.doctor.user.username} - {self.date} at {self.time}"

# Model for Appointment
class Appointment(models.Model):
    doctor = models.ForeignKey(DoctorNurseProfile, on_delete=models.CASCADE)
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()

    def __str__(self):
        return f"{self.patient.user.username} with {self.doctor.user.username} on {self.date} at {self.time}"
