from django.urls import path
from . import views

app_name = "tenants"

urlpatterns = [
    path("tarifs/", views.tarifs, name="tarifs"),
    path("inscription/", views.inscription, name="inscription"),
    path("plateforme/", views.plateforme_gestion, name="plateforme"),
]
