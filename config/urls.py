from django.contrib import admin
# pyrefly: ignore [missing-import]
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("", include("apps.restaurant.urls")),
    path("admin/", admin.site.urls),
    path("dashboard/", include("apps.dashboard.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("ventes/", include("apps.ventes.urls")),
    path("clients/", include("apps.clients.urls")),
    path("commandes/", include("apps.commandes.urls")),
    path("cuisine/", include("apps.cuisine.urls")),
    path("livraisons/", include("apps.livraison.urls")),
    path("menu/", include("apps.menu.urls")),
    path("stock/", include("apps.stock.urls")),
    path("fournisseurs/", include("apps.fournisseurs.urls")),
    path("tables/", include("apps.tables.urls")),
    path("rapports/", include("apps.rapports.urls")),
    path("parametres/", include("apps.parametres.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)