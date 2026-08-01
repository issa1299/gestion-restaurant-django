import json

from channels.generic.websocket import AsyncWebsocketConsumer


class CommandeConsumer(AsyncWebsocketConsumer):
    """
    Un seul consumer générique, utilisé par tous les postes.
    Le groupe rejoint dépend du rôle passé dans l'URL :
    ws/commandes/cuisine/, ws/commandes/serveurs/, ws/commandes/livreurs/, ws/commandes/dashboard/
    """

    async def connect(self):
        self.groupe = self.scope["url_route"]["kwargs"]["groupe"]
        await self.channel_layer.group_add(self.groupe, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.groupe, self.channel_name)

    async def notification(self, event):
        """Reçoit un événement envoyé via group_send et le transmet au navigateur."""
        await self.send(text_data=json.dumps({
            "evenement": event["evenement"],
            "data": event["data"],
        }))
