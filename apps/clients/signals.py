from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Client
from apps.notifications.utils import notifier_nouveau_client, notifier_client_modifie, notifier_client_supprime


@receiver(post_save, sender=Client)
def client_sauvegarde(sender, instance, created, **kwargs):
    """Synchronise les changements client en temps réel"""
    if created:
        notifier_nouveau_client(instance)
    else:
        notifier_client_modifie(instance)


@receiver(post_delete, sender=Client)
def client_supprime(sender, instance, **kwargs):
    """Notifie la suppression d'un client"""
    notifier_client_supprime(instance.id, instance.nom)