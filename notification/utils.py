from pyfcm import FCMNotification
from django.conf import settings
from .models import Device

push_service = FCMNotification(api_key=settings.FCM_API_KEY)

def send_push_notification_to_users(users, title, message, data=None):
    registration_ids = Device.objects.filter(user__in=users).values_list("registration_id", flat=True)
    registration_ids = list(registration_ids)
    if not registration_ids:
        return {"error": "No device tokens found."}

    result = push_service.notify_multiple_devices(
        registration_ids=registration_ids,
        message_title=title,
        message_body=message,
        data_message=data or {}
    )
    return result
