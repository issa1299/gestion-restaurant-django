from django.urls import path
from . import views

app_name = "stock"

urlpatterns = [
    path("", views.liste_stock, name="liste"),
    path("<int:stock_id>/", views.detail_stock, name="detail"),
    path("<int:stock_id>/modifier/", views.modifier_stock, name="modifier"),
    path("<int:stock_id>/supprimer/", views.supprimer_stock, name="supprimer"),
    path("<int:stock_id>/mouvement/", views.ajouter_mouvement, name="mouvement"),
    path("historique/", views.historique_mouvements, name="historique"),
]
