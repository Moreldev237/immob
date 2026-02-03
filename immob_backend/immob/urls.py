from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from core.views import (
    index_view, login_view, register_view, properties_view,
    property_detail_view, profile_view, favorites_view, reviews_view, contact_view
)

schema_view = get_schema_view(
    openapi.Info(
        title="IMMOB API",
        default_version='v1',
        description="API pour l'application de gestion immobilière IMMOB",
        terms_of_service="https://www.immob.cm/terms/",
        contact=openapi.Contact(email="contact@immob.cm"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Frontend - Serve index at root
    path('', index_view, name='index'),
    
    # Frontend pages
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('properties/', properties_view, name='properties'),
    path('properties/<uuid:property_id>/', property_detail_view, name='property_detail'),
    path('profile/', profile_view, name='profile'),
    path('favorites/', favorites_view, name='favorites'),
    path('reviews/', reviews_view, name='reviews'),
    path('contact/', contact_view, name='contact'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API Endpoints
    path('api/users/', include('users.urls')),
    path('api/properties/', include('properties.urls')),
    path('api/reviews/', include('reviews.urls')),
    path('api/notifications/', include('notifications.urls')),
    
    # JWT Authentication
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)