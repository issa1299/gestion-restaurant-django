from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


# Accueil accessible selon le rôle (évite les boucles de redirection)
ROLE_HOME = {
    "CLIENT": "menu:accueil",
    "VENDEUR": "menu:gestion",
    "LIVREUR": "livraison:liste",
}


def role_required(allowed_roles=[]):

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if not request.user.is_authenticated:
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