from django.urls import path
from . import views

app_name = "tenants"

urlpatterns = [
    path("inscription/", views.inscription, name="inscription"),
]
