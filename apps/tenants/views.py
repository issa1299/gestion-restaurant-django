from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.utils.text import slugify
from django.db import transaction

from .models import Restaurant
from apps.accounts.models import CustomUser
from apps.parametres.models import ParametreRestaurant


def inscription(request):
    """Inscription SaaS : crée un restaurant (en attente d'activation), le compte
    admin du restaurant et ses paramètres par défaut.

    Uniquement disponible en mode SaaS (SAAS_MODE=True).
    """
    if not settings.SAAS_MODE:
        return redirect("restaurant:bienvenue")

    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        prenom = request.POST.get("prenom", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        telephone = request.POST.get("telephone", "").strip()
        password = request.POST.get("password", "")

        erreurs = []
        if not nom:
            erreurs.append("Le nom du restaurant est obligatoire.")
        if not username or not email:
            erreurs.append("L'identifiant et l'e-mail sont obligatoires.")
        if not password or len(password) < 8:
            erreurs.append("Le mot de passe doit contenir au moins 8 caractères.")

        if not erreurs:
            base_slug = slugify(nom) or "restaurant"
            slug = base_slug
            n = 2
            while Restaurant.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{n}"
                n += 1

            try:
                with transaction.atomic():
                    restaurant = Restaurant.objects.create(
                        nom=nom,
                        slug=slug,
                        telephone=telephone,
                        email=email,
                        actif=False,  # activation manuelle par le superadmin
                    )
                    user = CustomUser.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        first_name=prenom,
                        role="ADMIN",
                        restaurant=restaurant,
                    )
                    ParametreRestaurant.objects.create(
                        restaurant=restaurant,
                        nom=nom,
                        telephone=telephone,
                        email=email,
                    )
            except Exception as e:
                erreurs.append(f"Erreur lors de la création du compte : {e}")

        if not erreurs:
            return render(
                request,
                "tenants/inscription_confirmee.html",
                {"restaurant_nom": nom},
            )

        for e in erreurs:
            messages.error(request, e)

    return render(request, "tenants/inscription.html", {})
