import json

from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from apps.menu.models import Categorie, Produit
from apps.stock.models import Stock, MouvementStock
from apps.ventes.models import Vente, DetailVente

User = get_user_model()


class VenteAccessTests(TestCase):
    """La caisse (POS) et l'historique sont réservés à ADMIN et CAISSIER."""

    def setUp(self):
        self.caissier = User.objects.create_user(
            username="cai_t", email="cai_t@test.com", password="Test12345", role="CAISSIER",
        )
        self.admin = User.objects.create_user(
            username="adm_t", email="adm_t@test.com", password="Test12345", role="ADMIN",
        )
        self.serveur = User.objects.create_user(
            username="ser_t", email="ser_t@test.com", password="Test12345", role="SERVEUR",
        )
        self.client_role = User.objects.create_user(
            username="cli_t", email="cli_t@test.com", password="Test12345", role="CLIENT",
        )

    def test_pos_accessible_caissier(self):
        c = Client()
        c.force_login(self.caissier)
        self.assertEqual(c.get("/ventes/").status_code, 200)

    def test_pos_interdit_admin(self):
        c = Client()
        c.force_login(self.admin)
        self.assertEqual(c.get("/ventes/").status_code, 302)

    def test_pos_interdit_serveur_et_client(self):
        for user in (self.serveur, self.client_role):
            c = Client()
            c.force_login(user)
            self.assertEqual(c.get("/ventes/").status_code, 302)

    def test_pos_interdit_anonyme(self):
        c = Client()
        resp = c.get("/ventes/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp.get("Location", ""))

    def test_historique_reserve_admin_caissier(self):
        c = Client()
        c.force_login(self.caissier)
        self.assertEqual(c.get("/ventes/historique/").status_code, 200)

    def test_historique_interdit_client(self):
        c = Client()
        c.force_login(self.client_role)
        self.assertEqual(c.get("/ventes/historique/").status_code, 302)


class EnregistrerVenteTests(TestCase):
    """La création d'une vente déduit le stock et calcule le total."""

    def setUp(self):
        self.caissier = User.objects.create_user(
            username="cai_t", email="cai_t@test.com", password="Test12345", role="CAISSIER",
        )
        self.client_role = User.objects.create_user(
            username="cli_t", email="cli_t@test.com", password="Test12345", role="CLIENT",
        )
        self.categorie = Categorie.objects.create(nom="Boissons")
        self.produit = Produit.objects.create(
            categorie=self.categorie, nom="Jus", prix=500,
        )
        self.stock = Stock.objects.create(produit=self.produit, quantite=10)

    def _post_vente(self, user, panier=None):
        c = Client()
        c.force_login(user)
        data = json.dumps({
            "panier": [{"id": self.produit.id, "qte": 2}] if panier is None else panier,
            "mode_paiement": "ESPECES",
        })
        return c.post(
            "/ventes/enregistrer/", data=data, content_type="application/json",
        )

    def test_vente_ok_total_et_stock(self):
        resp = self._post_vente(self.caissier)
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.content)
        self.assertTrue(body["success"])

        vente = Vente.objects.get(id=body["vente_id"])
        self.assertEqual(vente.total, 1000)
        self.assertEqual(vente.mode_paiement, "ESPECES")

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantite, 8)

        self.assertEqual(DetailVente.objects.filter(vente=vente).count(), 1)
        self.assertTrue(
            MouvementStock.objects.filter(
                produit=self.produit, type_mouvement="SORTIE", quantite=2,
            ).exists()
        )

    def test_vente_stock_insuffisant_refusee(self):
        resp = self._post_vente(
            self.caissier, [{"id": self.produit.id, "qte": 99}],
        )
        self.assertEqual(resp.status_code, 400)
        body = json.loads(resp.content)
        self.assertFalse(body["success"])
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantite, 10)

    def test_vente_panier_vide_refuse(self):
        resp = self._post_vente(self.caissier, [])
        self.assertEqual(resp.status_code, 400)

    def test_vente_interdite_pour_client(self):
        resp = self._post_vente(self.client_role)
        self.assertEqual(resp.status_code, 302)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantite, 10)

    def test_vente_interdite_pour_anonyme(self):
        c = Client()
        resp = c.post(
            "/ventes/enregistrer/",
            data=json.dumps({"panier": [], "mode_paiement": "ESPECES"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 302)


class AnnulationVenteTests(TestCase):
    """L'annulation d'une vente remet les produits en stock."""

    def setUp(self):
        self.caissier = User.objects.create_user(
            username="cai_a", email="cai_a@test.com", password="Test12345", role="CAISSIER",
        )
        self.categorie = Categorie.objects.create(nom="Boissons")
        self.produit = Produit.objects.create(
            categorie=self.categorie, nom="Jus", prix=500,
        )
        self.stock = Stock.objects.create(produit=self.produit, quantite=10)

        self.vente = Vente.objects.create(
            caissier=self.caissier, total=1000, mode_paiement="ESPECES",
        )
        DetailVente.objects.create(
            vente=self.vente, produit=self.produit, quantite=2, prix=500, sous_total=1000,
        )
        self.stock.quantite = 8
        self.stock.save()

    def test_page_annulation_accessible(self):
        c = Client()
        c.force_login(self.caissier)
        self.assertEqual(c.get(f"/ventes/{self.vente.id}/annuler/").status_code, 200)

    def test_annulation_remet_en_stock(self):
        c = Client()
        c.force_login(self.caissier)
        resp = c.post(f"/ventes/{self.vente.id}/annuler/")
        self.assertEqual(resp.status_code, 302)

        self.vente.refresh_from_db()
        self.assertTrue(self.vente.annulee)
        self.assertEqual(self.vente.annule_par, self.caissier)

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantite, 10)

        self.assertTrue(
            MouvementStock.objects.filter(
                produit=self.produit, type_mouvement="ENTREE", quantite=2,
            ).exists()
        )

    def test_annulation_double_refusee(self):
        c = Client()
        c.force_login(self.caissier)
        c.post(f"/ventes/{self.vente.id}/annuler/")

        # Deuxième annulation doit être bloquée (pas de double remise en stock)
        resp = c.get(f"/ventes/{self.vente.id}/annuler/")
        self.assertEqual(resp.status_code, 302)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantite, 10)

    def test_detail_vente_accessible(self):
        c = Client()
        c.force_login(self.caissier)
        resp = c.get(f"/ventes/{self.vente.id}/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Jus")

    def test_historique_filtre_annulees(self):
        c = Client()
        c.force_login(self.caissier)
        resp = c.get("/ventes/historique/?statut=annulees")
        self.assertEqual(resp.status_code, 200)
