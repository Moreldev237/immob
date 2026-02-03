from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from .managers import CustomUserManager


class User(AbstractUser):
    email = models.EmailField(blank=True, null=True,unique=True)
    REQUIRED_FIELDS = ['username']
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Le numéro de téléphone doit être au format: '+237XXXXXXXXX'"
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        null=True,
        verbose_name=_('numéro de téléphone')
    )
    
    # Champs additionnels
    profile_picture = models.ImageField(
        upload_to='users/profile_pictures/',
        blank=True,
        null=True,
        verbose_name=_('photo de profil')
    )
    is_verified = models.BooleanField(default=False, verbose_name=_('vérifié'))
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Champs spécifiques à l'immobilier
    is_agent = models.BooleanField(default=False, verbose_name=_('est agent immobilier'))
    agency_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('nom de l\'agence'))
    license_number = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('numéro de licence'))
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    objects = CustomUserManager()
    
    class Meta:
        verbose_name = _('utilisateur')
        verbose_name_plural = _('utilisateurs')
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True, verbose_name=_('biographie'))
    website = models.URLField(blank=True, null=True, verbose_name=_('site web'))
    facebook = models.URLField(blank=True, null=True, verbose_name=_('facebook'))
    twitter = models.URLField(blank=True, null=True, verbose_name=_('twitter'))
    instagram = models.URLField(blank=True, null=True, verbose_name=_('instagram'))
    linkedin = models.URLField(blank=True, null=True, verbose_name=_('linkedin'))
    
    # Préférences utilisateur
    preferred_language = models.CharField(
        max_length=10,
        default='fr',
        choices=[('fr', 'Français'), ('en', 'English')],
        verbose_name=_('langue préférée')
    )
    notification_email = models.BooleanField(default=True, verbose_name=_('notifications par email'))
    notification_sms = models.BooleanField(default=False, verbose_name=_('notifications par SMS'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('profil utilisateur')
        verbose_name_plural = _('profils utilisateurs')
    
    def __str__(self):
        return f"Profil de {self.user.email}"


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = _('jeton de réinitialisation')
        verbose_name_plural = _('jetons de réinitialisation')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Reset token for {self.user.email}"
    
    def is_valid(self):
        from django.utils import timezone
        return not self.is_used and timezone.now() < self.expires_at