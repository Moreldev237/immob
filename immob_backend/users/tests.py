from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase
from rest_framework import status

from .models import UserProfile, PasswordResetToken
from .managers import CustomUserManager

User = get_user_model()


class UserModelTests(TestCase):
    """Tests pour le modèle User"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        self.user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpass123'
        }
    
    def test_create_user_with_email(self):
        """Test création d'utilisateur avec email valide"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_create_user_without_email_raises_error(self):
        """Test que la création sans email lève une erreur"""
        self.user_data['email'] = ''
        with self.assertRaises(ValueError):
            User.objects.create_user(**self.user_data)
    
    def test_create_user_with_unique_email(self):
        """Test que l'email doit être unique"""
        User.objects.create_user(**self.user_data)
        self.user_data['email'] = 'test@example.com'
        self.user_data['username'] = 'testuser2'
        with self.assertRaises(Exception):  # IntegrityError
            User.objects.create_user(**self.user_data)
    
    def test_email_normalization(self):
        """Test normalisation de l'email"""
        user = User.objects.create_user(
            email='Test@EXAMPLE.COM',
            username='testuser2',
            password='testpass123'
        )
        self.assertEqual(user.email, 'test@example.com')
    
    def test_create_superuser(self):
        """Test création d'un superutilisateur"""
        user = User.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='adminpass123'
        )
        self.assertEqual(user.email, 'admin@example.com')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)
    
    def test_create_superuser_must_have_is_staff(self):
        """Test que le superuser doit avoir is_staff=True"""
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='admin@example.com',
                username='admin',
                password='adminpass123',
                is_staff=False
            )
    
    def test_create_superuser_must_have_is_superuser(self):
        """Test que le superuser doit avoir is_superuser=True"""
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='admin@example.com',
                username='admin',
                password='adminpass123',
                is_superuser=False
            )
    
    def test_full_name_property(self):
        """Test de la propriété full_name"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.full_name, 'Test User')
    
    def test_full_name_property_with_empty_names(self):
        """Test full_name avec des noms vides"""
        user = User.objects.create_user(
            email='test2@example.com',
            username='testuser2',
            password='testpass123'
        )
        self.assertEqual(user.full_name, '')
    
    def test_user_str_representation(self):
        """Test de la représentation string de l'utilisateur"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'test@example.com')
    
    def test_user_is_agent_default_false(self):
        """Test que is_agent est False par défaut"""
        user = User.objects.create_user(**self.user_data)
        self.assertFalse(user.is_agent)
    
    def test_user_is_verified_default_false(self):
        """Test que is_verified est False par défaut"""
        user = User.objects.create_user(**self.user_data)
        self.assertFalse(user.is_verified)
    
    def test_user_phone_number_validation(self):
        """Test validation du numéro de téléphone"""
        self.user_data['phone_number'] = '+237612345678'
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.phone_number, '+237612345678')
    
    def test_user_phone_number_invalid_format(self):
        """Test numéro de téléphone avec format invalide"""
        self.user_data['phone_number'] = 'invalid'
        with self.assertRaises(ValidationError):
            user = User.objects.create_user(**self.user_data)
            user.full_clean()


class UserProfileTests(TestCase):
    """Tests pour le modèle UserProfile"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        self.user = User.objects.create_user(
            email='profile@example.com',
            username='profileuser',
            password='testpass123'
        )
    
    def test_create_user_profile(self):
        """Test création du profil utilisateur"""
        profile = UserProfile.objects.create(user=self.user)
        self.assertEqual(profile.user, self.user)
        self.assertEqual(str(profile), 'Profil de profile@example.com')
    
    def test_user_profile_default_preferences(self):
        """Test des préférences par défaut du profil"""
        profile = UserProfile.objects.create(user=self.user)
        self.assertEqual(profile.preferred_language, 'fr')
        self.assertTrue(profile.notification_email)
        self.assertFalse(profile.notification_sms)
    
    def test_user_profile_bio_update(self):
        """Test mise à jour de la bio"""
        profile = UserProfile.objects.create(user=self.user)
        profile.bio = 'Nouvelle bio'
        profile.save()
        self.assertEqual(profile.bio, 'Nouvelle bio')
    
    def test_user_profile_social_links(self):
        """Test des liens sociaux"""
        profile = UserProfile.objects.create(
            user=self.user,
            website='https://example.com',
            facebook='https://facebook.com/example',
            twitter='https://twitter.com/example'
        )
        self.assertEqual(profile.website, 'https://example.com')
        self.assertEqual(profile.facebook, 'https://facebook.com/example')


class PasswordResetTokenTests(TestCase):
    """Tests pour le modèle PasswordResetToken"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        self.user = User.objects.create_user(
            email='reset@example.com',
            username='resetuser',
            password='testpass123'
        )
    
    def test_create_password_reset_token(self):
        """Test création d'un token de réinitialisation"""
        token = PasswordResetToken.objects.create(
            user=self.user,
            token='test-token-123',
            expires_at=timezone.now() + timedelta(hours=24)
        )
        self.assertEqual(token.user, self.user)
        self.assertEqual(token.token, 'test-token-123')
        self.assertFalse(token.is_used)
    
    def test_password_reset_token_is_valid(self):
        """Test validation du token de réinitialisation"""
        token = PasswordResetToken.objects.create(
            user=self.user,
            token='test-token-123',
            expires_at=timezone.now() + timedelta(hours=24)
        )
        self.assertTrue(token.is_valid())
    
    def test_password_reset_token_expired(self):
        """Test token expiré"""
        token = PasswordResetToken.objects.create(
            user=self.user,
            token='test-token-123',
            expires_at=timezone.now() - timedelta(hours=1)
        )
        self.assertFalse(token.is_valid())
    
    def test_password_reset_token_used(self):
        """Test token déjà utilisé"""
        token = PasswordResetToken.objects.create(
            user=self.user,
            token='test-token-123',
            expires_at=timezone.now() + timedelta(hours=24)
        )
        token.is_used = True
        token.save()
        self.assertFalse(token.is_valid())
    
    def test_str_representation(self):
        """Test représentation string du token"""
        token = PasswordResetToken.objects.create(
            user=self.user,
            token='test-token-123',
            expires_at=timezone.now() + timedelta(hours=24)
        )
        self.assertIn('reset@example.com', str(token))


