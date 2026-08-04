from django.db import models
from .crypto import chiffrer, dechiffrer, est_chiffree
from apps.tenants.mixins import TenantMixin
from apps.tenants.uploads import upload_restaurant


class ParametreRestaurant(TenantMixin):
    nom = models.CharField(max_length=100, default="RestaurantPro")
    adresse = models.TextField(blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    logo = models.ImageField(upload_to=upload_restaurant, blank=True, null=True)
    
    devise = models.CharField(max_length=10, default="FCFA")

    url_site = models.URLField(
        blank=True,
        null=True,
        default="",
        help_text="URL publique du site, utilisée pour générer les QR codes des tables (ex: http://192.168.1.156:8000 ou http://monresto.com)",
    )

    email_restaurant = models.EmailField(
        blank=True,
        default="",
        help_text="Adresse e-mail du restaurant (expéditeur des e-mails envoyés aux clients)",
    )
    smtp_host = models.CharField(max_length=100, blank=True, default="")
    smtp_port = models.PositiveIntegerField(default=587)
    smtp_user = models.CharField(max_length=100, blank=True, default="")
    smtp_password = models.CharField(max_length=200, blank=True, default="")

    message_ticket = models.TextField(blank=True, default="Merci de votre visite et à bientôt !")

    def save(self, *args, **kwargs):
        # Affecter le restaurant courant si absent
        if self.restaurant_id is None:
            from apps.tenants.context import get_current_restaurant
            restaurant = get_current_restaurant()
            if restaurant is not None:
                self.restaurant = restaurant
        # Chiffrer le mot de passe SMTP s'il est en clair
        if self.smtp_password and not est_chiffree(self.smtp_password):
            self.smtp_password = chiffrer(self.smtp_password)
        super(ParametreRestaurant, self).save(*args, **kwargs)

    def smtp_password_clair(self):
        """Retourne le mot de passe SMTP déchiffré (pour l'envoi d'e-mails)."""
        return dechiffrer(self.smtp_password)

    def smtp_config_complete(self):
        """True si tous les champs SMTP nécessaires sont renseignés."""
        return bool(
            self.smtp_host and self.smtp_user
            and self.smtp_password and self.email_restaurant
        )

    @classmethod
    def load(cls):
        """Charge (ou crée) les paramètres du restaurant courant."""
        from apps.tenants.context import get_current_restaurant_id
        rid = get_current_restaurant_id()
        if rid is None:
            # Mode plateforme / shell : premier paramètre existant
            obj = cls.all_objects.first()
            return obj or cls()
        obj, created = cls.all_objects.get_or_create(restaurant_id=rid)
        return obj

    def __str__(self):
        return f"Paramètres — {self.nom}"
