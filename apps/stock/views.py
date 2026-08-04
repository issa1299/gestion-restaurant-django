from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import models
from apps.accounts.decorators import role_required
from .models import Stock, MouvementStock
from apps.menu.models import Produit


@role_required(["ADMIN", "GÉRANT"])
def liste_stock(request):
    stocks = Stock.objects.select_related("produit__categorie").all()

    q = request.GET.get("q", "").strip()
    statut = request.GET.get("statut", "").strip()

    if q:
        stocks = stocks.filter(produit__nom__icontains=q)
    if statut in ("FAIBLE", "RUPTURE", "OK"):
        if statut == "RUPTURE":
            stocks = stocks.filter(quantite=0)
        elif statut == "FAIBLE":
            stocks = stocks.filter(quantite__gt=0).filter(quantite__lte=models.F("seuil_alerte"))
        elif statut == "OK":
            stocks = stocks.filter(quantite__gt=models.F("seuil_alerte"))

    stock_faible = [s for s in stocks if s.stock_faible]

    return render(request, "stock/liste.html", {
        "stocks": stocks,
        "stock_faible": stock_faible,
        "q": q,
        "statut": statut,
        "total_articles": stocks.count(),
        "articles_faibles": len(stock_faible),
        "articles_ok": stocks.count() - len(stock_faible),
    })


@role_required(["ADMIN", "GÉRANT"])
def detail_stock(request, stock_id):
    stock = get_object_or_404(Stock.objects.select_related("produit__categorie"), id=stock_id)
    mouvements = stock.produit.mouvements_stock.select_related("utilisateur")[:50]
    return render(request, "stock/detail.html", {
        "stock": stock,
        "mouvements": mouvements,
    })


@role_required(["GÉRANT"])
def modifier_stock(request, stock_id):
    stock = get_object_or_404(Stock, id=stock_id)

    if request.method == "POST":
        seuil = request.POST.get("seuil_alerte")
        try:
            seuil = int(seuil)
            if seuil < 0:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, "Le seuil d'alerte doit être un entier positif.")
            return redirect("stock:modifier", stock_id=stock.id)

        stock.seuil_alerte = seuil
        stock.save()
        messages.success(request, f"Seuil d'alerte de '{stock.produit.nom}' mis à jour ({seuil}).")
        return redirect("stock:detail", stock_id=stock.id)

    return render(request, "stock/form.html", {"stock": stock})


@role_required(["GÉRANT"])
def supprimer_stock(request, stock_id):
    stock = get_object_or_404(Stock, id=stock_id)

    if request.method == "POST":
        nom = stock.produit.nom
        stock.delete()
        messages.success(request, f"Ligne de stock de '{nom}' supprimée.")
        return redirect("stock:liste")

    return render(request, "stock/supprimer.html", {"stock": stock})


@role_required(["GÉRANT"])
def ajouter_mouvement(request, stock_id):
    stock = get_object_or_404(Stock, id=stock_id)

    if request.method == "POST":
        type_mouvement = request.POST.get("type_mouvement")
        quantite = int(request.POST.get("quantite", 0))
        commentaire = request.POST.get("commentaire", "")

        if quantite <= 0:
            messages.error(request, "La quantité doit être supérieure à 0.")
            return redirect("stock:liste")

        # Calculer la nouvelle quantité
        if type_mouvement == "ENTREE":
            stock.quantite += quantite
        elif type_mouvement == "SORTIE":
            if quantite > stock.quantite:
                messages.error(request, "Stock insuffisant pour cette sortie.")
                return redirect("stock:liste")
            stock.quantite -= quantite
        elif type_mouvement == "AJUSTEMENT":
            stock.quantite = quantite

        stock.save()

        MouvementStock.objects.create(
            produit=stock.produit,
            type_mouvement=type_mouvement,
            quantite=quantite,
            utilisateur=request.user,
            commentaire=commentaire,
        )

        messages.success(request, f"Mouvement enregistré pour {stock.produit.nom}.")
        return redirect("stock:liste")

    return render(request, "stock/mouvement.html", {"stock": stock})


@role_required(["ADMIN", "GÉRANT"])
def historique_mouvements(request):
    mouvements = MouvementStock.objects.select_related(
        "produit", "utilisateur"
    ).all()[:100]

    return render(request, "stock/historique.html", {
        "mouvements": mouvements,
    })
