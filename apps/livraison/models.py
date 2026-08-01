from django.db import models
from apps.commandes.models import Commande
from apps.accounts.models import CustomUser


class Livraison(models.Model):

    EN_ATTENTE = "EN_ATTENTE"
    EN_COURS = "EN_COURS"
    LIVREE = "LIVREE"
    ANNULEE = "ANNULEE"

    STATUTS = [
        (EN_ATTENTE, "En attente"),
        (EN_COURS, "En cours"),
        (LIVREE, "Livrée"),
        (ANNULEE, "Annulée"),
    ]

    commande = models.ForeignKey(
        Commande,
        on_delete=models.CASCADE,
        related_name="livraisons"
    )

    livreur = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="livraisons",
        limit_choices_to={"role": "LIVREUR"}
    )

    adresse = models.TextField(blank=True)

    telephone = models.CharField(max_length=20, blank=True)

    statut = models.CharField(
        max_length=20,
        choices=STATUTS,
        default=EN_ATTENTE
    )

    notes = models.TextField(blank=True)

    date_livraison = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Livraison"
        verbose_name_plural = "Livraisons"

    def __str__(self):
        return f"Livraison N° {self.id} - Commande N° {self.commande_id}"
