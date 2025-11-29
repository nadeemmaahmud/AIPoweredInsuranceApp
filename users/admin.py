from django.contrib import admin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'is_active', 'is_staff', 'date_joined')
    readonly_fields = ('date_joined',)

    fieldsets = (
        ('User Info', {
            'fields': ('email', 'name', 'date_joined'),
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
        }),
    )
