from django.urls import path
from . import views

app_name = "restaurant"

urlpatterns = [
    path("", views.bienvenue, name="bienvenue"),
    path("accueil/", views.accueil, name="accueil"),
    path("a-propos/", views.a_propos, name="a_propos"),
    path("galerie/", views.galerie, name="galerie"),
    path("livraison/", views.livraison, name="livraison"),
    path("temoignages/", views.temoignages, name="temoignages"),
    path("contact/", views.contact, name="contact"),
    path("reserver/", views.reserver, name="reserver"),
    path("reservations/", views.liste_reservations, name="reservations"),
    path("messages/", views.liste_messages, name="messages"),
    path("reservation/<int:pk>/statut/", views.changer_statut_reservation, name="changer_statut_reservation"),
    path("message/<int:pk>/lu/", views.marquer_message_lu, name="marquer_message_lu"),
    path("message/<int:pk>/repondre/", views.repondre_message, name="repondre_message"),
    path("galerie/gestion/", views.galerie_gestion, name="galerie_gestion"),
    path("galerie/<int:pk>/supprimer/", views.galerie_supprimer, name="galerie_supprimer"),
    path("temoignages/gestion/", views.temoignages_gestion, name="temoignages_gestion"),
    path("temoignages/ajouter/", views.temoignage_ajouter, name="temoignage_ajouter"),
    path("temoignages/<int:pk>/modifier/", views.temoignage_modifier, name="temoignage_modifier"),
    path("temoignages/<int:pk>/supprimer/", views.temoignage_supprimer, name="temoignage_supprimer"),
    path("temoignages/<int:pk>/toggle/", views.temoignage_toggle, name="temoignage_toggle"),
]
