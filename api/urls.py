from django.urls import path
from .views import (
    AddAvailableSlots, DoctorAvailableSlots, BookAppointment,
    DoctorUpcomingAppointments, DoctorPastAppointments,
    PatientUpcomingAppointments, PatientPastAppointments,
    UpdateAvailableSlot, UpdateAppointment
)

urlpatterns = [
    path('api/doctor/add_slots/', AddAvailableSlots.as_view(), name='add_slots'),  

    path('doctor/<int:doctor_id>/available_slots/', DoctorAvailableSlots.as_view(), name='get_available_slots'),

    path('slot/<int:slot_id>/update/', UpdateAvailableSlot.as_view(), name='update_available_slot'),

    path('book_appointment/', BookAppointment.as_view(), name='book_appointment'),

    path('appointment/<int:appointment_id>/update/', UpdateAppointment.as_view(), name='update_appointment'),

    path('doctor/appointments/upcoming/', DoctorUpcomingAppointments.as_view(), name='doctor_upcoming_appointments'),

    path('doctor/appointments/past/', DoctorPastAppointments.as_view(), name='doctor_past_appointments'),

    path('patient/appointments/upcoming/', PatientUpcomingAppointments.as_view(), name='patient_upcoming_appointments'),

    path('patient/appointments/past/', PatientPastAppointments.as_view(), name='patient_past_appointments'),
    
]
