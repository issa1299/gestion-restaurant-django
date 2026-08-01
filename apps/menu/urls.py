from django.urls import path
from . import views

app_name = "menu"

urlpatterns = [
    path("", views.index, name="accueil"),
    path("gestion/", views.gestion, name="gestion"),
    path("categorie/<int:categorie_id>/", views.categorie, name="categorie"),
    path("categorie/ajouter/", views.ajouter_categorie, name="ajouter_categorie"),
    path("categorie/<int:pk>/modifier/", views.modifier_categorie, name="modifier_categorie"),
    path("categorie/<int:pk>/supprimer/", views.supprimer_categorie, name="supprimer_categorie"),
    path("produit/ajouter/", views.ajouter_produit, name="ajouter_produit"),
    path("produit/<int:pk>/modifier/", views.modifier_produit, name="modifier_produit"),
    path("produit/<int:pk>/supprimer/", views.supprimer_produit, name="supprimer_produit"),
]
