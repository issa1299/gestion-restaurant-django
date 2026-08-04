from django.db import models
from django.utils.text import slugify


class Restaurant(models.Model):
    """Un restaurant locataire de la plateforme SaaS.

    L'abonnement est activé manuellement via le champ `actif` (interface admin).
    """

    nom = models.CharField(max_length=150)
    slug = models.SlugField(max_length=100, unique=True)

    adresse = models.CharField(max_length=255, blank=True, default="")
    telephone = models.CharField(max_length=20, blank=True, default="")
    email = models.EmailField(blank=True, default="")

    actif = models.BooleanField(
        default=True,
        help_text="Désactiver pour suspendre l'accès du restaurant (abonnement impayé, etc.)",
    )

    date_creation = models.DateTimeField(auto_now_add=True)
    abonnement_expire_le = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ["nom"]
        verbose_name = "Restaurant"
        verbose_name_plural = "Restaurants"

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom) or f"restaurant-{self.pk or 'nouveau'}"
        super().save(*args, **kwargs)
