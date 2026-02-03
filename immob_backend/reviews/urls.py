from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReviewViewSet, ApplicationFeedbackViewSet

router = DefaultRouter()
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'feedback', ApplicationFeedbackViewSet, basename='feedback')

urlpatterns = [
    path('', include(router.urls)),
]