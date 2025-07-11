from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework import serializers
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from api.models import Appointment
from users.models import DoctorNurseProfile, PatientProfile, User
from payment_subscribe.serializers import (
    SubscriptionStatusSerializer
)
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from rest_framework.status import HTTP_200_OK, HTTP_403_FORBIDDEN
from django.conf import settings
import requests



#######################################################################################

def get_paypal_access_token():
    url = f"{settings.PAYPAL_BASE_URL}/v1/oauth2/token"
    auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET)
    response = requests.post(url, data={'grant_type': 'client_credentials'}, auth=auth)
    response.raise_for_status()
    return response.json()['access_token']

class PaypalOrderStatusView(APIView):
    @swagger_auto_schema(
        operation_description="🔎 التحقق من حالة طلب PayPal باستخدام order_id",
        manual_parameters=[
            openapi.Parameter(
                'order_id',
                openapi.IN_PATH,
                description="معرّف الطلب من PayPal",
                type=openapi.TYPE_STRING
            )
        ],
        responses={
            200: openapi.Response(description="تم الدفع بنجاح"),
            400: openapi.Response(description="فشل الدفع أو الطلب غير مكتمل")
        }
    )
    def get(self, request, order_id):
        access_token = get_paypal_access_token()
        url = f"{settings.PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/capture"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

        response = requests.post(url, headers=headers)
        result = response.json()

        if response.status_code == 201 and result.get('status') == 'COMPLETED':
            return Response({
                "status": "success",
                "order_id": order_id,
                "details": result
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": "error",
                "message": "Payment not completed",
                "paypal_response": result
            }, status=status.HTTP_400_BAD_REQUEST)
        

###########################################################################


class CreatePaypalOrderView(APIView):
    @swagger_auto_schema(
        operation_description="🔄 إنشاء طلب دفع PayPal جديد بناءً على موعد",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'appointment_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="رقم الموعد")
            },
            required=['appointment_id']
        ),
        responses={
            200: openapi.Response(description="تم إنشاء الطلب وإرجاع رابط الدفع"),
            400: "خطأ في البيانات أو فشل الاتصال بـ PayPal"
        }
    )
    def post(self, request):
        appointment_id = request.data.get('appointment_id')
        if not appointment_id:
            return Response({'error': 'appointment_id مطلوب'}, status=status.HTTP_400_BAD_REQUEST)

        # جلب الموعد وسعر الدكتور
        try:
            appointment = Appointment.objects.get(id=appointment_id, patient__user=request.user)
            amount = appointment.doctor.price
        except Appointment.DoesNotExist:
            return Response({'error': 'الموعد غير موجود أو غير مرخص'}, status=status.HTTP_404_NOT_FOUND)

        # جلب التوكن
        access_token = get_paypal_access_token()
        url = f"{settings.PAYPAL_BASE_URL}/v2/checkout/orders"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

        data = {
            "intent": "AUTHORIZE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": "EUR",
                        "value": str(amount)
                    }
                }
            ],
            "application_context": {
                "return_url": "https://2d4850971ef1.ngrok-free.app/payment_subscribe/payment/success/",
                "cancel_url": "https://2d4850971ef1.ngrok-free.app/payment_subscribe/payment/cancel/"
            }
        }

        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        if response.status_code == 201:
            order_id = result.get('id')
            approval_url = next((link['href'] for link in result['links'] if link['rel'] == 'approve'), None)

            appointment.paypal_order_id = order_id
            appointment.save()
            print(f"🔗 تم ربط الموعد بالطلب: {order_id}")

            return Response({
                'status': 'success',
                'order_id': order_id,
                'approval_url': approval_url
            })

        return Response({
            'status': 'error',
            'paypal_response': result
        }, status=status.HTTP_400_BAD_REQUEST)




def paypal_payment_success(request):
    token = request.GET.get('token')
    if not token:
        return HttpResponse(" لا يوجد معرف الطلب")

    try:
        appointment = Appointment.objects.get(paypal_order_id=token)
    except Appointment.DoesNotExist:
        appointment = None

    
    if appointment:
        appointment.payment_status = Appointment.PaymentStatus.PENDING
        appointment.save()

    return HttpResponse(" 'paypal'تم استلام طلب الدفع بنجاح,سيتم تأكيد الدفع فور معالجته من")






