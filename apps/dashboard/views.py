from django.shortcuts import render
from apps.commandes.models import Commande
from apps.accounts.decorators import role_required
from apps.ventes.models import Vente
from apps.clients.models import Client
from apps.tables.models import Table
from apps.stock.models import Stock
from apps.restaurant.models import Reservation, ContactMessage
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncDate


@role_required(["ADMIN", "SERVEUR", "CUISINIER", "CAISSIER"])
def index(request):
    """Vue du dashboard avec données réelles"""
    
    # Date d'aujourd'hui
    aujourd_hui = timezone.now().date()
    il_y_a_7_jours = aujourd_hui - timedelta(days=6)
    
    # Commandes aujourd'hui
    commandes_ajourdhui = Commande.objects.filter(
        created_at__date=aujourd_hui
    ).count()
    
    # Chiffre d'affaires aujourd'hui
    ca_aujourdhui = Vente.objects.filter(
        created_at__date=aujourd_hui
    ).aggregate(total=Sum('total'))['total'] or 0
    
    # Total clients
    total_clients = Client.objects.count()
    
    # Tables occupées
    tables_occupees = Table.objects.filter(disponible=False).count()
    
    # Dernières commandes
    dernieres_commandes = Commande.objects.select_related(
        'client', 'table'
    ).prefetch_related('lignes')[:5]
    
    # Stock faible / rupture
    stocks = Stock.objects.select_related('produit').all()
    stock_faible_count = sum(1 for s in stocks if s.stock_faible and s.quantite > 0)
    stock_rupture_count = sum(1 for s in stocks if s.quantite == 0)
    
    # Ventes des 7 derniers jours
    ventes_7jours = Vente.objects.filter(
        created_at__date__gte=il_y_a_7_jours,
        created_at__date__lte=aujourd_hui
    )
    
    ventes_par_jour = ventes_7jours.annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        ca_jour=Sum('total'),
        nb=Count('id')
    ).order_by('date')
    
    dates_chart = [v['date'].strftime('%d/%m') for v in ventes_par_jour]
    ca_chart = [float(v['ca_jour']) for v in ventes_par_jour]
    
    # Réservations à confirmer et messages non lus
    reservations_recentes = Reservation.objects.filter(
        statut=Reservation.EN_ATTENTE
    )[:5]
    reservations_count = Reservation.objects.filter(
        statut=Reservation.EN_ATTENTE
    ).count()
    messages_non_lus = ContactMessage.objects.filter(lu=False)[:5]
    messages_non_lus_count = ContactMessage.objects.filter(lu=False).count()
    
    return render(
        request,
        "dashboard/index.html",
        {
            "commandes": commandes_ajourdhui,
            "groupe": "dashboard",
            "ca_total": ca_aujourdhui,
            "commandes_ajourdhui": commandes_ajourdhui,
            "total_clients": total_clients,
            "tables_occupees": tables_occupees,
            "dernieres_commandes": dernieres_commandes,
            "stock_faible_count": stock_faible_count,
            "stock_rupture_count": stock_rupture_count,
            "dates_chart": dates_chart,
            "ca_chart": ca_chart,
            "reservations_recentes": reservations_recentes,
            "reservations_count": reservations_count,
            "messages_non_lus": messages_non_lus,
            "messages_non_lus_count": messages_non_lus_count,
        }
    )
