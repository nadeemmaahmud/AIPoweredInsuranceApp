from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google.auth.exceptions import GoogleAuthError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser, EmailVerificationOTP, PasswordResetOTP
from .utils import ResponseMixin
from .serializers import (
    RegisterSerializer, LoginSerializer, CustomUserSerializer, EmailVerificationSerializer,
    ResendVerificationEmailSerializer,ForgotPasswordSerializer, ResetPasswordSerializer,
    SocialLoginRequestSerializer, SocialLoginResponseSerializer, ResendResetPasswordEmailSerializer
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

                This code will expire in 5 minutes.

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
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
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
                
                return Response({
                    'message': 'Email verified successfully! You can now login.',
                    'user': CustomUserSerializer(user).data,
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

                This code will expire in 5 minutes.

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

                This code will expire in 5 minutes.

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
    
class ResendResetPasswordEmailView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = ResendResetPasswordEmailSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = CustomUser.objects.get(email=email)
            PasswordResetOTP.objects.filter(user=user, is_used=False).update(is_used=True)
            reset_otp = PasswordResetOTP.objects.create(user=user)
            email_subject = 'Password Reset Request - SellnService'
            email_message = f"""
                Hello {user.name},

                You requested a new password reset code.

                Your password reset code is:

                {reset_otp.otp_code}

                This code will expire in 5 minutes.

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
                    'error': 'Failed to send password reset email. Please try again later.',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({
                'message': 'Password reset code sent successfully. Please check your email.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
def generate_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name or "",
        }
    }
 
 
class GoogleLoginAPIView(ResponseMixin, APIView):
    permission_classes = [AllowAny]
 
    @extend_schema(
        request=SocialLoginRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=SocialLoginResponseSerializer,
                description='Google authentication successful'
            ),
            400: OpenApiResponse(description='Invalid token or bad request')
        },
        examples=[
            OpenApiExample(
                "Google ID Token Request",
                value={"id_token": "ya29.a0AWY7CknF..."},
                request_only=True,
            ),
            OpenApiExample(
                "Successful Authentication Response",
                value={
                    "success": True,
                    "statusCode": 200,
                    "message": "Google authentication successful",
                    "data": {
                        "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                        "user": {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "email": "user@gmail.com",
                            "name": "John Doe"
                        }
                    },
                    "timestamp": "2025-10-19T10:30:00Z"
                },
                response_only=True,
            ),
        ],
        description=(
            "Authenticate user with Google ID token.\n\n"
            "**How it works:**\n"
            "1. Client app obtains ID token from Google Sign-In SDK\n"
            "2. Client sends the ID token to this endpoint\n"
            "3. Server verifies the token with Google\n"
            "4. If valid, creates/retrieves user and returns JWT tokens\n\n"
            "**Note:** If user doesn't exist, a new account is automatically created."
        ),
        tags=["Social Authentication"],
    )
    def post(self, request):
        serializer = SocialLoginRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(
                message='Validation failed',
                data={'errors': serializer.errors},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        token = serializer.validated_data['id_token']
        try:
            idinfo = id_token.verify_oauth2_token(
                token, 
                google_requests.Request()
            )

            email = idinfo.get("email")
            name = idinfo.get("name", "")
            google_uid = idinfo.get("sub")
            if not email:
                return self.error_response(
                    message='Google token did not return an email',
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            email_verified = idinfo.get("email_verified", False)
            if not email_verified:
                return self.error_response(
                    message='Google email is not verified',
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            user, created = CustomUser.objects.get_or_create(
                email=email.lower(),
                defaults={
                    'name': name,
                    'is_active': True,
                }
            )

            if not user.is_active:
                user.is_active = True
                user.save(update_fields=['is_active'])

            if not created and not user.name and name:
                user.name = name
                user.save(update_fields=['name'])

            tokens_data = generate_tokens_for_user(user)
            message = 'Account created and authenticated successfully' if created else 'Google authentication successful'
            return self.success_response(
                message=message,
                data=tokens_data,
                status_code=status.HTTP_200_OK
            )
        except GoogleAuthError as e:
            return self.error_response(
                message='Invalid Google token',
                data={'error': str(e)},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except ValueError as e:
            return self.error_response(
                message='Token verification failed',
                data={'error': str(e)},
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return self.error_response(
                message='Authentication failed',
                data={'error': str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )