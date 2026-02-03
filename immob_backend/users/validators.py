"""
Custom password validators for enhanced security.
"""
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class PasswordStrengthValidator:
    """
    Validates that passwords meet strength requirements.
    
    Requirements:
    - At least 10 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    - No more than 3 consecutive identical characters
    - Not based on common patterns
    """
    
    def __init__(self, min_length=10):
        self.min_length = min_length
    
    def validate(self, password, user=None):
        errors = []
        
        # Check minimum length
        if len(password) < self.min_length:
            errors.append(
                _('Le mot de passe doit contenir au moins %(min_length)d caractères.') %
                {'min_length': self.min_length}
            )
        
        # Check uppercase
        if not re.search(r'[A-Z]', password):
            errors.append(_('Le mot de passe doit contenir au moins une lettre majuscule.'))
        
        # Check lowercase
        if not re.search(r'[a-z]', password):
            errors.append(_('Le mot de passe doit contenir au moins une lettre minuscule.'))
        
        # Check digit
        if not re.search(r'\d', password):
            errors.append(_('Le mot de passe doit contenir au moins un chiffre.'))
        
        # Check special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append(_('Le mot de passe doit contenir au moins un caractère spécial (!@#$%^&*(),.?":{}|<>).'))
        
        # Check for consecutive identical characters (more than 3)
        if re.search(r'(.)\1{3,}', password):
            errors.append(_('Le mot de passe ne peut pas contenir plus de 3 caractères identiques consécutifs.'))
        
        if errors:
            raise ValidationError(errors)
    
    def get_help_text(self):
        return _(
            'Le mot de passe doit contenir au moins %(min_length)d caractères, '
            'incluant une lettre majuscule, une lettre minuscule, '
            'un chiffre et un caractère spécial.'
        ) % {'min_length': self.min_length}


class CommonPasswordValidator:
    """
    Validates that passwords are not common or easily guessable.
    """
    
    # Common password patterns to reject
    COMMON_PATTERNS = [
        r'^password$',
        r'^123456',
        r'^qwerty',
        r'^abc123',
        r'^letmein',
        r'^welcome',
        r'^admin',
        r'^login',
        r'^test',
    ]
    
    def validate(self, password, user=None):
        # Check against common patterns
        for pattern in self.COMMON_PATTERNS:
            if re.search(pattern, password, re.IGNORECASE):
                raise ValidationError(
                    _('Ce mot de passe est trop courant ou prévisible.'),
                    code='password_too_common'
                )
        
        # Check if password is based on user information
        if user:
            user_info = [
                user.username,
                user.email.split('@')[0] if user.email else '',
                user.first_name,
                user.last_name,
            ]
            
            password_lower = password.lower()
            for info in user_info:
                if info and len(info) >= 3:
                    if info.lower() in password_lower:
                        raise ValidationError(
                            _('Le mot de passe ne peut pas être basé sur vos informations personnelles.'),
                            code='password_based_on_user_info'
                        )
    
    def get_help_text(self):
        return _('Le mot de passe ne doit pas être trop courant ou basé sur vos informations personnelles.')


class MaximumLengthValidator:
    """
    Validates that the password isn't too long.
    Prevents DoS attacks with very long passwords.
    """
    
    MAX_LENGTH = 128
    
    def validate(self, password, user=None):
        if len(password) > self.MAX_LENGTH:
            raise ValidationError(
                _('Le mot de passe ne peut pas dépasser %(max_length)d caractères.') %
                {'max_length': self.MAX_LENGTH},
                code='password_too_long'
            )
    
    def get_help_text(self):
        return _(
            'Le mot de passe ne peut pas dépasser %(max_length)d caractères.'
        ) % {'max_length': self.MAX_LENGTH}

