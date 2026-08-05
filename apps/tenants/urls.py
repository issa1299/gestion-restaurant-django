from django.urls import path
from . import views

app_name = "tenants"

urlpatterns = [
    path("tarifs/", views.tarifs, name="tarifs"),
    path("inscription/", views.inscription, name="inscription"),
    path("plateforme/", views.plateforme_gestion, name="plateforme"),
    path("mon-abonnement/", views.mon_abonnement, name="mon_abonnement"),
    path("paiement/lancer/", views.lancer_paiement, name="lancer_paiement"),
    path("paiement/notif/", views.notif_paiement, name="notif_paiement"),
    path("paiement/retour/", views.retour_paiement, name="retour_paiement"),
]