def paypal_payment_cancel(request):
    token = request.GET.get('token')
    if token:
        try:
            appointment = Appointment.objects.get(paypal_order_id=token)
            appointment.payment_status = Appointment.PaymentStatus.CANCELLED
            appointment.save()
        except Appointment.DoesNotExist:
            pass
    return HttpResponse("❌ تم إلغاء الدفع من قبل المستخدم")




@csrf_exempt
def paypal_webhook(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        event = json.loads(request.body)
        event_type = event.get("event_type")
        resource = event.get("resource", {})

        if event_type == "PAYMENT.CAPTURE.COMPLETED":
            order_id = resource.get("supplementary_data", {}).get("related_ids", {}).get("order_id")

            if not order_id:
                print("❗ Order ID غير موجود في الـ Webhook")
                return JsonResponse({'error': 'Order ID not found'}, status=400)

            try:
                appointment = Appointment.objects.get(paypal_order_id=order_id)
                appointment.payment_status = Appointment.PaymentStatus.PAID
                appointment.save()
                print(f"✅ تم تحديث حالة الدفع للموعد: {appointment.id}")
            except Appointment.DoesNotExist:
                print("❗ لم يتم العثور على موعد مرتبط بـ Order ID:", order_id)

        return JsonResponse({'status': 'received'}, status=200)

    except Exception as e:
        print("❌ خطأ أثناء معالجة Webhook:", str(e))
        return JsonResponse({'error': 'Invalid payload'}, status=400)





##################الاشتراك ######################################

class IsDoctor(BasePermission):
    """✅ التحقق من أن المستخدم طبيب"""
    def has_permission(self, request, view):
        return request.user.user_type == User.User_Type.DOCTOR

class CreateDoctorSubscriptionView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

    def post(self, request):
        doctor = request.user.doctor_profile
        subscription_fee = 10  # تقدر تعدل السعر

        # 1. الحصول على access token
        access_token = get_paypal_access_token()
        url = f"{settings.PAYPAL_BASE_URL}/v2/checkout/orders"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

        # 2. تحضير بيانات الطلب
        data = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": "EUR",
                        "value": str(subscription_fee)
                    }
                }
            ],
            "application_context": {
                "return_url": "https://2d4850971ef1.ngrok-free.app/payment_subscribe/subscription/success/",
                "cancel_url": "https://2d4850971ef1.ngrok-free.app/payment_subscribe/subscription/cancel/"
            }
        }

        # 3. إنشاء الطلب
        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        if response.status_code == 201:
            order_id = result.get('id')
            doctor.paypal_order_id = order_id
            doctor.subscription_status = DoctorNurseProfile.SubscriptionStatus.PENDING
            doctor.save()

            approval_url = next(link['href'] for link in result['links'] if link['rel'] == 'approve')
            return Response({"payment_url": approval_url})

        return Response({"error": "فشل في إنشاء الطلب", "details": result}, status=400)


###########################3
@csrf_exempt
def paypal_webhook_subscription(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        event = json.loads(request.body)
        if event.get("event_type") == "PAYMENT.CAPTURE.COMPLETED":
            order_id = event.get("resource", {}).get("supplementary_data", {}).get("related_ids", {}).get("order_id")
            doctor = DoctorNurseProfile.objects.filter(paypal_order_id=order_id).first()
            if doctor:
                doctor.subscription_status = DoctorNurseProfile.SubscriptionStatus.ACTIVE
                doctor.save()
                print(f"✅ تم تفعيل اشتراك الدكتور: {doctor.id}")
            else:
                print("❗ لم يتم العثور على الدكتور")
        return JsonResponse({'status': 'received'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    
##################


class DoctorSubscriptionStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # تأكد إن المستخدم دكتور أو ممرض
        if user.user_type not in [user.User_Type.DOCTOR, user.User_Type.NURSE]:
            return Response({'error': 'غير مصرح به'}, status=HTTP_403_FORBIDDEN)

        try:
            profile = user.doctor_profile
            serializer = SubscriptionStatusSerializer(profile)
            return Response(serializer.data, status=HTTP_200_OK)
        except DoctorNurseProfile.DoesNotExist:
            return Response({'error': 'الملف غير موجود'}, status=404)
        


@csrf_exempt
def subscription_success(request):
    return HttpResponse("✅ تم استلام طلب الدفع بنجاح! سيتم تفعيل اشتراكك قريبًا.")

@csrf_exempt
def subscription_cancel(request):
    return HttpResponse("❌ تم إلغاء الدفع من قبل المستخدم.")

#################نهايه الاشتراك ##############################