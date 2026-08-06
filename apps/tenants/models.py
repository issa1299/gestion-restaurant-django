from django.db import models
from django.utils.text import slugify


class ParametrePlateforme(models.Model):
    """Paramètres globaux de la plateforme SaaS (coordonnées de paiement, etc.).
    Singleton : une seule ligne."""

    nom_plateforme = models.CharField(max_length=100, default="RestaurantPro")
    logo = models.ImageField(
        upload_to="plateforme/logos",
        blank=True,
        null=True,
        help_text="Logo de la plateforme (affiché dans la console)",
    )
    nom_beneficiaire = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Nom affiché pour les paiements (ex: votre nom)",
    )
    telephone_paiement = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="Numéro Mobile Money / téléphone où les restaurants doivent payer",
    )
    instruction_paiement = models.TextField(
        blank=True,
        default="",
        help_text="Texte affiché au gérant pour payer (ex: envoyer le montant, puis nous prévenir)",
    )

    # --- CinetPay (Mobile Money FCFA : Orange Money, Moov, Wave, MTN) ---
    cinetpay_active = models.BooleanField(
        default=False,
        help_text="Activer le paiement en ligne par CinetPay (Mobile Money).",
    )
    cinetpay_apikey = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="API key CinetPay (provient du panel CinetPay)",
    )
    cinetpay_site_id = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Site ID CinetPay",
    )
    cinetpay_devise = models.CharField(
        max_length=5,
        blank=True,
        default="XOF",
        help_text="Devise des paiements (XOF pour l'Afrique de l'Ouest / Mali)",
    )

    class Meta:
        verbose_name = "Paramètres de la plateforme"
        verbose_name_plural = "Paramètres de la plateforme"

    def save(self, *args, **kwargs):
        # Singleton : on réutilise toujours la première ligne
        self.pk = self._pk_unique()
        super().save(*args, **kwargs)

    def _pk_unique(self):
        obj = type(self).objects.first()
        return obj.pk if obj else None

    @classmethod
    def load(cls):
        obj = cls.objects.first()
        if obj is None:
            obj = cls()
            obj.save()
        return obj

    def __str__(self):
        return f"Paramètres plateforme — {self.nom_plateforme}"


class Paiement(models.Model):
    """Journal des paiements d'abonnement (CinetPay, Mobile Money)."""

    STATUT_CHOIX = [
        ("EN_ATTENTE", "En attente"),
        ("SUCCES", "Réussi"),
        ("ECHEC", "Échoué"),
        ("ANNULE", "Annulé"),
        ("REFUSE", "Refusé"),
    ]

    restaurant = models.ForeignKey(
        "Restaurant",
        on_delete=models.CASCADE,
        related_name="paiements",
        null=True,
        blank=True,
    )
    transaction_id = models.CharField(
        max_length=100, unique=True, help_text="Identifiant unique côté plateforme"
    )
    cinetpay_transaction_id = models.CharField(
        max_length=100, blank=True, default="", help_text="ID renvoyé par CinetPay"
    )
    montant = models.PositiveIntegerField(default=0, help_text="Montant en FCFA")
    devise = models.CharField(max_length=5, default="XOF")
    statut = models.CharField(max_length=20, choices=STATUT_CHOIX, default="EN_ATTENTE")
    description = models.CharField(max_length=255, blank=True, default="")
    telephone = models.CharField(max_length=30, blank=True, default="")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_maj = models.DateTimeField(auto_now=True)
    donnees = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-date_creation"]
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"

    def __str__(self):
        return f"{self.transaction_id} — {self.statut} ({self.montant} {self.devise})"


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
