from django.urls import path

from . import views

app_name = "parametres"

urlpatterns = [
    path("", views.index, name="index"),
    path("tester-connexion/", views.tester_connexion, name="tester_connexion"),
]
