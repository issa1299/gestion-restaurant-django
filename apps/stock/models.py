from django.db import models
from apps.menu.models import Produit


class Stock(models.Model):

    produit = models.OneToOneField(
        Produit,
        on_delete=models.CASCADE,
        related_name="stock"
    )

    quantite = models.PositiveIntegerField(default=0)

    seuil_alerte = models.PositiveIntegerField(default=5)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["produit__nom"]

    def __str__(self):
        return f"{self.produit.nom} ({self.quantite})"

    @property
    def stock_faible(self):
        return self.quantite <= self.seuil_alerte

class MouvementStock(models.Model):

    TYPE_MOUVEMENT = (

        ("ENTREE", "Entrée"),
        ("SORTIE", "Sortie"),
        ("AJUSTEMENT", "Ajustement"),

    )


    produit = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE,
        related_name="mouvements_stock"
    )


    type_mouvement = models.CharField(
        max_length=20,
        choices=TYPE_MOUVEMENT
    )


    quantite = models.IntegerField()


    date = models.DateTimeField(
        auto_now_add=True
    )


    utilisateur = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True
    )


    commentaire = models.TextField(
        blank=True,
        null=True
    )


    class Meta:
        ordering = ["-date"]


    def __str__(self):

        return f"{self.produit.nom} - {self.type_mouvement} ({self.quantite})"