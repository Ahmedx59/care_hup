# notifications/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import FCMDevice
from .tasks import send_push_notification_task  
