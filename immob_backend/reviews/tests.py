from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from rest_framework.test import APITestCase
from rest_framework import status

from properties.models import Property, PropertyCategory, PropertyType, Location
from .models import Review, ReviewLike, ReviewImage, ApplicationFeedback

User = get_user_model()


class ReviewTests(TestCase):
    """Tests pour le modèle Review"""
    
    def setUp(self):
        """Configuration initiale"""
        self.user = User.objects.create_user(
            email='review@example.com',
            username='reviewuser',
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
            address='Test address'
        )
        self.property = Property.objects.create(
            title='Property for Review',
            description='Description',
            property_type=self.property_type,
            location=self.location,
            owner=self.user,
            price=Decimal('10000000'),
            area=Decimal('50.00'),
            status='for_sale'
        )
    
    def test_create_review(self):
        """Test création d'un avis"""
        review = Review.objects.create(
            user=self.user,
            property=self.property,
            rating=5,
            title='Excellent bien',
            comment='Très belle propriété, je recommande'
        )
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.title, 'Excellent bien')
        self.assertTrue(review.is_approved)
    
    def test_review_rating_validation_min(self):
        """Test validation note minimum"""
        from django.core.exceptions import ValidationError
        review = Review(
            user=self.user,
            property=self.property,
            rating=0,  # Invalid
            title='Invalid rating',
            comment='Comment'
        )
        with self.assertRaises(ValidationError):
            review.full_clean()
    
    def test_review_rating_validation_max(self):
        """Test validation note maximum"""
        review = Review(
            user=self.user,
            property=self.property,
            rating=6,  # Invalid
            title='Invalid rating',
            comment='Comment'
        )
        with self.assertRaises(ValidationError):
            review.full_clean()
    
    def test_review_rating_boundary_values(self):
        """Test valeurs limites de la note"""
        # Rating 1 should be valid
        review = Review.objects.create(
            user=self.user,
            property=self.property,
            rating=1,
            title='Rating 1',
            comment='Minimum rating'
        )
        self.assertEqual(review.rating, 1)
        
        # Create another user for rating 5
        user2 = User.objects.create_user(
            email='user2@example.com',
            username='user2',
            password='testpass123'
        )
        review2 = Review.objects.create(
            user=user2,
            property=self.property,
            rating=5,
            title='Rating 5',
            comment='Maximum rating'
        )
        self.assertEqual(review2.rating, 5)
    
    def test_review_unique_together(self):
        """Test contrainte unique user/property"""
        Review.objects.create(
            user=self.user,
            property=self.property,
            rating=5,
            title='First Review',
            comment='Comment'
        )
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Review.objects.create(
                user=self.user,
                property=self.property,
                rating=4,
                title='Second Review',
                comment='Another comment'
            )
    
    def test_review_is_approved_default(self):
        """Test is_approved par défaut à False"""
        review = Review.objects.create(
            user=self.user,
            property=self.property,
            rating=4,
            title='Test',
            comment='Comment'
        )
        self.assertFalse(review.is_approved)
    
    def test_review_is_edited_default(self):
        """Test is_edited par défaut à False"""
        review = Review.objects.create(
            user=self.user,
            property=self.property,
            rating=4,
            title='Test',
            comment='Comment'
        )
        self.assertFalse(review.is_edited)
    
    def test_review_likes_count_default(self):
        """Test likes_count par défaut à 0"""
        review = Review.objects.create(
            user=self.user,
            property=self.property,
            rating=4,
            title='Test',
            comment='Comment'
        )
        self.assertEqual(review.likes_count, 0)
    
    def test_review_str(self):
        """Test str du review"""
        review = Review.objects.create(
            user=self.user,
            property=self.property,
            rating=5,
            title='Great',
            comment='Comment'
        )
        result = str(review)
        self.assertIn('review@example.com', result)
        self.assertIn('5/5', result)
    
    def test_review_is_verified_purchase_default(self):
        """Test is_verified_purchase par défaut à False"""
        review = Review.objects.create(
            user=self.user,
            property=self.property,
            rating=4,
            title='Test',
            comment='Comment'
        )
        self.assertFalse(review.is_verified_purchase)


