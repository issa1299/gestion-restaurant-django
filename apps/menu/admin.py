from django.contrib import admin
from .models import Categorie, Produit


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ("nom",)


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = (
        "nom",
        "categorie",
        "prix",
        "disponible",
    )

    list_filter = (
        "categorie",
        "disponible",
    )

    search_fields = (
        "nom",
    )