from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model"""
    
    is_read_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'user',
            'title',
            'message',
            'notification_type',
            'is_read',
            'is_read_display',
            'read_at',
            'link',
            'created_at',
        ]
        read_only_fields = ['id', 'user', 'created_at']


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating notifications"""
    
    class Meta:
        model = Notification
        fields = [
            'title',
            'message',
            'notification_type',
            'link',
        ]
    
    def create(self, validated_data):
        # Set the user from the request context
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class NotificationMarkReadSerializer(serializers.Serializer):
    """Serializer for marking notifications as read"""
    
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text=_('Liste des IDs de notifications à marquer comme lues. Si vide, toutes seront marquées.')
    )
    
    def validate_notification_ids(self, value):
        if value and len(value) == 0:
            raise serializers.ValidationError(_('La liste ne peut pas être vide.'))
        return value


class UnreadCountSerializer(serializers.Serializer):
    """Serializer for unread notification count"""
    
    count = serializers.IntegerField()
    unread_notifications = NotificationSerializer(many=True, read_only=True)

