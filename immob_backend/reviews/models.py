from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from properties.models import Property
import uuid

User = get_user_model()


class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews', verbose_name=_('utilisateur'))
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='reviews', verbose_name=_('propriété'))
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_('note')
    )
    title = models.CharField(max_length=200, verbose_name=_('titre de l\'avis'))
    comment = models.TextField(verbose_name=_('commentaire'))
    is_verified_purchase = models.BooleanField(default=False, verbose_name=_('achat vérifié'))
    likes_count = models.PositiveIntegerField(default=0, verbose_name=_('nombre de likes'))
    is_approved = models.BooleanField(default=False, verbose_name=_('approuvé'))
    is_edited = models.BooleanField(default=False, verbose_name=_('modifié'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('avis')
        verbose_name_plural = _('avis')
        ordering = ['-created_at']
        unique_together = ['user', 'property']
        indexes = [
            models.Index(fields=['property', 'rating']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.property.title} ({self.rating}/5)"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Mettre à jour la note moyenne de la propriété
        self.property.update_average_rating()


class ReviewLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_likes')
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='liked_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('like d\'avis')
        verbose_name_plural = _('likes d\'avis')
        unique_together = ['user', 'review']
    
    def __str__(self):
        return f"{self.user.email} liked review {self.review.id}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.review.likes_count = ReviewLike.objects.filter(review=self.review).count()
        self.review.save(update_fields=['likes_count'])


class ReviewImage(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='reviews/images/')
    caption = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('légende'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('image d\'avis')
        verbose_name_plural = _('images d\'avis')
    
    def __str__(self):
        return f"Image for review {self.review.id}"


class ApplicationFeedback(models.Model):
    FEEDBACK_TYPES = [
        ('general', 'Général'),
        ('bug', 'Bug/Rapport d\'erreur'),
        ('suggestion', 'Suggestion'),
        ('complaint', 'Plainte'),
        ('praise', 'Éloge'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedbacks')
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES, default='general', verbose_name=_('type de feedback'))
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
        verbose_name=_('note')
    )
    title = models.CharField(max_length=200, verbose_name=_('titre'))
    message = models.TextField(verbose_name=_('message'))
    email = models.EmailField(blank=True, null=True, verbose_name=_('email de contact'))
    is_resolved = models.BooleanField(default=False, verbose_name=_('résolu'))
    response = models.TextField(blank=True, null=True, verbose_name=_('réponse'))
    responded_at = models.DateTimeField(null=True, blank=True, verbose_name=_('date de réponse'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('feedback d\'application')
        verbose_name_plural = _('feedbacks d\'application')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.feedback_type}: {self.title}"