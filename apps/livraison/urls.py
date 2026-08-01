from django.urls import path

from . import views

app_name = "livraison"

urlpatterns = [
    path("", views.index, name="liste"),
    path("creer/<int:commande_id>/", views.creer_livraison, name="creer"),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/modifier/", views.modifier, name="modifier"),
    path("<int:pk>/supprimer/", views.supprimer, name="supprimer"),
    path("<int:pk>/statut/", views.changer_statut, name="changer_statut"),
]
