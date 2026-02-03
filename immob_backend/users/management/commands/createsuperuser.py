from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError


class Command(BaseCommand):
    help = 'Crée un superutilisateur en demandant le username, email et mot de passe'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Demander le username
        username = input('Username: ')
        if not username:
            self.stderr.write(self.style.ERROR('Le username ne peut pas être vide.'))
            return
        
        # Vérifier si le username existe déjà
        if User.objects.filter(username=username).exists():
            self.stderr.write(self.style.ERROR(f'Un utilisateur avec le username "{username}" existe déjà.'))
            return
        
        # Demander l'email
        email = input('Email address: ')
        if not email:
            self.stderr.write(self.style.ERROR("L'email ne peut pas être vide."))
            return
        
        # Vérifier si l'email existe déjà
        if User.objects.filter(email=email).exists():
            self.stderr.write(self.style.ERROR(f'Un utilisateur avec l\'email "{email}" existe déjà.'))
            return
        
        # Demander le mot de passe
        password = input('Password: ')
        if not password:
            self.stderr.write(self.style.ERROR('Le mot de passe ne peut pas être vide.'))
            return
        
        # Demander la confirmation du mot de passe
        password_confirm = input('Password (again): ')
        if password != password_confirm:
            self.stderr.write(self.style.ERROR('Les mots de passe ne correspondent pas.'))
            return
        
        # Créer le superutilisateur
        try:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(self.style.SUCCESS(f'Superutilisateur "{username}" créé avec succès!'))
        except ValidationError as e:
            self.stderr.write(self.style.ERROR(f'Erreur: {e}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Erreur lors de la création: {e}'))

