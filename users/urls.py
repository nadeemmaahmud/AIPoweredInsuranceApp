from django.urls import path
from .views import (
    RegisterView, LoginView, GoogleLoginAPIView,
    VerifyEmailView, ResendVerificationEmailView,
    ForgotPasswordView, ResetPasswordView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('auth/google/', GoogleLoginAPIView.as_view(), name='google_login'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('resend-verification/', ResendVerificationEmailView.as_view(), name='resend-verification'),
]
