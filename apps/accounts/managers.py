from django.contrib.auth.base_user import BaseUserManager
from apps.tenants.managers import TenantManager


class CustomUserManager(TenantManager, BaseUserManager):

    def get_by_natural_key(self, username):
        # L'authentification cherche l'utilisateur par son identifiant sur TOUS
        # les restaurants (la vérification du bon restaurant se fait ensuite
        # au niveau du middleware / de la vue de login).
        return self.all_objects().get(username=username)

    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire")

        email = self.normalize_email(email)

        user = self.model(
            username=username,
            email=email,
            **extra_fields
        )

        # Affecte automatiquement le restaurant courant si non précisé
        if user.restaurant_id is None:
            from apps.tenants.context import get_current_restaurant
            restaurant = get_current_restaurant()
            if restaurant is not None and not user.is_superuser:
                user.restaurant = restaurant

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, username, email, password=None, **extra_fields):

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(username, email, password, **extra_fields)