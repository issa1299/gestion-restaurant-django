from django.urls import path
from . import views

app_name = "tenants"

urlpatterns = [
    path("tarifs/", views.tarifs, name="tarifs"),
    path("inscription/", views.inscription, name="inscription"),
    path("plateforme/", views.plateforme_gestion, name="plateforme"),
    path("plateforme/dashboard/", views.dashboard_plateforme, name="dashboard_plateforme"),
    path("plateforme/stats/", views.stats_plateforme, name="stats_plateforme"),
    path("plateforme/plans/", views.plans_plateforme, name="plans_plateforme"),
    path("plateforme/paiements/", views.paiements_plateforme, name="paiements_plateforme"),
    path("plateforme/utilisateurs/", views.utilisateurs_plateforme, name="utilisateurs_plateforme"),
    path("plateforme/parametres/", views.parametres_plateforme, name="parametres_plateforme"),
    path("plateforme/creer-restaurant/", views.creer_restaurant_plateforme, name="creer_restaurant_plateforme"),
    path("mon-abonnement/", views.mon_abonnement, name="mon_abonnement"),
    path("mes-paiements/", views.mes_paiements, name="mes_paiements"),
    path("paiement/lancer/", views.lancer_paiement, name="lancer_paiement"),
    path("paiement/notif/", views.notif_paiement, name="notif_paiement"),
    path("paiement/retour/", views.retour_paiement, name="retour_paiement"),
]
