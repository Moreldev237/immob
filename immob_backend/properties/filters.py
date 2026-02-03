import django_filters
from .models import Property


class PropertyFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    min_area = django_filters.NumberFilter(field_name='area', lookup_expr='gte')
    max_area = django_filters.NumberFilter(field_name='area', lookup_expr='lte')
    min_bedrooms = django_filters.NumberFilter(field_name='bedrooms', lookup_expr='gte')
    max_bedrooms = django_filters.NumberFilter(field_name='bedrooms', lookup_expr='lte')
    min_bathrooms = django_filters.NumberFilter(field_name='bathrooms', lookup_expr='gte')
    max_bathrooms = django_filters.NumberFilter(field_name='bathrooms', lookup_expr='lte')
    
    location = django_filters.CharFilter(field_name='location__city', lookup_expr='icontains')
    region = django_filters.CharFilter(field_name='location__region')
    property_type = django_filters.CharFilter(field_name='property_type__name')
    
    has_pool = django_filters.BooleanFilter(field_name='has_pool')
    has_garage = django_filters.BooleanFilter(field_name='has_garage')
    has_security = django_filters.BooleanFilter(field_name='has_security')
    has_ac = django_filters.BooleanFilter(field_name='has_ac')
    
    class Meta:
        model = Property
        fields = [
            'status', 'property_type', 'min_price', 'max_price',
            'min_area', 'max_area', 'min_bedrooms', 'max_bedrooms',
            'min_bathrooms', 'max_bathrooms', 'location', 'region',
            'has_pool', 'has_garage', 'has_security', 'has_ac'
        ]