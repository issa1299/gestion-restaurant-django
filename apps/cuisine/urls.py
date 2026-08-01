from django.urls import path

from . import views

app_name = "cuisine"

urlpatterns = [
    path("", views.index, name="liste"),
]
