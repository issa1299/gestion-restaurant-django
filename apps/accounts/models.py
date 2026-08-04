from django.db import models
from django.contrib.auth.models import AbstractUser
from .managers import CustomUserManager
from apps.tenants.managers import TenantManager
from apps.tenants.uploads import upload_restaurant


class Role(models.TextChoices):
    ADMIN = "ADMIN", "Administrateur"
    CAISSIER = "CAISSIER", "Caissier"
    SERVEUR = "SERVEUR", "Serveur"
    CUISINIER = "CUISINIER", "Cuisinier"
    LIVREUR = "LIVREUR", "Livreur"
    GERANT = "GÉRANT", "Gérant"
    CLIENT = "CLIENT", "Client"


class CustomUser(AbstractUser):

    telephone = models.CharField(max_length=20, blank=True)

    adresse = models.CharField(
        max_length=255,
        blank=True
    )

    photo = models.ImageField(
        upload_to=upload_restaurant,
        blank=True,
        null=True
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CLIENT
    )

    is_verified = models.BooleanField(default=False)

    restaurant = models.ForeignKey(
        "tenants.Restaurant",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="utilisateurs",
        help_text="Restaurant auquel appartient l'utilisateur (vide pour la plateforme/superadmin)",
    )

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