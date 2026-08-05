from django.test import TestCase, Client
from django.urls import reverse

from apps.tenants.models import Restaurant, Plan, ParametrePlateforme, Paiement
from apps.accounts.models import CustomUser
from apps.parametres.models import ParametreRestaurant
from apps.menu.models import Categorie, Produit
from apps.clients.models import Client as ClientModel


class InscriptionTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.donnees = {
            "nom": "Chez Ali",
            "prenom": "Ali",
            "username": "ali_admin",
            "email": "ali@test.com",
            "telephone": "00112233",
            "password": "MotDePasse123",
        }

    def test_page_inscription_accessible(self):
        r = self.client.get(reverse("tenants:inscription"))
        self.assertEqual(r.status_code, 200)

    def test_inscription_cree_restaurant_inactif_et_admin(self):
        r = self.client.post(reverse("tenants:inscription"), self.donnees)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Chez Ali")

        resto = Restaurant.objects.get(slug="chez-ali")
        self.assertFalse(resto.actif)  # en attente d'activation manuelle

        user = CustomUser.objects.get(username="ali_admin")
        self.assertEqual(user.role, "ADMIN")
        self.assertEqual(user.restaurant, resto)

        # Paramètres par défaut créés
        self.assertTrue(ParametreRestaurant.objects.filter(restaurant=resto).exists())

    def test_inscription_slug_unique(self):
        self.client.post(reverse("tenants:inscription"), self.donnees)
        self.donnees["username"] = "ali2"
        self.donnees["email"] = "ali2@test.com"
        r = self.client.post(reverse("tenants:inscription"), self.donnees)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(Restaurant.objects.filter(slug="chez-ali-2").exists())

    def test_inscription_mot_de_passe_court_refuse(self):
        self.donnees["password"] = "court"
        r = self.client.post(reverse("tenants:inscription"), self.donnees)
        self.assertContains(r, "8 caractères")
        self.assertEqual(Restaurant.objects.count(), 0)


class IsolationTests(TestCase):

    def setUp(self):
        self.r1 = Restaurant.objects.create(nom="Resto Un", slug="resto-un")
        self.r2 = Restaurant.objects.create(nom="Resto Deux", slug="resto-deux")

        self.admin1 = CustomUser.objects.create_user(
            username="admin1", email="a1@test.com", password="Pass12345",
            role="ADMIN", restaurant=self.r1,
        )
        self.admin2 = CustomUser.objects.create_user(
            username="admin2", email="a2@test.com", password="Pass12345",
            role="ADMIN", restaurant=self.r2,
        )

        c1 = Categorie.objects.create(restaurant=self.r1, nom="C1")
        c2 = Categorie.objects.create(restaurant=self.r2, nom="C2")
        Produit.objects.create(restaurant=self.r1, categorie=c1, nom="P1", prix=100)
        Produit.objects.create(restaurant=self.r2, categorie=c2, nom="P2", prix=200)

    def test_aucune_fuite_entre_restaurants(self):
        from apps.tenants.context import set_current_restaurant
        try:
            set_current_restaurant(self.r1)
            self.assertEqual(Produit.objects.count(), 1)
            self.assertEqual(Produit.objects.first().nom, "P1")
            set_current_restaurant(self.r2)
            self.assertEqual(Produit.objects.count(), 1)
            self.assertEqual(Produit.objects.first().nom, "P2")
        finally:
            set_current_restaurant(None)

    def test_login_via_bon_sous_domaine(self):
        c = Client()
        r = c.post(
            "/accounts/login/",
            {"username": "admin1", "password": "Pass12345"},
            HTTP_HOST="resto-un.localhost",
        )
        self.assertEqual(r.status_code, 302)
        self.assertIn("dashboard", r["Location"])

    def test_login_refuse_mauvais_sous_domaine(self):
        # Utilisateur du resto 2 se connecte via le sous-domaine du resto 1
        c = Client()
        r = c.post(
            "/accounts/login/",
            {"username": "admin2", "password": "Pass12345"},
            HTTP_HOST="resto-un.localhost",
        )
        self.assertEqual(r.status_code, 200)  # page login ré-affichée avec erreur

    def test_login_refuse_restaurant_desactive(self):
        self.r1.actif = False
        self.r1.save()
        c = Client()
        r = c.post(
            "/accounts/login/",
            {"username": "admin1", "password": "Pass12345"},
            HTTP_HOST="resto-un.localhost",
        )
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "désactivé")

    def test_staff_desactive_bloque_acces(self):
        self.r1.actif = False
        self.r1.save()
        c = Client()
        c.force_login(self.admin1)
        r = c.get("/dashboard/", HTTP_HOST="resto-un.localhost")
        self.assertEqual(r.status_code, 302)
        self.assertIn("accounts/login", r["Location"])

    def test_client_creation_scope(self):
        from apps.tenants.context import set_current_restaurant
        try:
            set_current_restaurant(self.r1)
            ClientModel.objects.create(nom="Client R1", telephone="111")
            set_current_restaurant(self.r2)
            ClientModel.objects.create(nom="Client R2", telephone="222")
            set_current_restaurant(self.r1)
            self.assertEqual(ClientModel.objects.count(), 1)
            self.assertEqual(ClientModel.objects.first().nom, "Client R1")
        finally:
            set_current_restaurant(None)


