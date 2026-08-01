from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from apps.menu.models import Categorie, Produit
from apps.ventes.models import Vente, DetailVente
from apps.stock.models import Stock

User = get_user_model()


class RapportsTests(TestCase):
    """Rapports et export CSV réservés à l'admin."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="adm_r", email="adm_r@test.com", password="Test12345", role="ADMIN",
        )
        self.caissier = User.objects.create_user(
            username="cai_r", email="cai_r@test.com", password="Test12345", role="CAISSIER",
        )

        self.categorie = Categorie.objects.create(nom="Boissons")
        self.produit = Produit.objects.create(
            categorie=self.categorie, nom="Jus", prix=500,
        )
        Stock.objects.create(produit=self.produit, quantite=10)

        self.vente = Vente.objects.create(
            caissier=self.caissier, total=1000, mode_paiement="ESPECES",
        )
        DetailVente.objects.create(
            vente=self.vente, produit=self.produit, quantite=2, prix=500, sous_total=1000,
        )

    def test_index_accessible_admin(self):
        c = Client()
        c.force_login(self.admin)
        resp = c.get("/rapports/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "1000")

    def test_index_interdit_caissier(self):
        c = Client()
        c.force_login(self.caissier)
        resp = c.get("/rapports/")
        self.assertEqual(resp.status_code, 403)

    def test_export_csv_admin(self):
        c = Client()
        c.force_login(self.admin)
        resp = c.get("/rapports/export-csv/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get("Content-Type"), "text/csv")
        self.assertIn(".csv", resp.get("Content-Disposition", ""))

    def test_export_csv_interdit_caissier(self):
        c = Client()
        c.force_login(self.caissier)
        resp = c.get("/rapports/export-csv/")
        self.assertEqual(resp.status_code, 403)
