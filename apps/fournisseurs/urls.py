from django.urls import path
from . import views
from apps.tenants.decorators import plan_required

app_name = "fournisseurs"

urlpatterns = [
    path("", plan_required("stock")(views.liste_fournisseurs), name="liste"),
    path("ajouter/", plan_required("stock")(views.ajouter_fournisseur), name="ajouter"),
    path("modifier/<int:pk>/", plan_required("stock")(views.modifier_fournisseur), name="modifier"),
    path("supprimer/<int:pk>/", plan_required("stock")(views.supprimer_fournisseur), name="supprimer"),
    path("<int:pk>/", plan_required("stock")(views.detail_fournisseur), name="detail"),
    path("approvisionnements/ajouter/", plan_required("stock")(views.ajouter_approvisionnement), name="approvisionnement_ajouter"),
    path("approvisionnements/", plan_required("stock")(views.liste_approvisionnements), name="approvisionnements"),
]
