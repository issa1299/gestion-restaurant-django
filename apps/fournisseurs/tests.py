from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from apps.menu.models import Categorie, Produit
from apps.stock.models import Stock, MouvementStock
from apps.fournisseurs.models import Fournisseur, Approvisionnement

User = get_user_model()


class FournisseurAccessTests(TestCase):
    """La gestion des fournisseurs est réservée à ADMIN et GÉRANT."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="adm_f", email="adm_f@test.com", password="Test12345", role="ADMIN",
        )
        self.gerant = User.objects.create_user(
            username="ger_f", email="ger_f@test.com", password="Test12345", role="GÉRANT",
        )
        self.caissier = User.objects.create_user(
            username="cai_f", email="cai_f@test.com", password="Test12345", role="CAISSIER",
        )
        self.client_role = User.objects.create_user(
            username="cli_f", email="cli_f@test.com", password="Test12345", role="CLIENT",
        )

    def test_liste_accessible_admin_gerant(self):
        for user in (self.admin, self.gerant):
            c = Client()
            c.force_login(user)
            self.assertEqual(c.get("/fournisseurs/").status_code, 200)

    def test_liste_interdite_caissier_client(self):
        for user in (self.caissier, self.client_role):
            c = Client()
            c.force_login(user)
            self.assertEqual(c.get("/fournisseurs/").status_code, 302)


class FournisseurCRUDTests(TestCase):
    """CRUD complet des fournisseurs."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="adm_f", email="adm_f@test.com", password="Test12345", role="ADMIN",
        )
        self.gerant = User.objects.create_user(
            username="ger_f", email="ger_f@test.com", password="Test12345", role="GÉRANT",
        )
        self.categorie = Categorie.objects.create(nom="Boissons")
        self.produit = Produit.objects.create(
            categorie=self.categorie, nom="Jus", prix=500,
        )

    def test_ajout_fournisseur(self):
        c = Client()
        c.force_login(self.gerant)
        resp = c.post("/fournisseurs/ajouter/", {
            "nom": "Socima",
            "telephone": "223 000000",
            "email": "contact@socima.com",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Fournisseur.objects.filter(nom="Socima").exists())

    def test_ajout_doublon_refuse(self):
        Fournisseur.objects.create(nom="Socima")
        c = Client()
        c.force_login(self.gerant)
        resp = c.post("/fournisseurs/ajouter/", {"nom": "socima"})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Fournisseur.objects.filter(nom__iexact="socima").count(), 1)

    def test_modification_fournisseur(self):
        fournisseur = Fournisseur.objects.create(nom="Socima", telephone="223")
        c = Client()
        c.force_login(self.gerant)
        resp = c.post(f"/fournisseurs/modifier/{fournisseur.id}/", {
            "nom": "Socima SA",
            "telephone": "223 111111",
        })
        self.assertEqual(resp.status_code, 302)
        fournisseur.refresh_from_db()
        self.assertEqual(fournisseur.nom, "Socima SA")
        self.assertEqual(fournisseur.telephone, "223 111111")

    def test_modification_interdite_admin(self):
        fournisseur = Fournisseur.objects.create(nom="Socima", telephone="223")
        c = Client()
        c.force_login(self.admin)
        resp = c.post(f"/fournisseurs/modifier/{fournisseur.id}/", {
            "nom": "Socima SA",
            "telephone": "223 111111",
        })
        self.assertEqual(resp.status_code, 302)
        fournisseur.refresh_from_db()
        self.assertEqual(fournisseur.nom, "Socima")

    def test_suppression_fournisseur(self):
        fournisseur = Fournisseur.objects.create(nom="Socima")
        c = Client()
        c.force_login(self.gerant)
        resp = c.post(f"/fournisseurs/supprimer/{fournisseur.id}/")
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Fournisseur.objects.filter(id=fournisseur.id).exists())

    def test_detail_fournisseur(self):
        fournisseur = Fournisseur.objects.create(nom="Socima")
        c = Client()
        c.force_login(self.admin)
        resp = c.get(f"/fournisseurs/{fournisseur.id}/")
        self.assertEqual(resp.status_code, 200)


class ApprovisionnementTests(TestCase):
    """Un approvisionnement met à jour le stock et crée un mouvement."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="adm_f", email="adm_f@test.com", password="Test12345", role="ADMIN",
        )
        self.gerant = User.objects.create_user(
            username="ger_f", email="ger_f@test.com", password="Test12345", role="GÉRANT",
        )
        self.categorie = Categorie.objects.create(nom="Boissons")
        self.produit = Produit.objects.create(
            categorie=self.categorie, nom="Jus", prix=500,
        )
        self.stock = Stock.objects.create(produit=self.produit, quantite=5)
        self.fournisseur = Fournisseur.objects.create(nom="Socima")

    def test_approvisionnement_augmente_stock(self):
        c = Client()
        c.force_login(self.gerant)
        resp = c.post("/fournisseurs/approvisionnements/ajouter/", {
            "fournisseur": self.fournisseur.id,
            "produit": self.produit.id,
            "quantite": 10,
            "prix_unitaire": 300,
        })
        self.assertEqual(resp.status_code, 302)

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantite, 15)

        self.assertTrue(Approvisionnement.objects.filter(
            fournisseur=self.fournisseur, produit=self.produit, quantite=10,
        ).exists())

        self.assertTrue(MouvementStock.objects.filter(
            produit=self.produit, type_mouvement="ENTREE", quantite=10,
        ).exists())

    def test_approvisionnement_interdit_admin(self):
        c = Client()
        c.force_login(self.admin)
        resp = c.post("/fournisseurs/approvisionnements/ajouter/", {
            "fournisseur": self.fournisseur.id,
            "produit": self.produit.id,
            "quantite": 10,
        })
        self.assertEqual(resp.status_code, 302)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantite, 5)

    def test_approvisionnement_creer_stock_si_absent(self):
        nouveau = Produit.objects.create(
            categorie=self.categorie, nom="Café", prix=300,
        )
        c = Client()
        c.force_login(self.gerant)
        resp = c.post("/fournisseurs/approvisionnements/ajouter/", {
            "fournisseur": self.fournisseur.id,
            "produit": nouveau.id,
            "quantite": 4,
        })
        self.assertEqual(resp.status_code, 302)
        stock = Stock.objects.get(produit=nouveau)
        self.assertEqual(stock.quantite, 4)

    def test_approvisionnement_quantite_invalide(self):
        c = Client()
        c.force_login(self.gerant)
        resp = c.post("/fournisseurs/approvisionnements/ajouter/", {
            "fournisseur": self.fournisseur.id,
            "produit": self.produit.id,
            "quantite": 0,
        })
        self.assertEqual(resp.status_code, 302)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantite, 5)

    def test_liste_approvisionnements(self):
        c = Client()
        c.force_login(self.admin)
        resp = c.get("/fournisseurs/approvisionnements/")
        self.assertEqual(resp.status_code, 200)
