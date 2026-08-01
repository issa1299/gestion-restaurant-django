from django.contrib import admin
from .models import Livraison


@admin.register(Livraison)
class LivraisonAdmin(admin.ModelAdmin):
    list_display = ["id", "commande", "livreur", "statut", "date_livraison", "created_at"]
    list_filter = ["statut", "created_at"]
    search_fields = ["commande__id", "adresse", "telephone"]
    readonly_fields = ["created_at", "updated_at"]
