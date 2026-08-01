from django.test import TestCase, Client as DjangoClient
from django.contrib.auth import get_user_model

from apps.clients.models import Client

User = get_user_model()


class ClientAccessTests(TestCase):
    """La gestion des clients est réservée à ADMIN et CAISSIER."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="adm_t", email="adm_t@test.com", password="Test12345", role="ADMIN",
        )
        self.caissier = User.objects.create_user(
            username="cai_t", email="cai_t@test.com", password="Test12345", role="CAISSIER",
        )
        self.client_role = User.objects.create_user(
            username="cli_t", email="cli_t@test.com", password="Test12345", role="CLIENT",
        )
        self.serveur = User.objects.create_user(
            username="ser_t", email="ser_t@test.com", password="Test12345", role="SERVEUR",
        )
        self.client = Client.objects.create(
            nom="Jean Dupont", telephone="01020304",
        )

    def test_liste_accessible_admin_caissier(self):
        for user in (self.admin, self.caissier):
            c = DjangoClient()
            c.force_login(user)
            self.assertEqual(c.get("/clients/").status_code, 200)

    def test_liste_interdite_client_serveur(self):
        for user in (self.client_role, self.serveur):
            c = DjangoClient()
            c.force_login(user)
            self.assertEqual(c.get("/clients/").status_code, 302)

    def test_detail_interdit_client(self):
        c = DjangoClient()
        c.force_login(self.client_role)
        resp = c.get("/clients/%d/" % self.client.id)
        self.assertEqual(resp.status_code, 302)

    def test_detail_accessible_admin(self):
        c = DjangoClient()
        c.force_login(self.admin)
        resp = c.get("/clients/%d/" % self.client.id)
        self.assertEqual(resp.status_code, 200)

    def test_suppression_interdite_client(self):
        c = DjangoClient()
        c.force_login(self.client_role)
        resp = c.post("/clients/supprimer/%d/" % self.client.id)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Client.objects.filter(id=self.client.id).exists())

    def test_ajout_client_par_caissier(self):
        c = DjangoClient()
        c.force_login(self.caissier)
        resp = c.post("/clients/ajouter/", {
            "nom": "Marie Curie",
            "telephone": "06070809",
        })
        self.assertIn(resp.status_code, (200, 302))
        if resp.status_code == 302:
            self.assertTrue(Client.objects.filter(nom="Marie Curie").exists())
