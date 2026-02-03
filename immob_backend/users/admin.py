from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile, PasswordResetToken


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_agent', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_agent', 'is_staff', 'is_active', 'date_joined', 'groups')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'phone_number', 'agency_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Informations personnelles'), {'fields': ('username', 'first_name', 'last_name', 'phone_number', 'profile_picture')}),
        (_('Vérification'), {'fields': ('is_verified', 'verification_token')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Informations agent'), {'fields': ('is_agent', 'agency_name', 'license_number')}),
        (_('Dates importantes'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_agent'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login', 'verification_token')
    
    def get_queryset(self, request):
        return super().get_queryset(request)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'website', 'preferred_language', 'notification_email', 'notification_sms', 'created_at')
    list_filter = ('preferred_language', 'notification_email', 'notification_sms', 'created_at')
    search_fields = ('user__email', 'user__username', 'bio', 'website', 'facebook', 'twitter', 'instagram', 'linkedin')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user',)


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'expires_at', 'is_used')
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('user__email', 'token')
    readonly_fields = ('token', 'created_at')
    raw_id_fields = ('user',)

