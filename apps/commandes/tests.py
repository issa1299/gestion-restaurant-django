import json

from django.test import TestCase, Client as DjangoClient
from django.contrib.auth import get_user_model

from apps.menu.models import Categorie, Produit
from apps.commandes.models import Commande
from apps.clients.models import Client

User = get_user_model()


class CommandeAccessTests(TestCase):
    """La liste des commandes est réservée au personnel."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="adm_t", email="adm_t@test.com", password="Test12345", role="ADMIN",
        )
        self.client_role = User.objects.create_user(
            username="cli_t", email="cli_t@test.com", password="Test12345", role="CLIENT",
        )

    def test_liste_accessible_admin(self):
        c = DjangoClient()
        c.force_login(self.admin)
        self.assertEqual(c.get("/commandes/").status_code, 200)

    def test_liste_interdite_client(self):
        c = DjangoClient()
        c.force_login(self.client_role)
        self.assertEqual(c.get("/commandes/").status_code, 302)


class PasserCommandeTests(TestCase):
    """L'API publique de commande crée la commande et le client guest."""

    def setUp(self):
        self.categorie = Categorie.objects.create(nom="Plats")
        self.produit = Produit.objects.create(
            categorie=self.categorie, nom="Poulet", prix=2500,
        )

    def _passer(self, payload):
        c = DjangoClient()
        return c.post(
            "/commandes/client/passer-commande/",
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_commande_guest_ok(self):
        resp = self._passer({
            "panier": [{"id": self.produit.id, "qte": 2}],
            "mode": "SUR_PLACE",
            "guest_nom": "Paul Guest",
            "guest_telephone": "01112233",
        })
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.content)
        self.assertTrue(body["success"])

        commande = Commande.objects.get(id=body["commande_id"])
        self.assertEqual(commande.total, 5000)
        self.assertEqual(commande.type, Commande.SUR_PLACE)
        self.assertTrue(Client.objects.filter(nom="Paul Guest").exists())

    def test_livraison_requiert_adresse(self):
        resp = self._passer({
            "panier": [{"id": self.produit.id, "qte": 1}],
            "mode": "LIVRAISON",
            "guest_nom": "Paul Guest",
            "guest_telephone": "01112233",
            "adresse": "",
        })
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(Commande.objects.exists())

    def test_panier_vide_refuse(self):
        resp = self._passer({
            "panier": [],
            "mode": "SUR_PLACE",
            "guest_nom": "Paul",
            "guest_telephone": "01",
        })
        self.assertEqual(resp.status_code, 400)

    def test_guest_sans_nom_refuse(self):
        resp = self._passer({
            "panier": [{"id": self.produit.id, "qte": 1}],
            "mode": "SUR_PLACE",
            "guest_nom": "",
            "guest_telephone": "01112233",
        })
        self.assertEqual(resp.status_code, 400)

    def test_produit_indisponible_refuse(self):
        self.produit.disponible = False
        self.produit.save()
        resp = self._passer({
            "panier": [{"id": self.produit.id, "qte": 1}],
            "mode": "SUR_PLACE",
            "guest_nom": "Paul",
            "guest_telephone": "01",
        })
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(Commande.objects.exists())
