import json
import uuid
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.text import slugify
from django.db.models.functions import TruncMonth
from django.views.decorators.csrf import csrf_exempt

from . import paydunya
from .models import Paiement, ParametrePlateforme, Plan, Restaurant
from apps.accounts.models import CustomUser
from apps.parametres.models import ParametreRestaurant

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


def accueil_public(request):
    """Page d'accueil publique de la plateforme (visiteurs non connectés)."""
    return render(request, "tenants/accueil_public.html")


@user_passes_test(_est_superadmin, login_url="accounts:login")
def dashboard_plateforme(request):
    """Vue d'ensemble de la plateforme (superadmin) : présentation + chiffres."""
    maintenant = timezone.localdate()
    restaurants = list(Restaurant.objects.select_related("plan").all())

    actifs = sum(1 for r in restaurants if r.actif)
    expirants = sum(
        1 for r in restaurants if r.actif and r.abonnement_expire_le
        and 0 <= (r.abonnement_expire_le - maintenant).days <= 7
    )
    expires = sum(
        1 for r in restaurants
        if r.abonnement_expire_le and r.abonnement_expire_le < maintenant
    )
    revenus = (
        Paiement.objects.filter(statut="SUCCES").aggregate(t=Sum("montant"))["t"] or 0
    )
    nb_paiements = Paiement.objects.filter(statut="SUCCES").count()
    derniers_paiements = (
        Paiement.objects.select_related("restaurant").order_by("-date_creation")[:6]
    )

    return render(
        request,
        "tenants/dashboard_plateforme.html",
        {
            "restaurants": restaurants,
            "maintenant": maintenant,
            "stats": {
                "total": len(restaurants),
                "actifs": actifs,
                "expirants": expirants,
                "expires": expires,
                "revenus": revenus,
                "nb_paiements": nb_paiements,
            },
            "derniers_paiements": derniers_paiements,
            "plans": Plan.objects.filter(actif=True),
        },
    )


@user_passes_test(_est_superadmin, login_url="accounts:login")
def stats_plateforme(request):
    """Statistiques détaillées de la plateforme (revenus par mois, répartition)."""
    maintenant = timezone.localdate()
    restaurants_qs = Restaurant.objects.select_related("plan").all()

    revenus_par_mois = (
        Paiement.objects.filter(statut="SUCCES")
        .annotate(mois=TruncMonth("date_creation"))
        .values("mois")
        .annotate(total=Sum("montant"), nb=Count("id"))
        .order_by("mois")
    )

    repartition_plans = (
        Restaurant.objects.filter(plan__isnull=False)
        .values("plan__nom")
        .annotate(nb=Count("id"))
        .order_by("-nb")
    )

    stats = {
        "total": restaurants_qs.count(),
        "actifs": restaurants_qs.filter(actif=True).count(),
        "expirants": sum(
            1 for r in restaurants_qs if r.actif and r.abonnement_expire_le
            and 0 <= (r.abonnement_expire_le - maintenant).days <= 7
        ),
        "expires": sum(
            1 for r in restaurants_qs
            if r.abonnement_expire_le and r.abonnement_expire_le < maintenant
        ),
        "revenus": (
            Paiement.objects.filter(statut="SUCCES").aggregate(t=Sum("montant"))["t"] or 0
        ),
        "nb_paiements": Paiement.objects.filter(statut="SUCCES").count(),
    }

    mois_labels = []
    mois_values = []
    for ligne in revenus_par_mois:
        mois_labels.append(ligne["mois"].strftime("%b %Y") if ligne["mois"] else "—")
        mois_values.append(ligne["total"])

    return render(
        request,
        "tenants/stats_plateforme.html",
        {
            "stats": stats,
            "revenus_par_mois": list(revenus_par_mois),
            "repartition_plans": list(repartition_plans),
            "mois_labels": mois_labels,
            "mois_values": mois_values,
            "devise": ParametrePlateforme.load().paydunya_devise or "XOF",
        },
    )


