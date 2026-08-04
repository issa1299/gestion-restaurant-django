from django.db import models
from apps.tenants.mixins import TenantMixin
from apps.tenants.uploads import upload_restaurant


class Categorie(TenantMixin):
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta(TenantMixin.Meta):
        ordering = ["nom"]
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        constraints = [
            models.UniqueConstraint(
                fields=["restaurant", "nom"], name="unique_categorie_par_restaurant"
            )
        ]

    def __str__(self):
        return self.nom


class Produit(TenantMixin):
    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.CASCADE,
        related_name="produits"
    )

    nom = models.CharField(max_length=150)

    description = models.TextField(blank=True)

    prix = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    image = models.ImageField(
        upload_to=upload_restaurant,
        blank=True,
        null=True
    )

    disponible = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta(TenantMixin.Meta):
        ordering = ["nom"]
        verbose_name = "Produit"
        verbose_name_plural = "Produits"

    def __str__(self):
        return self.nom