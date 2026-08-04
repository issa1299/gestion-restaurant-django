import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from apps.clients.models import Client
from apps.notifications.consumers import groupe_reel


def envoyer_notification_broadcast(groupe, evenement, data, restaurant_id=None):
    """Envoie une notification en temps réel à TOUS les utilisateurs du groupe.

    Le nom de groupe est scopé par restaurant pour éviter les fuites entre
    établissements dans la même base partagée.
    """
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            groupe_reel(groupe, restaurant_id),
            {
                'type': 'notification',
                'evenement': evenement,
                'data': data,
            }
        )
    except Exception:
        # En mode développement local, on ignore silencieusement
        # si la couche de canal n'est pas encore disponible.
        pass


def notifier_nouveau_client(client):
    """Notifie tous les utilisateurs d'un nouveau client."""
    data = {
        'id': client.id,
        'nom': client.nom,
        'telephone': client.telephone,
        'email': client.email,
        'total_clients': Client.objects.filter(restaurant_id=client.restaurant_id).count(),
    }
    envoyer_notification_broadcast('clients', 'nouveau_client', data, client.restaurant_id)


def notifier_client_modifie(client):
    """Notifie tous les utilisateurs qu'un client a été modifié."""
    data = {
        'id': client.id,
        'nom': client.nom,
        'telephone': client.telephone,
        'email': client.email,
    }
    envoyer_notification_broadcast('clients', 'client_modifie', data, client.restaurant_id)


def notifier_client_supprime(client_id, client_nom, restaurant_id=None):
    """Notifie tous les utilisateurs qu'un client a été supprimé."""
    data = {
        'id': client_id,
        'nom': client_nom,
        'total_clients': Client.objects.filter(restaurant_id=restaurant_id).count(),
    }
    envoyer_notification_broadcast('clients', 'client_supprime', data, restaurant_id)


def notifier_nouvelle_commande(commande):
    """Notifie tous les utilisateurs d'une nouvelle commande."""
    articles = []
    for ligne in commande.lignes.all():
        articles.append({
            'nom': ligne.produit.nom,
            'quantite': ligne.quantite,
        })
    data = {
        'id': commande.id,
        'table': commande.table.numero if commande.table else 'À emporter',
        'articles': articles,
    }
    rid = commande.restaurant_id
    envoyer_notification_broadcast('commandes', 'nouvelle_commande', data, rid)
    envoyer_notification_broadcast('dashboard', 'nouvelle_commande', data, rid)
    envoyer_notification_broadcast('cuisine', 'nouvelle_commande', data, rid)


def notifier_changement_statut_commande(commande_id, ancien_statut, nouveau_statut, restaurant_id=None):
    """Notifie tous les utilisateurs du changement de statut d'une commande."""
    from apps.commandes.models import Commande
    if restaurant_id is None:
        commande = Commande.all_objects.filter(pk=commande_id).first()
        restaurant_id = commande.restaurant_id if commande else None
    data = {
        'id': commande_id,
        'ancien_statut': dict(Commande.STATUTS).get(ancien_statut, ancien_statut),
        'nouveau_statut': dict(Commande.STATUTS).get(nouveau_statut, nouveau_statut),
    }
    envoyer_notification_broadcast('commandes', 'statut_commande', data, restaurant_id)
    envoyer_notification_broadcast('dashboard', 'statut_commande', data, restaurant_id)
    envoyer_notification_broadcast('cuisine', 'statut_commande', data, restaurant_id)
    if nouveau_statut == Commande.PRETE:
        data['a_livrer'] = True
        envoyer_notification_broadcast('livraison', 'statut_commande', data, restaurant_id)
