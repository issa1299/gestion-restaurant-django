import uuid
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt

from . import cinetpay
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
            pp.cinetpay_active = request.POST.get("cinetpay_active") == "on"
            pp.cinetpay_apikey = request.POST.get("cinetpay_apikey", "")
            pp.cinetpay_site_id = request.POST.get("cinetpay_site_id", "")
            pp.cinetpay_devise = request.POST.get("cinetpay_devise", "XOF")
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

    restaurants = Restaurant.objects.select_related("plan").all()
    plans = Plan.objects.all()
    maintenant = timezone.localdate()
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
        },
    )


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
    """Initie un paiement CinetPay pour l'abonnement du restaurant connecté."""
    if request.user.is_superuser:
        return redirect("tenants:plateforme")

    restaurant = request.user.restaurant
    parametres = ParametrePlateforme.load()

    if not parametres.cinetpay_active:
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
    nom = admin_user.first_name if admin_user else ""
    prenom = admin_user.last_name if admin_user else ""

    description = f"Abonnement RestaurantPro - {plan.nom} (1 mois)"
    # URLs absolues : notify = webhook, return = page d'accueil
    base_url = request.build_absolute_uri("/").rstrip("/")
    notify_url = f"{base_url}/tenants/paiement/notif/"
    return_url = f"{base_url}/tenants/paiement/retour/"

    paiement = Paiement.objects.create(
        restaurant=restaurant,
        transaction_id=transaction_id,
        montant=montant,
        devise=parametres.cinetpay_devise or "XOF",
        statut="EN_ATTENTE",
        description=description,
    )

    try:
        reponse = cinetpay.initialiser_paiement(
            apikey=parametres.cinetpay_apikey,
            site_id=parametres.cinetpay_site_id,
            transaction_id=transaction_id,
            montant=montant,
            devise=parametres.cinetpay_devise or "XOF",
            description=description,
            notify_url=notify_url,
            return_url=return_url,
            customer_name=prenom,
            customer_surname=nom,
            channels="MOBILE_MONEY",
        )
    except cinetpay.CinetPayError as e:
        paiement.statut = "ECHEC"
        paiement.donnees = {"erreur": str(e)}
        paiement.save(update_fields=["statut", "donnees"])
        messages.error(request, f"Échec de l'initiation du paiement : {e}")
        return redirect("tenants:mon_abonnement")

    data = reponse.get("data", {})
    paiement.cinetpay_transaction_id = data.get("payment_id", "")
    paiement.donnees = reponse
    paiement.save(update_fields=["cinetpay_transaction_id", "donnees"])

    payment_url = data.get("payment_url")
    if not payment_url:
        paiement.statut = "ECHEC"
        paiement.save(update_fields=["statut"])
        messages.error(request, "CinetPay n'a pas renvoyé d'URL de paiement.")
        return redirect("tenants:mon_abonnement")

    # Enregistre l'ID dans la session pour le retour
    request.session["paiement_en_cours"] = transaction_id
    return redirect(payment_url)


@csrf_exempt
def notif_paiement(request):
    """Webhook CinetPay (notify_url). Reçoit le statut du paiement, le vérifie
    via l'API /v2/payment/check puis prolonge l'abonnement si réussi.

    Doit répondre HTTP 200 (GET et POST). CinetPay n'envoie pas le statut
    directement : il faut l'interroger via l'API de vérification.
    """
    transaction_id = request.POST.get("cpm_trans_id") or ""
    site_id = request.POST.get("cpm_site_id") or ""

    if request.method != "POST":
        return HttpResponse("OK", status=200)

    if not transaction_id:
        return HttpResponse("OK", status=200)

    parametres = ParametrePlateforme.load()
    paiement = Paiement.objects.filter(transaction_id=transaction_id).first()

    if paiement is None:
        # Transaction inconnue : on répond quand même 200 pour CinetPay
        return HttpResponse("OK", status=200)

    if paiement.statut == "SUCCES":
        # Déjà traité (les notifications peuvent arriver plusieurs fois)
        return HttpResponse("OK", status=200)

    try:
        reponse = cinetpay.verifier_paiement(
            apikey=parametres.cinetpay_apikey,
            site_id=parametres.cinetpay_site_id,
            transaction_id=transaction_id,
        )
    except cinetpay.CinetPayError:
        return HttpResponse("OK", status=200)

    code = str(reponse.get("code"))
    data = reponse.get("data", {}) or {}
    statut_cinetpay = (data.get("status") or "").lower()

    if paiement.restaurant_id:
        paiement.cinetpay_transaction_id = data.get("payment_id", "")
        paiement.telephone = data.get("phone_number", "") or data.get("cel_phone_num", "")

    if statut_cinetpay == "accepted" or code == "0":
        with transaction.atomic():
            # Recharge le paiement verrouillé pour éviter la double activation
            paiement = Paiement.objects.select_for_update().get(pk=paiement.pk)
            if paiement.statut != "SUCCES":
                paiement.statut = "SUCCES"
                paiement.donnees = reponse
                paiement.save(update_fields=["statut", "donnees"])
                if paiement.restaurant_id:
                    _prolonger_abonnement(paiement.restaurant)
    elif statut_cinetpay in ("refused", "cancelled", "failed"):
        paiement.statut = "REFUSE"
        paiement.donnees = reponse
        paiement.save(update_fields=["statut", "donnees"])
    else:
        paiement.statut = "EN_ATTENTE"
        paiement.donnees = reponse
        paiement.save(update_fields=["statut", "donnees"])

    return HttpResponse("OK", status=200)


def retour_paiement(request):
    """URL de retour CinetPay (return_url). Vérifie le paiement en cours et
    affiche le résultat au gérant."""
    transaction_id = request.POST.get("transaction_id") or request.GET.get(
        "transaction_id"
    )
    if not transaction_id:
        transaction_id = request.session.pop("paiement_en_cours", None)

    paiement = Paiement.objects.filter(transaction_id=transaction_id).first()
    if paiement is None:
        messages.info(request, "Aucun paiement trouvé.")
        return redirect("tenants:mon_abonnement")

    parametres = ParametrePlateforme.load()
    try:
        reponse = cinetpay.verifier_paiement(
            apikey=parametres.cinetpay_apikey,
            site_id=parametres.cinetpay_site_id,
            transaction_id=paiement.transaction_id,
        )
    except cinetpay.CinetPayError as e:
        messages.error(request, f"Erreur de vérification du paiement : {e}")
        return redirect("tenants:mon_abonnement")

    code = str(reponse.get("code"))
    data = reponse.get("data", {}) or {}
    statut = (data.get("status") or "").lower()

    if statut == "accepted" or code == "0":
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
    else:
        messages.warning(
            request,
            "Votre paiement n'a pas encore été confirmé. "
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
