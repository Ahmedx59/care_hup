from rest_framework import serializers
from .models import Chat, Message
from users.models import User
from django.utils import timezone
from datetime import timedelta
import pytz


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    timestamp = serializers.SerializerMethodField()  

    class Meta:
        model = Message
        fields = ['id', 'content', 'timestamp', 'is_read', 'sender_name']

    def get_sender_name(self, obj):
        return obj.sender.get_full_name()

    def get_timestamp(self, obj):
        egypt_tz = pytz.timezone("Africa/Cairo")
        local_time = obj.timestamp.astimezone(egypt_tz)
        now = timezone.now().astimezone(egypt_tz)

        if local_time.date() == now.date():
            return f"Today at {local_time.strftime('%I:%M %p')}"
        elif local_time.date() == (now - timedelta(days=1)).date():
            return f"Yesterday at {local_time.strftime('%I:%M %p')}"
        else:
            return local_time.strftime("%b %d at %I:%M %p")


class ChatSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    
    class Meta:
        model = Chat
        fields = [
            'id',
            'created_at',
            'other_user',
            'last_message',
            'unread_count'
        ]
    
    def get_other_user(self, obj):
        request = self.context.get('request')
        user = request.user
        
        if user == obj.patient.user:
            target = obj.doctor or obj.nurse
            user_type = 'Doctor' if obj.doctor else 'Nurse'
        else:
            target = obj.patient
            user_type = 'Patient'
        
        return {
            "id": target.user.id,
            "name": target.user.get_full_name(),
            "type": user_type,
            "image": self._get_user_image_url(target.user, request)
        }
    
    def get_last_message(self, obj):
        last_message = obj.messages.first()
        if last_message:
            egypt_tz = pytz.timezone("Africa/Cairo")
            local_time = last_message.timestamp.astimezone(egypt_tz)
            now = timezone.now().astimezone(egypt_tz)

            if local_time.date() == now.date():
                formatted_time = f"Today at {local_time.strftime('%I:%M %p')}"
            elif local_time.date() == (now - timedelta(days=1)).date():
                formatted_time = f"Yesterday at {local_time.strftime('%I:%M %p')}"
            else:
                formatted_time = local_time.strftime("%b %d at %I:%M %p")

            return {
                "content": last_message.content,
                "timestamp": formatted_time,
                "is_read": last_message.is_read,
                "sender_id": last_message.sender.id
            }
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        return obj.messages.exclude(sender=request.user).filter(is_read=False).count()
    
    def _get_user_image_url(self, user, request):
        if user.image:
            return request.build_absolute_uri(user.image.url)
        return None
