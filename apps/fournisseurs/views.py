from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse

from apps.accounts.decorators import role_required
from apps.menu.models import Produit
from apps.stock.models import Stock, MouvementStock

from .models import Fournisseur, Approvisionnement


@role_required(["ADMIN", "GÉRANT"])
def liste_fournisseurs(request):
    q = request.GET.get("q", "").strip()
    fournisseurs = Fournisseur.objects.all()

    if q:
        fournisseurs = fournisseurs.filter(
            nom__icontains=q
        ) | fournisseurs.filter(telephone__icontains=q)

    total = fournisseurs.count()
    nb_approvisionnements = Approvisionnement.objects.count()
    nb_produits = Produit.objects.count()

    return render(request, "fournisseurs/liste.html", {
        "fournisseurs": fournisseurs,
        "q": q,
        "total": total,
        "nb_approvisionnements": nb_approvisionnements,
        "nb_produits": nb_produits,
    })


@role_required(["ADMIN", "GÉRANT"])
def detail_fournisseur(request, pk):
    fournisseur = get_object_or_404(Fournisseur, pk=pk)
    approvisionnements = fournisseur.approvisionnements.select_related("produit", "utilisateur")
    total_depenses = sum(a.total for a in approvisionnements)

    return render(request, "fournisseurs/detail.html", {
        "fournisseur": fournisseur,
        "approvisionnements": approvisionnements,
        "total_depenses": total_depenses,
        "nb_approvisionnements": approvisionnements.count(),
    })


@role_required(["GÉRANT"])
def ajouter_fournisseur(request):
    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        if not nom:
            messages.error(request, "Le nom du fournisseur est requis.")
            return redirect("fournisseurs:ajouter")

        if Fournisseur.objects.filter(nom__iexact=nom).exists():
            messages.error(request, f"Le fournisseur '{nom}' existe déjà.")
            return redirect("fournisseurs:ajouter")

        Fournisseur.objects.create(
            nom=nom,
            telephone=request.POST.get("telephone", "").strip(),
            email=request.POST.get("email", "").strip(),
            adresse=request.POST.get("adresse", "").strip(),
            description=request.POST.get("description", "").strip(),
        )
        messages.success(request, f"Fournisseur '{nom}' créé avec succès.")
        return redirect("fournisseurs:liste")

    return render(request, "fournisseurs/form.html", {"edition": False})


@role_required(["GÉRANT"])
def modifier_fournisseur(request, pk):
    fournisseur = get_object_or_404(Fournisseur, pk=pk)

    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        if not nom:
            messages.error(request, "Le nom du fournisseur est requis.")
            return redirect("fournisseurs:modifier", pk=pk)

        if Fournisseur.objects.filter(nom__iexact=nom).exclude(pk=pk).exists():
            messages.error(request, f"Le fournisseur '{nom}' existe déjà.")
            return redirect("fournisseurs:modifier", pk=pk)

        fournisseur.nom = nom
        fournisseur.telephone = request.POST.get("telephone", "").strip()
        fournisseur.email = request.POST.get("email", "").strip()
        fournisseur.adresse = request.POST.get("adresse", "").strip()
        fournisseur.description = request.POST.get("description", "").strip()
        fournisseur.save()

        messages.success(request, f"Fournisseur '{nom}' modifié.")
        return redirect("fournisseurs:detail", pk=pk)

    return render(request, "fournisseurs/form.html", {
        "fournisseur": fournisseur,
        "edition": True,
    })


@role_required(["GÉRANT"])
def supprimer_fournisseur(request, pk):
    fournisseur = get_object_or_404(Fournisseur, pk=pk)

    if request.method == "POST":
        nom = fournisseur.nom
        fournisseur.delete()
        messages.success(request, f"Fournisseur '{nom}' supprimé.")
        return redirect("fournisseurs:liste")

    return render(request, "fournisseurs/supprimer.html", {"fournisseur": fournisseur})


@role_required(["GÉRANT"])
def ajouter_approvisionnement(request):
    if request.method == "POST":
        fournisseur_id = request.POST.get("fournisseur")
        produit_id = request.POST.get("produit")
        quantite = request.POST.get("quantite")
        prix_unitaire = request.POST.get("prix_unitaire", "0")
        commentaire = request.POST.get("commentaire", "").strip()

        if not produit_id or not quantite:
            messages.error(request, "Le produit et la quantité sont requis.")
            return redirect("fournisseurs:approvisionnements")

        try:
            quantite = int(quantite)
            if quantite <= 0:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, "La quantité doit être un entier supérieur à 0.")
            return redirect("fournisseurs:approvisionnements")

        try:
            prix_unitaire = float(prix_unitaire)
            if prix_unitaire < 0:
                raise ValueError
        except (ValueError, TypeError):
            prix_unitaire = 0

        produit = get_object_or_404(Produit, pk=produit_id)
        fournisseur = None
        if fournisseur_id:
            fournisseur = get_object_or_404(Fournisseur, pk=fournisseur_id)

        # Mettre à jour le stock
        stock, _ = Stock.objects.get_or_create(produit=produit)
        stock.quantite += quantite
        stock.save()

        MouvementStock.objects.create(
            produit=produit,
            type_mouvement="ENTREE",
            quantite=quantite,
            utilisateur=request.user,
            commentaire=f"Approvisionnement {fournisseur.nom if fournisseur else 'N/A'}",
        )

        Approvisionnement.objects.create(
            fournisseur=fournisseur,
            produit=produit,
            quantite=quantite,
            prix_unitaire=prix_unitaire,
            utilisateur=request.user,
            commentaire=commentaire,
        )

        messages.success(
            request,
            f"{quantite} x {produit.nom} ajouté(s) au stock via {fournisseur.nom if fournisseur else 'aucun fournisseur'}."
        )
        return redirect("fournisseurs:approvisionnements")

    fournisseurs = Fournisseur.objects.all()
    produits = Produit.objects.select_related("stock").all()

    return render(request, "fournisseurs/approvisionnement_form.html", {
        "fournisseurs": fournisseurs,
        "produits": produits,
    })


@role_required(["ADMIN", "GÉRANT"])
def liste_approvisionnements(request):
    q = request.GET.get("q", "").strip()
    approvisionnements = Approvisionnement.objects.select_related(
        "fournisseur", "produit", "utilisateur"
    )

    if q:
        approvisionnements = approvisionnements.filter(
            produit__nom__icontains=q
        ) | approvisionnements.filter(fournisseur__nom__icontains=q)

    total_depenses = sum(a.total for a in approvisionnements)

    return render(request, "fournisseurs/approvisionnements.html", {
        "approvisionnements": approvisionnements,
        "q": q,
        "nb": approvisionnements.count(),
        "total_depenses": total_depenses,
    })
