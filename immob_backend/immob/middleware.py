"""
Security Headers Middleware
Adds important HTTP security headers to all responses.
"""
import bleach
from django.conf import settings


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to every response.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Remove server information
        if 'Server' in response:
            del response['Server']
        if 'X-Powered-By' in response:
            del response['X-Powered-By']
        
        return response


def sanitize_input(value):
    """
    Sanitize user input to prevent XSS attacks.
    """
    if value is None:
        return None
    
    if isinstance(value, str):
        # Allow basic HTML tags but remove dangerous ones
        allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'p', 'br', 'ul', 'ol', 'li']
        allowed_attributes = {}
        
        return bleach.clean(
            value,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        )
    
    if isinstance(value, list):
        return [sanitize_input(item) for item in value]
    
    if isinstance(value, dict):
        return {key: sanitize_input(val) for key, val in value.items()}
    
    return value


def sanitize_html(value):
    """
    Sanitize HTML content more strictly.
    """
    if value is None:
        return None
    
    if isinstance(value, str):
        # Strict sanitization - remove all HTML tags
        return bleach.clean(value, tags=[], attributes={}, strip=True)
    
    return value


def custom_exception_handler(exc, context):
    """
    Custom exception handler for Django REST Framework.
    Adds additional security headers to error responses.
    """
    from rest_framework.views import exception_handler
    from rest_framework.response import Response
    from django.http import Http404
    from rest_framework import status
    
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Add security headers to error response
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        
        # Sanitize error messages in production
        if not settings.DEBUG:
            if hasattr(response, 'data'):
                if isinstance(response.data, dict):
                    # Remove sensitive information from error responses
                    sensitive_keys = ['detail', 'username', 'email', 'token']
                    for key in sensitive_keys:
                        if key in response.data:
                            response.data[key] = '[REDACTED]'
    
    # Handle specific exceptions
    if isinstance(exc, Http404):
        response = Response(
            {'error': 'Resource not found'},
            status=status.HTTP_404_NOT_FOUND
        )
        response['X-Content-Type-Options'] = 'nosniff'
        return response
    
    return response

