from django.db import models
from users.models import DoctorNurseProfile, PatientProfile
from users.models import User

class Chat(models.Model):
    doctor = models.ForeignKey(DoctorNurseProfile, related_name='doctor_chats', null=True, blank=True, on_delete=models.CASCADE)
    patient = models.ForeignKey(PatientProfile, related_name='patient_chats', on_delete=models.CASCADE)
    nurse = models.ForeignKey(DoctorNurseProfile, related_name='nurse_chats', null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class Message(models.Model):
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username}: {self.content[:30]}"