from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings
from django.utils.text import slugify
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from .models import Restaurant
from apps.accounts.models import CustomUser
from apps.parametres.models import ParametreRestaurant
from .models import Plan

LABELS_MODULES = {
    "menu": "Menu en ligne illimité",
    "commandes": "Commandes et encaissement",
    "caisse": "Gestion de la caisse",
    "clients": "Gestion des clients",
    "tables": "Plan de salle et réservations",
    "notifications": "Notifications en temps réel",
    "stock": "Gestion de stock complète",
    "livraison": "Livraison en ligne",
    "rapports": "Rapports et exportations",
    "multi_caisses": "Multi-caisses",
    "cuisine": "Écran cuisine",
}


def _module_label(module):
    return LABELS_MODULES.get(module, module.replace("_", " ").capitalize())


def tarifs(request):
    """Page publique des tarifs mensuels, lue depuis la base (modèle Plan)."""
    plans = []
    for i, plan in enumerate(Plan.objects.filter(actif=True), start=1):
        plans.append(
            {
                "nom": plan.nom,
                "prix": plan.prix_mensuel,
                "slogan": f"Jusqu'à {plan.nb_utilisateurs_max} utilisateurs",
                "features": [_module_label(m) for m in plan.modules],
                "populaire": plan.nom == "Pro",
                "icone": (
                    "fa-store" if i == 1 else
                    "fa-rocket" if i == 2 else
                    "fa-crown"
                ),
            }
        )
    return render(request, "tenants/tarifs.html", {"plans": plans})


def _est_superadmin(user):
    return user.is_authenticated and user.is_superuser


@user_passes_test(_est_superadmin, login_url="accounts:login")
def plateforme_gestion(request):
    """Page de gestion plateforme (superadmin uniquement) :
    activer/désactiver un restaurant, changer son plan et son abonnement."""
    if request.method == "POST":
        restaurant_id = request.POST.get("restaurant_id")
        action = request.POST.get("action")
        restaurant = Restaurant.objects.filter(pk=restaurant_id).first()

        if restaurant is not None:
            if action == "changer_plan":
                plan_id = request.POST.get("plan")
                plan = Plan.objects.filter(pk=plan_id).first()
                if plan is not None:
                    restaurant.plan = plan
                    restaurant.save()
                    messages.success(
                        request,
                        f"Plan de « {restaurant.nom} » mis à jour : {plan.nom}.",
                    )
            elif action == "renouveler":
                # Prolonge l'abonnement d'un mois à partir d'aujourd'hui
                base = timezone.localdate()
                if restaurant.abonnement_expire_le and restaurant.abonnement_expire_le > base:
                    base = restaurant.abonnement_expire_le
                restaurant.abonnement_expire_le = base + timedelta(days=30)
                restaurant.actif = True
                restaurant.save()
                messages.success(
                    request,
                    f"Abonnement de « {restaurant.nom} » prolongé "
                    f"jusqu'au {restaurant.abonnement_expire_le}.",
                )
            elif action == "activer":
                restaurant.actif = True
                restaurant.save()
                messages.success(request, f"« {restaurant.nom} » activé.")
            elif action == "desactiver":
                restaurant.actif = False
                restaurant.save()
                messages.success(request, f"« {restaurant.nom} » désactivé.")

    restaurants = Restaurant.objects.select_related("plan").all()
    plans = Plan.objects.all()
    maintenant = timezone.localdate()
    return render(
        request,
        "tenants/plateforme.html",
        {
            "restaurants": restaurants,
            "plans": plans,
            "maintenant": maintenant,
        },
    )


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
                    plan_essentiel = Plan.objects.filter(nom="Essentiel").first()
                    restaurant = Restaurant.objects.create(
                        nom=nom,
                        slug=slug,
                        telephone=telephone,
                        email=email,
                        actif=False,  # activation manuelle par le superadmin
                        plan=plan_essentiel,
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
