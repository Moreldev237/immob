from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()


class PropertyCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name=_('nom'))
    description = models.TextField(blank=True, null=True, verbose_name=_('description'))
    icon = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('icône'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('catégorie de propriété')
        verbose_name_plural = _('catégories de propriétés')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class PropertyType(models.Model):
    name = models.CharField(max_length=100, verbose_name=_('nom'))
    category = models.ForeignKey(PropertyCategory, on_delete=models.CASCADE, related_name='types')
    description = models.TextField(blank=True, null=True, verbose_name=_('description'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('type de propriété')
        verbose_name_plural = _('types de propriétés')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.category.name})"


class Location(models.Model):
    REGIONS = [
        ('adamaoua', 'Adamaoua'),
        ('centre', 'Centre'),
        ('est', 'Est'),
        ('extreme_nord', 'Extrême-Nord'),
        ('littoral', 'Littoral'),
        ('nord', 'Nord'),
        ('nord_ouest', 'Nord-Ouest'),
        ('ouest', 'Ouest'),
        ('sud', 'Sud'),
        ('sud_ouest', 'Sud-Ouest'),
    ]
    
    name = models.CharField(max_length=100, verbose_name=_('nom'))
    region = models.CharField(max_length=20, choices=REGIONS, verbose_name=_('région'))
    city = models.CharField(max_length=100, verbose_name=_('ville'))
    quarter = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('quartier'))
    address = models.TextField(verbose_name=_('adresse complète'))
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, verbose_name=_('latitude'))
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, verbose_name=_('longitude'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('localisation')
        verbose_name_plural = _('localisations')
        ordering = ['city', 'quarter']
    
    def __str__(self):
        return f"{self.city}, {self.quarter or ''}"


class Property(models.Model):
    STATUS_CHOICES = [
        ('for_sale', 'À vendre'),
        ('for_rent', 'À louer'),
        ('sold', 'Vendu'),
        ('rented', 'Loué'),
        ('pending', 'En attente'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, verbose_name=_('titre'))
    description = models.TextField(verbose_name=_('description'))
    property_type = models.ForeignKey(PropertyType, on_delete=models.PROTECT, related_name='properties')
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name='properties')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name=_('statut'))
    
    # Caractéristiques principales
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_('prix'))
    currency = models.CharField(max_length=3, default='XAF', verbose_name=_('devise'))
    area = models.DecimalField(max_digits=8, decimal_places=2, verbose_name=_('superficie (m²)'))
    bedrooms = models.PositiveIntegerField(default=0, verbose_name=_('chambres'))
    bathrooms = models.PositiveIntegerField(default=0, verbose_name=_('salles de bain'))
    parking_spaces = models.PositiveIntegerField(default=0, verbose_name=_('places de parking'))
    
    # Caractéristiques supplémentaires
    has_kitchen = models.BooleanField(default=True, verbose_name=_('cuisine'))
    has_living_room = models.BooleanField(default=True, verbose_name=_('salon'))
    has_dining_room = models.BooleanField(default=False, verbose_name=_('salle à manger'))
    has_balcony = models.BooleanField(default=False, verbose_name=_('balcon'))
    has_garden = models.BooleanField(default=False, verbose_name=_('jardin'))
    has_pool = models.BooleanField(default=False, verbose_name=_('piscine'))
    has_garage = models.BooleanField(default=False, verbose_name=_('garage'))
    has_security = models.BooleanField(default=False, verbose_name=_('sécurité'))
    has_internet = models.BooleanField(default=False, verbose_name=_('internet'))
    has_ac = models.BooleanField(default=False, verbose_name=_('climatisation'))
    
    # Informations du propriétaire/agent
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_properties', verbose_name=_('propriétaire'))
    agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_properties', verbose_name=_('agent'))
    
    # Métadonnées
    is_featured = models.BooleanField(default=False, verbose_name=_('en vedette'))
    is_verified = models.BooleanField(default=False, verbose_name=_('vérifié'))
    views_count = models.PositiveIntegerField(default=0, verbose_name=_('nombre de vues'))
    favorites_count = models.PositiveIntegerField(default=0, verbose_name=_('nombre de favoris'))
    favorited_by = models.ManyToManyField(User, through='Favorite', related_name='favorite_properties', blank=True, verbose_name=_('favorisé par'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True, verbose_name=_('date de publication'))
    
    class Meta:
        verbose_name = _('propriété')
        verbose_name_plural = _('propriétés')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['price']),
            models.Index(fields=['property_type']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if self.status in ['for_sale', 'for_rent'] and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()
        super().save(*args, **kwargs)


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='properties/images/')
    caption = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('légende'))
    is_primary = models.BooleanField(default=False, verbose_name=_('image principale'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('ordre'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('image de propriété')
        verbose_name_plural = _('images de propriétés')
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"Image for {self.property.title}"
    
    def save(self, *args, **kwargs):
        if self.is_primary:
            # Désactiver les autres images principales pour cette propriété
            PropertyImage.objects.filter(property=self.property, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='favorites')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('favori')
        verbose_name_plural = _('favoris')
        unique_together = ['user', 'property']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} favorited {self.property.title}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Mettre à jour le compteur de favoris
        self.property.favorites_count = self.property.favorites.count()
        self.property.save(update_fields=['favorites_count'])

    def delete(self, *args, **kwargs):
        property_obj = self.property
        super().delete(*args, **kwargs)
        # Mettre à jour le compteur de favoris après suppression
        property_obj.favorites_count = property_obj.favorites.count()
        property_obj.save(update_fields=['favorites_count'])


class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_history')
    query = models.TextField(verbose_name=_('requête de recherche'))
    filters = models.JSONField(default=dict, blank=True, verbose_name=_('filtres'))
    results_count = models.PositiveIntegerField(default=0, verbose_name=_('nombre de résultats'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('historique de recherche')
        verbose_name_plural = _('historiques de recherche')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Search by {self.user.email}: {self.query[:50]}..."