class ReviewLikeTests(TestCase):
    """Tests pour le modèle ReviewLike"""
    
    def setUp(self):
        """Configuration initiale"""
        self.user = User.objects.create_user(
            email='like@example.com',
            username='likeuser',
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
            title='Property for Like',
            description='Description',
            property_type=self.property_type,
            location=self.location,
            owner=self.user,
            price=Decimal('20000000'),
            area=Decimal('100.00'),
            status='for_sale'
        )
        self.review = Review.objects.create(
            user=self.user,
            property=self.property,
            rating=5,
            title='Great Property',
            comment='Excellent!'
        )
    
    def test_create_review_like(self):
        """Test création d'un like"""
        like = ReviewLike.objects.create(
            user=self.user,
            review=self.review
        )
        self.assertEqual(like.user, self.user)
        self.assertEqual(like.review, self.review)
    
    def test_like_unique_together(self):
        """Test contrainte unique user/review"""
        ReviewLike.objects.create(user=self.user, review=self.review)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            ReviewLike.objects.create(user=self.user, review=self.review)
    
    def test_like_updates_count(self):
        """Test mise à jour du compteur de likes"""
        user2 = User.objects.create_user(
            email='user2@example.com',
            username='user2',
            password='testpass123'
        )
        ReviewLike.objects.create(user=self.user, review=self.review)
        ReviewLike.objects.create(user=user2, review=self.review)
        self.review.refresh_from_db()
        self.assertEqual(self.review.likes_count, 2)
    
    def test_like_str(self):
        """Test str du like"""
        like = ReviewLike.objects.create(
            user=self.user,
            review=self.review
        )
        result = str(like)
        self.assertIn('like@example.com', result)
    
    def test_multiple_users_can_like(self):
        """Test que plusieurs utilisateurs peuvent like"""
        user2 = User.objects.create_user(
            email='user2@example.com',
            username='user2',
            password='testpass123'
        )
        user3 = User.objects.create_user(
            email='user3@example.com',
            username='user3',
            password='testpass123'
        )
        ReviewLike.objects.create(user=self.user, review=self.review)
        ReviewLike.objects.create(user=user2, review=self.review)
        ReviewLike.objects.create(user=user3, review=self.review)
        self.assertEqual(ReviewLike.objects.filter(review=self.review).count(), 3)


class ReviewImageTests(TestCase):
    """Tests pour le modèle ReviewImage"""
    
    def setUp(self):
        """Configuration initiale"""
        self.user = User.objects.create_user(
            email='image@example.com',
            username='imageuser',
            password='testpass123'
        )
        self.category = PropertyCategory.objects.create(name='Appartement')
        self.property_type = PropertyType.objects.create(
            name='F3',
            category=self.category
        )
        self.location = Location.objects.create(
            name='Test',
            region='centre',
            city='Yaoundé',
            address='Test'
        )
        self.property = Property.objects.create(
            title='Property for Image',
            description='Description',
            property_type=self.property_type,
            location=self.location,
            owner=self.user,
            price=Decimal('15000000'),
            area=Decimal('75.00'),
            status='for_sale'
        )
        self.review = Review.objects.create(
            user=self.user,
            property=self.property,
            rating=4,
            title='Good',
            comment='Nice property'
        )
    
    def test_create_review_image(self):
        """Test création d'une image d'avis"""
        image = ReviewImage.objects.create(
            review=self.review,
            image='reviews/test.jpg',
            caption='Photo de la propriété'
        )
        self.assertEqual(str(image), 'Image for review ' + str(self.review.id))
    
    def test_review_image_caption(self):
        """Test légende de l'image"""
        image = ReviewImage.objects.create(
            review=self.review,
            image='reviews/photo.jpg',
            caption='Vue du salon'
        )
        self.assertEqual(image.caption, 'Vue du salon')


