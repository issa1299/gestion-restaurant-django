from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from apps.tables.models import Table

User = get_user_model()


class TableAccessTests(TestCase):
    """Les tables sont réservées à ADMIN et SERVEUR."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="adm_t", email="adm_t@test.com", password="Test12345", role="ADMIN",
        )
        self.serveur = User.objects.create_user(
            username="ser_t", email="ser_t@test.com", password="Test12345", role="SERVEUR",
        )
        self.client_role = User.objects.create_user(
            username="cli_t", email="cli_t@test.com", password="Test12345", role="CLIENT",
        )
        self.table = Table.objects.create(numero=1, capacite=4)

    def test_liste_accessible_admin_serveur(self):
        for user in (self.admin, self.serveur):
            c = Client()
            c.force_login(user)
            self.assertEqual(c.get("/tables/").status_code, 200)

    def test_liste_interdite_client(self):
        c = Client()
        c.force_login(self.client_role)
        self.assertEqual(c.get("/tables/").status_code, 302)

    def test_creer_table_interdit_client(self):
        c = Client()
        c.force_login(self.client_role)
        self.assertEqual(c.get("/tables/creer/").status_code, 302)

    def test_supprimer_table_accessible_serveur(self):
        c = Client()
        c.force_login(self.serveur)
        self.assertEqual(c.get("/tables/1/supprimer/").status_code, 200)

    def test_supprimer_table_interdite_admin(self):
        c = Client()
        c.force_login(self.admin)
        self.assertEqual(c.get("/tables/1/supprimer/").status_code, 302)


class TableToggleTests(TestCase):
    """Un serveur peut basculer la disponibilité d'une table."""

    def setUp(self):
        self.serveur = User.objects.create_user(
            username="ser_t", email="ser_t@test.com", password="Test12345", role="SERVEUR",
        )
        self.client_role = User.objects.create_user(
            username="cli_t", email="cli_t@test.com", password="Test12345", role="CLIENT",
        )
        self.table = Table.objects.create(numero=2, capacite=6)

    def test_toggle_par_serveur(self):
        c = Client()
        c.force_login(self.serveur)
        resp = c.get("/tables/%d/toggle/" % self.table.id)
        self.assertEqual(resp.status_code, 302)
        self.table.refresh_from_db()
        self.assertFalse(self.table.disponible)

    def test_toggle_interdit_client(self):
        c = Client()
        c.force_login(self.client_role)
        resp = c.get("/tables/%d/toggle/" % self.table.id)
        self.assertEqual(resp.status_code, 302)
        self.table.refresh_from_db()
        self.assertTrue(self.table.disponible)
