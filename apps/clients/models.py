from django.db import models


class Client(models.Model):

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
        upload_to="clients/",
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


    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Client"
        verbose_name_plural = "Clients"


    def __str__(self):
        return self.nom

