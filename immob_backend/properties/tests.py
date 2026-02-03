from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Property, PropertyCategory, PropertyType, Location, PropertyImage, Favorite, SearchHistory

User = get_user_model()


class PropertyCategoryTests(TestCase):
    """Tests pour le modèle PropertyCategory"""
    
    def test_create_category(self):
        """Test création d'une catégorie"""
        category = PropertyCategory.objects.create(
            name='Appartement',
            description='Logements en appartement'
        )
        self.assertEqual(category.name, 'Appartement')
        self.assertEqual(str(category), 'Appartement')
    
    def test_category_ordering(self):
        """Test ordering des catégories"""
        cat2 = PropertyCategory.objects.create(name='Maison', order=2)
        cat1 = PropertyCategory.objects.create(name='Bureau', order=1)
        categories = list(PropertyCategory.objects.all())
        self.assertEqual(categories[0].name, 'Bureau')
        self.assertEqual(categories[1].name, 'Maison')


class PropertyTypeTests(TestCase):
    """Tests pour le modèle PropertyType"""
    
    def setUp(self):
        """Configuration initiale"""
        self.category = PropertyCategory.objects.create(
            name='Appartement',
            description='Logements en appartement'
        )
    
    def test_create_property_type(self):
        """Test création d'un type de propriété"""
        prop_type = PropertyType.objects.create(
            name='F2',
            category=self.category,
            description='Appartement 2 pièces'
        )
        self.assertEqual(prop_type.name, 'F2')
        self.assertEqual(str(prop_type), 'F2 (Appartement)')
        self.assertEqual(prop_type.category, self.category)


class LocationTests(TestCase):
    """Tests pour le modèle Location"""
    
    def test_create_location(self):
        """Test création d'une localisation"""
        location = Location.objects.create(
            name='Centre ville',
            region='centre',
            city='Yaoundé',
            quarter='Biyem-assi',
            address='Rue 1234, Biyem-assi'
        )
        self.assertEqual(location.city, 'Yaoundé')
        self.assertEqual(location.quarter, 'Biyem-assi')
        self.assertEqual(str(location), 'Yaoundé, Biyem-assi')
    
    def test_location_with_coordinates(self):
        """Test localisation avec coordonnées GPS"""
        location = Location.objects.create(
            name='Centre ville',
            region='centre',
            city='Douala',
            address='Rue principale',
            latitude=Decimal('4.051100'),
            longitude=Decimal('9.767900')
        )
        self.assertIsNotNone(location.latitude)
        self.assertIsNotNone(location.longitude)
    
    def test_location_region_choices(self):
        """Test des choix de région"""
        location = Location.objects.create(
            name='Test',
            region='littoral',
            city='Douala',
            address='Test address'
        )
        self.assertEqual(location.region, 'littoral')
    
    def test_location_str_with_no_quarter(self):
        """Test str sans quartier"""
        location = Location.objects.create(
            name='Test',
            region='centre',
            city='Yaoundé',
            address='Test address',
            quarter=None
        )
        self.assertEqual(str(location), 'Yaoundé, ')


