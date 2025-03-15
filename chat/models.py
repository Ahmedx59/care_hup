from django.db import models
from users.models import User, DoctorNurseProfile, PatientProfile

class Chat(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE)
    doctor = models.ForeignKey(DoctorNurseProfile, null=True, blank=True, on_delete=models.SET_NULL)
    nurse = models.ForeignKey(DoctorNurseProfile, related_name='nurse_chats', null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    participants = models.ManyToManyField(User, related_name='chats')

    class Meta:
        unique_together = [['patient', 'doctor'], ['patient', 'nurse']]

    def __str__(self):
        return f"Chat {self.id}"


class Message(models.Model):
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:30]}"