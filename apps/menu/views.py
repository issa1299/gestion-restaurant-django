from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Prefetch
from apps.menu.models import Categorie, Produit
from apps.accounts.decorators import role_required
from apps.notifications.utils import envoyer_notification_broadcast
from PIL import Image
import os
from django.conf import settings


def index(request):
    """Affiche le menu complet avec toutes les catégories (public)"""
    categories = Categorie.objects.prefetch_related(
        Prefetch("produits", queryset=Produit.objects.filter(disponible=True))
    ).all()
    table_numero = request.GET.get("table", "")
    return render(request, "menu/index.html", {
        "categories": categories,
        "table_numero": table_numero,
    })


@role_required(["ADMIN", "GÉRANT"])
def gestion(request):
    """Page interne de gestion du menu (staff)"""
    categories = Categorie.objects.prefetch_related("produits").all()
    total_produits = Produit.objects.count()
    total_indisponibles = Produit.objects.filter(disponible=False).count()
    return render(request, "menu/gestion.html", {
        "categories": categories,
        "total_produits": total_produits,
        "total_indisponibles": total_indisponibles,
    })


@role_required(["ADMIN", "GÉRANT", "CLIENT", "SERVEUR", "CUISINIER", "CAISSIER", "LIVREUR"])
def categorie(request, categorie_id):
    """Affiche les produits d'une catégorie"""
    categorie = get_object_or_404(Categorie, id=categorie_id)
    produits = categorie.produits.filter(disponible=True)
    categories = Categorie.objects.all()
    return render(request, "menu/categorie.html", {
        "categorie": categorie,
        "produits": produits,
        "categories": categories
    })


@role_required(["GÉRANT"])
def ajouter_categorie(request):
    """Ajouter une nouvelle catégorie"""
    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        description = request.POST.get("description", "").strip()

        if not nom:
            messages.error(request, "Le nom de la catégorie est requis.")
            return redirect("menu:ajouter_categorie")

        if Categorie.objects.filter(nom__iexact=nom).exists():
            messages.error(request, f"La catégorie '{nom}' existe déjà.")
            return redirect("menu:ajouter_categorie")

        categorie = Categorie.objects.create(
            nom=nom,
            description=description
        )
        messages.success(request, f"Catégorie '{categorie.nom}' créée avec succès.")
        return redirect("menu:gestion")

    return render(request, "menu/categorie_form.html", {"edition": False})


@role_required(["GÉRANT"])
def modifier_categorie(request, pk):
    """Modifier une catégorie"""
    categorie = get_object_or_404(Categorie, pk=pk)

    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        description = request.POST.get("description", "").strip()

        if not nom:
            messages.error(request, "Le nom de la catégorie est requis.")
            return redirect("menu:gestion")

        if Categorie.objects.filter(nom__iexact=nom).exclude(pk=pk).exists():
            messages.error(request, f"La catégorie '{nom}' existe déjà.")
            return redirect("menu:gestion")

        categorie.nom = nom
        categorie.description = description
        categorie.save()
        messages.success(request, f"Catégorie '{categorie.nom}' modifiée.")
        return redirect("menu:gestion")

    return render(request, "menu/categorie_form.html", {
        "categorie": categorie,
        "edition": True
    })


@role_required(["GÉRANT"])
def supprimer_categorie(request, pk):
    """Supprimer une catégorie"""
    categorie = get_object_or_404(Categorie, pk=pk)

    if request.method == "POST":
        nom = categorie.nom
        categorie.delete()
        messages.success(request, f"Catégorie '{nom}' supprimée.")
        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Méthode non autorisée."}, status=405)


@role_required(["GÉRANT"])
def ajouter_produit(request):
    """Ajouter un nouveau produit au menu"""
    categories = Categorie.objects.all()

    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        categorie_id = request.POST.get("categorie")
        prix = request.POST.get("prix")
        description = request.POST.get("description", "").strip()
        disponible = request.POST.get("disponible") == "on"

        if not nom or not categorie_id or not prix:
            messages.error(request, "Nom, catégorie et prix sont requis.")
            return redirect("menu:ajouter_produit")

        try:
            prix = float(prix)
            if prix <= 0:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, "Le prix doit être un nombre valide supérieur à 0.")
            return redirect("menu:ajouter_produit")

        categorie = get_object_or_404(Categorie, id=categorie_id)
        produit = Produit.objects.create(
            categorie=categorie,
            nom=nom,
            description=description,
            prix=prix,
            disponible=disponible,
        )

        # Gestion de l'image uploadée
        image_file = request.FILES.get("image")
        if image_file:
            # Vérifier que c'est une image valide
            try:
                img = Image.open(image_file)
                img.verify()
                image_file.seek(0)
                produit.image = image_file
                produit.save()
            except Exception:
                messages.warning(request, "Le fichier n'est pas une image valide.")

        # Notification temps réel
        envoyer_notification_broadcast("menu", "produit_ajoute", {
            "id": produit.id,
            "nom": produit.nom,
            "categorie": categorie.nom,
            "prix": str(produit.prix),
            "disponible": produit.disponible,
            "image_url": produit.image.url if produit.image else "",
        })

        messages.success(request, f"Produit '{produit.nom}' ajouté au menu.")
        return redirect("menu:gestion")

    return render(request, "menu/produit_form.html", {
        "categories": categories,
        "edition": False
    })


@role_required(["GÉRANT"])
def modifier_produit(request, pk):
    """Modifier un produit"""
    produit = get_object_or_404(Produit, pk=pk)
    categories = Categorie.objects.all()

    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        categorie_id = request.POST.get("categorie")
        prix = request.POST.get("prix")
        description = request.POST.get("description", "").strip()
        disponible = request.POST.get("disponible") == "on"

        if not nom or not categorie_id or not prix:
            messages.error(request, "Nom, catégorie et prix sont requis.")
            return redirect("menu:modifier_produit", pk=pk)

        try:
            prix = float(prix)
            if prix <= 0:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, "Le prix doit être un nombre valide.")
            return redirect("menu:modifier_produit", pk=pk)

        produit.nom = nom
        produit.categorie = get_object_or_404(Categorie, id=categorie_id)
        produit.description = description
        produit.prix = prix
        produit.disponible = disponible
        produit.save()
        messages.success(request, f"Produit '{produit.nom}' modifié.")
        return redirect("menu:gestion")

    return render(request, "menu/produit_form.html", {
        "produit": produit,
        "categories": categories,
        "edition": True
    })


@role_required(["GÉRANT"])
def supprimer_produit(request, pk):
    """Supprimer un produit"""
    produit = get_object_or_404(Produit, pk=pk)

    if request.method == "POST":
        nom = produit.nom
        produit.delete()
        messages.success(request, f"Produit '{nom}' supprimé.")
        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Méthode non autorisée."}, status=405)
