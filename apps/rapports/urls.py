from django.urls import path
from . import views
from apps.tenants.decorators import plan_required

app_name = "rapports"

urlpatterns = [
    path("", plan_required("rapports")(views.index), name="index"),
    path("export-csv/", plan_required("rapports")(views.export_csv), name="export_csv"),
]
