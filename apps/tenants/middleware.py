from django.conf import settings
from .context import set_current_restaurant
from .models import Restaurant


class TenantMiddleware:
    """Résout le restaurant courant de la requête et le rend disponible.

    En mode SaaS (SAAS_MODE=True) :
    1. Sous-domaine (ex: monresto.exemple.com) → Restaurant.slug
    2. Utilisateur connecté → son restaurant
    3. Défaut : premier restaurant actif (mode mono / dev)

    En mode simple (SAAS_MODE=False) : le sous-domaine est ignoré,
    on utilise toujours le restaurant de l'utilisateur ou le premier actif,
    pour un comportement identique à l'ancienne version mono-restaurant.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        restaurant = self._resoudre(request)
        set_current_restaurant(restaurant)
        request.restaurant = restaurant
        try:
            response = self.get_response(request)
        finally:
            set_current_restaurant(None)
        return response

    def _est_domaine_tunnel(self, request):
        """Domaines de tunnel (Cloudflare, ngrok, Serveo...) : pas d'isolation
        par sous-domaine, on ne scope pas le restaurant automatiquement."""
        host = request.get_host().split(":")[0]
        return (
            host.endswith(".trycloudflare.com")
            or host.endswith(".ngrok.app")
            or host.endswith(".serveo.net")
        )

    def _resoudre(self, request):
        user = getattr(request, "user", None)

        # Superadmin plateforme : non scopé (voit tous les restaurants)
        if user is not None and user.is_authenticated and user.is_superuser:
            return None

        if self._est_domaine_tunnel(request):
            # Tunnel : le restaurant vient de l'utilisateur connecté (ou None)
            if user is not None and user.is_authenticated and user.restaurant_id:
                return user.restaurant
            return None

        if settings.SAAS_MODE:
            # 1. Sous-domaine (slug) si présent
            restaurant = self._depuis_sous_domaine(request)
            if restaurant is not None:
                return restaurant

        # 2. Utilisateur connecté
        if user is not None and user.is_authenticated and user.restaurant_id:
            return user.restaurant

        # 3. Défaut : premier restaurant actif
        return Restaurant.objects.filter(actif=True).order_by("pk").first()

    def _depuis_sous_domaine(self, request):
        host = request.get_host().split(":")[0]
        # Domaines de tunnel (Cloudflare, ngrok...) : ne pas interpréter
        # le sous-domaine aléatoire comme un slug de restaurant.
        if host.endswith(".trycloudflare.com") or host.endswith(".ngrok.app"):
            return None
        labels = host.split(".")
        if len(labels) < 2:
            return None
        slug = labels[0]
        if slug in ("www", "localhost", "127", "0", "192"):
            return None
        return Restaurant.objects.filter(slug=slug, actif=True).first()
