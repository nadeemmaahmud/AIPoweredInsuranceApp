from celery import shared_task
from django.contrib.auth import get_user_model
from .utils import send_push_notification_to_users

User = get_user_model()

@shared_task
def send_monthly_notification():
    users = User.objects.filter(is_active=True)
    title = "Monthly Update"
    message = "Here’s your monthly notification!"
    data = {"type": "monthly_update"}
    
    result = send_push_notification_to_users(users, title, message, data)
    return result
