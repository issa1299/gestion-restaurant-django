from django.urls import path

from . import views
from apps.tenants.decorators import plan_required

app_name = "cuisine"

urlpatterns = [
    path("", plan_required("cuisine")(views.index), name="liste"),
]
