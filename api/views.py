from datetime import date, datetime
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework import serializers
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import AvailableSlot, Appointment
from users.models import DoctorNurseProfile, PatientProfile, User
from .serializers import (
    AvailableSlotSerializer,
    AppointmentSerializer,
    PatientAppointmentSerializer,
    PatientPastAppointmentsSerializer,
    UpcomingAppointmentsSerializer
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

        serializer.save(doctor=doctor, patient=patient)

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
        ).select_related('doctor__user', 'doctor__specialty').order_by('-date', '-time')

        serializer = PatientPastAppointmentsSerializer(appointments, many=True)
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
        ).select_related('doctor__user', 'doctor__specialty').order_by('date', 'time')

        serializer = UpcomingAppointmentsSerializer(appointments, many=True)
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