from django.shortcuts import render

from apps.commandes.models import Commande
from apps.accounts.decorators import role_required


@role_required(["ADMIN", "CUISINIER"])
def index(request):
    """Vue dédiée au rôle cuisinier : commandes en attente ou en préparation."""

    commandes = Commande.objects.filter(
        statut__in=[
            Commande.EN_ATTENTE,
            Commande.EN_PREPARATION
        ]
    ).prefetch_related("lignes__produit")

    stats = {
        "en_attente": commandes.filter(statut=Commande.EN_ATTENTE).count(),
        "en_cours": commandes.filter(statut=Commande.EN_PREPARATION).count(),
        "pretes": Commande.objects.filter(statut=Commande.PRETE).count(),
    }

    return render(
        request,
        "cuisine/index.html",
        {
            "commandes": commandes,
            "stats": stats,
        }
    )