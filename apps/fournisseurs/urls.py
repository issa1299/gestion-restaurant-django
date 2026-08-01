from django.urls import path
from . import views

app_name = "fournisseurs"

urlpatterns = [
    path("", views.liste_fournisseurs, name="liste"),
    path("ajouter/", views.ajouter_fournisseur, name="ajouter"),
    path("modifier/<int:pk>/", views.modifier_fournisseur, name="modifier"),
    path("supprimer/<int:pk>/", views.supprimer_fournisseur, name="supprimer"),
    path("<int:pk>/", views.detail_fournisseur, name="detail"),
    path("approvisionnements/ajouter/", views.ajouter_approvisionnement, name="approvisionnement_ajouter"),
    path("approvisionnements/", views.liste_approvisionnements, name="approvisionnements"),
]
