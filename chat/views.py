from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Chat, Message
from .serializers import ChatSerializer, MessageSerializer
from users.models import User, DoctorNurseProfile, PatientProfile
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from notifications.tasks import send_new_chat_notification

class StartChatView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['target_id'],
            properties={
                'target_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            },
        ),
        responses={201: ChatSerializer, 400: "Bad Request"}
    )
    def post(self, request):
        user = request.user

        if not hasattr(user, 'patient_profile'):
            return Response(
                {"error": "Only patients can start a chat."},
                status=status.HTTP_403_FORBIDDEN
            )

        target_id = request.data.get('target_id')

        try:
            target_profile = get_object_or_404(DoctorNurseProfile, id=target_id)

            chat, created = Chat.objects.get_or_create(
                patient=user.patient_profile,
                doctor=target_profile if target_profile.user.user_type == User.User_Type.DOCTOR else None,
                nurse=target_profile if target_profile.user.user_type == User.User_Type.NURSE else None
            )

            chat.participants.add(user, target_profile.user)

            return Response(
                ChatSerializer(chat, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SendMessageView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['chat_id', 'content'],
            properties={
                'chat_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'content': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={201: MessageSerializer, 400: "Bad Request"}
    )
    def post(self, request):
        chat_id = request.data.get('chat_id')
        content = request.data.get('content')
        
        chat = get_object_or_404(Chat, id=chat_id)

        if request.user not in chat.participants.all():
            return Response(
                {"error": "You are not a participant in this chat."},
                status=status.HTTP_403_FORBIDDEN
            )

        message = Message.objects.create(
            chat=chat,
            sender=request.user,
            content=content
        )
        
        # إرسال الإشعار في الخلفية باستخدام Celery
        send_new_chat_notification.delay(message.id)

        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)


class ChatListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        chats = Chat.objects.filter(participants=user).prefetch_related(
            'messages',
            'participants',
            'doctor__user',
            'nurse__user',
            'patient__user'
        ).distinct()
        
        return Response(ChatSerializer(
            chats,
            many=True,
            context={'request': request}
        ).data)


class ChatHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, chat_id):
        user = request.user
        chat = get_object_or_404(Chat, id=chat_id)

        chat.messages.exclude(sender=user).update(is_read=True)

        messages = chat.messages.all()
        return Response(MessageSerializer(messages, many=True).data)
