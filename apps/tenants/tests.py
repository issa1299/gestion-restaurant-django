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


class PayDunyaTests(TestCase):

    MASTER = "TEST_MASTER_KEY"

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

    def _configurer_paydunya(self, active=True):
        pp = ParametrePlateforme.load()
        pp.paydunya_active = active
        pp.paydunya_master_key = self.MASTER
        pp.paydunya_private_key = "TEST_PRIVATE_KEY"
        pp.paydunya_token = "TEST_TOKEN"
        pp.paydunya_mode = "test"
        pp.paydunya_devise = "XOF"
        pp.save()
        return pp

    def _ipn_data(self, token="test_ABC", statut="completed"):
        import hashlib
        import json
        return json.dumps({
            "response_code": "00",
            "hash": hashlib.sha512(self.MASTER.encode("utf-8")).hexdigest(),
            "invoice": {"token": token},
            "status": statut,
        })

    def test_bouton_payer_affiche_si_actif(self):
        self._configurer_paydunya(True)
        r = self.client.get(reverse("tenants:mon_abonnement"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Payer 15000 FCFA par Mobile Money")

    def test_pas_de_bouton_si_paydunya_inactif(self):
        self._configurer_paydunya(False)
        r = self.client.get(reverse("tenants:mon_abonnement"))
        self.assertNotContains(r, "par Mobile Money")

    def test_lancer_paiement_sans_paydunya_affiche_erreur(self):
        self._configurer_paydunya(False)
        r = self.client.post(reverse("tenants:lancer_paiement"))
        self.assertRedirects(r, reverse("tenants:mon_abonnement"))
        self.assertEqual(Paiement.objects.count(), 0)

    def test_lancer_paiement_creer_transaction_et_redirige(self):
        from unittest import mock
        from apps.tenants import paydunya
        self._configurer_paydunya(True)
        reponse_fake = {
            "response_code": "00",
            "response_text": "https://app.paydunya.com/sandbox-checkout/invoice/test_ABC",
            "token": "test_ABC",
        }
        with mock.patch.object(paydunya, "initialiser_paiement", return_value=reponse_fake):
            r = self.client.post(reverse("tenants:lancer_paiement"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("https://app.paydunya.com/sandbox-checkout/invoice/test_ABC", r["Location"])
        paiement = Paiement.objects.first()
        self.assertIsNotNone(paiement)
        self.assertEqual(paiement.statut, "EN_ATTENTE")
        self.assertEqual(paiement.paydunya_token, "test_ABC")

    def test_lancer_paiement_erreur_api_cree_paiement_echec(self):
        from unittest import mock
        from apps.tenants import paydunya
        self._configurer_paydunya(True)
        with mock.patch.object(
            paydunya, "initialiser_paiement", side_effect=paydunya.PayDunyaError("boom")
        ):
            r = self.client.post(reverse("tenants:lancer_paiement"))
        self.assertRedirects(r, reverse("tenants:mon_abonnement"))
        paiement = Paiement.objects.first()
        self.assertIsNotNone(paiement)
        self.assertEqual(paiement.statut, "ECHEC")

    def test_ipn_succes_prolonge_abonnement(self):
        self._configurer_paydunya(True)
        Paiement.objects.create(
            restaurant=self.resto,
            transaction_id="ABO-1-TEST123",
            paydunya_token="test_ABC",
            montant=15000,
            statut="EN_ATTENTE",
        )
        r = self.client.post(reverse("tenants:notif_paiement"), {"data": self._ipn_data()})
        self.assertEqual(r.status_code, 200)
        paiement = Paiement.objects.first()
        paiement.refresh_from_db()
        self.resto.refresh_from_db()
        self.assertEqual(paiement.statut, "SUCCES")
        self.assertIsNotNone(self.resto.abonnement_expire_le)

    def test_ipn_hash_invalide_ignore(self):
        import json
        self._configurer_paydunya(True)
        Paiement.objects.create(
            restaurant=self.resto,
            transaction_id="ABO-1-TEST123",
            paydunya_token="test_ABC",
            montant=15000,
            statut="EN_ATTENTE",
        )
        data = json.loads(self._ipn_data())
        data["hash"] = "Mauvais hash"
        r = self.client.post(reverse("tenants:notif_paiement"), {"data": json.dumps(data)})
        self.assertEqual(r.status_code, 200)
        paiement = Paiement.objects.first()
        paiement.refresh_from_db()
        self.assertEqual(paiement.statut, "EN_ATTENTE")

    def test_ipn_avec_transaction_inconnue_repond_200(self):
        r = self.client.post(reverse("tenants:notif_paiement"), {"data": self._ipn_data(token="INCONNU")})
        self.assertEqual(r.status_code, 200)

    def test_retour_sans_transaction_redirige(self):
        r = self.client.get(reverse("tenants:retour_paiement"))
        self.assertRedirects(r, reverse("tenants:mon_abonnement"))

    def test_retour_paiement_complete_confirme(self):
        from unittest import mock
        from apps.tenants import paydunya
        self._configurer_paydunya(True)
        Paiement.objects.create(
            restaurant=self.resto,
            transaction_id="ABO-1-TEST123",
            paydunya_token="test_ABC",
            montant=15000,
            statut="EN_ATTENTE",
        )
        reponse_fake = {"status": "completed", "invoice": {"token": "test_ABC"}}
        with mock.patch.object(paydunya, "verifier_paiement", return_value=reponse_fake):
            r = self.client.get(reverse("tenants:retour_paiement"), {"token": "test_ABC"})
        self.assertRedirects(r, reverse("tenants:mon_abonnement"))
        paiement = Paiement.objects.first()
        paiement.refresh_from_db()
        self.assertEqual(paiement.statut, "SUCCES")