@user_passes_test(_est_superadmin, login_url="accounts:login")
def plans_plateforme(request):
    """Gestion des plans (créer, modifier, activer/désactiver)."""
    if request.method == "POST":
        action = request.POST.get("action")
        nom = request.POST.get("nom", "").strip()
        if action == "creer" and nom:
            Plan.objects.create(
                nom=nom,
                prix_mensuel=int(request.POST.get("prix_mensuel") or 0),
                nb_utilisateurs_max=int(request.POST.get("nb_utilisateurs_max") or 1),
                nb_caisses_max=int(request.POST.get("nb_caisses_max") or 1),
                actif=request.POST.get("actif") == "on",
            )
            messages.success(request, f"Plan « {nom} » créé.")
        elif action == "modifier":
            plan = Plan.objects.filter(pk=request.POST.get("plan_id")).first()
            if plan:
                plan.nom = nom or plan.nom
                plan.prix_mensuel = int(request.POST.get("prix_mensuel") or plan.prix_mensuel)
                plan.nb_utilisateurs_max = int(request.POST.get("nb_utilisateurs_max") or plan.nb_utilisateurs_max)
                plan.nb_caisses_max = int(request.POST.get("nb_caisses_max") or plan.nb_caisses_max)
                plan.actif = request.POST.get("actif") == "on"
                plan.save()
                messages.success(request, f"Plan « {plan.nom} » mis à jour.")
        elif action == "supprimer":
            plan = Plan.objects.filter(pk=request.POST.get("plan_id")).first()
            if plan:
                Plan.objects.filter(pk=plan.pk).update(actif=False)
                messages.success(request, f"Plan « {plan.nom} » désactivé.")
        return redirect("tenants:plans_plateforme")

    plans = Plan.objects.all().order_by("ordre", "nom")
    return render(request, "tenants/plans_plateforme.html", {"plans": plans})


@user_passes_test(_est_superadmin, login_url="accounts:login")
def paiements_plateforme(request):
    """Historique complet des paiements avec filtres."""
    qs = Paiement.objects.select_related("restaurant")
    statut = request.GET.get("statut", "")
    recherche = request.GET.get("q", "").strip()

    if statut:
        qs = qs.filter(statut=statut)
    if recherche:
        qs = qs.filter(
            Q(transaction_id__icontains=recherche)
            | Q(restaurant__nom__icontains=recherche)
            | Q(telephone__icontains=recherche)
        )
    paiements = qs.order_by("-date_creation")
    total = paiements.aggregate(t=Sum("montant"))["t"] or 0
    return render(
        request,
        "tenants/paiements_plateforme.html",
        {
            "paiements": paiements,
            "statut": statut,
            "recherche": recherche,
            "total": total,
            "montants_par_statut": {
                p["statut"]: p["total"]
                for p in Paiement.objects.values("statut").annotate(total=Sum("montant"))
            },
        },
    )


@user_passes_test(_est_superadmin, login_url="accounts:login")
def utilisateurs_plateforme(request):
    """Liste des utilisateurs (comptes) par restaurant."""
    utilisateurs = CustomUser.objects.select_related("restaurant").order_by("restaurant__nom", "username")
    return render(
        request,
        "tenants/utilisateurs_plateforme.html",
        {"utilisateurs": utilisateurs},
    )


@user_passes_test(_est_superadmin, login_url="accounts:login")
def parametres_plateforme(request):
    """Paramètres généraux + coordonnées de paiement + PayDunya."""
    pp = ParametrePlateforme.load()
    if request.method == "POST":
        pp.nom_plateforme = request.POST.get("nom_plateforme", "RestaurantPro")
        pp.nom_beneficiaire = request.POST.get("nom_beneficiaire", "")
        pp.telephone_paiement = request.POST.get("telephone_paiement", "")
        pp.instruction_paiement = request.POST.get("instruction_paiement", "")
        pp.paydunya_active = request.POST.get("paydunya_active") == "on"
        pp.paydunya_master_key = request.POST.get("paydunya_master_key", "")
        pp.paydunya_private_key = request.POST.get("paydunya_private_key", "")
        pp.paydunya_token = request.POST.get("paydunya_token", "")
        pp.paydunya_mode = request.POST.get("paydunya_mode", "test")
        pp.paydunya_devise = request.POST.get("paydunya_devise", "XOF")
        if request.FILES.get("logo"):
            pp.logo = request.FILES["logo"]
        pp.save()
        messages.success(request, "Paramètres de la plateforme mis à jour.")
        return redirect("tenants:parametres_plateforme")
    return render(
        request,
        "tenants/parametres_plateforme.html",
        {"parametres": pp},
    )


