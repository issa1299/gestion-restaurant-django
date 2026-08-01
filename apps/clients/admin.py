from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):

    list_display = (
        "nom",
        "telephone",
        "email",
        "created_at",
    )

    search_fields = (
        "nom",
        "telephone",
    )