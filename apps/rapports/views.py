import csv

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F
from django.utils import timezone
from django.http import HttpResponse
from datetime import timedelta, datetime
from apps.ventes.models import Vente, DetailVente
from apps.commandes.models import Commande


def _obtenir_periode(request):
    aujourd_hui = timezone.now().date()
    il_y_a_7_jours = aujourd_hui - timedelta(days=6)

    date_debut_str = request.GET.get('date_debut')
    date_fin_str = request.GET.get('date_fin')

    if date_debut_str and date_fin_str:
        try:
            date_debut = datetime.strptime(date_debut_str, "%Y-%m-%d").date()
            date_fin = datetime.strptime(date_fin_str, "%Y-%m-%d").date()
        except ValueError:
            date_debut = il_y_a_7_jours
            date_fin = aujourd_hui
    else:
        date_debut = il_y_a_7_jours
        date_fin = aujourd_hui

    return date_debut, date_fin


@login_required
def index(request):
    if request.user.role not in ["ADMIN"]:
        return render(request, "base/403.html", status=403)

    date_debut, date_fin = _obtenir_periode(request)

    ventes_periode = Vente.objects.filter(
        created_at__date__gte=date_debut,
        created_at__date__lte=date_fin
    )

    ca_total = ventes_periode.aggregate(total=Sum('total'))['total'] or 0
    nb_ventes = ventes_periode.count()

    # Ventes par jour (pour le graphique)
    from django.db.models.functions import TruncDate
    ventes_par_jour = ventes_periode.annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        ca_jour=Sum('total'),
        nb=Count('id')
    ).order_by('date')

    dates_chart = [v['date'].strftime('%d/%m') for v in ventes_par_jour]
    ca_chart = [float(v['ca_jour']) for v in ventes_par_jour]

    # Top produits
    top_produits = DetailVente.objects.filter(
        vente__created_at__date__gte=date_debut,
        vente__created_at__date__lte=date_fin
    ).values('produit__nom').annotate(
        total_qte=Sum('quantite'),
        total_ca=Sum('sous_total')
    ).order_by('-total_qte')[:5]

    # Mode de paiement
    ca_par_mode = ventes_periode.values('mode_paiement').annotate(
        total=Sum('total')
    ).order_by('-total')

    # CA par caissier
    ca_par_caissier = ventes_periode.values('caissier__username').annotate(
        total=Sum('total'),
        nb=Count('id')
    ).order_by('-total')

    # CA par table (via les commandes sur place)
    ca_par_table = Commande.objects.filter(
        table__isnull=False,
        created_at__date__gte=date_debut,
        created_at__date__lte=date_fin,
        statut__in=[Commande.LIVREE, Commande.PRETE]
    ).values('table__numero').annotate(
        nb=Count('id')
    ).order_by('-nb')

    # Panier moyen
    panier_moyen = (ca_total / nb_ventes) if nb_ventes else 0

    context = {
        'date_debut': date_debut.strftime("%Y-%m-%d"),
        'date_fin': date_fin.strftime("%Y-%m-%d"),
        'ca_total': ca_total,
        'nb_ventes': nb_ventes,
        'panier_moyen': panier_moyen,
        'dates_chart': dates_chart,
        'ca_chart': ca_chart,
        'top_produits': top_produits,
        'ca_par_mode': ca_par_mode,
        'ca_par_caissier': ca_par_caissier,
        'ca_par_table': ca_par_table,
    }

    return render(request, "rapports/index.html", context)


@login_required
def export_csv(request):
    """Exporte les ventes de la période en CSV."""
    if request.user.role not in ["ADMIN"]:
        return render(request, "base/403.html", status=403)

    date_debut, date_fin = _obtenir_periode(request)

    ventes = Vente.objects.filter(
        created_at__date__gte=date_debut,
        created_at__date__lte=date_fin
    ).select_related('caissier').order_by('created_at')

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="rapport_ventes_{date_debut}_{date_fin}.csv"'
    )

    writer = csv.writer(response, delimiter=";")
    writer.writerow(["N°", "Date", "Caissier", "Mode de paiement", "Total (FCFA)", "Statut"])

    for vente in ventes:
        writer.writerow([
            vente.id,
            vente.created_at.strftime("%d/%m/%Y %H:%M"),
            vente.caissier.username if vente.caissier else "",
            vente.get_mode_paiement_display(),
            vente.total,
            "Annulée" if vente.annulee else "Valide",
        ])

    return response
