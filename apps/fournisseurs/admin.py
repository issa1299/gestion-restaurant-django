from django.contrib import admin
from .models import Fournisseur, Approvisionnement


@admin.register(Fournisseur)
class FournisseurAdmin(admin.ModelAdmin):
    list_display = ("nom", "telephone", "email", "created_at")
    search_fields = ("nom", "telephone", "email")


@admin.register(Approvisionnement)
class ApprovisionnementAdmin(admin.ModelAdmin):
    list_display = ("produit", "fournisseur", "quantite", "prix_unitaire", "date")
    list_filter = ("date", "fournisseur")
    search_fields = ("produit__nom", "fournisseur__nom")
