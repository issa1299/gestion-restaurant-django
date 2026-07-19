from django.db import models
from django.contrib.auth.models import AbstractUser
from .managers import CustomUserManager


class Role(models.TextChoices):
    ADMIN = "ADMIN", "Administrateur"
    CAISSIER = "CAISSIER", "Caissier"
    SERVEUR = "SERVEUR", "Serveur"
    CUISINIER = "CUISINIER", "Cuisinier"
    LIVREUR = "LIVREUR", "Livreur"
    VENDEUR = "VENDEUR", "Vendeur"
    CLIENT = "CLIENT", "Client"


class CustomUser(AbstractUser):

    telephone = models.CharField(max_length=20, blank=True)

    adresse = models.CharField(
        max_length=255,
        blank=True
    )

    photo = models.ImageField(
        upload_to="users/",
        blank=True,
        null=True
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CLIENT
    )

    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    objects = CustomUserManager()

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return f"{self.username} ({self.role})"