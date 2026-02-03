from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Avg
from django.core.cache import cache
from django.conf import settings
from django.shortcuts import get_object_or_404

from .models import Review, ReviewLike, ApplicationFeedback
from .serializers import (
    ReviewSerializer, ReviewCreateSerializer, 
    ReviewLikeSerializer, ApplicationFeedbackSerializer
)


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet optimisé pour les reviews avec:
    - Cache Redis pour les listes
    - Annotations pour éviter les requêtes N+1
    - select_related et prefetch_related optimisés
    """
    
    def get_queryset(self):
        """Optimiser le queryset avec annotations"""
        queryset = Review.objects.filter(
            is_approved=True
        ).select_related(
            'user', 'property', 'property__property_type', 'property__location'
        ).prefetch_related(
            'images', 'likes', 'user__profile'
        ).annotate(
            likes_annotate_count=Count('likes', distinct=True),
            user_has_liked=Count(
                'likes',
                filter=Q(likes__user=self.request.user) if self.request.user.is_authenticated else None,
                distinct=True
            )
        )
        
        # Filtrer par propriété si spécifié
        property_id = self.request.query_params.get('property', None)
        if property_id:
            queryset = queryset.filter(property_id=property_id)
        
        # Filtrer par utilisateur si spécifié
        user_id = self.request.query_params.get('user', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filtrer par note minimale si spécifié
        min_rating = self.request.query_params.get('min_rating', None)
        if min_rating:
            queryset = queryset.filter(rating__gte=min_rating)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """Optimiser la liste avec cache"""
        cache_key = self._get_cache_key('review_list', request)
        cached_response = cache.get(cache_key)
        
        if cached_response is not None:
            return Response(cached_response)
        
        response = super().list(request, *args, **kwargs)
        
        # Mettre en cache la réponse
        cache.set(cache_key, response.data, settings.CACHE_TIMEOUT_REVIEWS)
        
        return response
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ReviewCreateSerializer
        return ReviewSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        # Invalider le cache des reviews
        self._invalidate_review_cache()
    
    def perform_update(self, serializer):
        serializer.save()
        self._invalidate_review_cache()
    
    def perform_destroy(self, instance):
        instance.delete()
        self._invalidate_review_cache()
    
    def _get_cache_key(self, prefix, request):
        """Générer une clé de cache basée sur les paramètres de requête"""
        params = dict(request.query_params)
        sorted_params = '&'.join(f'{k}={v}' for k, v in sorted(params.items()))
        return f'{prefix}:{hash(sorted_params)}' if sorted_params else prefix
    
    def _invalidate_review_cache(self):
        """Invalider tous les caches liés aux reviews"""
        cache.delete_pattern('review_list:*')
        cache.delete('property_reviews_stats')
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Ajouter/retirer un like avec optimisations"""
        review = self.get_object()
        
        # Vérifier si déjà liké
        like, created = ReviewLike.objects.get_or_create(
            user=request.user,
            review=review
        )
        
        if not created:
            like.delete()
            return Response({'message': 'Like retiré', 'is_liked': False})
        
        return Response({'message': 'Like ajouté', 'is_liked': True})
    
    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        """Récupérer les reviews de l'utilisateur avec cache"""
        cache_key = f'my_reviews_{request.user.id}'
        cached = cache.get(cache_key)
        
        if cached:
            return Response(cached)
        
        reviews = Review.objects.filter(
            user=request.user
        ).select_related(
            'property', 'property__location'
        ).prefetch_related('images').order_by('-created_at')
        
        serializer = self.get_serializer(reviews, many=True)
        
        # Cache pour 2 minutes
        cache.set(cache_key, serializer.data, 120)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def property_reviews_stats(self, request):
        """Statistiques des reviews pour une propriété avec cache"""
        property_id = request.query_params.get('property_id')
        
        if not property_id:
            return Response(
                {'error': 'property_id est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cache_key = f'review_stats_{property_id}'
        cached = cache.get(cache_key)
        
        if cached:
            return Response(cached)
        
        stats = Review.objects.filter(
            property_id=property_id,
            is_approved=True
        ).aggregate(
            total_reviews=Count('id'),
            avg_rating=Avg('rating'),
            rating_distribution=Count('rating', output_field=IntegerField())
        )
        
        # Distribution des notes
        rating_dist = Review.objects.filter(
            property_id=property_id,
            is_approved=True
        ).values('rating').annotate(
            count=Count('id')
        ).order_by('rating')
        
        response_data = {
            'total_reviews': stats['total_reviews'] or 0,
            'avg_rating': round(stats['avg_rating'] or 0, 2),
            'rating_distribution': {r['rating']: r['count'] for r in rating_dist},
        }
        
        cache.set(cache_key, response_data, 600)  # 10 minutes
        return Response(response_data)


class ApplicationFeedbackViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationFeedbackSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return ApplicationFeedback.objects.all().select_related('user').order_by('-created_at')
        return ApplicationFeedback.objects.filter(user=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save()
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def respond(self, request, pk=None):
        feedback = self.get_object()
        response_text = request.data.get('response', '')
        
        if not response_text:
            return Response(
                {'error': 'Le texte de réponse est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        feedback.response = response_text
        feedback.is_resolved = True
        feedback.responded_at = timezone.now()
        feedback.save()
        
        # Envoyer une notification par email si l'utilisateur a fourni un email
        if feedback.email:
            send_mail(
                subject=f"Réponse à votre feedback: {feedback.title}",
                message=f"Cher utilisateur,\n\nVoici notre réponse à votre feedback:\n\n{response_text}\n\nCordialement,\nL'équipe IMMOB",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[feedback.email],
                fail_silently=True,
            )
        
        return Response({'message': 'Réponse envoyée avec succès'})


# Import manquant pour timezone
from django.utils import timezone
from django.core.mail import send_mail
from django.db.models import IntegerField

