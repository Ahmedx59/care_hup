from datetime import date, datetime
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework import serializers
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from notifications.tasks import send_push_notification_task, send_new_appointment_notification
from notifications.tasks import send_cancellation_notification  
from .models import AvailableSlot, Appointment
from users.models import DoctorNurseProfile, PatientProfile, User
from .serializers import (
    AvailableSlotSerializer,
    AppointmentSerializer,
    PatientAppointmentSerializer,
    PatientPastAppointmentsSerializer,
    UpcomingAppointmentsSerializer,
)


# ================ Permissions ================
class IsDoctor(BasePermission):
    """✅ التحقق من أن المستخدم طبيب"""
    def has_permission(self, request, view):
        return request.user.user_type == User.User_Type.DOCTOR


# ================ Doctor Endpoints ================
class AddAvailableSlots(APIView):
    """✅ إضافة مواعيد متاحة للطبيب"""
    permission_classes = [IsAuthenticated, IsDoctor]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'date': openapi.Schema(type=openapi.TYPE_STRING, format="date"),
                    'times': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_STRING, format="time")
                    )
                },
                required=['date', 'times']
            ),
        ),
        responses={
            201: "تم الإضافة بنجاح",
            400: "بيانات غير صالحة",
            403: "غير مصرح به"
        }
    )
    def post(self, request):
        try:
            doctor = request.user.doctor_profile
        except AttributeError:
            return Response(
                {"error": "المستخدم ليس طبيبًا"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        if not isinstance(request.data, list):
            return Response(
                {"error": "يجب إرسال البيانات كقائمة"},
                status=status.HTTP_400_BAD_REQUEST
            )

        slots_to_create = []
        errors = []
        
        for slot_data in request.data:
            date = slot_data.get('date')
            times = slot_data.get('times', [])
            
            if not date or not times:
                errors.append("كل عنصر يجب أن يحتوي على تاريخ وأوقات")
                continue
                
            for time in times:
                if AvailableSlot.objects.filter(
                    doctor=doctor,
                    date=date,
                    time=time
                ).exists():
                    errors.append(f"الموعد {date} - {time} موجود مسبقًا")
                    continue
                    
                slots_to_create.append(AvailableSlot(
                    doctor=doctor,
                    date=date,
                    time=time
                ))

        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        AvailableSlot.objects.bulk_create(slots_to_create, ignore_conflicts=True)
        return Response(
            {"message": "تمت الإضافة بنجاح", "added_slots": len(slots_to_create)},
            status=status.HTTP_201_CREATED
        )


class DoctorAvailableSlots(APIView):
    """✅ عرض المواعيد المتاحة للطبيب"""
    def get(self, request, doctor_id):
        slots = AvailableSlot.objects.filter(doctor_id=doctor_id)
        if not slots:
            return Response(
                {"message": "لا توجد مواعيد متاحة"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = AvailableSlotSerializer(slots, many=True)
        return Response(serializer.data)


class UpdateAvailableSlot(APIView):
    """✅ تحديث موعد متاح"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'date': openapi.Schema(type=openapi.TYPE_STRING, format="date"),
                'time': openapi.Schema(type=openapi.TYPE_STRING, format="time")
            },
            required=['date', 'time']
        )
    )
    def put(self, request, slot_id):
        try:
            slot = AvailableSlot.objects.get(id=slot_id, doctor__user=request.user)
        except AvailableSlot.DoesNotExist:
            return Response(
                {"error": "الموعد غير موجود أو غير مصرح بالتعديل"},
                status=status.HTTP_404_NOT_FOUND
            )

        new_date = request.data.get('date')
        new_time = request.data.get('time')

        if not new_date or not new_time:
            return Response(
                {"error": "يجب إدخال تاريخ ووقت جديدين"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            datetime.strptime(new_date, "%Y-%m-%d")
            datetime.strptime(new_time, "%H:%M")
        except ValueError:
            return Response(
                {"error": "تنسيق غير صحيح (YYYY-MM-DD للتاريخ و HH:MM للوقت)"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if AvailableSlot.objects.filter(
            doctor=slot.doctor, 
            date=new_date, 
            time=new_time
        ).exclude(id=slot.id).exists():
            return Response(
                {"error": "هذا الموعد موجود مسبقًا"},
                status=status.HTTP_400_BAD_REQUEST
            )

        slot.date = new_date
        slot.time = new_time
        slot.save()

        serializer = AvailableSlotSerializer(slot)
        return Response({
            "message": "تم التحديث بنجاح",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class CancelAppointment(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, appointment_id):
        try:
            appointment = Appointment.objects.select_related('doctor__user', 'patient__user').get(
                id=appointment_id,
                patient__user=request.user
            )
        except Appointment.DoesNotExist:
            return Response({"error": "الحجز غير موجود أو غير مصرح به"}, status=status.HTTP_404_NOT_FOUND)

        if appointment.date < date.today():
            return Response({"error": "هذا الموعد قد انتهى ولا يمكن إلغاؤه"}, status=status.HTTP_400_BAD_REQUEST)

        # إرجاع الموعد إلى المواعيد المتاحة
        AvailableSlot.objects.create(
            doctor=appointment.doctor,
            date=appointment.date,
            time=appointment.time
        )

        # 👇 حفظ البيانات المهمة قبل الحذف
        appointment_data = {
            'doctor_id': appointment.doctor.user.id,
            'patient_name': appointment.patient.user.get_full_name() or appointment.patient.user.username,
            'date': str(appointment.date),
            'time': str(appointment.time),
            'appointment_id': appointment.id
        }

        # حذف الحجز
        appointment.delete()

        # إرسال إشعار إلى الدكتور بالخلفية
        send_cancellation_notification.delay(appointment_data)

        return Response({"message": "تم إلغاء الحجز القادم بنجاح"}, status=status.HTTP_200_OK)
# ================ Patient Endpoints ================

class BookAppointment(generics.CreateAPIView):
    """✅ حجز موعد جديد"""
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        try:
            patient = PatientProfile.objects.get(user=self.request.user)
        except PatientProfile.DoesNotExist:
            raise serializers.ValidationError({"error": "المريض غير موجود"})

        doctor_id = self.request.data.get('doctor')
        date = self.request.data.get('date')
        time = self.request.data.get('time')

        if not all([doctor_id, date, time]):
            raise serializers.ValidationError({"error": "بيانات ناقصة"})

        try:
            doctor = DoctorNurseProfile.objects.get(id=int(doctor_id))
        except (ValueError, DoctorNurseProfile.DoesNotExist):
            raise serializers.ValidationError({"error": "طبيب غير موجود"})

        slot = AvailableSlot.objects.filter(
            doctor=doctor, 
            date=date, 
            time=time
        ).first()

        if not slot:
            raise serializers.ValidationError({"error": "الموعد غير متاح"})

        if Appointment.objects.filter(
            doctor=doctor, 
            date=date, 
            time=time
        ).count() >= 3:
            raise serializers.ValidationError({"error": "الموعد مكتمل"})

        # حفظ الموعد
        appointment = serializer.save(doctor=doctor, patient=patient)

        # === إشعار بالخلفية باستخدام Celery ===
        # 1. للمريض
        send_push_notification_task.delay(
            user_id=self.request.user.id,
            title="Appointment Confirmed",
            body=f"Your appointment with Dr. {doctor.user.get_full_name() or doctor.user.username} is scheduled on {date} at {time}",
            data={
                'type': 'appointment_confirmation',
                'appointment_id': str(appointment.id)
            }
        )

        # 2. للطبيب
        send_push_notification_task.delay(
            user_id=doctor.user.id,
            title="New Appointment",
            body=f"{patient.user.get_full_name() or patient.user.username} booked a new appointment on {date} at {time}",
            data={
                'type': 'new_appointment',
                'appointment_id': str(appointment.id)
            }
        )
        # =====================================

        if Appointment.objects.filter(
            doctor=doctor, 
            date=date, 
            time=time
        ).count() >= 3:
            slot.delete()


# ================ Appointment Management ================
class DoctorUpcomingAppointments(APIView):
    """✅ مواعيد الطبيب القادمة"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            doctor = DoctorNurseProfile.objects.get(user=request.user)
        except DoctorNurseProfile.DoesNotExist:
            return Response(
                {"error": "غير مصرح به"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        appointments = Appointment.objects.filter(
            doctor=doctor,
            date__gte=date.today()
        ).select_related('patient').order_by('date', 'time')

        serializer = PatientAppointmentSerializer(appointments, many=True)
        return Response(serializer.data)


class DoctorPastAppointments(APIView):
    """✅ مواعيد الطبيب السابقة"""
    permission_classes = [IsAuthenticated, IsDoctor]

    def get(self, request):
        try:
            doctor = DoctorNurseProfile.objects.get(user=request.user)
        except DoctorNurseProfile.DoesNotExist:
            return Response(
                {"error": "غير مصرح به"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        appointments = Appointment.objects.filter(
            doctor=doctor,
            date__lt=date.today()
        ).select_related('patient').order_by('-date', '-time')

        serializer = PatientAppointmentSerializer(appointments, many=True)
        return Response(serializer.data)


class PatientPastAppointments(APIView):
    """✅ مواعيد المريض السابقة"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            patient = PatientProfile.objects.get(user=request.user)
        except PatientProfile.DoesNotExist:
            return Response(
                {"error": "غير مصرح به"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        appointments = Appointment.objects.filter(
            patient=patient,
            date__lt=date.today()
        ).select_related('doctor__user').order_by('-date', '-time')

        serializer = PatientPastAppointmentsSerializer(appointments, many=True, context={'request': request})
        return Response(serializer.data)


class PatientUpcomingAppointments(APIView):
    """✅ مواعيد المريض القادمة"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            patient = PatientProfile.objects.get(user=request.user)
        except PatientProfile.DoesNotExist:
            return Response(
                {"error": "غير مصرح به"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        appointments = Appointment.objects.filter(
            patient=patient,
            date__gte=date.today()
        ).select_related('doctor__user').order_by('date', 'time')

        serializer = UpcomingAppointmentsSerializer(appointments, many=True, context={'request': request})
        return Response(serializer.data)


class UpdateAppointment(APIView):
    """✅ تحديث الموعد"""
    permission_classes = [IsAuthenticated]

    def get(self, request, appointment_id):
        try:
            appointment = Appointment.objects.get(
                id=appointment_id, 
                patient__user=request.user
            )
        except Appointment.DoesNotExist:
            return Response(
                {"error": "الموعد غير موجود"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        available_slots = AvailableSlot.objects.filter(
            doctor=appointment.doctor, 
            date__gte=date.today()
        ).order_by('date', 'time')

        return Response({
            "appointment": AppointmentSerializer(appointment).data,
            "available_slots": AvailableSlotSerializer(available_slots, many=True).data
        })

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'date': openapi.Schema(type=openapi.TYPE_STRING, format="date"),
                'time': openapi.Schema(type=openapi.TYPE_STRING, format="time")
            }
        )
    )
    def put(self, request, appointment_id):
        try:
            appointment = Appointment.objects.get(
                id=appointment_id, 
                patient__user=request.user
            )
        except Appointment.DoesNotExist:
            return Response(
                {"error": "الموعد غير موجود"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        new_date = request.data.get('date')
        new_time = request.data.get('time')

        if not new_date or not new_time:
            return Response(
                {"error": "يجب إدخال تاريخ ووقت جديدين"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if appointment.date < date.today():
            return Response(
                {"error": "لا يمكن تعديل المواعيد المنتهية"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not AvailableSlot.objects.filter(
            doctor=appointment.doctor,
            date=new_date,
            time=new_time
        ).exists():
            return Response(
                {"error": "الموعد الجديد غير متاح"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # استعادة الموعد القديم
        AvailableSlot.objects.create(
            doctor=appointment.doctor,
            date=appointment.date,
            time=appointment.time
        )

        # تحديث الموعد الجديد
        appointment.date = new_date
        appointment.time = new_time
        appointment.save()

        # حذف الموعد الجديد من المتاح
        AvailableSlot.objects.filter(
            doctor=appointment.doctor,
            date=new_date,
            time=new_time
        ).delete()

        return Response({
            "message": "تم التحديث بنجاح",
            "appointment": AppointmentSerializer(appointment).data
        })
    

class DeleteAvailableSlot(APIView):
    """✅ إلغاء موعد متاح للطبيب (طالما لم يتم حجزه)"""
    permission_classes = [IsAuthenticated, IsDoctor]

    def delete(self, request, slot_id):
        try:
            slot = AvailableSlot.objects.get(id=slot_id, doctor__user=request.user)
        except AvailableSlot.DoesNotExist:
            return Response(
                {"error": "الموعد غير موجود أو غير مصرح بحذفه"},
                status=status.HTTP_404_NOT_FOUND
            )

        # ✅ نتحقق إن محدش حجزه قبل ما نحذفه
        if Appointment.objects.filter(
            doctor=slot.doctor,
            date=slot.date,
            time=slot.time
        ).exists():
            return Response(
                {"error": "لا يمكن حذف الموعد لأنه تم حجزه بالفعل"},
                status=status.HTTP_400_BAD_REQUEST
            )

        slot.delete()
        return Response({"message": "تم حذف الموعد بنجاح"}, status=status.HTTP_200_OK)
