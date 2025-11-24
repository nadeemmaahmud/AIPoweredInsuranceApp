from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password
from .models import (
    CustomUser,
    PendingRegistration,
    PendingVerificationOTP,
    PasswordResetOTP,
)
from .serializers import (
    RegisterSerializer, LoginSerializer,
    OtpVerificationSerializer, ResendOtpVerificationSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer, VerifyResetOTPSerializer,
    CustomUserSerializer,
)

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data
            email = data['email']
            name = data.get('name') or data.get('first_name') or ''
            raw_password = data['password']

            # remove any previous pending registrations for this email
            PendingRegistration.objects.filter(email=email).delete()

            # store hashed password (never store raw password)
            pending = PendingRegistration.objects.create(
                email=email,
                name=name,
                password_hashed=make_password(raw_password),
            )

            otp = PendingVerificationOTP.objects.create(pending=pending)

            email_subject = 'Verify Your Email - SellnService'
            email_message = f"""
Hello {name},

Thank you for registering with SellnService!

Your email verification code is:

{otp.otp_code}

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
                    [email],
                    fail_silently=False,
                )
            except Exception as e:
                PendingVerificationOTP.objects.filter(pending=pending).delete()
                pending.delete()
                return Response({
                    'error': 'Failed to send verification email.',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({
                'message': 'Registration recorded. Verify the OTP sent to your email to complete account creation.'
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class VerifyUserOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        otp_code = request.data.get('otp')
        user_data = request.data.get('user_data')

        # Find the pending registration
        try:
            pending = PendingRegistration.objects.get(email=email)
        except PendingRegistration.DoesNotExist:
            return Response({'error': 'No pending registration found for this email.'}, status=status.HTTP_400_BAD_REQUEST)

        otp_obj = PendingVerificationOTP.objects.filter(pending=pending, otp_code=otp_code, is_used=False).order_by('-created_at').first()
        if not otp_obj or not otp_obj.is_valid():
            return Response({'error': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)

        # Create actual user using the stored hashed password
        user = CustomUser.objects.create(
            email=pending.email,
            name=pending.name,
            is_active=True,
        )
        user.password = pending.password_hashed
        user.save()

        otp_obj.is_used = True
        otp_obj.save()

        # cleanup pending data
        PendingVerificationOTP.objects.filter(pending=pending).delete()
        pending.delete()

        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'Email verified. Registration successful.',
            'user': CustomUserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)

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
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = OtpVerificationSerializer(data=request.data)
        if serializer.is_valid():
            # This endpoint will verify pending registration OTP and create user
            email = serializer.validated_data['email']
            otp_code = serializer.validated_data['otp_code']

            try:
                pending = PendingRegistration.objects.get(email=email)
            except PendingRegistration.DoesNotExist:
                return Response({'error': 'No pending registration found for this email.'}, status=status.HTTP_400_BAD_REQUEST)

            otp_obj = PendingVerificationOTP.objects.filter(pending=pending, otp_code=otp_code, is_used=False).order_by('-created_at').first()
            if not otp_obj or not otp_obj.is_valid():
                return Response({'error': 'Invalid or expired verification code.'}, status=status.HTTP_400_BAD_REQUEST)

            user = CustomUser.objects.create(
                email=pending.email,
                name=pending.name,
                is_active=True,
            )
            user.password = pending.password_hashed
            user.save()

            otp_obj.is_used = True
            otp_obj.save()

            PendingVerificationOTP.objects.filter(pending=pending).delete()
            pending.delete()

            refresh = RefreshToken.for_user(user)

            return Response({
                'message': 'Email verified successfully and account created.',
                'user': CustomUserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResendVerificationEmailView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = ResendOtpVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            # find pending registration
            try:
                pending = PendingRegistration.objects.get(email=email)
            except PendingRegistration.DoesNotExist:
                return Response({'error': 'No pending registration found for this email.'}, status=status.HTTP_400_BAD_REQUEST)

            # mark old pending otps used and create new one
            PendingVerificationOTP.objects.filter(pending=pending, is_used=False).update(is_used=True)
            otp = PendingVerificationOTP.objects.create(pending=pending)

            email_subject = 'Verify Your Email - SellnService'
            email_message = f"""
Hello {pending.name},

You requested a new email verification code.

Your verification code is:

{otp.otp_code}

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
                    [pending.email],
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
                Hello {user.first_name},

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

class VerifyResetOTPView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = VerifyResetOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp_code = serializer.validated_data['otp_code']
            
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
                
                return Response({
                    'message': 'OTP verified successfully. You can now reset your password.',
                    'email': email
                }, status=status.HTTP_200_OK)
                
            except CustomUser.DoesNotExist:
                return Response({
                    'error': 'No user found with this email address.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
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