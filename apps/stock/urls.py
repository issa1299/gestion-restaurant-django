from django.urls import path
from . import views
from apps.tenants.decorators import plan_required

app_name = "stock"

urlpatterns = [
    path("", plan_required("stock")(views.liste_stock), name="liste"),
    path("<int:stock_id>/", plan_required("stock")(views.detail_stock), name="detail"),
    path("<int:stock_id>/modifier/", plan_required("stock")(views.modifier_stock), name="modifier"),
    path("<int:stock_id>/supprimer/", plan_required("stock")(views.supprimer_stock), name="supprimer"),
    path("<int:stock_id>/mouvement/", plan_required("stock")(views.ajouter_mouvement), name="mouvement"),
    path("historique/", plan_required("stock")(views.historique_mouvements), name="historique"),
]
