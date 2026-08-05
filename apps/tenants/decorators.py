from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def plan_required(module):
    """Restreint l'accès d'une vue staff si le module n'est pas inclus
    dans le plan d'abonnement du restaurant.

    Le superadmin de la plateforme n'est jamais bloqué.
    """

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return redirect("accounts:login")

            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            restaurant = request.user.restaurant

            # Restaurant sans plan (ancien) : on autorise par défaut
            if restaurant is None or restaurant.plan is None:
                return view_func(request, *args, **kwargs)

            if not restaurant.plan.a_module(module):
                messages.error(
                    request,
                    f"Cette fonctionnalité est incluse dans un plan supérieur. "
                    f"Votre plan actuel est « {restaurant.plan.nom} ».",
                )
                from apps.accounts.decorators import ROLE_HOME
                return redirect(ROLE_HOME.get(request.user.role, "dashboard:index"))

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
