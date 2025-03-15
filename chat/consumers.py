from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, ChatMessage
from .Serializers import ChatMessageSerializer
import json

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.user = self.scope['user']
        
        if await self.validate_participation():
            await self.channel_layer.group_add(
                f"chat_{self.room_id}",
                self.channel_name
            )
            await self.accept()
        else:
            await self.close()

    @database_sync_to_async
    def validate_participation(self):
        return ChatRoom.objects.filter(
            id=self.room_id,
            participants=self.user
        ).exists()

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'send_message':
            await self.handle_message(data)
        elif action == 'get_history':
            await self.send_history()
        elif action == 'mark_read':
            await self.mark_messages_read()

    @database_sync_to_async
    def create_message(self, content):
        room = ChatRoom.objects.get(id=self.room_id)
        message = ChatMessage.objects.create(
            room=room,
            sender=self.user,
            content=content
        )
        return message

    async def handle_message(self, data):
        message = await self.create_message(data['content'])
        serializer = ChatMessageSerializer(message)
        
        await self.channel_layer.group_send(
            f"chat_{self.room_id}",
            {
                'type': 'chat_message',
                'message': serializer.data
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['message']))

    @database_sync_to_async
    def get_messages(self):
        return list(ChatMessage.objects.filter(room_id=self.room_id).order_by('timestamp'))

    async def send_history(self):
        messages = await self.get_messages()
        serializer = ChatMessageSerializer(messages, many=True)
        await self.send(text_data=json.dumps({
            'action': 'history',
            'data': serializer.data
        }))

    @database_sync_to_async
    def mark_messages_read(self):
        ChatMessage.objects.filter(
            room_id=self.room_id,
            is_read=False
        ).exclude(sender=self.user).update(is_read=True)