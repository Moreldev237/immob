from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
import re
import bleach
from .models import (
    Property, PropertyCategory, PropertyType, 
    Location, PropertyImage, Favorite, SearchHistory
)

User = get_user_model()

# Maximum file upload size (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_IMAGES_PER_PROPERTY = 10


def sanitize_input(value):
    """
    Sanitize user input to prevent XSS attacks.
    """
    if value is None:
        return None
    
    if isinstance(value, str):
        # Remove potential XSS vectors
        value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
        value = re.sub(r'<iframe[^>]*>.*?</iframe>', '', value, flags=re.IGNORECASE | re.DOTALL)
        value = re.sub(r'<object[^>]*>.*?</object>', '', value, flags=re.IGNORECASE | re.DOTALL)
        value = re.sub(r'<embed[^>]*>', '', value, flags=re.IGNORECASE)
        value = re.sub(r'javascript:', '', value, flags=re.IGNORECASE)
        value = re.sub(r'on\w+\s*=', '', value, flags=re.IGNORECASE)
        
        # Remove excessive whitespace
        value = ' '.join(value.split())
        
        return value.strip()
    
    if isinstance(value, list):
        return [sanitize_input(item) for item in value]
    
    if isinstance(value, dict):
        return {key: sanitize_input(val) for key, val in value.items()}
    
    return value


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ['id', 'image', 'caption', 'is_primary', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate_image(self, value):
        # Validate file size
        if value.size > MAX_FILE_SIZE:
            raise ValidationError(f"L'image ne peut pas dépasser {MAX_FILE_SIZE // (1024*1024)}MB.")
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if value.content_type not in allowed_types:
            raise ValidationError("Type de fichier non autorisé. Utilisez JPEG, PNG, GIF ou WebP.")
        
        return value


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            'id', 'name', 'region', 'city', 'quarter', 
            'address', 'latitude', 'longitude'
        ]
    
    def validate_name(self, value):
        return sanitize_input(value)
    
    def validate_region(self, value):
        return sanitize_input(value)
    
    def validate_city(self, value):
        return sanitize_input(value)
    
    def validate_quarter(self, value):
        return sanitize_input(value)
    
    def validate_address(self, value):
        return sanitize_input(value)
    
    def validate_latitude(self, value):
        if value is not None and (value < -90 or value > 90):
            raise serializers.ValidationError("Latitude invalide.")
        return value
    
    def validate_longitude(self, value):
        if value is not None and (value < -180 or value > 180):
            raise serializers.ValidationError("Longitude invalide.")
        return value


class PropertyTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyType
        fields = ['id', 'name', 'category', 'description']
    
    def validate_name(self, value):
        return sanitize_input(value)
    
    def validate_description(self, value):
        return sanitize_input(value)


class PropertyCategorySerializer(serializers.ModelSerializer):
    types = PropertyTypeSerializer(many=True, read_only=True)
    
    class Meta:
        model = PropertyCategory
        fields = ['id', 'name', 'description', 'icon', 'types']
    
    def validate_name(self, value):
        return sanitize_input(value)
    
    def validate_description(self, value):
        return sanitize_input(value)


class PropertySerializer(serializers.ModelSerializer):
    images = PropertyImageSerializer(many=True, read_only=True)
    location = LocationSerializer(read_only=True)
    property_type = PropertyTypeSerializer(read_only=True)
    owner = serializers.StringRelatedField()
    agent = serializers.StringRelatedField()
    is_favorited = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Property
        fields = [
            'id', 'title', 'description', 'property_type', 'location', 'status',
            'price', 'currency', 'area', 'bedrooms', 'bathrooms', 'parking_spaces',
            'has_kitchen', 'has_living_room', 'has_dining_room', 'has_balcony',
            'has_garden', 'has_pool', 'has_garage', 'has_security', 'has_internet',
            'has_ac', 'owner', 'agent', 'is_featured', 'is_verified', 'views_count',
            'favorites_count', 'images', 'is_favorited', 'average_rating', 'review_count',
            'created_at', 'updated_at', 'published_at'
        ]
        read_only_fields = [
            'id', 'views_count', 'favorites_count', 'created_at', 'updated_at',
            'published_at'
        ]
    
    def validate_title(self, value):
        return sanitize_input(value)
    
    def validate_description(self, value):
        return sanitize_input(value)
    
    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Le prix ne peut pas être négatif.")
        return value
    
    def validate_area(self, value):
        if value < 0:
            raise serializers.ValidationError("La surface ne peut pas être négative.")
        if value > 1000000:  # Max 1 million square meters
            raise serializers.ValidationError("Surface invalide.")
        return value
    
    def validate_bedrooms(self, value):
        if value < 0:
            raise serializers.ValidationError("Nombre de chambres invalide.")
        if value > 100:
            raise serializers.ValidationError("Nombre de chambres trop élevé.")
        return value
    
    def validate_bathrooms(self, value):
        if value < 0:
            raise serializers.ValidationError("Nombre de salles de bain invalide.")
        if value > 100:
            raise serializers.ValidationError("Nombre de salles de bain trop élevé.")
        return value
    
    def validate_parking_spaces(self, value):
        if value < 0:
            raise serializers.ValidationError("Nombre de places de parking invalide.")
        return value
    
    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorites.filter(id=request.user.id).exists()
        return False
    
    def get_average_rating(self, obj):
        from reviews.models import Review
        reviews = Review.objects.filter(property=obj, is_approved=True)
        if reviews.exists():
            return round(reviews.aggregate(avg=models.Avg('rating'))['avg'], 1)
        return 0
    
    def get_review_count(self, obj):
        from reviews.models import Review
        return Review.objects.filter(property=obj, is_approved=True).count()


class PropertyCreateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
        max_length=MAX_IMAGES_PER_PROPERTY
    )
    location_data = serializers.JSONField(write_only=True)
    
    class Meta:
        model = Property
        fields = [
            'title', 'description', 'property_type', 'location_data',
            'status', 'price', 'currency', 'area', 'bedrooms', 'bathrooms',
            'parking_spaces', 'has_kitchen', 'has_living_room', 'has_dining_room',
            'has_balcony', 'has_garden', 'has_pool', 'has_garage', 'has_security',
            'has_internet', 'has_ac', 'images'
        ]
    
    def validate_title(self, value):
        value = sanitize_input(value)
        if len(value) < 5:
            raise serializers.ValidationError("Le titre doit contenir au moins 5 caractères.")
        if len(value) > 200:
            raise serializers.ValidationError("Le titre ne peut pas dépasser 200 caractères.")
        return value
    
    def validate_description(self, value):
        value = sanitize_input(value)
        if len(value) < 10:
            raise serializers.ValidationError("La description doit contenir au moins 10 caractères.")
        if len(value) > 10000:
            raise serializers.ValidationError("La description ne peut pas dépasser 10000 caractères.")
        return value
    
    def validate_images(self, value):
        if len(value) > MAX_IMAGES_PER_PROPERTY:
            raise serializers.ValidationError(
                f"Vous ne pouvez pas télécharger plus de {MAX_IMAGES_PER_PROPERTY} images."
            )
        
        for image in value:
            if image.size > MAX_FILE_SIZE:
                raise ValidationError(
                    f"L'image {image.name} dépasse la taille maximale de "
                    f"{MAX_FILE_SIZE // (1024*1024)}MB."
                )
        
        return value
    
    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Le prix ne peut pas être négatif.")
        if value > 1000000000:  # Max 1 billion
            raise serializers.ValidationError("Prix invalide.")
        return value
    
    def validate_area(self, value):
        if value < 0:
            raise serializers.ValidationError("La surface ne peut pas être négative.")
        if value > 1000000:
            raise serializers.ValidationError("Surface invalide.")
        return value
    
    def create(self, validated_data):
        images = validated_data.pop('images', [])
        location_data = validated_data.pop('location_data', {})
        
        # Sanitize location data
        location_data = sanitize_input(location_data)
        
        # Create or get location
        location, created = Location.objects.get_or_create(
            region=location_data.get('region', ''),
            city=location_data.get('city', ''),
            quarter=location_data.get('quarter', ''),
            defaults={
                'name': location_data.get('name', ''),
                'address': location_data.get('address', ''),
                'latitude': location_data.get('latitude'),
                'longitude': location_data.get('longitude'),
            }
        )
        
        # Create property
        validated_data['location'] = location
        validated_data['owner'] = self.context['request'].user
        
        property = Property.objects.create(**validated_data)
        
        # Add images
        for i, image_file in enumerate(images):
            PropertyImage.objects.create(
                property=property,
                image=image_file,
                is_primary=(i == 0),
                order=i
            )
        
        return property


class FavoriteSerializer(serializers.ModelSerializer):
    property = PropertySerializer(read_only=True)
    property_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Favorite
        fields = ['id', 'property', 'property_id', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate_property_id(self, value):
        # Validate UUID format
        try:
            value = str(value)
        except (TypeError, ValueError):
            raise serializers.ValidationError("Format d'UUID invalide.")
        return value


class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = ['id', 'query', 'filters', 'results_count', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate_query(self, value):
        return sanitize_input(value)
    
    def validate_filters(self, value):
        return sanitize_input(value)

