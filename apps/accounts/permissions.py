from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


def setup_permissions():

    roles_permissions = {

        "Administrateur": [
            "add",
            "change",
            "delete",
            "view",
        ],

        "Caissier": [
            "view",
            "add",
        ],

        "Serveur": [
            "view",
            "add",
        ],

        "Cuisinier": [
            "view",
            "change",
        ],

        "Livreur": [
            "view",
            "change",
        ],

        "Gérant": [
            "view",
            "add",
        ],

        "Client": [
            "view",
        ],
    }