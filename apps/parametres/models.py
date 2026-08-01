from django.db import models

class ParametreRestaurant(models.Model):
    nom = models.CharField(max_length=100, default="RestaurantPro")
    adresse = models.TextField(blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    logo = models.ImageField(upload_to="parametres/", blank=True, null=True)
    
    devise = models.CharField(max_length=10, default="FCFA")
    
    message_ticket = models.TextField(blank=True, default="Merci de votre visite et à bientôt !")

    def save(self, *args, **kwargs):
        # S'assurer qu'il n'y a qu'une seule instance
        self.pk = 1
        super(ParametreRestaurant, self).save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Paramètres du Restaurant"
