from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from apps.commandes.models import Commande, LigneCommande
from apps.commandes.forms import CommandeForm, LigneCommandeFormSet
from apps.accounts.decorators import role_required
from apps.menu.models import Produit
from apps.clients.models import Client
from apps.notifications.utils import notifier_changement_statut_commande, notifier_nouvelle_commande


@role_required(["ADMIN", "SERVEUR", "CUISINIER"])
def index(request):
    """Liste des commandes"""
    commandes = Commande.objects.all().prefetch_related("lignes__produit", "client", "table", "serveur")
    stats = {
        "en_attente": commandes.filter(statut=Commande.EN_ATTENTE).count(),
        "en_preparation": commandes.filter(statut=Commande.EN_PREPARATION).count(),
        "pretes": commandes.filter(statut=Commande.PRETE).count(),
    }
    return render(request, "commandes/index.html", {
        "commandes": commandes,
        "stats": stats,
        "groupe": "commandes"
    })


@role_required(["SERVEUR"])
def ajouter(request):
    """Ajouter une nouvelle commande"""
    from apps.menu.models import Categorie
    produits = Produit.objects.filter(disponible=True).select_related('categorie', 'stock')
    categories = Categorie.objects.all()
    
    if request.method == "POST":
        form = CommandeForm(request.POST)
        formset = LigneCommandeFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            commande = form.save()
            formset.instance = commande
            formset.save()
            notifier_nouvelle_commande(commande)
            messages.success(request, f"Commande N° {commande.id} créée avec succès.")
            return redirect('commandes:liste')
    else:
        form = CommandeForm()
        formset = LigneCommandeFormSet()
    
    return render(request, "commandes/ajouter.html", {
        'form': form,
        'formset': formset,
        'produits': produits,
        'categories': categories,
        'groupe': 'commandes'
    })


@role_required(["ADMIN", "SERVEUR", "CUISINIER"])
def detail(request, pk):
    """Détail d'une commande"""
    commande = get_object_or_404(
        Commande.objects.prefetch_related("lignes__produit"),
        pk=pk
    )
    return render(request, "commandes/detail.html", {
        "commande": commande,
        "groupe": "commandes"
    })


@role_required(["SERVEUR"])
def modifier(request, pk):
    """Modifier une commande"""
    commande = get_object_or_404(Commande, pk=pk)
    produits = Produit.objects.filter(disponible=True)
    
    if request.method == "POST":
        form = CommandeForm(request.POST, instance=commande)
        formset = LigneCommandeFormSet(request.POST, instance=commande)
        
        if form.is_valid() and formset.is_valid():
            commande = form.save()
            formset.instance = commande
            # Lignes à conserver (celles envoyées dans le formset, non supprimées)
            ids_conserves = [
                form.cleaned_data["id"].id
                for form in formset.forms
                if form.cleaned_data.get("id") and not form.cleaned_data.get("DELETE")
            ]
            # Supprimer les lignes retirées du panier (absentes du formset soumis)
            commande.lignes.exclude(id__in=ids_conserves).delete()
            formset.save()
            messages.success(request, f"Commande N° {commande.id} modifiée.")
            return redirect('commandes:detail', pk=commande.pk)
    else:
        form = CommandeForm(instance=commande)
        formset = LigneCommandeFormSet(instance=commande)
    
    return render(request, "commandes/ajouter.html", {
        'form': form,
        'formset': formset,
        'produits': produits,
        'commande': commande,
        'edition': True,
        'groupe': 'commandes'
    })


@role_required(["SERVEUR", "CUISINIER"])
def changer_statut(request, pk):
    """Changer le statut d'une commande (AJAX)"""
    if request.method != "POST":
        return JsonResponse({"error": "Méthode non autorisée"}, status=405)
    
    commande = get_object_or_404(Commande, pk=pk)
    nouveau_statut = request.POST.get("statut")
    
    statuts_valides = [s[0] for s in Commande.STATUTS]
    if nouveau_statut not in statuts_valides:
        return JsonResponse({"error": "Statut invalide"}, status=400)
    
    ancien_statut = commande.statut
    commande.statut = nouveau_statut
    commande.save()
    
    # Notification WebSocket
    notifier_changement_statut_commande(commande.id, ancien_statut, nouveau_statut)
    
    return JsonResponse({
        "success": True,
        "id": commande.id,
        "ancien_statut": ancien_statut,
        "nouveau_statut": nouveau_statut,
        "statut_display": commande.get_statut_display()
    })


def client_commander(request):
    """Page de commande pour les clients avec panier interactif (publique)"""
    produits = Produit.objects.filter(disponible=True)
    return render(request, "commandes/client_commander.html", {
        "produits": produits,
        "groupe": "commandes"
    })


@require_POST
@csrf_exempt
def client_passer_commande(request):
    """API: Le client valide son panier et crée une commande (support guest)"""
    import json
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Données invalides."}, status=400)
    
    panier = data.get("panier", [])
    mode = data.get("mode", "SUR_PLACE")
    adresse = data.get("adresse", "")
    telephone = data.get("telephone", "")
    guest_nom = data.get("guest_nom", "").strip()
    guest_telephone = data.get("guest_telephone", "").strip()
    
    if not panier:
        return JsonResponse({"success": False, "message": "Panier vide."}, status=400)
    
    if mode == "LIVRAISON" and not adresse:
        return JsonResponse({"success": False, "message": "Adresse de livraison requise."}, status=400)
    
    # Gestion client : connecté ou guest
    if request.user.is_authenticated and request.user.role != "CLIENT":
        user = request.user
        client, _ = Client.objects.get_or_create(
            nom=user.username,
            defaults={
                "telephone": user.telephone,
                "email": user.email,
                "adresse": user.adresse,
            }
        )
    else:
        # Guest ou CLIENT connecté
        if request.user.is_authenticated and request.user.role == "CLIENT":
            nom = request.user.username
            tel = request.user.telephone
            email = request.user.email
        else:
            # Guest: nom et téléphone obligatoires
            if not guest_nom:
                return JsonResponse({"success": False, "message": "Votre nom est requis."}, status=400)
            if not guest_telephone:
                return JsonResponse({"success": False, "message": "Votre téléphone est requis."}, status=400)
            nom = guest_nom
            tel = guest_telephone
            email = ""
        
        client, _ = Client.objects.get_or_create(
            nom=nom,
            defaults={
                "telephone": tel,
                "email": email,
                "adresse": adresse,
            }
        )
    
    ids_produits = [int(item.get("id")) for item in panier]
    produits = {p.id: p for p in Produit.objects.filter(id__in=ids_produits, disponible=True)}
    
    if len(produits) != len(ids_produits):
        return JsonResponse({"success": False, "message": "Certains produits ne sont plus disponibles."}, status=400)
    
    commande = Commande.objects.create(
        client=client,
        type=mode if mode in (Commande.SUR_PLACE, Commande.LIVRAISON) else Commande.SUR_PLACE,
        statut=Commande.EN_ATTENTE,
        adresse_livraison=adresse if mode == "LIVRAISON" else "",
        telephone_livraison=telephone if mode == "LIVRAISON" else guest_telephone,
    )
    
    for item in panier:
        produit = produits[int(item["id"])]
        quantite = int(item.get("qte", 1))
        prix = produit.prix
        LigneCommande.objects.create(
            commande=commande,
            produit=produit,
            quantite=quantite,
            prix=prix,
        )
    
    notifier_nouvelle_commande(commande)
    
    return JsonResponse({
        "success": True,
        "commande_id": commande.id,
        "message": f"Commande N° {commande.id} créée !"
    })
