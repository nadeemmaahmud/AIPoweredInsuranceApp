from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser, EmailVerificationOTP, PasswordResetOTP
from .serializers import (
    RegisterSerializer, LoginSerializer, CustomUserSerializer, EmailVerificationSerializer,
    ResendVerificationEmailSerializer,ForgotPasswordSerializer, ResetPasswordSerializer
)

class RegisterView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            verification_otp = EmailVerificationOTP.objects.create(user=user)
            email_subject = 'Verify Your Email - SellnService'
            email_message = f"""
                Hello {user.name},

                Thank you for registering with SellnService!

                Your email verification code is:

                {verification_otp.otp_code}

                This code will expire in 15 minutes.

                If you didn't create an account, please ignore this email.

                Best regards,
                SellnService Team
            """
            
            try:
                send_mail(
                    email_subject,
                    email_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
            except Exception as e:
                EmailVerificationOTP.objects.filter(user=user).delete()
                user.delete()
                return Response({
                    'error': 'Failed to send verification email. Please try again later.',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({
                'message': 'User registered successfully. Please check your email for the verification code.',
                'user': CustomUserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'Login successful',
                'user': CustomUserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

class VerifyEmailView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp_code = serializer.validated_data['otp_code']
            
            try:
                user = CustomUser.objects.get(email=email)
                
                if user.is_active:
                    return Response({
                        'message': 'Email is already verified. You can login now.'
                    }, status=status.HTTP_200_OK)
                
                verification_otp = EmailVerificationOTP.objects.filter(
                    user=user,
                    otp_code=otp_code,
                    is_used=False
                ).order_by('-created_at').first()
                
                if not verification_otp:
                    return Response({
                        'error': 'Invalid verification code.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                if not verification_otp.is_valid():
                    return Response({
                        'error': 'Verification code has expired. Please request a new one.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                user.is_active = True
                user.save()
                
                verification_otp.is_used = True
                verification_otp.save()
                
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'message': 'Email verified successfully! You can now login.',
                }, status=status.HTTP_200_OK)
                
            except CustomUser.DoesNotExist:
                return Response({
                    'error': 'No user found with this email address.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResendVerificationEmailView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = ResendVerificationEmailSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = CustomUser.objects.get(email=email)
            EmailVerificationOTP.objects.filter(user=user, is_used=False).update(is_used=True)
            verification_otp = EmailVerificationOTP.objects.create(user=user)
            email_subject = 'Verify Your Email - SellnService'
            email_message = f"""
                Hello {user.name},

                You requested a new email verification code.

                Your verification code is:

                {verification_otp.otp_code}

                This code will expire in 15 minutes.

                If you didn't request this, please ignore this email.

                Best regards,
                SellnService Team
            """
            
            try:
                send_mail(
                    email_subject,
                    email_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
            except Exception as e:
                return Response({
                    'error': 'Failed to send verification email. Please try again later.',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({
                'message': 'Verification code sent successfully. Please check your email.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = CustomUser.objects.get(email=email)
            PasswordResetOTP.objects.filter(user=user, is_used=False).update(is_used=True)
            reset_otp = PasswordResetOTP.objects.create(user=user)
            email_subject = 'Password Reset Request - SellnService'
            email_message = f"""
                Hello {user.name},

                You requested to reset your password.

                Your password reset code is:

                {reset_otp.otp_code}

                This code will expire in 15 minutes.

                If you didn't request this, please ignore this email and your password will remain unchanged.

                Best regards,
                SellnService Team
            """
            
            try:
                send_mail(
                    email_subject,
                    email_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
            except Exception as e:
                return Response({
                    'error': 'Failed to send password reset email. Please try again later.',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({
                'message': 'Password reset code sent to your email.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp_code = serializer.validated_data['otp_code']
            new_password = serializer.validated_data['new_password']
            
            try:
                user = CustomUser.objects.get(email=email)
                reset_otp = PasswordResetOTP.objects.filter(
                    user=user,
                    otp_code=otp_code,
                    is_used=False
                ).order_by('-created_at').first()
                
                if not reset_otp:
                    return Response({
                        'error': 'Invalid reset code.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                if not reset_otp.is_valid():
                    return Response({
                        'error': 'Reset code has expired. Please request a new one.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                user.set_password(new_password)
                user.save()
                reset_otp.is_used = True
                reset_otp.save()
                
                return Response({
                    'message': 'Password reset successful! You can now login with your new password.'
                }, status=status.HTTP_200_OK)
                
            except CustomUser.DoesNotExist:
                return Response({
                    'error': 'No user found with this email address.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)