class PropertyTests(TestCase):
    """Tests pour le modèle Property"""
    
    def setUp(self):
        """Configuration initiale"""
        self.user = User.objects.create_user(
            email='property@example.com',
            username='propertyuser',
            password='testpass123'
        )
        self.category = PropertyCategory.objects.create(
            name='Appartement',
            description='Logements'
        )
        self.property_type = PropertyType.objects.create(
            name='F3',
            category=self.category
        )
        self.location = Location.objects.create(
            name='Centre',
            region='centre',
            city='Yaoundé',
            address='Rue test'
        )
    
    def test_create_property(self):
        """Test création d'une propriété"""
        property = Property.objects.create(
            title='Superbe Appartement F3',
            description='Un bel appartement bien situé',
            property_type=self.property_type,
            location=self.location,
            owner=self.user,
            price=Decimal('15000000'),
            area=Decimal('75.50'),
            bedrooms=3,
            bathrooms=2
        )
        self.assertEqual(property.title, 'Superbe Appartement F3')
        self.assertEqual(property.status, 'pending')
        self.assertEqual(property.price, Decimal('15000000'))
    
    def test_property_auto_publish_date_for_sale(self):
        """Test date de publication automatique pour 'à vendre'"""
        property = Property.objects.create(
            title='Property For Sale',
            description='Description',
            property_type=self.property_type,
            location=self.location,
            owner=self.user,
            price=Decimal('10000000'),
            area=Decimal('50.00'),
            status='for_sale'
        )
        self.assertIsNotNone(property.published_at)
    
    def test_property_auto_publish_date_for_rent(self):
        """Test date de publication automatique pour 'à louer'"""
        property = Property.objects.create(
            title='Property For Rent',
            description='Description',
            property_type=self.property_type,
            location=self.location,
            owner=self.user,
            price=Decimal('50000'),
            area=Decimal('40.00'),
            status='for_rent'
        )
        self.assertIsNotNone(property.published_at)
    
    def test_property_no_auto_publish_for_pending(self):
        """Test pas de date de publication pour 'en attente'"""
        property = Property.objects.create(
            title='Pending Property',
            description='Description',
            property_type=self.property_type,
            location=self.location,
            owner=self.user,
            price=Decimal('10000000'),
            area=Decimal('50.00'),
            status='pending'
        )
        self.assertIsNone(property.published_at)
    
    def test_property_amenities_defaults(self):
        """Test des commodités par défaut"""
        property = Property.objects.create(
            title='Property with amenities',
            description='Description',
            property_type=self.property_type,
            location=self.location,
            owner=self.user,
            price=Decimal('10000000'),
            area=Decimal('50.00')
        )
        self.assertTrue(property.has_kitchen)
        self.assertTrue(property.has_living_room)
        self.assertFalse(property.has_pool)
        self.assertFalse(property.has_garden)
    
    def test_property_str(self):
        """Test str de la propriété"""
        property = Property.objects.create(
            title='Test Property',
            description='Description',
            property_type=self.property_type,
            location=self.location,
            owner=self.user,
            price=Decimal('10000000'),
            area=Decimal('50.00')
        )
        self.assertEqual(str(property), 'Test Property')
    
    def test_property_status_choices(self):
        """Test des choix de statut"""
        for status_value, status_label in Property.STATUS_CHOICES:
            property = Property.objects.create(
                title=f'Property {status_value}',
                description='Description',
                property_type=self.property_type,
                location=self.location,
                owner=self.user,
                price=Decimal('10000000'),
                area=Decimal('50.00'),
                status=status_value
            )
            self.assertEqual(property.status, status_value)
    
    def test_property_currency_default(self):
        """Test devise par défaut"""
        property = Property.objects.create(
            title='Test Property',
            description='Description',
            property_type=self.property_type,
            location=self.location,
            owner=self.user,
            price=Decimal('10000000'),
            area=Decimal('50.00')
        )
        self.assertEqual(property.currency, 'XAF')
    
    def test_property_views_count_default(self):
        """Test compteur de vues par défaut"""
        property = Property.objects.create(
            title='Test Property',
            description='Description',
            property_type=self.property_type,
            location=self.location,
            owner=self.user,
            price=Decimal('10000000'),
            area=Decimal('50.00')
        )
        self.assertEqual(property.views_count, 0)
    
    def test_property_favorites_count_default(self):
        """Test compteur de favoris par défaut"""
        property = Property.objects.create(
            title='Test Property',
            description='Description',
            property_type=self.property_type,
            location=self.location,
            owner=self.user,
            price=Decimal('10000000'),
            area=Decimal('50.00')
        )
        self.assertEqual(property.favorites_count, 0)


class PropertyImageTests(TestCase):
    """Tests pour le modèle PropertyImage"""
    
    def setUp(self):
        """Configuration initiale"""
        self.user = User.objects.create_user(
            email='image@example.com',
            username='imageuser',
            password='testpass123'
        )
        self.category = PropertyCategory.objects.create(name='Maison')
        self.property_type = PropertyType.objects.create(
            name='Villa',
            category=self.category
        )
        self.location = Location.objects.create(
            name='Test',
            region='centre',
            city='Yaoundé',
            address='Test'
        )
        self.property = Property.objects.create(
            title='Property with images',
            description='Description',
            property_type=self.property_type,
            location=self.location,
            owner=self.user,
            price=Decimal('20000000'),
            area=Decimal('100.00')
        )
    
    def test_create_property_image(self):
        """Test création d'une image de propriété"""
        image = PropertyImage.objects.create(
            property=self.property,
            image='properties/test.jpg',
            caption='Vue extérieure'
        )
        self.assertEqual(str(image), 'Image for Property with images')
    
    def test_single_primary_image(self):
        """Test qu'une seule image peut être primaire"""
        img1 = PropertyImage.objects.create(
            property=self.property,
            image='properties/img1.jpg',
            is_primary=True
        )
        img2 = PropertyImage.objects.create(
            property=self.property,
            image='properties/img2.jpg',
            is_primary=True
        )
        img1.refresh_from_db()
        self.assertFalse(img1.is_primary)
        self.assertTrue(img2.is_primary)
    
    def test_image_ordering(self):
        """Test ordering des images"""
        img3 = PropertyImage.objects.create(
            property=self.property,
            image='properties/img3.jpg',
            order=3
        )
        img1 = PropertyImage.objects.create(
            property=self.property,
            image='properties/img1.jpg',
            order=1
        )
        img2 = PropertyImage.objects.create(
            property=self.property,
            image='properties/img2.jpg',
            order=2
        )
        images = list(self.property.images.all())
        self.assertEqual(images[0].order, 1)
        self.assertEqual(images[1].order, 2)
        self.assertEqual(images[2].order, 3)


