from apps.stock.models import Stock
from apps.commandes.models import Commande


def navbar_notifications(request):
    """
    Context processor qui fournit les données réelles pour la navbar :
    - Alertes stock faible / rupture
    - Dernières commandes en attente / en préparation
    - Nombre de notifications non lues
    """
    context = {}

    if request.user.is_authenticated:
        # === Notifications stock ===
        stocks = Stock.objects.select_related("produit__categorie").all()
        stock_rupture = [s for s in stocks if s.quantite == 0]
        stock_faible = [s for s in stocks if s.stock_faible and s.quantite > 0]

        # === Dernières commandes récentes ===
        commandes_recentes = Commande.objects.filter(
            statut__in=["EN_ATTENTE", "EN_PREPARATION", "PRETE"]
        ).select_related("client", "table").order_by("-created_at")[:5]

        # === Stats pour les badges ===
        nb_alertes_stock = len(stock_rupture) + len(stock_faible)
        nb_commandes_en_attente = Commande.objects.filter(
            statut__in=["EN_ATTENTE", "EN_PREPARATION"]
        ).count()

        # Nombre total de notifications (stock faible/rupture + commandes récentes)
        nb_notifications = nb_alertes_stock + min(nb_commandes_en_attente, 5)

        # === Messages (représentés par les commandes prêtes qui attendent) ===
        commandes_pretes = Commande.objects.filter(
            statut="PRETE"
        ).select_related("client", "table").order_by("-created_at")[:3]
        nb_messages = commandes_pretes.count()

        # Assembler les alertes stock pour les notifications
        alertes_stock = []
        for s in stock_rupture[:3]:
            alertes_stock.append({
                "type": "rupture",
                "produit": s.produit.nom,
                "quantite": s.quantite,
                "icone": "triangle-exclamation",
                "couleur_icone": "red",
                "message": f"{s.produit.nom} en rupture",
            })
        for s in stock_faible[:3]:
            alertes_stock.append({
                "type": "faible",
                "produit": s.produit.nom,
                "quantite": s.quantite,
                "icone": "box-open",
                "couleur_icone": "yellow",
                "message": f"{s.produit.nom} stock faible ({s.quantite})",
            })

        # Assembler les notifications de commandes
        notifications_commandes = []
        for cmd in commandes_recentes:
            client_nom = cmd.client.nom if cmd.client else "Client"
            if cmd.type == "LIVRAISON":
                table_info = "Livraison"
            elif cmd.table:
                table_info = f"Table {cmd.table.numero}"
            else:
                table_info = "Sur place"
            notifications_commandes.append({
                "id": cmd.id,
                "client": client_nom,
                "table": table_info,
                "statut": cmd.statut,
                "icone": "utensils",
                "couleur_icone": "blue",
                "message": f"Commande N° {cmd.id} - {table_info}",
            })

        # Combiner : alertes stock d'abord, puis commandes récentes
        notifications_list = alertes_stock + notifications_commandes

        context.update({
            "notifications_list": notifications_list[:8],  # max 8 items
            "nb_notifications": nb_notifications,
            "commandes_pretes_list": commandes_pretes,
            "nb_messages": nb_messages,
            "stock_rupture_count": len(stock_rupture),
            "stock_faible_count": len(stock_faible),
        })
    else:
        context.update({
            "notifications_list": [],
            "nb_notifications": 0,
            "commandes_pretes_list": [],
            "nb_messages": 0,
            "stock_rupture_count": 0,
            "stock_faible_count": 0,
        })

    return context
