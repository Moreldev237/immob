from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifier
    for authentication instead of usernames.
    """
    def create_user(self, email, password, username=None, **extra_fields):
        """
        Create and save a User with the given email, username and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))
        if not username:
            raise ValueError(_('The Username must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given username, email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, username=username, **extra_fields)

    def get_by_username_or_email(self, identifier):
        """
        Get user by username or email.
        Returns the user if found, raises DoesNotExist otherwise.
        """
        try:
            # Try to find by username first
            return self.get(username=identifier)
        except ObjectDoesNotExist:
            pass

        try:
            # Try to find by email
            return self.get(email__iexact=identifier)
        except ObjectDoesNotExist:
            pass

        # If neither worked, raise DoesNotExist
        raise ObjectDoesNotExist(
            _("No user found with username or email: %(identifier)s") % {'identifier': identifier}
        )
