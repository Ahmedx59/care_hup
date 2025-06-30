# notifications/tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from api.models import Appointment
from chat.models import Message
from .fcm import send_push_notification


@shared_task
def send_appointment_reminders():
    """
    Background task to send reminders for appointments that start in exactly 1 hour
    """
    now = timezone.now()
    target_time = now + timedelta(hours=1)

    start_range = target_time - timedelta(minutes=10)
    end_range = target_time + timedelta(minutes=10)

    appointments = Appointment.objects.filter(
        reminder_sent=False,
        date__gte=start_range.date(),
        date__lte=end_range.date(),
        time__gte=start_range.time(),
        time__lte=end_range.time()
    )

    print(f"🔍 Found {appointments.count()} appointments that need reminders")

    for appointment in appointments:
        try:
            doctor_user = appointment.doctor.user
            doctor_name = f"{doctor_user.first_name} {doctor_user.last_name}".strip()
            if not doctor_name:
                doctor_name = doctor_user.username

            send_push_notification(
                user=appointment.patient.user,
                title="Appointment Reminder",
                body=f"Your appointment with Dr. {doctor_name} is in 1 hour",
                data={
                    'type': 'appointment_reminder',
                    'appointment_id': str(appointment.id)
                }
            )
            appointment.reminder_sent = True
            appointment.save()
            print(f"✅ Reminder sent for appointment ID: {appointment.id}")
        except Exception as e:
            print(f"❌ Failed to send reminder for appointment ID: {appointment.id} - {str(e)}")


@shared_task
def send_new_chat_notification(message_id):
    """
    Background task to send notification for a new chat message
    """
    try:
        message = Message.objects.select_related('chat', 'sender').get(id=message_id)
        chat = message.chat
        sender = message.sender

        recipients = chat.participants.exclude(id=sender.id)
        sender_name = f"{sender.first_name} {sender.last_name}".strip()
        if not sender_name:
            sender_name = sender.username

        for recipient in recipients:
            send_push_notification(
                user=recipient,
                title="New Message",
                body=f"You received a new message from {sender_name}",
                data={
                    'type': 'new_message',
                    'chat_id': str(chat.id),
                    'message_id': str(message.id),
                    'sender_id': str(sender.id)
                }
            )
        print(f"📨 Chat notification sent for message ID: {message.id}")
    except Exception as e:
        print(f"❌ Failed to send chat notification for message ID: {message_id} - {str(e)}")


@shared_task
def send_new_appointment_notification(appointment_id):
    """
    Background task to notify doctor about a new appointment
    """
    from api.models import Appointment
    from .fcm import send_push_notification

    try:
        appointment = Appointment.objects.select_related('doctor__user', 'patient__user').get(id=appointment_id)
        doctor = appointment.doctor.user
        patient = appointment.patient.user

        doctor_name = f"{doctor.first_name} {doctor.last_name}".strip() or doctor.username
        patient_name = f"{patient.first_name} {patient.last_name}".strip() or patient.username

        send_push_notification(
            user=doctor,
            title="New Appointment",
            body=f"{patient_name} booked a new appointment on {appointment.date} at {appointment.time}",
            data={
                'type': 'new_appointment',
                'appointment_id': str(appointment.id)
            }
        )
        print(f"✅ New appointment notification sent to doctor {doctor.username}, appointment ID {appointment.id}")
    except Exception as e:
        print(f"❌ Failed to send new appointment notification: {str(e)}")


@shared_task
def send_push_notification_task(user_id, title, body, data=None):
    """
    General background task to send a push notification to a specific user by ID
    """
    from users.models import User
    from .fcm import send_push_notification

    try:
        user = User.objects.get(id=user_id)
        send_push_notification(user=user, title=title, body=body, data=data)
        print(f"📤 Notification sent to user {user.username}")
    except Exception as e:
        print(f"❌ Failed to send notification to user {user_id} - {str(e)}")
@shared_task
def send_cancellation_notification(appointment_data):
    """
    Background task to notify doctor when a patient cancels an appointment
    """
    from users.models import User
    from .fcm import send_push_notification

    try:
        doctor = User.objects.get(id=appointment_data['doctor_id'])
        send_push_notification(
            user=doctor,
            title="Appointment Cancelled",
            body=f"{appointment_data['patient_name']} has cancelled the appointment scheduled on {appointment_data['date']} at {appointment_data['time']}",
            data={
                'type': 'appointment_cancellation',
                'appointment_id': str(appointment_data['appointment_id'])
            }
        )
        print(f"✅ Cancellation notification sent to doctor {doctor.username}, appointment ID {appointment_data['appointment_id']}")
    except Exception as e:
        print(f"❌ Failed to send cancellation notification: {str(e)}")
