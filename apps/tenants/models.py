from django.db import models
from django.utils.text import slugify


class Plan(models.Model):
    """Un plan d'abonnement proposé aux restaurants."""

    nom = models.CharField(max_length=50, unique=True)
    prix_mensuel = models.IntegerField(default=0, help_text="Prix par mois (en FCFA)")
    nb_utilisateurs_max = models.PositiveIntegerField(default=1)
    nb_caisses_max = models.PositiveIntegerField(default=1)
    modules = models.JSONField(
        default=list,
        help_text="Liste des modules autorisés : menu, commandes, caisse, stock, "
                  "livraison, rapports, cuisine, multi_caisses...",
    )
    actif = models.BooleanField(default=True)
    ordre = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordre"]
        verbose_name = "Plan d'abonnement"
        verbose_name_plural = "Plans d'abonnement"

    def __str__(self):
        return self.nom

    def a_module(self, module):
        return module in self.modules


class Restaurant(models.Model):
    """Un restaurant locataire de la plateforme SaaS.

    L'abonnement est activé manuellement via le champ `actif` (interface admin).
    """

    nom = models.CharField(max_length=150)
    slug = models.SlugField(max_length=100, unique=True)

    plan = models.ForeignKey(
        Plan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="restaurants",
        help_text="Plan d'abonnement du restaurant",
    )

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

    def est_expire(self):
        """True si la date d'expiration est dépassée (ou mal remplie)."""
        if self.abonnement_expire_le is None:
            return False
        return self.abonnement_expire_le < self._date_jour()

    @staticmethod
    def _date_jour():
        from django.utils import timezone
        return timezone.localdate()

    def a_module(self, module):
        """True si le plan du restaurant autorise ce module."""
        return self.plan is not None and self.plan.a_module(module)

    def autorise_utilisateur(self):
        """True si le restaurant peut encore créer un utilisateur (limite du plan)."""
        from apps.accounts.models import CustomUser
        if self.plan is None:
            return True
        nb = CustomUser.objects.filter(restaurant=self).count()
        return nb < self.plan.nb_utilisateurs_max