class ApplicationFeedbackTests(TestCase):
    """Tests pour le modèle ApplicationFeedback"""
    
    def setUp(self):
        """Configuration initiale"""
        self.user = User.objects.create_user(
            email='feedback@example.com',
            username='feedbackuser',
            password='testpass123'
        )
    
    def test_create_feedback(self):
        """Test création d'un feedback"""
        feedback = ApplicationFeedback.objects.create(
            user=self.user,
            feedback_type='suggestion',
            rating=5,
            title='Suggestion',
            message='Ajouter une fonctionnalité de recherche avancée'
        )
        self.assertEqual(feedback.feedback_type, 'suggestion')
        self.assertEqual(feedback.title, 'Suggestion')
        self.assertFalse(feedback.is_resolved)
    
    def test_feedback_types(self):
        """Test types de feedback"""
        for feedback_type, _ in ApplicationFeedback.FEEDBACK_TYPES:
            feedback = ApplicationFeedback.objects.create(
                user=self.user,
                feedback_type=feedback_type,
                title=f'Test {feedback_type}',
                message='Message'
            )
            self.assertEqual(feedback.feedback_type, feedback_type)
    
    def test_feedback_rating_validation(self):
        """Test validation note feedback"""
        from django.core.exceptions import ValidationError
        feedback = ApplicationFeedback(
            user=self.user,
            feedback_type='general',
            rating=6,  # Invalid
            title='Test',
            message='Message'
        )
        with self.assertRaises(ValidationError):
            feedback.full_clean()
    
    def test_feedback_optional_rating(self):
        """Test note optionnelle"""
        feedback = ApplicationFeedback.objects.create(
            user=self.user,
            feedback_type='bug',
            title='Bug report',
            message='Description du bug',
            rating=None
        )
        self.assertIsNone(feedback.rating)
    
    def test_feedback_with_email(self):
        """Test feedback avec email (utilisateur non connecté)"""
        feedback = ApplicationFeedback.objects.create(
            user=None,
            email='visitor@example.com',
            feedback_type='general',
            title='Visitor feedback',
            message='Je suis un visiteur'
        )
        self.assertIsNone(feedback.user)
        self.assertEqual(feedback.email, 'visitor@example.com')
    
    def test_feedback_str(self):
        """Test str du feedback"""
        feedback = ApplicationFeedback.objects.create(
            user=self.user,
            feedback_type='suggestion',
            title='My Suggestion',
            message='Message'
        )
        result = str(feedback)
        self.assertIn('suggestion', result)
        self.assertIn('My Suggestion', result)
    
    def test_feedback_response_tracking(self):
        """Test suivi de la réponse"""
        feedback = ApplicationFeedback.objects.create(
            user=self.user,
            feedback_type='complaint',
            title='Complaint',
            message='I have a complaint'
        )
        feedback.response = 'We have addressed your complaint.'
        feedback.is_resolved = True
        feedback.responded_at = timezone.now()
        feedback.save()
        
        self.assertTrue(feedback.is_resolved)
        self.assertIsNotNone(feedback.response)
        self.assertIsNotNone(feedback.responded_at)


