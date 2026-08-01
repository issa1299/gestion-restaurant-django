from django.db import models
from apps.menu.models import Produit
from apps.accounts.models import CustomUser


class Fournisseur(models.Model):

    nom = models.CharField(max_length=150, unique=True)

    telephone = models.CharField(max_length=20, blank=True, default="")

    email = models.EmailField(blank=True, default="")

    adresse = models.TextField(blank=True, default="")

    description = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nom"]
        verbose_name = "Fournisseur"
        verbose_name_plural = "Fournisseurs"

    def __str__(self):
        return self.nom


class Approvisionnement(models.Model):

    fournisseur = models.ForeignKey(
        Fournisseur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approvisionnements"
    )

    produit = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE,
        related_name="approvisionnements"
    )

    quantite = models.PositiveIntegerField()

    prix_unitaire = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    utilisateur = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    date = models.DateTimeField(auto_now_add=True)

    commentaire = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-date"]
        verbose_name = "Approvisionnement"
        verbose_name_plural = "Approvisionnements"

    def __str__(self):
        return f"{self.quantite} x {self.produit.nom} — {self.fournisseur or 'N/A'}"

    @property
    def total(self):
        return self.quantite * self.prix_unitaire
