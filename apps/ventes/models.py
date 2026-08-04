from django.db import models
from apps.accounts.models import CustomUser
from apps.menu.models import Produit
from apps.tenants.mixins import TenantMixin


class Vente(TenantMixin):

    MODE_PAIEMENT = (

        ("ESPECES", "Espèces"),
        ("ORANGE", "Orange Money"),
        ("WAVE", "Wave"),
        ("CARTE", "Carte bancaire"),

    )


    caissier = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="ventes"
    )


    total = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )


    mode_paiement = models.CharField(
        max_length=20,
        choices=MODE_PAIEMENT
    )


    created_at = models.DateTimeField(
        auto_now_add=True
    )

    annulee = models.BooleanField(
        default=False,
        verbose_name="Vente annulée"
    )

    annule_le = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Annulée le"
    )

    annule_par = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ventes_annulees"
    )

    class Meta(TenantMixin.Meta):

        ordering = ["-created_at"]


    def __str__(self):

        return f"Vente N° {self.id}"




class DetailVente(TenantMixin):


    vente = models.ForeignKey(
        Vente,
        on_delete=models.CASCADE,
        related_name="details"
    )


    produit = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE
    )


    quantite = models.PositiveIntegerField()


    prix = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )


    sous_total = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )


    def __str__(self):

        return self.produit.nom