def _est_superadmin(user):
    return user.is_authenticated and user.is_superuser


@user_passes_test(_est_superadmin, login_url="accounts:login")
def plateforme_gestion(request):
    """Page de gestion plateforme (superadmin uniquement) :
    activer/désactiver un restaurant, changer son plan et son abonnement."""
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "parametres":
            pp = ParametrePlateforme.load()
            pp.nom_beneficiaire = request.POST.get("nom_beneficiaire", "")
            pp.telephone_paiement = request.POST.get("telephone_paiement", "")
            pp.instruction_paiement = request.POST.get("instruction_paiement", "")
            pp.paydunya_active = request.POST.get("paydunya_active") == "on"
            pp.paydunya_master_key = request.POST.get("paydunya_master_key", "")
            pp.paydunya_private_key = request.POST.get("paydunya_private_key", "")
            pp.paydunya_token = request.POST.get("paydunya_token", "")
            pp.paydunya_mode = request.POST.get("paydunya_mode", "test")
            pp.paydunya_devise = request.POST.get("paydunya_devise", "XOF")
            pp.save()
            messages.success(request, "Coordonnées de paiement mises à jour.")
            return redirect("tenants:plateforme")

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
            elif action == "paiement_manuel":
                # Paiement Mobile Money manuel reçu : on prolonge +30j et on trace
                _prolonger_abonnement(restaurant)
                Paiement.objects.create(
                    restaurant=restaurant,
                    transaction_id=f"MANUEL-{restaurant.pk}-{uuid.uuid4().hex[:8].upper()}",
                    montant=restaurant.plan.prix_mensuel if restaurant.plan else 0,
                    devise="XOF",
                    statut="SUCCES",
                    description="Paiement Mobile Money manuel (validé par la plateforme)",
                )
                messages.success(
                    request,
                    f"Paiement manuel enregistré : abonnement de « {restaurant.nom} » "
                    f"prolongé jusqu'au {restaurant.abonnement_expire_le}.",
                )

    maintenant = timezone.localdate()

    # --- Statistiques plateforme ---
    restaurants_qs = Restaurant.objects.select_related("plan").all()
    total_restaurants = restaurants_qs.count()
    actifs = restaurants_qs.filter(actif=True).count()
    expirants = sum(
        1 for r in restaurants_qs if r.actif and r.abonnement_expire_le
        and 0 <= (r.abonnement_expire_le - maintenant).days <= 7
    )
    expires = sum(
        1 for r in restaurants_qs
        if r.abonnement_expire_le and r.abonnement_expire_le < maintenant
    )
    sans_abonnement = sum(
        1 for r in restaurants_qs if not r.abonnement_expire_le
    )
    revenus_paydunya = (
        Paiement.objects.filter(statut="SUCCES").aggregate(t=Sum("montant"))["t"] or 0
    )
    paiements_succes = Paiement.objects.filter(statut="SUCCES").count()

    restaurants = list(restaurants_qs)
    plans = Plan.objects.all()
    parametres = ParametrePlateforme.load()
    paiements = (
        Paiement.objects.select_related("restaurant")
        .order_by("-date_creation")[:50]
    )
    return render(
        request,
        "tenants/plateforme.html",
        {
            "restaurants": restaurants,
            "plans": plans,
            "maintenant": maintenant,
            "parametres": parametres,
            "paiements": paiements,
            "stats": {
                "total": total_restaurants,
                "actifs": actifs,
                "expirants": expirants,
                "expires": expires,
                "sans_abonnement": sans_abonnement,
                "revenus": revenus_paydunya,
                "paiements_succes": paiements_succes,
            },
        },
    )


