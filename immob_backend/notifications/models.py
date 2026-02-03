from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Notification(models.Model):
    """Model to store user notifications"""
    
    class NotificationType(models.TextChoices):
        PROPERTY_UPDATE = 'property_update', _('Mise à jour de propriété')
        NEW_MESSAGE = 'new_message', _('Nouveau message')
        FAVORITE_UPDATE = 'favorite_update', _('Mise à jour favorite')
        SYSTEM = 'system', _('Système')
        REVIEW_RESPONSE = 'review_response', _('Réponse à un avis')
        PAYMENT = 'payment', _('Paiement')
        BOOKING = 'booking', _('Réservation')
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('utilisateur')
    )
    title = models.CharField(max_length=255, verbose_name=_('titre'))
    message = models.TextField(verbose_name=_('message'))
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM,
        verbose_name=_('type de notification')
    )
    is_read = models.BooleanField(default=False, verbose_name=_('lu'))
    read_at = models.DateTimeField(blank=True, null=True, verbose_name=_('lu le'))
    link = models.URLField(blank=True, null=True, verbose_name=_('lien'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('créé le'))
    
    class Meta:
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"
    
    def mark_as_read(self):
        """Mark the notification as read"""
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    @property
    def is_read_display(self):
        """Return a human-readable status"""
        return _('Oui') if self.is_read else _('Non')