class CustomUserManagerTests(TestCase):
    """Tests pour CustomUserManager"""
    
    def test_create_user_manager(self):
        """Test création utilisateur via manager"""
        manager = CustomUserManager()
        manager.model = User
        user = manager.create_user(
            email='manager@example.com',
            password='testpass123'
        )
        self.assertEqual(user.email, 'manager@example.com')
    
    def test_get_by_username_or_email_with_username(self):
        """Test récupération utilisateur par username"""
        User.objects.create_user(
            email='lookup@example.com',
            username='lookupuser',
            password='testpass123'
        )
        manager = CustomUserManager()
        manager.model = User
        user = manager.get_by_username_or_email('lookupuser')
        self.assertEqual(user.username, 'lookupuser')
    
    def test_get_by_username_or_email_with_email(self):
        """Test récupération utilisateur par email"""
        User.objects.create_user(
            email='lookup@example.com',
            username='lookupuser',
            password='testpass123'
        )
        manager = CustomUserManager()
        manager.model = User
        user = manager.get_by_username_or_email('lookup@example.com')
        self.assertEqual(user.email, 'lookup@example.com')
    
    def test_get_by_username_or_email_not_found(self):
        """Test utilisateur non trouvé"""
        manager = CustomUserManager()
        manager.model = User
        with self.assertRaises(Exception):
            manager.get_by_username_or_email('nonexistent')


class UserSerializerTests(APITestCase):
    """Tests pour les serializers User"""
    
    def setUp(self):
        """Configuration initiale"""
        self.user = User.objects.create_user(
            email='serializer@example.com',
            username='serializeruser',
            password='testpass123'
        )
    
    def test_user_serializer_fields(self):
        """Test champs du serializer"""
        from .serializers import UserSerializer
        serializer = UserSerializer(self.user)
        data = serializer.data
        self.assertEqual(data['email'], 'serializer@example.com')
        self.assertEqual(data['username'], 'serializeruser')
        self.assertIn('id', data)
        self.assertIn('date_joined', data)
    
    def test_user_create_serializer_valid(self):
        """Test serializer de création valide"""
        from .serializers import UserCreateSerializer
        data = {
            'email': 'new@example.com',
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'newpass123',
            'password2': 'newpass123'
        }
        serializer = UserCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_user_create_serializer_password_mismatch(self):
        """Test mot de passe différent"""
        from .serializers import UserCreateSerializer
        data = {
            'email': 'new@example.com',
            'username': 'newuser',
            'password': 'newpass123',
            'password2': 'differentpassword'
        }
        serializer = UserCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)


class UserViewSetTests(APITestCase):
    """Tests pour UserViewSet"""
    
    def setUp(self):
        """Configuration initiale"""
        self.user = User.objects.create_user(
            email='viewset@example.com',
            username='viewsetuser',
            password='testpass123'
        )
    
    def test_user_registration(self):
        """Test inscription utilisateur"""
        data = {
            'email': 'register@example.com',
            'username': 'registeruser',
            'password': 'registerpass123',
            'password2': 'registerpass123'
        }
        response = self.client.post('/api/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)
    
    def test_user_login(self):
        """Test connexion utilisateur"""
        data = {
            'username_or_email': 'viewset@example.com',
            'password': 'testpass123'
        }
        response = self.client.post('/api/token/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_user_profile_requires_auth(self):
        """Test que profile nécessite une authentification"""
        response = self.client.get('/api/users/profile/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_user_profile_authenticated(self):
        """Test accès au profil avec auth"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/users/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'viewset@example.com')

