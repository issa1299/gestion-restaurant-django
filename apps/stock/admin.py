from django.contrib import admin
from .models import Stock, MouvementStock


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):

    list_display = (
        "produit",
        "quantite",
        "seuil_alerte",
        "updated_at",
    )


@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):

    list_display = (
        "produit",
        "type_mouvement",
        "quantite",
        "utilisateur",
        "date",
    )

    list_filter = (
        "type_mouvement",
        "date",
    )

    search_fields = (
        "produit__nom",
    )