@user_passes_test(_est_superadmin, login_url="accounts:login")
def creer_restaurant_plateforme(request):
    """Formulaire superadmin : crée un restaurant + compte gérant + abonnement."""
    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        prenom = request.POST.get("prenom", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        telephone = request.POST.get("telephone", "").strip()
        adresse = request.POST.get("adresse", "").strip()
        password = request.POST.get("password", "")
        plan_id = request.POST.get("plan")
        abonnement = request.POST.get("abonnement_mois")

        erreurs = []
        if not nom:
            erreurs.append("Le nom du restaurant est obligatoire.")
        if not username or not email:
            erreurs.append("L'identifiant et l'e-mail du gérant sont obligatoires.")
        if not password or len(password) < 8:
            erreurs.append("Le mot de passe doit contenir au moins 8 caractères.")
        if CustomUser.objects.filter(username=username).exists():
            erreurs.append("Cet identifiant est déjà utilisé.")

        plan = Plan.objects.filter(pk=plan_id).first() if plan_id else None

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
                        adresse=adresse,
                        actif=True,
                        plan=plan,
                    )
                    if abonnement and abonnement.isdigit():
                        restaurant.abonnement_expire_le = (
                            timezone.localdate() + timedelta(days=int(abonnement) * 30)
                        )
                        restaurant.save(update_fields=["abonnement_expire_le"])
                    CustomUser.objects.create_user(
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
                messages.success(
                    request,
                    f"Restaurant « {nom} » créé (compte : {username}).",
                )
                return redirect("tenants:plateforme")
            except Exception as e:
                erreurs.append(f"Erreur lors de la création : {e}")

        for e in erreurs:
            messages.error(request, e)

    return render(
        request,
        "tenants/creer_restaurant_plateforme.html",
        {"plans": Plan.objects.filter(actif=True)},
    )


@user_passes_test(_est_superadmin, login_url="accounts:login")
def creer_utilisateur_plateforme(request):
    """Formulaire superadmin : crée un utilisateur dans un restaurant existant."""
    if request.method == "POST":
        restaurant_id = request.POST.get("restaurant")
        prenom = request.POST.get("prenom", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        role = request.POST.get("role", "SERVEUR")
        password = request.POST.get("password", "")

        restaurant = Restaurant.objects.filter(pk=restaurant_id).first()
        erreurs = []
        if restaurant is None:
            erreurs.append("Veuillez choisir un restaurant.")
        if not username or not email:
            erreurs.append("L'identifiant et l'e-mail sont obligatoires.")
        if not password or len(password) < 8:
            erreurs.append("Le mot de passe doit contenir au moins 8 caractères.")
        if CustomUser.objects.filter(username=username).exists():
            erreurs.append("Cet identifiant est déjà utilisé.")

        if not erreurs:
            try:
                CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=prenom,
                    role=role,
                    restaurant=restaurant,
                )
                messages.success(
                    request,
                    f"Utilisateur « {username} » créé dans « {restaurant.nom} ».",
                )
                return redirect("tenants:utilisateurs_plateforme")
            except Exception as e:
                erreurs.append(f"Erreur lors de la création : {e}")

        for e in erreurs:
            messages.error(request, e)

    return render(
        request,
        "tenants/creer_utilisateur_plateforme.html",
        {
            "restaurants": Restaurant.objects.order_by("nom"),
            "roles": CustomUser.Role.choices if hasattr(CustomUser, "Role") else CustomUser._meta.get_field("role").choices,
        },
    )


@user_passes_test(_est_superadmin, login_url="accounts:login")
def modifier_restaurant_plateforme(request, pk):
    """Formulaire superadmin : modifier les infos d'un restaurant existant."""
    restaurant = Restaurant.objects.filter(pk=pk).first()
    if restaurant is None:
        messages.error(request, "Restaurant introuvable.")
        return redirect("tenants:plateforme")

    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        telephone = request.POST.get("telephone", "").strip()
        adresse = request.POST.get("adresse", "").strip()
        email = request.POST.get("email", "").strip()
        plan_id = request.POST.get("plan")

        if not nom:
            messages.error(request, "Le nom du restaurant est obligatoire.")
        else:
            restaurant.nom = nom
            restaurant.telephone = telephone
            restaurant.adresse = adresse
            restaurant.email = email
            plan = Plan.objects.filter(pk=plan_id).first() if plan_id else None
            restaurant.plan = plan
            restaurant.save()
            ParametreRestaurant.objects.filter(restaurant=restaurant).update(
                nom=nom, telephone=telephone, email=email
            )
            messages.success(request, f"Restaurant « {nom} » mis à jour.")
            return redirect("tenants:plateforme")

    return render(
        request,
        "tenants/modifier_restaurant_plateforme.html",
        {
            "restaurant": restaurant,
            "plans": Plan.objects.all(),
        },
    )


@login_required
def recu_paiement(request, pk):
    """Reçu de paiement imprimable (gérant de son paiement / superadmin de tous)."""
    paiement = Paiement.objects.filter(pk=pk).select_related("restaurant").first()
    if paiement is None:
        messages.error(request, "Paiement introuvable.")
        return redirect("dashboard:index")

    if not request.user.is_superuser:
        restaurant = request.user.restaurant
        if restaurant is None or paiement.restaurant_id != restaurant.id:
            messages.error(request, "Vous n'avez pas accès à ce reçu.")
            return redirect("tenants:mes_paiements")

    parametres = ParametrePlateforme.load()
    pp = None
    if paiement.restaurant:
        pp = ParametreRestaurant.objects.filter(restaurant=paiement.restaurant).first()

    return render(
        request,
        "tenants/recu_paiement.html",
        {
            "paiement": paiement,
            "parametres": parametres,
            "pp": pp,
        },
    )


@login_required
def recu_paiement_pdf(request, pk):
    """Télécharge le reçu de paiement en vrai PDF (ReportLab)."""
    from .recu_pdf import generer_recu_pdf

    paiement = Paiement.objects.filter(pk=pk).select_related("restaurant").first()
    if paiement is None:
        raise Http404("Paiement introuvable.")

    if not request.user.is_superuser:
        restaurant = request.user.restaurant
        if restaurant is None or paiement.restaurant_id != restaurant.id:
            raise Http404("Vous n'avez pas accès à ce reçu.")

    parametres = ParametrePlateforme.load()
    pdf = generer_recu_pdf(paiement, parametres)

    nom_fichier = f"recu-{paiement.transaction_id}.pdf"
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{nom_fichier}"'
    return response


@login_required
def mon_abonnement(request):
    """Page du gérant : voir son plan, sa date d'expiration et comment payer."""
    if request.user.is_superuser:
        return redirect("tenants:plateforme")

    restaurant = request.user.restaurant
    if restaurant is None:
        messages.error(request, "Votre compte n'est pas rattaché à un restaurant.")
        return redirect("dashboard:index")

    parametres = ParametrePlateforme.load()
    maintenant = timezone.localdate()
    jours_restants = None
    if restaurant.abonnement_expire_le:
        jours_restants = (restaurant.abonnement_expire_le - maintenant).days

    # Horodatage d'expiration pour le compte à rebours (JS)
    expiration_ts = None
    if restaurant.abonnement_expire_le:
        expiration_ts = timezone.make_aware(
            timezone.datetime.combine(
                restaurant.abonnement_expire_le,
                timezone.datetime.max.time(),
            )
        ).timestamp() * 1000

    return render(
        request,
        "tenants/mon_abonnement.html",
        {
            "restaurant": restaurant,
            "plan": restaurant.plan,
            "parametres": parametres,
            "maintenant": maintenant,
            "jours_restants": jours_restants,
            "expiration_ts": int(expiration_ts) if expiration_ts else None,
        },
    )


@login_required
def mes_paiements(request):
    """Historique des paiements de l'abonnement du gérant (PayDunya + manuel)."""
    if request.user.is_superuser:
        return redirect("tenants:plateforme")

    restaurant = request.user.restaurant
    if restaurant is None:
        messages.error(request, "Votre compte n'est pas rattaché à un restaurant.")
        return redirect("dashboard:index")

    paiements = (
        Paiement.objects.filter(restaurant=restaurant)
        .order_by("-date_creation")
    )
    return render(
        request,
        "tenants/mes_paiements.html",
        {"paiements": paiements, "restaurant": restaurant},
    )


def _prolonger_abonnement(restaurant, jours=30):
    """Prolonge l'abonnement d'un restaurant de `jours` jours (sans double comptage)."""
    base = timezone.localdate()
    if restaurant.abonnement_expire_le and restaurant.abonnement_expire_le > base:
        base = restaurant.abonnement_expire_le
    restaurant.abonnement_expire_le = base + timedelta(days=jours)
    restaurant.actif = True
    restaurant.save(update_fields=["abonnement_expire_le", "actif"])


@login_required
def lancer_paiement(request):
    """Initie un paiement PayDunya pour l'abonnement du restaurant connecté."""
    if request.user.is_superuser:
        return redirect("tenants:plateforme")

    restaurant = request.user.restaurant
    parametres = ParametrePlateforme.load()

    if not parametres.paydunya_active:
        messages.error(request, "Le paiement en ligne n'est pas encore disponible.")
        return redirect("tenants:mon_abonnement")

    plan = restaurant.plan
    if plan is None or not plan.prix_mensuel:
        messages.error(request, "Aucun montant d'abonnement configuré pour votre plan.")
        return redirect("tenants:mon_abonnement")

    montant = plan.prix_mensuel
    transaction_id = f"ABO-{restaurant.pk}-{uuid.uuid4().hex[:10].upper()}"

    # Récupération du gérant (nom du client)
    admin_user = restaurant.utilisateurs.filter(role="ADMIN").first()
    nom = admin_user.get_full_name() if admin_user else ""
    telephone = getattr(admin_user, "telephone", "") if admin_user else ""

    description = (
        f"Abonnement {parametres.nom_plateforme or 'RestaurantPro'} "
        f"- {plan.nom} (1 mois)"
    )
    # URLs absolues : callback = webhook IPN, return/cancel = page de retour
    base_url = request.build_absolute_uri("/").rstrip("/")
    callback_url = f"{base_url}/tenants/paiement/notif/"
    return_url = f"{base_url}/tenants/paiement/retour/"
    cancel_url = f"{base_url}/tenants/paiement/retour/"

    paiement = Paiement.objects.create(
        restaurant=restaurant,
        transaction_id=transaction_id,
        montant=montant,
        devise=parametres.paydunya_devise or "XOF",
        statut="EN_ATTENTE",
        description=description,
    )

    try:
        reponse = paydunya.initialiser_paiement(
            master_key=parametres.paydunya_master_key,
            private_key=parametres.paydunya_private_key,
            token=parametres.paydunya_token,
            mode=parametres.paydunya_mode or "test",
            montant=montant,
            description=description,
            store_name=parametres.nom_plateforme or "RestaurantPro",
            callback_url=callback_url,
            return_url=return_url,
            cancel_url=cancel_url,
            customer_name=nom,
            customer_phone=telephone,
        )
    except paydunya.PayDunyaError as e:
        paiement.statut = "ECHEC"
        paiement.donnees = {"erreur": str(e)}
        paiement.save(update_fields=["statut", "donnees"])
        messages.error(request, f"Échec de l'initiation du paiement : {e}")
        return redirect("tenants:mon_abonnement")

    invoice_token = reponse.get("token", "")
    payment_url = reponse.get("response_text")
    if not payment_url or not invoice_token:
        paiement.statut = "ECHEC"
        paiement.save(update_fields=["statut"])
        messages.error(request, "PayDunya n'a pas renvoyé d'URL de paiement.")
        return redirect("tenants:mon_abonnement")

    paiement.paydunya_token = invoice_token
    paiement.donnees = reponse
    paiement.save(update_fields=["paydunya_token", "donnees"])

    # Enregistre le token dans la session pour le retour
    request.session["paiement_en_cours"] = invoice_token
    return redirect(payment_url)


@csrf_exempt
def notif_paiement(request):
    """Webhook IPN PayDunya (callback_url). Reçoit le statut du paiement,
    vérifie le hash (SHA-512 de la master key) puis prolonge l'abonnement
    si réussi.

    PayDunya fait un POST application/x-www-form-urlencoded avec le champ
    "data" contenant le JSON de la transaction. Doit répondre HTTP 200.
    """
    if request.method != "POST":
        return HttpResponse("OK", status=200)

    raw = request.POST.get("data") or request.body.decode("utf-8", errors="replace")
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return HttpResponse("OK", status=200)

    parametres = ParametrePlateforme.load()
    if not paydunya.verifier_hash(parametres.paydunya_master_key, data.get("hash", "")):
        # Requête non émise par PayDunya : on ignore
        return HttpResponse("OK", status=200)

    statut = (data.get("status") or "").lower()
    invoice_token = (data.get("invoice") or {}).get("token", "")
    paiement = Paiement.objects.filter(paydunya_token=invoice_token).first()
    if paiement is None:
        # Transaction inconnue : on répond quand même 200 pour PayDunya
        return HttpResponse("OK", status=200)

    if statut == "completed":
        with transaction.atomic():
            # Recharge le paiement verrouillé pour éviter la double activation
            paiement = Paiement.objects.select_for_update().get(pk=paiement.pk)
            if paiement.statut != "SUCCES":
                paiement.statut = "SUCCES"
                paiement.donnees = data
                paiement.save(update_fields=["statut", "donnees"])
                if paiement.restaurant_id:
                    _prolonger_abonnement(paiement.restaurant)
    elif statut in ("failed", "cancelled"):
        paiement.statut = "ANNULE" if statut == "cancelled" else "ECHEC"
        paiement.donnees = data
        paiement.save(update_fields=["statut", "donnees"])
    else:
        paiement.statut = "EN_ATTENTE"
        paiement.donnees = data
        paiement.save(update_fields=["statut", "donnees"])

    return HttpResponse("OK", status=200)


def retour_paiement(request):
    """URL de retour PayDunya (return_url / cancel_url). PayDunya ajoute
    ?token=invoice_token. Vérifie le statut et affiche le résultat au gérant."""
    invoice_token = request.GET.get("token") or request.POST.get("token") or ""
    if not invoice_token:
        invoice_token = request.session.pop("paiement_en_cours", None) or ""

    paiement = Paiement.objects.filter(paydunya_token=invoice_token).first()
    if paiement is None:
        messages.info(request, "Aucun paiement trouvé.")
        return redirect("tenants:mon_abonnement")

    parametres = ParametrePlateforme.load()
    try:
        reponse = paydunya.verifier_paiement(
            master_key=parametres.paydunya_master_key,
            private_key=parametres.paydunya_private_key,
            token=parametres.paydunya_token,
            mode=parametres.paydunya_mode or "test",
            invoice_token=invoice_token,
        )
    except paydunya.PayDunyaError as e:
        messages.error(request, f"Erreur de vérification du paiement : {e}")
        return redirect("tenants:mon_abonnement")

    statut = (reponse.get("status") or "").lower()

    if statut == "completed":
        if paiement.statut != "SUCCES":
            paiement.statut = "SUCCES"
            paiement.donnees = reponse
            paiement.save(update_fields=["statut", "donnees"])
            if paiement.restaurant_id:
                _prolonger_abonnement(paiement.restaurant)
        messages.success(
            request,
            "Paiement confirmé ! Votre abonnement a été prolongé d'un mois.",
        )
    elif statut in ("failed", "cancelled"):
        paiement.statut = "ANNULE" if statut == "cancelled" else "ECHEC"
        paiement.donnees = reponse
        paiement.save(update_fields=["statut", "donnees"])
        messages.warning(
            request,
            "Votre paiement a été annulé ou a échoué. Réessayez si besoin.",
        )
    else:
        paiement.statut = "EN_ATTENTE"
        paiement.donnees = reponse
        paiement.save(update_fields=["statut", "donnees"])
        messages.warning(
            request,
            "Votre paiement est en attente de confirmation. "
            "Réessayez ou contactez la plateforme.",
        )

    request.session.pop("paiement_en_cours", None)
    return redirect("tenants:mon_abonnement")


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
