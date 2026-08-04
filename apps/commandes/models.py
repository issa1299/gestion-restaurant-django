from django.db import models

from apps.clients.models import Client
from apps.menu.models import Produit
from apps.tables.models import Table
from apps.accounts.models import CustomUser
from apps.tenants.mixins import TenantMixin


class Commande(TenantMixin):

    EN_ATTENTE = "EN_ATTENTE"
    EN_PREPARATION = "EN_PREPARATION"
    PRETE = "PRETE"
    LIVREE = "LIVREE"
    ANNULEE = "ANNULEE"

    SUR_PLACE = "SUR_PLACE"
    A_EMPORTER = "A_EMPORTER"
    LIVRAISON = "LIVRAISON"

    TYPES = [
        (SUR_PLACE, "Sur place"),
        (A_EMPORTER, "À emporter"),
        (LIVRAISON, "Livraison"),
    ]

    STATUTS = [
        (EN_ATTENTE, "En attente"),
        (EN_PREPARATION, "En préparation"),
        (PRETE, "Prête"),
        (LIVREE, "Livrée"),
        (ANNULEE, "Annulée"),
    ]

    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="commandes"
    )

    table = models.ForeignKey(
        Table,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    serveur = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={"role": "SERVEUR"}
    )

    adresse_livraison = models.TextField(
        blank=True,
        default="",
        verbose_name="Adresse de livraison"
    )

    telephone_livraison = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name="Téléphone de livraison"
    )

    type = models.CharField(
        max_length=20,
        choices=TYPES,
        default=SUR_PLACE,
        verbose_name="Type de commande"
    )

    statut = models.CharField(
        max_length=30,
        choices=STATUTS,
        default=EN_ATTENTE
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta(TenantMixin.Meta):
        ordering = ["-created_at"]
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"

    def __str__(self):
        return f"Commande N° {self.id}"

    @property
    def total(self):
        return sum(
            ligne.sous_total
            for ligne in self.lignes.all()
        )


class LigneCommande(TenantMixin):

    commande = models.ForeignKey(
        Commande,
        on_delete=models.CASCADE,
        related_name="lignes"
    )

    produit = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE
    )

    quantite = models.PositiveIntegerField(default=1)

    prix = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    @property
    def sous_total(self):
        return self.quantite * self.prix

    def __str__(self):
        return self.produit.nom