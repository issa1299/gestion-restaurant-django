from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission


@receiver(post_migrate)
def create_roles(sender, **kwargs):

    roles = [
        "Administrateur",
        "Caissier",
        "Serveur",
        "Cuisinier",
        "Livreur",
        "Vendeur",
        "Client",
    ]

    for role in roles:
        Group.objects.get_or_create(name=role)