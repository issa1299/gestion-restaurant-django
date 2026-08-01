from django.contrib import admin
from .models import ParametreRestaurant


@admin.register(ParametreRestaurant)
class ParametreRestaurantAdmin(admin.ModelAdmin):
    list_display = ("nom", "telephone", "email", "devise")
