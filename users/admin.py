from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserVerificationOTP, PendingVerificationOTP, PasswordResetOTP, PendingRegistration

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['email', 'name', 'is_staff', 'is_active', 'date_joined']
    list_filter = ['is_staff', 'is_active', 'date_joined']
    search_fields = ['email', 'name']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('name',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    
    readonly_fields = ['date_joined', 'last_login']

@admin.register(PendingVerificationOTP)
class PendingVerificationOTPAdmin(admin.ModelAdmin):
    list_display = ['pending', 'otp_code', 'created_at', 'expires_at', 'is_used', 'is_valid']
    list_filter = ['is_used', 'created_at', 'expires_at']
    search_fields = ['pending__email', 'otp_code']
    readonly_fields = ['otp_code', 'created_at', 'expires_at']
    ordering = ['-created_at']

    def is_valid(self, obj):
        return obj.is_valid()
    is_valid.boolean = True
    is_valid.short_description = 'Valid'


@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'otp_code', 'created_at', 'expires_at', 'is_used', 'is_valid']
    list_filter = ['is_used', 'created_at', 'expires_at']
    search_fields = ['user__email', 'otp_code', 'token']
    readonly_fields = ['otp_code', 'created_at', 'expires_at', 'token']
    ordering = ['-created_at']

    def is_valid(self, obj):
        return obj.is_valid()
    is_valid.boolean = True
    is_valid.short_description = 'Valid'

admin.site.register(CustomUser, CustomUserAdmin)
