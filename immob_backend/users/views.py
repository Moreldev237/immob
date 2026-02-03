from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django_ratelimit.decorators import ratelimit
import uuid
import logging

from .models import UserProfile, PasswordResetToken
from .serializers import (
    UserSerializer, UserCreateSerializer, CustomTokenObtainPairSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer
)

logger = logging.getLogger(__name__)
User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'password_reset', 'password_reset_confirm']:
            return [permissions.AllowAny()]
        return super().get_permissions()
    
    def get_object(self):
        if self.action in ['update', 'partial_update', 'destroy', 'profile']:
            return self.request.user
        return super().get_object()
    
    @method_decorator(ratelimit(key='ip', rate='5/h', block=True))
    @action(detail=False, methods=['get', 'put', 'patch'])
    def profile(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)
    
    @method_decorator(ratelimit(key='ip', rate='3/h', block=True))
    @action(detail=False, methods=['post'])
    def password_reset(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            
            # Créer un token de réinitialisation
            token = uuid.uuid4().hex
            expires_at = timezone.now() + timezone.timedelta(hours=1)  # Réduit à 1 heure pour la sécurité
            
            # Supprimer les anciens tokens non utilisés
            PasswordResetToken.objects.filter(
                user=user,
                is_used=False
            ).delete()
            
            reset_token = PasswordResetToken.objects.create(
                user=user,
                token=token,
                expires_at=expires_at
            )
            
            # Envoyer l'email de réinitialisation
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
            
            subject = "Réinitialisation de votre mot de passe IMMOB"
            html_message = render_to_string('emails/password_reset.html', {
                'user': user,
                'reset_url': reset_url,
            })
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.warning(f"Password reset requested for email: {email}")
            
        except User.DoesNotExist:
            # Ne pas révéler si l'email existe ou non
            pass
        
        return Response({
            'message': 'Un email de réinitialisation a été envoyé si le compte existe.'
        })
    
    @method_decorator(ratelimit(key='ip', rate='10/h', block=True))
    @action(detail=False, methods=['post'])
    def password_reset_confirm(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        reset_token = serializer.validated_data['reset_token']
        new_password = serializer.validated_data['new_password']
        
        # Vérifier si le token est valide
        if not reset_token.is_valid():
            return Response(
                {'error': 'Le token de réinitialisation est invalide ou expiré.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mettre à jour le mot de passe
        user = reset_token.user
        user.set_password(new_password)
        user.save()
        
        # Marquer le token comme utilisé
        reset_token.is_used = True
        reset_token.save()
        
        # Invalider tous les tokens de session
        RefreshToken.for_user(user)
        
        logger.warning(f"Password reset completed for user: {user.email}")
        
        return Response({
            'message': 'Mot de passe réinitialisé avec succès.'
        })
    
    @method_decorator(ratelimit(key='ip', rate='20/h', block=True))
    @action(detail=False, methods=['post'])
    def logout(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Déconnexion réussie.'})
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(ratelimit(key='ip', rate='10/h', block=True), name='post')
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        # Journaliser les tentatives de connexion échouées
        username = request.data.get('email', '')
        if username:
            logger.warning(f"Login attempt for email: {username}")
        
        return super().post(request, *args, **kwargs)

