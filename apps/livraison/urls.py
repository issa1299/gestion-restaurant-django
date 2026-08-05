from django.urls import path

from . import views
from apps.tenants.decorators import plan_required

app_name = "livraison"

urlpatterns = [
    path("", plan_required("livraison")(views.index), name="liste"),
    path("creer/<int:commande_id>/", plan_required("livraison")(views.creer_livraison), name="creer"),
    path("<int:pk>/", plan_required("livraison")(views.detail), name="detail"),
    path("<int:pk>/modifier/", plan_required("livraison")(views.modifier), name="modifier"),
    path("<int:pk>/supprimer/", plan_required("livraison")(views.supprimer), name="supprimer"),
    path("<int:pk>/statut/", plan_required("livraison")(views.changer_statut), name="changer_statut"),
]
