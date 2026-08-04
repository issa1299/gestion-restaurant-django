import asyncio
from django.test import TestCase
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async

from config.asgi import application
from django.contrib.auth import get_user_model


User = get_user_model()


@database_sync_to_async
def creer_user():
    return User.objects.create_user(
        username="ws_test_admin", email="ws@test.com",
        password="Test12345", role="ADMIN",
    )


class WebSocketTests(TestCase):

    async def test_groupe_protege_refuse_anonyme(self):
        communicator = WebsocketCommunicator(application, "/ws/commandes/dashboard/")
        connecte, _ = await communicator.connect()
        self.assertFalse(connecte)
        await communicator.disconnect()

    async def test_groupe_public_accepte_anonyme(self):
        communicator = WebsocketCommunicator(application, "/ws/commandes/menu/")
        connecte, _ = await communicator.connect()
        self.assertTrue(connecte)
        await communicator.disconnect()

    async def test_groupe_protege_accepte_bon_role(self):
        user = await creer_user()
        communicator = WebsocketCommunicator(application, "/ws/commandes/dashboard/")
        communicator.scope["user"] = user
        connecte, _ = await communicator.connect()
        self.assertTrue(connecte)
        await communicator.disconnect()

    async def test_reception_broadcast_livraison(self):
        user = await creer_user()
        communicator = WebsocketCommunicator(application, "/ws/commandes/livraison/")
        communicator.scope["user"] = user
        connecte, _ = await communicator.connect()
        self.assertTrue(connecte)

        from channels.layers import get_channel_layer
        from apps.notifications.consumers import groupe_reel
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            groupe_reel("livraison", None),
            {
                "type": "notification",
                "evenement": "statut_commande",
                "data": {"id": 1, "a_livrer": True, "nouveau_statut": "Prête"},
            },
        )
        reponse = await asyncio.wait_for(communicator.receive_json_from(), timeout=2)
        self.assertEqual(reponse["evenement"], "statut_commande")
        self.assertTrue(reponse["data"]["a_livrer"])
        await communicator.disconnect()

    async def test_isolation_between_restaurants(self):
        from apps.tenants.models import Restaurant
        from apps.notifications.consumers import groupe_reel
        from channels.layers import get_channel_layer

        r1 = await database_sync_to_async(Restaurant.objects.create)(
            nom="Resto WS 1", slug="ws-resto-1"
        )
        r2 = await database_sync_to_async(Restaurant.objects.create)(
            nom="Resto WS 2", slug="ws-resto-2"
        )
        user = await creer_user()
        user.restaurant = r1
        await database_sync_to_async(user.save)()

        communicator = WebsocketCommunicator(application, "/ws/commandes/dashboard/")
        communicator.scope["user"] = user
        connecte, _ = await communicator.connect()
        self.assertTrue(connecte)

        channel_layer = get_channel_layer()
        # Message dans le groupe du resto 2 -> ne doit PAS arriver au resto 1
        await channel_layer.group_send(
            groupe_reel("dashboard", r2.id),
            {"type": "notification", "evenement": "secret", "data": {"x": 1}},
        )
        # Message dans le groupe du resto 1 -> doit arriver
        await channel_layer.group_send(
            groupe_reel("dashboard", r1.id),
            {"type": "notification", "evenement": "ok", "data": {"x": 2}},
        )
        reponse = await asyncio.wait_for(communicator.receive_json_from(), timeout=2)
        self.assertEqual(reponse["evenement"], "ok")
        self.assertNotEqual(reponse["evenement"], "secret")
        await communicator.disconnect()
