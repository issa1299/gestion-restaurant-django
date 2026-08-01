from django.contrib import admin
from .models import Reservation, ContactMessage, PhotoGalerie, Temoignage


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ["nom", "date", "heure", "nombre_personnes", "telephone", "statut"]
    list_filter = ["statut", "date"]
    search_fields = ["nom", "telephone", "email"]
    list_editable = ["statut"]


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ["nom", "email", "sujet", "lu", "created_at"]
    list_filter = ["lu"]
    search_fields = ["nom", "email", "message"]
    list_editable = ["lu"]


@admin.register(PhotoGalerie)
class PhotoGalerieAdmin(admin.ModelAdmin):
    list_display = ["titre", "created_at"]
    search_fields = ["titre", "description"]


@admin.register(Temoignage)
class TemoignageAdmin(admin.ModelAdmin):
    list_display = ["nom", "note", "actif", "created_at"]
    list_filter = ["note", "actif"]
    search_fields = ["nom", "message"]
    list_editable = ["actif", "note"]
