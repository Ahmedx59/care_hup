# notifications/models.py
from django.db import models
from users.models import User

class FCMDevice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    registration_id = models.TextField()
    device_type = models.CharField(max_length=10)  # e.g., "android", "ios"
    active = models.BooleanField(default=True)  
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.device_type}"