from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
import logging

from .models import Notification
from .serializers import (
    NotificationSerializer,
    NotificationCreateSerializer,
    NotificationMarkReadSerializer,
)

logger = logging.getLogger(__name__)


@method_decorator(ratelimit(key='user', rate='30/h', block=True), name='dispatch')
class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user notifications.
    
    Endpoints:
    - GET /api/notifications/ - List all notifications for the authenticated user
    - POST /api/notifications/ - Create a new notification (for system use)
    - GET /api/notifications/{id}/ - Retrieve a specific notification
    - PUT /api/notifications/{id}/ - Update a notification
    - PATCH /api/notifications/{id}/ - Partial update a notification
    - DELETE /api/notifications/{id}/ - Delete a notification
    - POST /api/notifications/mark_all_read/ - Mark all notifications as read
    - POST /api/notifications/mark_read/ - Mark specific notifications as read
    - GET /api/notifications/unread_count/ - Get unread count
    """
    
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return notifications for the authenticated user, ordered by creation date"""
        return Notification.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return NotificationCreateSerializer
        return NotificationSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return super().get_permissions()
    
    def list(self, request, *args, **kwargs):
        """List all notifications for the authenticated user"""
        queryset = self.get_queryset()
        
        # Optional: Filter by read status
        is_read = request.query_params.get('is_read')
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')
        
        # Optional: Filter by type
        notification_type = request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'unread_count': queryset.filter(is_read=False).count(),
            'notifications': serializer.data
        })
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific notification and mark as read"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # Auto-mark as read when retrieved
        if not instance.is_read:
            instance.mark_as_read()
            instance.refresh_from_db()
            serializer = self.get_serializer(instance)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get the count of unread notifications"""
        count = self.get_queryset().filter(is_read=False).count()
        unread_notifications = self.get_queryset().filter(is_read=False)[:5]
        
        return Response({
            'count': count,
            'unread_notifications': NotificationSerializer(unread_notifications, many=True).data
        })
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read for the authenticated user"""
        queryset = self.get_queryset().filter(is_read=False)
        count = queryset.count()
        
        if count > 0:
            now = timezone.now()
            queryset.update(is_read=True, read_at=now)
            logger.info(f"Marked {count} notifications as read for user {request.user.email}")
        
        return Response({
            'message': f'{count} notifications marked as read.',
            'count': count
        })
    
    @action(detail=False, methods=['post'])
    def mark_read(self, request):
        """Mark specific notifications as read"""
        serializer = NotificationMarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        notification_ids = serializer.validated_data.get('notification_ids', [])
        
        if notification_ids:
            # Mark specific notifications as read
            queryset = self.get_queryset().filter(id__in=notification_ids, is_read=False)
            count = queryset.count()
            now = timezone.now()
            queryset.update(is_read=True, read_at=now)
            
            logger.info(f"Marked {count} specific notifications as read for user {request.user.email}")
            
            return Response({
                'message': f'{count} notifications marked as read.',
                'count': count
            })
        else:
            # If no IDs provided, mark the most recent unread notification
            instance = self.get_queryset().filter(is_read=False).first()
            if instance:
                instance.mark_as_read()
                return Response({
                    'message': '1 notification marked as read.',
                    'count': 1
                })
            return Response({
                'message': 'No unread notifications to mark.',
                'count': 0
            })
    
    def create(self, request, *args, **kwargs):
        """Create a new notification"""
        # Only allow creation for the authenticated user (self-notification)
        # or by system/admin (you might want to add admin checks here)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Ensure the user can only create notifications for themselves
        if serializer.validated_data.get('user') != request.user:
            # If no user specified, use the request user
            serializer.validated_data['user'] = request.user
        
        notification = serializer.save()
        
        logger.info(f"Created notification {notification.id} for user {request.user.email}")
        
        output_serializer = NotificationSerializer(notification)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    def destroy(self, request, *args, **kwargs):
        """Delete a notification"""
        instance = self.get_object()
        notification_id = instance.id
        instance.delete()
        
        logger.info(f"Deleted notification {notification_id} for user {request.user.email}")
        
        return Response(status=status.HTTP_204_NO_CONTENT)

