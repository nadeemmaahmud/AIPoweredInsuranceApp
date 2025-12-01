from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import random
import string

class CustomUserManager(BaseUserManager):
    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, name, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    languages = (
        ('en', 'English'),
        ('es', 'Spanish'),
    )
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_subscribed = models.BooleanField(default=False)
    language = models.CharField(max_length=2, choices=languages, default='en')
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return self.email

class EmailVerificationOTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='verification_tokens')
    otp_code = models.CharField(max_length=4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Email Verification OTP'
        verbose_name_plural = 'Email Verification OTPs'
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.otp_code:
            self.otp_code = ''.join(random.choices(string.digits, k=4))
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(minutes=5)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at
    
    def __str__(self):
        return f"OTP for {self.user.email} - {self.otp_code}"

class PasswordResetOTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='password_reset_otps')
    otp_code = models.CharField(max_length=4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Password Reset OTP'
        verbose_name_plural = 'Password Reset OTPs'
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.otp_code:
            self.otp_code = ''.join(random.choices(string.digits, k=4))
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(minutes=5)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at
    
    def __str__(self):
        return f"Password Reset OTP for {self.user.email} - {self.otp_code}"