class FavoriteTests(TestCase):
    """Tests pour le modèle Favorite"""
    
    def setUp(self):
        """Configuration initiale"""
        self.user = User.objects.create_user(
            email='favorite@example.com',
            username='favoriteuser',
            password='testpass123'
        )
        self.category = PropertyCategory.objects.create(name='Appartement')
        self.property_type = PropertyType.objects.create(
            name='F2',
            category=self.category
        )
        self.location = Location.objects.create(
            name='Test',
            region='centre',
            city='Yaoundé',
            address='Test'
        )
        self.property = Property.objects.create(
            title='Property to favorite',
            description='Description',
            property_type=self.property_type,
            location=self.location,
            owner=self.user,
            price=Decimal('10000000'),
            area=Decimal('50.00')
        )
    
    def test_create_favorite(self):
        """Test création d'un favori"""
        favorite = Favorite.objects.create(
            user=self.user,
            property=self.property
        )
        self.assertEqual(favorite.user, self.user)
        self.assertEqual(favorite.property, self.property)
    
    def test_favorite_unique_together(self):
        """Test contrainte unique sur user et property"""
        Favorite.objects.create(user=self.user, property=self.property)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Favorite.objects.create(user=self.user, property=self.property)
    
    def test_favorite_updates_count(self):
        """Test mise à jour du compteur de favoris"""
        Favorite.objects.create(user=self.user, property=self.property)
        self.property.refresh_from_db()
        self.assertEqual(self.property.favorites_count, 1)
    
    def test_favorite_str(self):
        """Test str du favori"""
        favorite = Favorite.objects.create(
            user=self.user,
            property=self.property
        )
        self.assertIn('favorite@example.com', str(favorite))
    
    def test_multiple_users_can_favorite(self):
        """Test que plusieurs utilisateurs peuvent favorite la même propriété"""
        user2 = User.objects.create_user(
            email='user2@example.com',
            username='user2',
            password='testpass123'
        )
        Favorite.objects.create(user=self.user, property=self.property)
        Favorite.objects.create(user=user2, property=self.property)
        self.property.refresh_from_db()
        self.assertEqual(self.property.favorites_count, 2)


class SearchHistoryTests(TestCase):
    """Tests pour le modèle SearchHistory"""
    
    def setUp(self):
        """Configuration initiale"""
        self.user = User.objects.create_user(
            email='search@example.com',
            username='searchuser',
            password='testpass123'
        )
    
    def test_create_search_history(self):
        """Test création d'historique de recherche"""
        search = SearchHistory.objects.create(
            user=self.user,
            query='Appartement Yaoundé',
            filters={'city': 'Yaoundé', 'type': 'apartment'},
            results_count=10
        )
        self.assertEqual(search.query, 'Appartement Yaoundé')
        self.assertEqual(search.results_count, 10)
    
    def test_search_history_str(self):
        """Test str de l'historique"""
        search = SearchHistory.objects.create(
            user=self.user,
            query='Maison avec piscine',
            results_count=5
        )
        result = str(search)
        self.assertIn('search@example.com', result)
        self.assertIn('Maison avec', result)


class PropertySerializerTests(APITestCase):
    """Tests pour les serializers de propriétés"""
    
    def setUp(self):
        """Configuration initiale"""
        self.user = User.objects.create_user(
            email='serializer@example.com',
            username='serializeruser',
            password='testpass123'
        )
        self.category = PropertyCategory.objects.create(name='Maison')
        self.property_type = PropertyType.objects.create(
            name='Villa',
            category=self.category
        )
        self.location = Location.objects.create(
            name='Test',
            region='centre',
            city='Yaoundé',
            address='Test address'
        )
    
    def test_property_serializer_fields(self):
        """Test champs du serializer"""
        from .serializers import PropertySerializer
        property = Property.objects.create(
            title='Test Villa',
            description='Beautiful villa',
            property_type=self.property_type,
            location=self.location,
            owner=self.user,
            price=Decimal('50000000'),
            area=Decimal('200.00'),
            bedrooms=4,
            bathrooms=3
        )
        serializer = PropertySerializer(property)
        data = serializer.data
        self.assertEqual(data['title'], 'Test Villa')
        self.assertEqual(data['bedrooms'], 4)
        self.assertIn('id', data)
        self.assertIn('created_at', data)
    
    def test_property_create_serializer_valid(self):
        """Test serializer de création valide"""
        from .serializers import PropertyCreateSerializer
        data = {
            'title': 'New Property',
            'description': 'Description',
            'property_type': self.property_type.id,
            'location_data': {
                'name': 'New Location',
                'region': 'littoral',
                'city': 'Douala',
                'address': 'New address'
            },
            'price': '10000000',
            'area': '75.00',
            'bedrooms': 2,
            'bathrooms': 1
        }
        serializer = PropertyCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())


