from django.db import models
from users.models import User

class FCMDevice(models.Model):
    DEVICE_TYPE_CHOICES = [
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('web', 'Web'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    registration_id = models.TextField()
    device_type = models.CharField(max_length=10, choices=DEVICE_TYPE_CHOICES)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'registration_id')  
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.device_type}"
