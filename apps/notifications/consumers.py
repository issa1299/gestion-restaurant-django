import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class CommandeConsumer(AsyncWebsocketConsumer):
    """Consumer pour les notifications de commandes en temps réel"""

    async def connect(self):
        self.groupe = self.scope["url_route"]["kwargs"]["groupe"]
        await self.channel_layer.group_add(self.groupe, self.channel_name)
        await self.accept()
        print(f"✓ Client connecté au groupe: {self.groupe}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.groupe, self.channel_name)
        print(f"✗ Client déconnecté du groupe: {self.groupe}")

    async def notification(self, event):
        """Reçoit une notification et la transmet au client"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'evenement': event['evenement'],
            'data': event['data'],
        }))