from django.urls import path
from . import views

app_name = "clients"

urlpatterns = [

    path(
        "",
        views.liste_clients,
        name="list"
    ),

    path(
        "ajouter/",
        views.ajouter_client,
        name="add"
    ),
    
    path(
    "modifier/<int:pk>/",
    views.modifier_client,
    name="edit"
    ),
    path(
    "supprimer/<int:pk>/",
    views.supprimer_client,
    name="delete"
    ),

    path(
    "<int:pk>/",
    views.detail_client,
    name="detail"
),
]