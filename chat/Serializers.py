from rest_framework import serializers
from .models import Chat, Message
from users.models import User

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.username', read_only=True)
    timestamp = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    
    class Meta:
        model = Message
        fields = ['id', 'content', 'timestamp', 'is_read', 'sender_name']

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
        
        # تحديد الطرف الآخر
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
            return {
                "content": last_message.content,
                "timestamp": last_message.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
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