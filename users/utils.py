from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from .models import UserVerificationOTP, CustomUser
import logging

logger = logging.getLogger(__name__)

def send_verification_email(user: CustomUser) -> bool:
    UserVerificationOTP.objects.filter(user=user).delete()
    otp = UserVerificationOTP.objects.create(user=user)

    base_url = getattr(settings, "SITE_URL", "http://127.0.0.1:8000").rstrip('/')
    reset_path = reverse("customuser-reset-password")
    otp = f"{otp.otp_code}"

    subject = "Clamea Account Verification OTP"

    message = (
        f"Hi {user.name or user.email},\n\n"
        "You're required to verify first to do the action.\n"
        "Please enter the below OTP to verify yourself:\n\n"
        f"{otp}\n\n"
        "This OTP expires in 2 minutes for security reasons.\n"
        "If you didn't request this verification, please ignore this email."
    )
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@clamea.local")

    logger.info(f"[User Verification Email] To={user.email} OTP={otp}")

    try:
        send_mail(subject, message, from_email, [user.email], fail_silently=False)
        logger.info("[User Verification Email] Sent successfully")
        return True
    except Exception as e:
        logger.exception(f"[User Verification Email] Failed: {e}")
        return False