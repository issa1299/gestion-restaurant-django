from django.contrib import admin
from .models import Restaurant


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ("nom", "slug", "actif", "abonnement_expire_le", "date_creation")
    list_filter = ("actif",)
    search_fields = ("nom", "slug", "email")
    list_editable = ("actif", "abonnement_expire_le")
    fieldsets = (
        (None, {"fields": ("nom", "slug")}),
        ("Coordonnées", {"fields": ("adresse", "telephone", "email")}),
        ("Abonnement", {"fields": ("actif", "abonnement_expire_le")}),
    )
