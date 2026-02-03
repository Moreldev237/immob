from rest_framework import serializers
from django.contrib.auth import get_user_model
from properties.models import Property
from .models import Review, ReviewLike, ReviewImage, ApplicationFeedback
import re

User = get_user_model()

# Maximum file upload size (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_IMAGES_PER_REVIEW = 5


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


class ReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewImage
        fields = ['id', 'image', 'caption', 'created_at']
    
    def validate_image(self, value):
        # Validate file size
        if value.size > MAX_FILE_SIZE:
            raise serializers.ValidationError(f"L'image ne peut pas dépasser {MAX_FILE_SIZE // (1024*1024)}MB.")
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Type de fichier non autorisé. Utilisez JPEG, PNG, GIF ou WebP.")
        
        return value


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    property_title = serializers.SerializerMethodField()
    user_profile_picture = serializers.SerializerMethodField()
    images = ReviewImageSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'user', 'user_profile_picture', 'property', 'property_title',
            'rating', 'title', 'comment', 'is_verified_purchase', 'likes_count',
            'is_approved', 'is_edited', 'images', 'is_liked', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'likes_count']
    
    def validate_title(self, value):
        return sanitize_input(value)
    
    def validate_comment(self, value):
        return sanitize_input(value)
    
    def get_property_title(self, obj):
        return obj.property.title
    
    def get_user_profile_picture(self, obj):
        if obj.user.profile_picture:
            return obj.user.profile_picture.url
        return None
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ReviewLike.objects.filter(user=request.user, review=obj).exists()
        return False
    
    def validate(self, attrs):
        user = self.context['request'].user
        property_id = attrs.get('property').id
        
        # Check if user already reviewed this property
        if Review.objects.filter(user=user, property_id=property_id).exists():
            raise serializers.ValidationError(
                "Vous avez déjà donné un avis pour cette propriété."
            )
        
        return attrs


class ReviewCreateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
        max_length=MAX_IMAGES_PER_REVIEW
    )
    
    class Meta:
        model = Review
        fields = ['property', 'rating', 'title', 'comment', 'images']
    
    def validate_title(self, value):
        value = sanitize_input(value)
        if len(value) < 3:
            raise serializers.ValidationError("Le titre doit contenir au moins 3 caractères.")
        if len(value) > 100:
            raise serializers.ValidationError("Le titre ne peut pas dépasser 100 caractères.")
        return value
    
    def validate_comment(self, value):
        value = sanitize_input(value)
        if len(value) < 10:
            raise serializers.ValidationError("Le commentaire doit contenir au moins 10 caractères.")
        if len(value) > 5000:
            raise serializers.ValidationError("Le commentaire ne peut pas dépasser 5000 caractères.")
        return value
    
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("La note doit être comprise entre 1 et 5.")
        return value
    
    def validate_images(self, value):
        if len(value) > MAX_IMAGES_PER_REVIEW:
            raise serializers.ValidationError(
                f"Vous ne pouvez pas télécharger plus de {MAX_IMAGES_PER_REVIEW} images."
            )
        
        for image in value:
            if image.size > MAX_FILE_SIZE:
                raise serializers.ValidationError(
                    f"L'image {image.name} dépasse la taille maximale de "
                    f"{MAX_FILE_SIZE // (1024*1024)}MB."
                )
        
        return value
    
    def create(self, validated_data):
        images = validated_data.pop('images', [])
        validated_data['user'] = self.context['request'].user
        
        review = Review.objects.create(**validated_data)
        
        # Add images
        for image_file in images:
            ReviewImage.objects.create(review=review, image=image_file)
        
        return review


class ReviewLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewLike
        fields = ['id', 'review', 'created_at']
        read_only_fields = ['id', 'created_at']


class ApplicationFeedbackSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField()
    
    class Meta:
        model = ApplicationFeedback
        fields = [
            'id', 'user', 'user_email', 'feedback_type', 'rating', 'title',
            'message', 'email', 'is_resolved', 'response', 'responded_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'response', 'responded_at']
    
    def validate_title(self, value):
        return sanitize_input(value)
    
    def validate_message(self, value):
        return sanitize_input(value)
    
    def validate_email(self, value):
        if value:
            return value.lower().strip()
        return value
    
    def get_user_email(self, obj):
        return obj.user.email if obj.user else None
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

