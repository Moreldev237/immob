from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.core.exceptions import ObjectDoesNotExist
import re
from .models import UserProfile, PasswordResetToken

User = get_user_model()


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


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'bio', 'website', 'facebook', 'twitter', 'instagram', 'linkedin',
            'preferred_language', 'notification_email', 'notification_sms'
        ]
    
    def validate_bio(self, value):
        return sanitize_input(value)
    
    def validate_website(self, value):
        if value:
            # Basic URL validation
            if not value.startswith(('http://', 'https://')):
                value = 'https://' + value
        return value
    
    def validate_facebook(self, value):
        if value:
            if not value.startswith(('http://', 'https://')):
                value = 'https://' + value
        return value
    
    def validate_twitter(self, value):
        if value:
            if not value.startswith(('http://', 'https://')):
                value = 'https://' + value
        return value
    
    def validate_instagram(self, value):
        if value:
            if not value.startswith(('http://', 'https://')):
                value = 'https://' + value
        return value
    
    def validate_linkedin(self, value):
        if value:
            if not value.startswith(('http://', 'https://')):
                value = 'https://' + value
        return value


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=False)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'phone_number',
            'profile_picture', 'is_agent', 'agency_name', 'license_number',
            'is_verified', 'profile', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'is_verified', 'date_joined', 'last_login']
    
    def validate_username(self, value):
        value = sanitize_input(value)
        if len(value) < 3:
            raise serializers.ValidationError("Le nom d'utilisateur doit contenir au moins 3 caractères.")
        if len(value) > 150:
            raise serializers.ValidationError("Le nom d'utilisateur ne peut pas dépasser 150 caractères.")
        # Only allow alphanumeric characters and underscores
        if not re.match(r'^\w+$', value):
            raise serializers.ValidationError("Le nom d'utilisateur ne peut contenir que des lettres, chiffres et underscores.")
        return value
    
    def validate_first_name(self, value):
        return sanitize_input(value)
    
    def validate_last_name(self, value):
        return sanitize_input(value)
    
    def validate_agency_name(self, value):
        return sanitize_input(value)
    
    def validate_license_number(self, value):
        return sanitize_input(value)
    
    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        
        # Mettre à jour l'utilisateur
        instance = super().update(instance, validated_data)
        
        # Mettre à jour le profil
        if profile_data:
            profile, created = UserProfile.objects.get_or_create(user=instance)
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        
        return instance


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    profile = UserProfileSerializer(required=False)
    
    class Meta:
        model = User
        fields = [
            'email', 'username', 'first_name', 'last_name', 'phone_number',
            'password', 'password2', 'profile', 'is_agent', 'agency_name',
            'license_number'
        ]
    
    def validate_username(self, value):
        value = sanitize_input(value)
        if len(value) < 3:
            raise serializers.ValidationError("Le nom d'utilisateur doit contenir au moins 3 caractères.")
        if len(value) > 150:
            raise serializers.ValidationError("Le nom d'utilisateur ne peut pas dépasser 150 caractères.")
        if not re.match(r'^\w+$', value):
            raise serializers.ValidationError("Le nom d'utilisateur ne peut contenir que des lettres, chiffres et underscores.")
        return value
    
    def validate_email(self, value):
        value = value.lower().strip()
        return value
    
    def validate_first_name(self, value):
        return sanitize_input(value)
    
    def validate_last_name(self, value):
        return sanitize_input(value)
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        profile_data = validated_data.pop('profile', None)
        password = validated_data.pop('password')
        
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        
        # Créer le profil utilisateur
        if profile_data:
            UserProfile.objects.create(user=user, **profile_data)
        else:
            UserProfile.objects.create(user=user)
        
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_or_email = serializers.CharField()
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Ajouter des claims personnalisés
        token['email'] = user.email
        token['username'] = user.username
        token['is_agent'] = user.is_agent
        token['is_verified'] = user.is_verified

        return token

    def validate(self, attrs):
        username_or_email = attrs.get('username_or_email')
        password = attrs.get('password')

        # Essayer de trouver l'utilisateur par username ou email
        try:
            user = User.objects.get_by_username_or_email(username_or_email)
        except ObjectDoesNotExist:
            raise serializers.ValidationError({
                'username_or_email': 'Aucun utilisateur trouvé avec ce nom d\'utilisateur ou email.'
            })

        # Vérifier le mot de passe
        if not user.check_password(password):
            raise serializers.ValidationError({
                'password': 'Mot de passe incorrect.'
            })

        # Vérifier si l'utilisateur est actif
        if not user.is_active:
            raise serializers.ValidationError({
                'username_or_email': 'Ce compte est désactivé.'
            })

        # Générer les tokens
        refresh = self.get_token(user)

        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

        # Ajouter des informations utilisateur supplémentaires
        data['user'] = UserSerializer(user).data

        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        # Normalize email
        value = value.lower().strip()
        
        # Check if user exists (but don't reveal this information)
        # Just validate format
        if '@' not in value:
            raise serializers.ValidationError("Format d'email invalide.")
        
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True)
    
    def validate_token(self, value):
        # Sanitize token input
        value = sanitize_input(value)
        if len(value) != 32:  # UUID hex string length
            raise serializers.ValidationError("Jeton de réinitialisation invalide.")
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Les mots de passe ne correspondent pas."})
        
        try:
            reset_token = PasswordResetToken.objects.get(
                token=attrs['token'],
                is_used=False
            )
            if not reset_token.is_valid():
                raise serializers.ValidationError({"token": "Le jeton de réinitialisation a expiré."})
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError({"token": "Jeton de réinitialisation invalide."})
        
        attrs['reset_token'] = reset_token
        return attrs

