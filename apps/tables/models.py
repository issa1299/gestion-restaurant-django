from django.db import models
from apps.tenants.mixins import TenantMixin


class Table(TenantMixin):
    numero = models.PositiveIntegerField()
    capacite = models.PositiveIntegerField(default=4)

    disponible = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta(TenantMixin.Meta):
        ordering = ["numero"]
        verbose_name = "Table"
        verbose_name_plural = "Tables"
        constraints = [
            models.UniqueConstraint(
                fields=["restaurant", "numero"], name="unique_table_par_restaurant"
            )
        ]

    def __str__(self):
        return f"Table {self.numero}"