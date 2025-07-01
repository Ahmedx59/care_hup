# notifications/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import FCMDevice
from .serializers import FCMDeviceSerializer

class RegisterDeviceView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=FCMDeviceSerializer,
        responses={
            201: "تم تسجيل الجهاز بنجاح",
            400: "طلب غير صالح"
        }
    )
    def post(self, request):
        serializer = FCMDeviceSerializer(data=request.data)
        if serializer.is_valid():
            # حذف التسجيل القديم إن وجد
            FCMDevice.objects.filter(
                registration_id=serializer.validated_data['registration_id']
            ).delete()

            FCMDevice.objects.create(
                user=request.user,
                **serializer.validated_data
            )
            return Response({"status": "success"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)