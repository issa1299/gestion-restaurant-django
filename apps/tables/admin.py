from django.contrib import admin
from .models import Table


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ("numero", "capacite", "disponible")
    list_filter = ("disponible",)
