from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import PropertyCategory, PropertyType, Location, Property, PropertyImage, Favorite, SearchHistory


@admin.register(PropertyCategory)
class PropertyCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'icon', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PropertyType)
class PropertyTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'description', 'created_at')
    list_filter = ('category',)
    search_fields = ('name', 'description', 'category__name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'city', 'quarter', 'address', 'created_at')
    list_filter = ('region', 'city')
    search_fields = ('name', 'city', 'quarter', 'address')
    readonly_fields = ('created_at', 'updated_at')


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1
    fields = ('image', 'caption', 'is_primary', 'order')
    raw_id_fields = ('property',)


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'property_type', 'location', 'status', 'price', 'currency', 'area', 'bedrooms', 'bathrooms', 'owner', 'is_featured', 'is_verified', 'views_count', 'favorites_count', 'created_at')
    list_filter = ('status', 'property_type', 'location__region', 'location__city', 'is_featured', 'is_verified', 'created_at')
    search_fields = ('title', 'description', 'owner__email', 'owner__username', 'location__city', 'location__quarter')
    ordering = ('-created_at',)
    readonly_fields = ('views_count', 'favorites_count', 'created_at', 'updated_at', 'published_at')
    raw_id_fields = ('property_type', 'location', 'owner', 'agent')
    inlines = [PropertyImageInline]
    
    fieldsets = (
        (_('Informations générales'), {'fields': ('title', 'description', 'property_type', 'location', 'status')}),
        (_('Prix et superficie'), {'fields': ('price', 'currency', 'area')}),
        (_('Caractéristiques'), {'fields': ('bedrooms', 'bathrooms', 'parking_spaces', 'has_kitchen', 'has_living_room', 'has_dining_room', 'has_balcony', 'has_garden', 'has_pool', 'has_garage', 'has_security', 'has_internet', 'has_ac')}),
        (_('Propriétaire/Agent'), {'fields': ('owner', 'agent')}),
        (_('Métadonnées'), {'fields': ('is_featured', 'is_verified', 'views_count', 'favorites_count', 'published_at', 'created_at', 'updated_at')}),
    )


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('property', 'caption', 'is_primary', 'order', 'created_at')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('property__title', 'caption')
    readonly_fields = ('created_at',)
    raw_id_fields = ('property',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'property', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'user__username', 'property__title')
    readonly_fields = ('created_at',)
    raw_id_fields = ('user', 'property')


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'query', 'results_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'user__username', 'query')
    readonly_fields = ('created_at',)
    raw_id_fields = ('user',)

