import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


# Groupes accessibles sans authentification (public, ex. le menu)
GROUPES_PUBLICS = {"menu"}


# Rôles autorisés à écouter chaque groupe temps réel.
# Important : les groupes sensibles (clients, dashboard, livraison, ...)
# exposent des données personnelles → restreints au bon rôle.
GROUPES_PAR_ROLE = {
    "dashboard": {"ADMIN", "CAISSIER", "SERVEUR", "CUISINIER"},
    "commandes": {"ADMIN", "SERVEUR", "CUISINIER"},
    "cuisine": {"CUISINIER", "ADMIN"},
    "livraison": {"LIVREUR", "ADMIN"},
    "clients": {"ADMIN", "CAISSIER"},
}


def _groupe_autorise(user, groupe):
    if groupe in GROUPES_PUBLICS:
        return True
    if user is None or not user.is_authenticated:
        return False
    return user.role in GROUPES_PAR_ROLE.get(groupe, set())


@database_sync_to_async
def _restaurant_id_depuis_scope(scope):
    """Détermine le restaurant à partir de l'utilisateur connecté, ou du sous-domaine."""
    user = scope.get("user")
    if user is not None and user.is_authenticated and user.restaurant_id:
        return user.restaurant_id

    from apps.tenants.models import Restaurant

    host = ""
    for key, value in scope.get("headers", []):
        if key == b"host":
            host = value.decode("latin-1").split(":")[0]
            break
    labels = host.split(".")
    if len(labels) >= 2 and labels[0] not in ("www", "localhost", "127", "0", "192"):
        resto = Restaurant.objects.filter(slug=labels[0], actif=True).first()
        if resto is not None:
            return resto.id

    resto = Restaurant.objects.filter(actif=True).order_by("pk").first()
    return resto.id if resto else None


def groupe_reel(groupe, restaurant_id):
    """Nom de groupe Channels scopé par restaurant."""
    return f"{groupe}_{restaurant_id or 'global'}"


class CommandeConsumer(AsyncWebsocketConsumer):
    """Consumer pour les notifications de commandes en temps réel"""

    async def connect(self):
        self.groupe = self.scope["url_route"]["kwargs"]["groupe"]

        if not _groupe_autorise(self.scope["user"], self.groupe):
            await self.close()
            return

        self.restaurant_id = await _restaurant_id_depuis_scope(self.scope)
        self.groupe_reel = groupe_reel(self.groupe, self.restaurant_id)

        await self.channel_layer.group_add(self.groupe_reel, self.channel_name)
        await self.accept()
        print(f"Client connecte au groupe: {self.groupe_reel}")

    async def disconnect(self, close_code):
        if hasattr(self, "groupe_reel"):
            await self.channel_layer.group_discard(self.groupe_reel, self.channel_name)
            print(f"Client deconnecte du groupe: {self.groupe_reel}")

    async def notification(self, event):
        """Reçoit une notification et la transmet au client"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'evenement': event['evenement'],
            'data': event['data'],
        }))