class CinetPayTests(TestCase):

    def setUp(self):
        self.resto = Restaurant.objects.create(nom="Resto Pay", slug="resto-pay")
        self.plan = Plan.objects.create(nom="Pro Pay", prix_mensuel=15000, modules=["menu", "caisse"])
        self.resto.plan = self.plan
        self.resto.save()
        self.admin = CustomUser.objects.create_user(
            username="payadmin", email="pay@test.com", password="Pass12345",
            role="ADMIN", restaurant=self.resto,
        )
        self.client.force_login(self.admin)

    def _configurer_cinetpay(self, active=True):
        pp = ParametrePlateforme.load()
        pp.cinetpay_active = active
        pp.cinetpay_apikey = "TEST_APIKEY"
        pp.cinetpay_site_id = "12345"
        pp.cinetpay_devise = "XOF"
        pp.save()
        return pp

    def test_bouton_payer_affiche_si_actif(self):
        self._configurer_cinetpay(True)
        r = self.client.get(reverse("tenants:mon_abonnement"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Payer 15000 FCFA par Mobile Money")

    def test_pas_de_bouton_si_cinetpay_inactif(self):
        self._configurer_cinetpay(False)
        r = self.client.get(reverse("tenants:mon_abonnement"))
        self.assertNotContains(r, "par Mobile Money")

    def test_lancer_paiement_sans_cinetpay_affiche_erreur(self):
        self._configurer_cinetpay(False)
        r = self.client.post(reverse("tenants:lancer_paiement"))
        self.assertRedirects(r, reverse("tenants:mon_abonnement"))
        self.assertEqual(Paiement.objects.count(), 0)

    def test_lancer_paiement_creer_transaction_et_redirige(self):
        from unittest import mock
        from apps.tenants import cinetpay
        self._configurer_cinetpay(True)
        reponse_fake = {
            "code": "0",
            "message": "OK",
            "data": {"payment_url": "https://checkout.cinetpay.com/test", "payment_id": "CP123"},
        }
        with mock.patch.object(cinetpay, "initialiser_paiement", return_value=reponse_fake):
            r = self.client.post(reverse("tenants:lancer_paiement"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("https://checkout.cinetpay.com/test", r["Location"])
        paiement = Paiement.objects.first()
        self.assertIsNotNone(paiement)
        self.assertEqual(paiement.statut, "EN_ATTENTE")
        self.assertEqual(paiement.cinetpay_transaction_id, "CP123")

    def test_lancer_paiement_erreur_api_cree_paiement_echec(self):
        from unittest import mock
        from apps.tenants import cinetpay
        self._configurer_cinetpay(True)
        with mock.patch.object(
            cinetpay, "initialiser_paiement", side_effect=cinetpay.CinetPayError("boom")
        ):
            r = self.client.post(reverse("tenants:lancer_paiement"))
        self.assertRedirects(r, reverse("tenants:mon_abonnement"))
        paiement = Paiement.objects.first()
        self.assertIsNotNone(paiement)
        self.assertEqual(paiement.statut, "ECHEC")

    def test_notif_succes_prolonge_abonnement(self):
        from unittest import mock
        from apps.tenants import cinetpay
        self._configurer_cinetpay(True)
        paiement = Paiement.objects.create(
            restaurant=self.resto,
            transaction_id="ABO-1-TEST123",
            montant=15000,
            statut="EN_ATTENTE",
        )
        reponse_fake = {
            "code": "0",
            "data": {"status": "ACCEPTED", "payment_id": "CP123"},
        }
        with mock.patch.object(cinetpay, "verifier_paiement", return_value=reponse_fake):
            r = self.client.post(
                reverse("tenants:notif_paiement"),
                {"cpm_trans_id": "ABO-1-TEST123", "cpm_site_id": "12345"},
            )
        self.assertEqual(r.status_code, 200)
        paiement.refresh_from_db()
        self.resto.refresh_from_db()
        self.assertEqual(paiement.statut, "SUCCES")
        self.assertIsNotNone(self.resto.abonnement_expire_le)

    def test_notif_avec_transaction_inconnue_repond_200(self):
        r = self.client.post(
            reverse("tenants:notif_paiement"),
            {"cpm_trans_id": "INCONNU", "cpm_site_id": "12345"},
        )
        self.assertEqual(r.status_code, 200)

    def test_retour_sans_transaction_redirige(self):
        r = self.client.get(reverse("tenants:retour_paiement"))
        self.assertRedirects(r, reverse("tenants:mon_abonnement"))
