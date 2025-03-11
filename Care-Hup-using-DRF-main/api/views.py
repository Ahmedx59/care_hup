from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import AvailableSlot, Appointment
from users.models import DoctorNurseProfile, PatientProfile
from .serializers import AvailableSlotSerializer, AppointmentSerializer

# إضافة مواعيد للطبيب
class AddAvailableSlots(APIView):
    def post(self, request, doctor_id):
        try:
            doctor = DoctorNurseProfile.objects.get(id=doctor_id)
        except DoctorNurseProfile.DoesNotExist:
            return Response({"error": "Doctor not found"}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        days_and_times = data.get('days_and_times')  # قائمة الأيام والساعات

        if not days_and_times:
            return Response({"error": "Days and times are required"}, status=status.HTTP_400_BAD_REQUEST)

        for entry in days_and_times:
            date = entry.get('date')  
            times = entry.get('times')  

            if not date or not times:
                return Response({"error": "Each day must have a date and times"}, status=status.HTTP_400_BAD_REQUEST)

            for time in times:
                AvailableSlot.objects.create(doctor=doctor, date=date, time=time)

        return Response({"message": "Slots added successfully"}, status=status.HTTP_201_CREATED)

# عرض المواعيد المتاحة للطبيب
class DoctorAvailableSlots(APIView):
    def get(self, request, doctor_id):
        slots = AvailableSlot.objects.filter(doctor_id=doctor_id)
        if not slots:
            return Response({"message": "No available slots for this doctor."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = AvailableSlotSerializer(slots, many=True)
        return Response(serializer.data)

# تعديل موعد متاح
class UpdateAvailableSlot(APIView):
    def put(self, request, slot_id):
        try:
            slot = AvailableSlot.objects.get(id=slot_id)
        except AvailableSlot.DoesNotExist:
            return Response({"error": "Slot not found"}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        new_date = data.get('date')
        new_time = data.get('time')

        if not new_date or not new_time:
            return Response({"error": "Date and time are required"}, status=status.HTTP_400_BAD_REQUEST)

        slot.date = new_date
        slot.time = new_time
        slot.save()

        slot_serializer = AvailableSlotSerializer(slot)
        return Response({"message": "Slot updated successfully", "slot": slot_serializer.data}, status=status.HTTP_200_OK)


# حجز موعد للمريض
class BookAppointment(APIView):
    def post(self, request):
        data = request.data
        doctor_id = data.get('doctor_id')
        patient_id = data.get('patient_id')
        date = data.get('date')
        time = data.get('time')

        try:
            doctor = DoctorNurseProfile.objects.get(id=doctor_id)
        except DoctorNurseProfile.DoesNotExist:
            return Response({"error": "Doctor not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            patient = PatientProfile.objects.get(id=patient_id)
        except PatientProfile.DoesNotExist:
            return Response({"error": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)

        slot_exists = AvailableSlot.objects.filter(doctor=doctor, date=date, time=time).exists()
        if not slot_exists:
            return Response({"error": "Slot not available"}, status=status.HTTP_400_BAD_REQUEST)

        appointment = Appointment.objects.create(doctor=doctor, patient=patient, date=date, time=time)
        AvailableSlot.objects.filter(doctor=doctor, date=date, time=time).delete()

        appointment_serializer = AppointmentSerializer(appointment)
        return Response({"message": "Appointment booked successfully", "appointment": appointment_serializer.data}, status=status.HTTP_201_CREATED)

# عرض المواعيد القادمة للطبيب
class DoctorUpcomingAppointments(APIView):
    def get(self, request, doctor_id):
        now = datetime.now()
        upcoming_appointments = Appointment.objects.filter(doctor_id=doctor_id, date__gte=now).order_by('date', 'time')

        if not upcoming_appointments:
            return Response({"message": "No upcoming appointments."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AppointmentSerializer(upcoming_appointments, many=True)
        return Response(serializer.data)

# عرض المواعيد السابقة للطبيب
class DoctorPastAppointments(APIView):
    def get(self, request, doctor_id):
        now = datetime.now()
        past_appointments = Appointment.objects.filter(doctor_id=doctor_id, date__lt=now).order_by('-date', '-time')

        if not past_appointments:
            return Response({"message": "No past appointments."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AppointmentSerializer(past_appointments, many=True)
        return Response(serializer.data)

# عرض المواعيد القادمة للمريض
class PatientUpcomingAppointments(APIView):
    def get(self, request, patient_id):
        now = datetime.now()
        upcoming_appointments = Appointment.objects.filter(patient_id=patient_id, date__gte=now).order_by('date', 'time')

        if not upcoming_appointments:
            return Response({"message": "No upcoming appointments."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AppointmentSerializer(upcoming_appointments, many=True)
        return Response(serializer.data)

# عرض المواعيد السابقة للمريض
class PatientPastAppointments(APIView):
    def get(self, request, patient_id):
        now = datetime.now()
        past_appointments = Appointment.objects.filter(patient_id=patient_id, date__lt=now).order_by('-date', '-time')

        if not past_appointments:
            return Response({"message": "No past appointments."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AppointmentSerializer(past_appointments, many=True)
        return Response(serializer.data)
# تعديل موعد
class UpdateAppointment(APIView):
    def put(self, request, appointment_id):
        try:
            # محاولة الحصول على الحجز باستخدام appointment_id
            appointment = Appointment.objects.get(id=appointment_id)
        except Appointment.DoesNotExist:
            return Response({"error": "Appointment not found"}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        new_date = data.get('date')
        new_time = data.get('time')

        if not new_date or not new_time:
            return Response({"error": "Date and time are required"}, status=status.HTTP_400_BAD_REQUEST)

        # تحديث الحجز
        appointment.date = new_date
        appointment.time = new_time
        appointment.save()

        appointment_serializer = AppointmentSerializer(appointment)
        return Response({"message": "Appointment updated successfully", "appointment": appointment_serializer.data})

    def put(self, request, appointment_id):
        data = request.data
        date = data.get('date')
        time = data.get('time')

        try:
            appointment = Appointment.objects.get(id=appointment_id)
        except Appointment.DoesNotExist:
            return Response({"error": "Appointment not found"}, status=status.HTTP_404_NOT_FOUND)

        # تحقق من أن الموعد هو موعد قادم
        if appointment.date < datetime.now().date():
            return Response({"error": "You cannot modify past appointments."}, status=status.HTTP_400_BAD_REQUEST)

        # تحقق من توفر الموعد الجديد
        slot_exists = AvailableSlot.objects.filter(doctor=appointment.doctor, date=date, time=time).exists()
        if not slot_exists:
            return Response({"error": "Slot not available"}, status=status.HTTP_400_BAD_REQUEST)

        # تحديث الموعد
        appointment.date = date
        appointment.time = time
        appointment.save()

        # إرجاع تفاصيل الموعد بعد التحديث
        appointment_serializer = AppointmentSerializer(appointment)
        return Response({"message": "Appointment updated successfully", "appointment": appointment_serializer.data}, status=status.HTTP_200_OK)