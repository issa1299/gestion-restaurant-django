from django.db import models


class Table(models.Model):
    numero = models.PositiveIntegerField(unique=True)
    capacite = models.PositiveIntegerField(default=4)

    disponible = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["numero"]
        verbose_name = "Table"
        verbose_name_plural = "Tables"

    def __str__(self):
        return f"Table {self.numero}"