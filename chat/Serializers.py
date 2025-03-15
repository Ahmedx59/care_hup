from rest_framework import serializers
from .models import Chat, Message

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'

class ChatSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ['id', 'doctor', 'patient', 'nurse', 'created_at', 'last_message', 'unread_count']

    def get_last_message(self, obj):
        last_message = obj.messages.order_by('-timestamp').first()
        if last_message:
            return {
                "content": last_message.content,
                "sender": last_message.sender.username,
                "timestamp": last_message.timestamp,
            }
        return None

    def get_unread_count(self, obj):
        request_user = self.context.get('request').user
        return obj.messages.filter(is_read=False).exclude(sender=request_user).count()