class ReviewSerializerTests(APITestCase):
    """Tests pour les serializers de reviews"""
    
    def setUp(self):
        """Configuration initiale"""
        self.user = User.objects.create_user(
            email='serializer@example.com',
            username='serializeruser',
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
            title='Property for Serializer',
            description='Description',
            property_type=self.property_type,
            location=self.location,
            owner=self.user,
            price=Decimal('10000000'),
            area=Decimal('50.00'),
            status='for_sale'
        )
    
    def test_review_serializer_fields(self):
        """Test champs du serializer"""
        from .serializers import ReviewSerializer
        review = Review.objects.create(
            user=self.user,
            property=self.property,
            rating=5,
            title='Excellent',
            comment='Great property!'
        )
        serializer = ReviewSerializer(review)
        data = serializer.data
        self.assertEqual(data['rating'], 5)
        self.assertEqual(data['title'], 'Excellent')
        self.assertIn('id', data)
        self.assertIn('created_at', data)
    
    def test_review_create_serializer_valid(self):
        """Test serializer de création valide"""
        from .serializers import ReviewCreateSerializer
        data = {
            'property': self.property.id,
            'rating': 4,
            'title': 'Good property',
            'comment': 'I really liked it'
        }
        serializer = ReviewCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_review_create_serializer_invalid_rating(self):
        """Test serializer création avec note invalide"""
        from .serializers import ReviewCreateSerializer
        data = {
            'property': self.property.id,
            'rating': 6,  # Invalid
            'title': 'Bad rating',
            'comment': 'Comment'
        }
        serializer = ReviewCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class ReviewViewSetTests(APITestCase):
    """Tests pour ReviewViewSet"""
    
    def setUp(self):
        """Configuration initiale"""
        self.user = User.objects.create_user(
            email='viewset@example.com',
            username='viewsetuser',
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
            title='Property for ViewSet',
            description='Description',
            property_type=self.property_type,
            location=self.location,
            owner=self.user,
            price=Decimal('25000000'),
            area=Decimal('120.00'),
            status='for_sale'
        )
        self.review = Review.objects.create(
            user=self.user,
            property=self.property,
            rating=5,
            title='Amazing Villa',
            comment='This is a great property!'
        )
    
    def test_list_reviews(self):
        """Test liste des avis"""
        response = self.client.get('/api/reviews/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_retrieve_review(self):
        """Test détail d'un avis"""
        response = self.client.get(f'/api/reviews/{self.review.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Amazing Villa')
    
    def test_create_review_requires_auth(self):
        """Test création nécessite auth"""
        data = {
            'property': self.property.id,
            'rating': 4,
            'title': 'New Review',
            'comment': 'Great!'
        }
        response = self.client.post('/api/reviews/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_review_with_auth(self):
        """Test création avec auth"""
        self.client.force_authenticate(user=self.user)
        data = {
            'property': self.property.id,
            'rating': 4,
            'title': 'New Review',
            'comment': 'Great!'
        }
        response = self.client.post('/api/reviews/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_like_review(self):
        """Test like d'un avis"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/reviews/{self.review.id}/like/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_liked'])
    
    def test_unlike_review(self):
        """Test unlike d'un avis"""
        self.client.force_authenticate(user=self.user)
        # Like first
        self.client.post(f'/api/reviews/{self.review.id}/like/')
        # Unlike
        response = self.client.post(f'/api/reviews/{self.review.id}/like/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_liked'])
    
    def test_my_reviews(self):
        """Test mes avis"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/reviews/my_reviews/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_filter_by_property(self):
        """Test filtrage par propriété"""
        response = self.client.get(f'/api/reviews/?property={self.property.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_filter_by_min_rating(self):
        """Test filtrage par note minimale"""
        response = self.client.get('/api/reviews/?min_rating=4')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ApplicationFeedbackViewSetTests(APITestCase):
    """Tests pour ApplicationFeedbackViewSet"""
    
    def setUp(self):
        """Configuration initiale"""
        self.user = User.objects.create_user(
            email='feedbackuser@example.com',
            username='feedbackuser',
            password='testpass123'
        )
    
    def test_create_feedback(self):
        """Test création feedback"""
        data = {
            'feedback_type': 'suggestion',
            'title': 'My Suggestion',
            'message': 'Add more features'
        }
        response = self.client.post('/api/feedback/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_create_feedback_with_auth(self):
        """Test création feedback avec auth"""
        self.client.force_authenticate(user=self.user)
        data = {
            'feedback_type': 'bug',
            'title': 'Bug found',
            'message': 'There is a bug in the search'
        }
        response = self.client.post('/api/feedback/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_list_feedback_for_user(self):
        """Test liste feedback pour utilisateur"""
        ApplicationFeedback.objects.create(
            user=self.user,
            feedback_type='suggestion',
            title='Suggestion 1',
            message='Message 1'
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/feedback/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_feedback_with_rating(self):
        """Test feedback avec note"""
        data = {
            'feedback_type': 'praise',
            'rating': 5,
            'title': 'Great app',
            'message': 'I love this app!'
        }
        response = self.client.post('/api/feedback/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

