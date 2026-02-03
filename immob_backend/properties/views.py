from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg, Sum, Case, When, IntegerField
from django.core.cache import cache
from django.conf import settings
from django.shortcuts import get_object_or_404
from .models import Property, Favorite, SearchHistory, PropertyCategory
from .serializers import (
    PropertySerializer, PropertyCreateSerializer, 
    FavoriteSerializer, SearchHistorySerializer,
    PropertyCategorySerializer
)
from .filters import PropertyFilter


class PropertyViewSet(viewsets.ModelViewSet):
    """
    ViewSet optimisé pour les propriétés avec:
    - Cache Redis pour les listes et endpoints fréquents
    - Annotations pour éviter les requêtes N+1
    - Requêtes optimisées avec select_related et prefetch_related
    """
    
    def get_queryset(self):
        """Optimiser le queryset avec annotations et relations pré-chargées"""
        queryset = Property.objects.select_related(
            'property_type', 'location', 'owner', 'agent'
        ).prefetch_related(
            'images', 'amenities', 'property_type__category'
        ).annotate(
            favorites_annotate_count=Count('favorites', distinct=True),
            reviews_count=Count('reviews', distinct=True),
            reviews_avg_rating=Avg('reviews__rating', default=0),
            total_likes=Count('reviews__liked_by', distinct=True),
        ).filter(
            status__in=['for_sale', 'for_rent']
        )
        
        # Filtrer par statut (par défaut, exclure vendu/loué)
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filtrer les propriétés vérifiées si demandé
        verified_only = self.request.query_params.get('verified', None)
        if verified_only and verified_only.lower() == 'true':
            queryset = queryset.filter(is_verified=True)
        
        # Filtrer les propriétés en vedette si demandé
        featured_only = self.request.query_params.get('featured', None)
        if featured_only and featured_only.lower() == 'true':
            queryset = queryset.filter(is_featured=True)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PropertyCreateSerializer
        return PropertySerializer
    
    def list(self, request, *args, **kwargs):
        """Optimiser la liste avec cache"""
        # Créer une clé de cache basée sur les paramètres de requête
        cache_key = self._get_cache_key('property_list', request)
        
        # Essayer de récupérer du cache
        cached_response = cache.get(cache_key)
        if cached_response is not None:
            return Response(cached_response)
        
        # Exécuter la requête
        response = super().list(request, *args, **kwargs)
        
        # Mettre en cache la réponse
        cache.set(cache_key, response.data, settings.CACHE_TIMEOUT_PROPERTY_LIST)
        
        return response
    
    def retrieve(self, request, *args, **kwargs):
        """Optimiser le détail avec cache et incrémentation de vues"""
        # Créer une clé de cache basée sur l'ID de la propriété
        pk = kwargs.get('pk')
        cache_key = f'property_detail_{pk}'
        
        # Si c'est une mise à jour de vues (pas de cache)
        instance = self.get_object()
        
        # Incrémenter le compteur de vues (avec atomic update)
        from django.db.models import F
        Property.objects.filter(pk=pk).update(views_count=F('views_count') + 1)
        
        # Rafraîchir l'instance pour avoir la valeur mise à jour
        instance.refresh_from_db()
        
        serializer = self.get_serializer(instance)
        
        # Mettre en cache le détail
        cache.set(cache_key, serializer.data, settings.CACHE_TIMEOUT_PROPERTY_DETAIL)
        
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
        # Invalider le cache des listes
        self._invalidate_property_cache()
    
    def perform_update(self, serializer):
        serializer.save()
        # Invalider le cache
        self._invalidate_property_cache()
    
    def perform_destroy(self, instance):
        instance.delete()
        # Invalider le cache
        self._invalidate_property_cache()
    
    def _get_cache_key(self, prefix, request):
        """Générer une clé de cache basée sur les paramètres de requête"""
        params = dict(request.query_params)
        # Trier les paramètres pour une clé cohérente
        sorted_params = '&'.join(f'{k}={v}' for k, v in sorted(params.items()))
        return f'{prefix}:{hash(sorted_params)}' if sorted_params else prefix
    
    def _invalidate_property_cache(self):
        """Invalider tous les caches liés aux propriétés"""
        # En production, vous pourriez utiliser Redis pattern deletion
        cache.delete_pattern('property_list:*')
        cache.delete('property_stats')
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Récupérer les catégories avec cache"""
        cache_key = 'property_categories'
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return Response(cached_data)
        
        categories = PropertyCategory.objects.prefetch_related(
            'types', 'types__properties'
        ).annotate(
            property_count=Count('types__properties', distinct=True)
        ).order_by('name')
        
        serializer = PropertyCategorySerializer(categories, many=True)
        cache.set(cache_key, serializer.data, settings.CACHE_TIMEOUT_CATEGORIES)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Récupérer les propriétés en vedette avec cache"""
        cache_key = 'property_featured'
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return Response(cached_data)
        
        queryset = self.get_queryset().filter(is_featured=True)[:8]
        serializer = self.get_serializer(queryset, many=True)
        
        # Mettre en cache pour 10 minutes
        cache.set(cache_key, serializer.data, 600)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Récupérer les statistiques avec cache et optimisation"""
        cache_key = 'property_stats'
        cached_stats = cache.get(cache_key)
        
        if cached_stats is not None:
            return Response(cached_stats)
        
        # Une seule requête optimisée pour toutes les stats
        from django.db.models import Case, When, IntegerField, Value
        
        stats = Property.objects.aggregate(
            total_properties=Count('id'),
            for_sale=Count('id', filter=Q(status='for_sale')),
            for_rent=Count('id', filter=Q(status='for_rent')),
            featured_properties=Count('id', filter=Q(is_featured=True)),
            verified_properties=Count('id', filter=Q(is_verified=True)),
            total_views=Sum('views_count'),
            avg_price_for_sale=Avg('price', filter=Q(status='for_sale')),
            avg_price_for_rent=Avg('price', filter=Q(status='for_rent')),
        )
        
        # Calculer les totaux par type de propriété
        property_types_stats = Property.objects.values('property_type__name').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        response_data = {
            'total_properties': stats['total_properties'],
            'for_sale': stats['for_sale'],
            'for_rent': stats['for_rent'],
            'featured_properties': stats['featured_properties'],
            'verified_properties': stats['verified_properties'],
            'total_views': stats['total_views'] or 0,
            'avg_price_for_sale': round(stats['avg_price_for_sale'] or 0, 2),
            'avg_price_for_rent': round(stats['avg_price_for_rent'] or 0, 2),
            'top_property_types': list(property_types_stats),
        }
        
        cache.set(cache_key, response_data, settings.CACHE_TIMEOUT_STATS)
        
        return Response(response_data)
    
    @action(detail=False, methods=['get'])
    def search_suggestions(self, request):
        """Suggestions de recherche avec cache"""
        cache_key = 'search_suggestions'
        cached = cache.get(cache_key)
        
        if cached:
            return Response(cached)
        
        # Récupérer les termes de recherche populaires
        suggestions = SearchHistory.objects.values('search_term').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        terms = [s['search_term'] for s in suggestions]
        
        # Ajouter les villes populaires
        popular_cities = Property.objects.values_list('location__city', flat=True).distinct()[:10]
        
        response_data = {
            'search_terms': terms,
            'popular_cities': list(popular_cities),
        }
        
        cache.set(cache_key, response_data, 1800)  # 30 minutes
        return Response(response_data)


class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Favorite.objects.filter(
            user=self.request.user
        ).select_related(
            'property', 'property__location', 'property__property_type'
        ).prefetch_related('property__images')
    
    def create(self, request, *args, **kwargs):
        property_id = request.data.get('property_id')
        
        if not property_id:
            return Response(
                {'error': 'property_id est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        property_obj = get_object_or_404(Property, id=property_id)
        
        # Vérifier si déjà dans les favoris
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            property=property_obj
        )
        
        if not created:
            favorite.delete()
            return Response(
                {'message': 'Retiré des favoris', 'is_favorited': False},
                status=status.HTTP_200_OK
            )
        
        serializer = self.get_serializer(favorite)
        return Response(
            {'message': 'Ajouté aux favoris', 'is_favorited': True, 'favorite': serializer.data},
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def check(self, request):
        property_id = request.query_params.get('property_id')
        
        if not property_id:
            return Response(
                {'error': 'property_id est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        is_favorited = Favorite.objects.filter(
            user=request.user,
            property_id=property_id
        ).exists()
        
        return Response({'is_favorited': is_favorited})
    
    def perform_destroy(self, instance):
        instance.delete()
        # Invalider le cache de liste de favoris si nécessaire
        cache.delete(f'favorites_list_{self.request.user.id}')

