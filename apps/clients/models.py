from django.db import models
from apps.tenants.mixins import TenantMixin
from apps.tenants.uploads import upload_restaurant


class Client(TenantMixin):

    nom = models.CharField(
        max_length=100
    )

    telephone = models.CharField(
        max_length=20,
        blank=True
    )

    email = models.EmailField(
        blank=True,
        null=True
    )

    adresse = models.CharField(
        max_length=255,
        blank=True
    )

    photo = models.ImageField(
        upload_to=upload_restaurant,
        blank=True,
        null=True
    )

    date_naissance = models.DateField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )


    class Meta(TenantMixin.Meta):
        ordering = ["-created_at"]
        verbose_name = "Client"
        verbose_name_plural = "Clients"


    def __str__(self):
        return self.nom

