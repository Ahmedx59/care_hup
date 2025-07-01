# notifications/fcm.py
import os
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings

def initialize_firebase():
    try:
        if not firebase_admin._apps:
            cred_path = os.path.join(settings.BASE_DIR, 'service_account_key.json')
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase initialized successfully.")
    except Exception as e:
        print(f"🔥 Firebase initialization error: {str(e)}")

def send_push_notification(user, title, body, data=None):
    """
    Send push notification to a specific user
    """
    try:
        from .models import FCMDevice
        
        if not firebase_admin._apps:
            initialize_firebase()
        
        devices = FCMDevice.objects.filter(user=user, active=True)

        if not devices.exists():
            print(f"🚫 No active devices found for user: {user.username}")
            return False

        print(f"📨 Sending notification to {user.username} ({devices.count()} devices):")
        print(f"📌 Title: {title}")
        print(f"📝 Body: {body}")
        print(f"📦 Data: {data}")

        for device in devices:
            try:
                message = messaging.Message(
                    notification=messaging.Notification(title=title, body=body),
                    data=data or {},
                    token=device.registration_id
                )
                response = messaging.send(message)
                print(f"✅ Successfully sent to device ID: {device.id}")
            except Exception as e:
                print(f"❌ Failed to send notification to device ID: {device.id}: {str(e)}")
                device.active = False
                device.save()

        return True
    except Exception as e:
        print(f"🚨 Error sending push notification: {str(e)}")
        return False
