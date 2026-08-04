from django.db import models
from .managers import TenantManager


class TenantMixin(models.Model):
    """Ajoute le champ restaurant + manager scopé à un modèle métier.

    - `objects` : manager tenant (filtre automatiquement par restaurant courant)
    - `all_objects` : manager non filtré (admin plateforme, migrations, shell)
    """

    restaurant = models.ForeignKey(
        "tenants.Restaurant",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="+",
        help_text="Restaurant propriétaire de cette ligne",
    )

    objects = TenantManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True
        base_manager_name = "all_objects"

    def save(self, *args, **kwargs):
        # Affecte automatiquement le restaurant courant si absent
        if self.restaurant_id is None:
            from .context import get_current_restaurant

            restaurant = get_current_restaurant()
            if restaurant is not None:
                self.restaurant = restaurant
        super().save(*args, **kwargs)
