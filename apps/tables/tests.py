from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from apps.tables.models import Table
from apps.parametres.models import ParametreRestaurant

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


class QRTableTests(TestCase):
    """Le QR code de la table est public et pointe vers le menu."""

    def setUp(self):
        self.table = Table.objects.create(numero=3, capacite=4)

    def test_qr_public_et_png(self):
        resp = Client().get("/tables/qr/%d/" % self.table.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get("Content-Type"), "image/png")
        self.assertEqual(resp.content[:8], b"\x89PNG\r\n\x1a\n")
        self.assertIn('table_3_qr.png', resp.get("Content-Disposition", ""))

    def test_qr_table_inexistante_404(self):
        resp = Client().get("/tables/qr/9999/")
        self.assertEqual(resp.status_code, 404)

    def test_url_menu_table_avec_url_site(self):
        from apps.tables.views import url_menu_table
        url = url_menu_table(3, "http://192.168.1.156:8000/")
        self.assertEqual(url, "http://192.168.1.156:8000/menu/?table=3")

    def test_url_menu_table_sans_base(self):
        from apps.tables.views import url_menu_table
        url = url_menu_table(3, "")
        self.assertEqual(url, "/menu/?table=3")

    def test_qr_utilise_url_site_parametre(self):
        ParametreRestaurant.load().url_site = "http://192.168.1.156:8000"
        ParametreRestaurant.load().save()
        resp = Client().get("/tables/qr/%d/" % self.table.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get("Content-Type"), "image/png")

    def test_qr_print_reserve_personnel(self):
        """La page imprimable des QR nécessite la connexion."""
        self.assertEqual(Client().get("/tables/qr-print/").status_code, 302)

    def test_qr_print_contient_toutes_tables(self):
        """La page imprimable affiche un QR par table."""
        from apps.tables.views import url_menu_table
        from apps.parametres.models import ParametreRestaurant
        Table.objects.create(numero=4, capacite=2)
        ParametreRestaurant.load().url_site = ""
        ParametreRestaurant.load().save()
        admin = User.objects.create_user(
            username="adm_qr", email="adm_qr@test.com", password="Test12345", role="ADMIN",
        )
        c = Client()
        c.force_login(admin)
        resp = c.get("/tables/qr-print/")
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode("utf-8", errors="ignore")
        self.assertIn("Table 3", html)
        self.assertIn("Table 4", html)
        self.assertIn('download="qr_table_3.png"', html)
        self.assertIn('download="qr_table_4.png"', html)
        self.assertEqual(html.count('<div class="card">'), 2)


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
        resp = c.post("/tables/%d/toggle/" % self.table.id)
        self.assertEqual(resp.status_code, 302)
        self.table.refresh_from_db()
        self.assertFalse(self.table.disponible)

    def test_toggle_interdit_client(self):
        c = Client()
        c.force_login(self.client_role)
        resp = c.post("/tables/%d/toggle/" % self.table.id)
        self.assertEqual(resp.status_code, 302)
        self.table.refresh_from_db()
        self.assertTrue(self.table.disponible)

    def test_toggle_refuse_sur_get(self):
        c = Client()
        c.force_login(self.serveur)
        resp = c.get("/tables/%d/toggle/" % self.table.id)
        self.assertEqual(resp.status_code, 405)
        self.table.refresh_from_db()
        self.assertTrue(self.table.disponible)
