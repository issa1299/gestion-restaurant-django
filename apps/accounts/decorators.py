from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


# Accueil accessible selon le rôle (évite les boucles de redirection)
ROLE_HOME = {
    "CLIENT": "menu:accueil",
    "GÉRANT": "menu:gestion",
    "LIVREUR": "livraison:liste",
}


def role_required(allowed_roles=[]):

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return redirect("accounts:login")

            # Un utilisateur de restaurant dont l'abonnement est désactivé
            # ne doit plus accéder aux interfaces staff.
            if (
                request.user.restaurant_id
                and not request.user.restaurant.actif
                and not request.user.is_superuser
            ):
                messages.error(
                    request,
                    "Votre établissement est désactivé. Contactez l'administrateur."
                )
                return redirect("accounts:login")

            if request.user.role in allowed_roles:

                return view_func(
                    request,
                    *args,
                    **kwargs
                )


            messages.error(
                request,
                "Accès refusé : vous n'avez pas la permission."
            )

            return redirect(ROLE_HOME.get(request.user.role, "dashboard:index"))


        return wrapper

    return decorator