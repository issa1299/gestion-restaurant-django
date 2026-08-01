from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from apps.menu.models import Categorie, Produit
from apps.stock.models import Stock, MouvementStock

User = get_user_model()


class StockAccessTests(TestCase):
    """Le stock est réservé à ADMIN et VENDEUR."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="adm_t", email="adm_t@test.com", password="Test12345", role="ADMIN",
        )
        self.vendeur = User.objects.create_user(
            username="ven_t", email="ven_t@test.com", password="Test12345", role="VENDEUR",
        )
        self.client_role = User.objects.create_user(
            username="cli_t", email="cli_t@test.com", password="Test12345", role="CLIENT",
        )
        self.serveur = User.objects.create_user(
            username="ser_t", email="ser_t@test.com", password="Test12345", role="SERVEUR",
        )

    def test_stock_accessible_admin_vendeur(self):
        for user in (self.admin, self.vendeur):
            c = Client()
            c.force_login(user)
            self.assertEqual(c.get("/stock/").status_code, 200)

    def test_stock_interdit_client_serveur(self):
        for user in (self.client_role, self.serveur):
            c = Client()
            c.force_login(user)
            self.assertEqual(c.get("/stock/").status_code, 302)

    def test_historique_stock_reserve_admin_vendeur(self):
        for user in (self.admin, self.vendeur):
            c = Client()
            c.force_login(user)
            self.assertEqual(c.get("/stock/historique/").status_code, 200)

    def test_historique_stock_interdit_client(self):
        c = Client()
        c.force_login(self.client_role)
        self.assertEqual(c.get("/stock/historique/").status_code, 302)


class MouvementStockTests(TestCase):
    """Un mouvement ENTREE augmente le stock et crée un MouvementStock."""

    def setUp(self):
        self.vendeur = User.objects.create_user(
            username="ven_t", email="ven_t@test.com", password="Test12345", role="VENDEUR",
        )
        self.categorie = Categorie.objects.create(nom="Aliments")
        self.produit = Produit.objects.create(
            categorie=self.categorie, nom="Riz", prix=1000,
        )
        self.stock = Stock.objects.create(produit=self.produit, quantite=5)

    def test_entree_augmente_stock(self):
        c = Client()
        c.force_login(self.vendeur)
        resp = c.post(
            "/stock/%d/mouvement/" % self.stock.id,
            {"type_mouvement": "ENTREE", "quantite": 7},
        )
        self.assertEqual(resp.status_code, 302)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantite, 12)
        self.assertTrue(
            MouvementStock.objects.filter(
                produit=self.produit, type_mouvement="ENTREE", quantite=7,
            ).exists()
        )

    def test_sortie_sup_stock_refusee(self):
        c = Client()
        c.force_login(self.vendeur)
        resp = c.post(
            "/stock/%d/mouvement/" % self.stock.id,
            {"type_mouvement": "SORTIE", "quantite": 50},
        )
        self.assertEqual(resp.status_code, 302)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantite, 5)

    def test_quantite_zero_refusee(self):
        c = Client()
        c.force_login(self.vendeur)
        resp = c.post(
            "/stock/%d/mouvement/" % self.stock.id,
            {"type_mouvement": "ENTREE", "quantite": 0},
        )
        self.assertEqual(resp.status_code, 302)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantite, 5)

    def test_mouvement_interdit_client(self):
        c = Client()
        client_user = User.objects.create_user(
            username="cli2_t", email="cli2_t@test.com", password="Test12345", role="CLIENT",
        )
        c.force_login(client_user)
        resp = c.post(
            "/stock/%d/mouvement/" % self.stock.id,
            {"type_mouvement": "ENTREE", "quantite": 1},
        )
        self.assertEqual(resp.status_code, 302)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantite, 5)


class StockDetailModifSupprTests(TestCase):
    """Détail, modification et suppression d'une ligne de stock."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="adm_s", email="adm_s@test.com", password="Test12345", role="ADMIN",
        )
        self.vendeur = User.objects.create_user(
            username="ven_s", email="ven_s@test.com", password="Test12345", role="VENDEUR",
        )
        self.categorie = Categorie.objects.create(nom="Aliments")
        self.produit = Produit.objects.create(
            categorie=self.categorie, nom="Riz", prix=1000,
        )
        self.stock = Stock.objects.create(produit=self.produit, quantite=5, seuil_alerte=3)

    def test_detail_stock(self):
        c = Client()
        c.force_login(self.admin)
        resp = c.get("/stock/%d/" % self.stock.id)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Riz")

    def test_modifier_seuil_alerte(self):
        c = Client()
        c.force_login(self.vendeur)
        resp = c.post("/stock/%d/modifier/" % self.stock.id, {"seuil_alerte": 8})
        self.assertEqual(resp.status_code, 302)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.seuil_alerte, 8)

    def test_modifier_interdit_admin(self):
        c = Client()
        c.force_login(self.admin)
        resp = c.post("/stock/%d/modifier/" % self.stock.id, {"seuil_alerte": 8})
        self.assertEqual(resp.status_code, 302)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.seuil_alerte, 3)

    def test_supprimer_ligne_stock(self):
        c = Client()
        c.force_login(self.vendeur)
        resp = c.post("/stock/%d/supprimer/" % self.stock.id)
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Stock.objects.filter(id=self.stock.id).exists())

    def test_filtre_recherche(self):
        c = Client()
        c.force_login(self.admin)
        resp = c.get("/stock/?q=Riz")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Riz")

    def test_filtre_statut_rupture(self):
        c = Client()
        c.force_login(self.admin)
        resp = c.get("/stock/?statut=RUPTURE")
        self.assertEqual(resp.status_code, 200)
