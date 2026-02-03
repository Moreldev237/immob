from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PropertyViewSet, FavoriteViewSet

router = DefaultRouter()
router.register(r'properties', PropertyViewSet, basename='property')
router.register(r'favorites', FavoriteViewSet, basename='favorite')

urlpatterns = [
    path('', include(router.urls)),

    # Additional endpoints at root level for easier access
    path('featured/', PropertyViewSet.as_view({'get': 'featured'}), name='property-featured'),
    path('stats/', PropertyViewSet.as_view({'get': 'stats'}), name='property-stats'),
]
