from django.urls import path
from . import views

app_name = "commandes"

urlpatterns = [
    path("", views.index, name="liste"),
    path("ajouter/", views.ajouter, name="ajouter"),
    path("client/", views.client_commander, name="client_commander"),
    path("client/passer-commande/", views.client_passer_commande, name="client_passer_commande"),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/modifier/", views.modifier, name="modifier"),
    path("<int:pk>/statut/", views.changer_statut, name="changer_statut"),
]
