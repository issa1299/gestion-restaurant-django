import json

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib import messages
from django.contrib.sessions.models import Session
from django.db.models import Q
from .models import DetailVente, Vente
from apps.menu.models import Produit
from apps.stock.models import MouvementStock, Stock
from apps.accounts.decorators import role_required
from apps.accounts.models import CustomUser
from apps.parametres.models import ParametreRestaurant



@role_required(["CAISSIER"])
def pos(request):
    from apps.menu.models import Categorie
    produits = Produit.objects.filter(disponible=True).select_related('categorie', 'stock')
    categories = Categorie.objects.all()
    parametre = ParametreRestaurant.load()

    return render(
        request,
        "ventes/pos.html",
        {
            "produits": produits,
            "categories": categories,
            "parametre": parametre,
        }
    )


@role_required(["CAISSIER"])
def enregistrer_vente(request):
    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Méthode non autorisée."
        }, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "message": "Données invalides."
        }, status=400)

    panier = data.get("panier", [])
    mode = data.get("mode_paiement")

    if not panier:
        return JsonResponse({
            "success": False,
            "message": "Le panier est vide."
        }, status=400)

    ids_produits = [int(item.get("id")) for item in panier]
    produits = {
        produit.id: produit
        for produit in Produit.objects.filter(id__in=ids_produits)
    }

    for item in panier:
        produit_id = int(item.get("id"))
        produit = produits.get(produit_id)

        if produit is None:
            return JsonResponse({
                "success": False,
                "message": "Produit introuvable."
            }, status=404)

        quantite = int(item.get("qte", 0))

        if quantite <= 0:
            return JsonResponse({
                "success": False,
                "message": f"Quantité invalide : {produit.nom}"
            }, status=400)

        stock = Stock.objects.filter(produit=produit).first()

        if stock is None or stock.quantite < quantite:
            return JsonResponse({
                "success": False,
                "message": f"Stock insuffisant : {produit.nom}"
            }, status=400)

    total = 0

    with transaction.atomic():
        vente = Vente.objects.create(
            caissier=request.user,
            total=0,
            mode_paiement=mode
        )

        for item in panier:
            produit = produits[int(item["id"])]
            quantite = int(item["qte"])
            prix = produit.prix
            sous_total = prix * quantite
            total += sous_total

            DetailVente.objects.create(
                vente=vente,
                produit=produit,
                quantite=quantite,
                prix=prix,
                sous_total=sous_total
            )

            stock = Stock.objects.select_for_update().filter(produit=produit).first()


            if not stock:
                raise Exception(f"Stock absent pour {produit.nom}" )
            stock.quantite -= quantite
            stock.save()

            MouvementStock.objects.create(
                produit=produit,
                type_mouvement="SORTIE",
                quantite=quantite,
                utilisateur=request.user,
                commentaire=f"Vente N° {vente.id}"
            )

        vente.total = total
        vente.save()

    return JsonResponse({
        "success": True,
        "vente_id": vente.id
    })


@role_required(["ADMIN", "CAISSIER"])
def ticket(request, vente_id):
    vente = get_object_or_404(
        Vente,
        id=vente_id
    )
    parametre = ParametreRestaurant.load()

    return render(
        request,
        "ventes/ticket.html",
        {
            "vente": vente,
            "parametre": parametre,
        }
    )


@role_required(["ADMIN", "CAISSIER"])
def detail_vente(request, vente_id):
    vente = get_object_or_404(
        Vente.objects.select_related("caissier", "annule_par"),
        id=vente_id
    )
    parametre = ParametreRestaurant.load()

    return render(
        request,
        "ventes/detail.html",
        {
            "vente": vente,
            "parametre": parametre,
        }
    )


@role_required(["CAISSIER"])
def annuler_vente(request, vente_id):
    """Annule une vente et remet les produits en stock."""
    vente = get_object_or_404(Vente, id=vente_id)

    if vente.annulee:
        messages.error(request, "Cette vente a déjà été annulée.")
        return redirect("ventes:detail", vente_id=vente.id)

    if request.method == "POST":
        with transaction.atomic():
            vente.annulee = True
            vente.annule_le = timezone.now()
            vente.annule_par = request.user
            vente.save()

            for detail in vente.details.all():
                stock, _ = Stock.objects.get_or_create(produit=detail.produit)
                stock.quantite += detail.quantite
                stock.save()

                MouvementStock.objects.create(
                    produit=detail.produit,
                    type_mouvement="ENTREE",
                    quantite=detail.quantite,
                    utilisateur=request.user,
                    commentaire=f"Retour stock — annulation vente N° {vente.id}",
                )

        messages.success(
            request,
            f"Vente N° {vente.id} annulée. Les produits ont été remis en stock."
        )
        return redirect("ventes:historique")

    return render(request, "ventes/annuler.html", {"vente": vente})


@role_required(["ADMIN", "CAISSIER"])
def historique(request):

    ventes = Vente.objects.select_related("caissier").order_by("-created_at")

    # Filtres serveur
    q = request.GET.get("q", "").strip()
    date = request.GET.get("date", "").strip()
    statut = request.GET.get("statut", "").strip()

    if q:
        ventes = ventes.filter(
            Q(id__icontains=q) | Q(caissier__username__icontains=q)
        )
    if date:
        ventes = ventes.filter(created_at__date=date)
    if statut == "annulees":
        ventes = ventes.filter(annulee=True)
    elif statut == "valides":
        ventes = ventes.filter(annulee=False)

    sessions = Session.objects.filter(
        expire_date__gte=timezone.now()
    )

    users_online = []

    for session in sessions:
        data = session.get_decoded()
        user_id = data.get("_auth_user_id")
        if user_id:
            users_online.append(user_id)

    users_online = list(set(users_online))

    utilisateurs_connectes = CustomUser.objects.filter(
        id__in=users_online,
        is_active=True
    )

    total = sum(
        vente.total for vente in ventes
    )

    return render(
        request,
        "ventes/historique.html",
        {
            "ventes": ventes,
            "total": total,
            "utilisateurs_connectes": utilisateurs_connectes,
            "nombre_connectes": utilisateurs_connectes.count(),
            "q": q,
            "date": date,
            "statut": statut,
        }
    )