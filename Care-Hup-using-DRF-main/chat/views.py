from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from users.models import DoctorNurseProfile, PatientProfile
from users.models import User
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Chat, Message
from .Serializers import ChatSerializer, MessageSerializer

class StartChatView(APIView):
    def post(self, request, *args, **kwargs):
        doctor_id = request.data.get('doctor_id')
        patient_id = request.data.get('patient_id')
        nurse_id = request.data.get('nurse_id')

        doctor = get_object_or_404(DoctorNurseProfile, id=doctor_id) if doctor_id else None
        patient = get_object_or_404(PatientProfile, id=patient_id)
        nurse = get_object_or_404(DoctorNurseProfile, id=nurse_id) if nurse_id else None

        chat, created = Chat.objects.get_or_create(doctor=doctor, patient=patient, nurse=nurse)
        return Response(ChatSerializer(chat, context={'request': request}).data, status=status.HTTP_200_OK)

class SendMessageView(APIView):
    def post(self, request, *args, **kwargs):
        chat_id = request.data.get('chat_id')
        sender_id = request.data.get('sender_id')
        content = request.data.get('content')

        if not content:
            return Response({"error": "Message content cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

        chat = get_object_or_404(Chat, id=chat_id)
        sender = get_object_or_404(User, id=sender_id)

        message = Message.objects.create(chat=chat, sender=sender, content=content)
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)

class ChatListView(APIView):
    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get('user_id')
        user = get_object_or_404(User, id=user_id)

        # الحصول على ملف الطبيب/الممرض أو المريض
        doctor_nurse_profile = getattr(user, 'doctor_profile', None)
        patient_profile = getattr(user, 'patient_profile', None)

        # تنفيذ الاستعلام بناءً على نوع المستخدم
        chats = Chat.objects.filter(
            Q(doctor=doctor_nurse_profile) | 
            Q(patient=patient_profile) |  # استخدام PatientProfile بدلًا من User
            Q(nurse=doctor_nurse_profile)
        )

        serialized_chats = ChatSerializer(chats, many=True, context={'request': request}).data
        return Response(serialized_chats, status=status.HTTP_200_OK)


class ChatHistoryView(APIView):
    def get(self, request, *args, **kwargs):
        chat_id = kwargs.get('chat_id')
        chat = get_object_or_404(Chat, id=chat_id)

        messages = chat.messages.order_by('timestamp')
        serialized_messages = MessageSerializer(messages, many=True).data

        if request.user and request.user.is_authenticated:
            chat.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

        return Response(serialized_messages, status=status.HTTP_200_OK)