class PropertyViewSetTests(APITestCase):
    """Tests pour PropertyViewSet"""
    
    def setUp(self):
        """Configuration initiale"""
        self.user = User.objects.create_user(
            email='viewset@example.com',
            username='viewsetuser',
            password='testpass123'
        )
        self.category = PropertyCategory.objects.create(name='Appartement')
        self.property_type = PropertyType.objects.create(
            name='F2',
            category=self.category
        )
        self.location = Location.objects.create(
            name='Test',
            region='centre',
            city='Yaoundé',
            address='Test'
        )
        self.property = Property.objects.create(
            title='Test Property',
            description='Description',
            property_type=self.property_type,
            location=self.location,
            owner=self.user,
            price=Decimal('10000000'),
            area=Decimal('50.00'),
            status='for_sale'
        )
    
    def test_list_properties(self):
        """Test liste des propriétés"""
        response = self.client.get('/api/properties/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_retrieve_property(self):
        """Test détail d'une propriété"""
        response = self.client.get(f'/api/properties/{self.property.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Property')
    
    def test_create_property_requires_auth(self):
        """Test création nécessite auth"""
        data = {
            'title': 'New Property',
            'description': 'Description',
            'property_type': self.property_type.id,
            'location_data': {
                'name': 'New',
                'region': 'centre',
                'city': 'Yaoundé',
                'address': 'Test'
            },
            'price': '10000000',
            'area': '50.00'
        }
        response = self.client.post('/api/properties/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_property_with_auth(self):
        """Test création avec auth"""
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'New Property',
            'description': 'Description',
            'property_type': self.property_type.id,
            'location_data': {
                'name': 'New',
                'region': 'centre',
                'city': 'Yaoundé',
                'address': 'Test'
            },
            'price': '10000000',
            'area': '50.00'
        }
        response = self.client.post('/api/properties/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_featured_properties(self):
        """Test propriétés en vedette"""
        self.property.is_featured = True
        self.property.save()
        response = self.client.get('/api/properties/featured/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_property_categories(self):
        """Test catégories de propriétés"""
        response = self.client.get('/api/properties/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class FavoriteViewSetTests(APITestCase):
    """Tests pour FavoriteViewSet"""
    
    def setUp(self):
        """Configuration initiale"""
        self.user = User.objects.create_user(
            email='favorite@example.com',
            username='favoriteuser',
            password='testpass123'
        )
        self.category = PropertyCategory.objects.create(name='Appartement')
        self.property_type = PropertyType.objects.create(
            name='F2',
            category=self.category
        )
        self.location = Location.objects.create(
            name='Test',
            region='centre',
            city='Yaoundé',
            address='Test'
        )
        self.property = Property.objects.create(
            title='Property to Favorite',
            description='Description',
            property_type=self.property_type,
            location=self.location,
            owner=self.user,
            price=Decimal('10000000'),
            area=Decimal('50.00'),
            status='for_sale'
        )
    
    def test_create_favorite(self):
        """Test création favori"""
        self.client.force_authenticate(user=self.user)
        data = {'property_id': str(self.property.id)}
        response = self.client.post('/api/favorites/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Favorite.objects.exists())
    
    def test_toggle_favorite(self):
        """Test toggle favori"""
        self.client.force_authenticate(user=self.user)
        data = {'property_id': str(self.property.id)}
        # Add
        self.client.post('/api/favorites/', data, format='json')
        # Remove
        response = self.client.post('/api/favorites/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_favorited'])
    
    def test_list_favorites(self):
        """Test liste favoris"""
        Favorite.objects.create(user=self.user, property=self.property)
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/favorites/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_check_favorite(self):
        """Test vérification favori"""
        Favorite.objects.create(user=self.user, property=self.property)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/favorites/check/?property_id={self.property.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_favorited'])

