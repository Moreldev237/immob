from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Review, ReviewLike, ReviewImage, ApplicationFeedback


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'property', 'rating', 'title', 'is_verified_purchase', 'is_approved', 'likes_count', 'is_edited', 'created_at')
    list_filter = ('rating', 'is_verified_purchase', 'is_approved', 'is_edited', 'created_at')
    search_fields = ('user__email', 'user__username', 'property__title', 'title', 'comment')
    ordering = ('-created_at',)
    readonly_fields = ('likes_count', 'created_at', 'updated_at')
    raw_id_fields = ('user', 'property')
    
    fieldsets = (
        (_('Avis'), {'fields': ('user', 'property', 'rating', 'title', 'comment')}),
        (_('Statut'), {'fields': ('is_verified_purchase', 'is_approved', 'is_edited')}),
        (_('Métadonnées'), {'fields': ('likes_count', 'created_at', 'updated_at')}),
    )


@admin.register(ReviewLike)
class ReviewLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'review', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'user__username', 'review__id', 'review__property__title')
    readonly_fields = ('created_at',)
    raw_id_fields = ('user', 'review')


@admin.register(ReviewImage)
class ReviewImageAdmin(admin.ModelAdmin):
    list_display = ('review', 'caption', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('review__id', 'review__user__email', 'caption')
    readonly_fields = ('created_at',)
    raw_id_fields = ('review',)


@admin.register(ApplicationFeedback)
class ApplicationFeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'feedback_type', 'rating', 'title', 'is_resolved', 'created_at')
    list_filter = ('feedback_type', 'is_resolved', 'rating', 'created_at')
    search_fields = ('user__email', 'title', 'message', 'email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'responded_at')
    raw_id_fields = ('user',)
    
    fieldsets = (
        (_('Feedback'), {'fields': ('user', 'feedback_type', 'rating', 'title', 'message', 'email')}),
        (_('Réponse'), {'fields': ('is_resolved', 'response', 'responded_at')}),
        (_('Dates'), {'fields': ('created_at', 'updated_at')}),
    )

