from django.db import models


class Reservation(models.Model):
    EN_ATTENTE = "EN_ATTENTE"
    CONFIRMEE = "CONFIRMEE"
    ANNULEE = "ANNULEE"
    STATUTS = [
        (EN_ATTENTE, "En attente"),
        (CONFIRMEE, "Confirmée"),
        (ANNULEE, "Annulée"),
    ]

    nom = models.CharField(max_length=120)
    telephone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    date = models.DateField()
    heure = models.TimeField()
    nombre_personnes = models.PositiveIntegerField(default=2)
    message = models.TextField(blank=True, null=True)
    statut = models.CharField(max_length=20, choices=STATUTS, default=EN_ATTENTE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Réservation"
        verbose_name_plural = "Réservations"

    def __str__(self):
        return f"Réservation {self.nom} - {self.date} {self.heure}"


class ContactMessage(models.Model):
    nom = models.CharField(max_length=120)
    email = models.EmailField()
    telephone = models.CharField(max_length=20, blank=True, null=True)
    sujet = models.CharField(max_length=200, blank=True, default="")
    message = models.TextField()
    lu = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Message de contact"
        verbose_name_plural = "Messages de contact"

    def __str__(self):
        return f"Message de {self.nom} - {self.created_at:%d/%m/%Y}"


class PhotoGalerie(models.Model):
    titre = models.CharField(max_length=150, blank=True, default="")
    image = models.ImageField(upload_to="galerie/")
    description = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Photo"
        verbose_name_plural = "Photos galerie"

    def __str__(self):
        return self.titre or f"Photo {self.id}"


class Temoignage(models.Model):
    nom = models.CharField(max_length=120)
    note = models.PositiveSmallIntegerField(default=5)
    message = models.TextField()
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Témoignage"
        verbose_name_plural = "Témoignages"

    def __str__(self):
        return f"Témoignage de {self.nom} ({self.note}★)"
