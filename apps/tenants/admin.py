from django.contrib import admin
from .models import Restaurant, Plan, Paiement


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ("nom", "slug", "plan", "actif", "abonnement_expire_le", "date_creation")
    list_filter = ("actif", "plan")
    search_fields = ("nom", "slug", "email")
    list_editable = ("actif", "abonnement_expire_le", "plan")
    fieldsets = (
        (None, {"fields": ("nom", "slug")}),
        ("Coordonnées", {"fields": ("adresse", "telephone", "email")}),
        ("Abonnement", {"fields": ("plan", "actif", "abonnement_expire_le")}),
    )


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_id",
        "restaurant",
        "montant",
        "devise",
        "statut",
        "date_creation",
    )
    list_filter = ("statut", "devise")
    search_fields = ("transaction_id", "paydunya_token", "telephone")
    readonly_fields = ("date_creation", "date_maj")


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("nom", "prix_mensuel", "nb_utilisateurs_max", "nb_caisses_max", "actif")
    list_filter = ("actif",)
    search_fields = ("nom",)
