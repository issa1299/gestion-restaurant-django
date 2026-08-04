import json

from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from apps.menu.models import Produit, Categorie


class CommandeApiSecuriteTests(TestCase):
    """CSRF pour connectés + rate-limit anti-spam sur la commande client."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="adm_test", email="adm@t.fr",
            password="pass12345", role="ADMIN",
        )
        self.cat = Categorie.objects.create(nom="TestSec5")
        self.prod = Produit.objects.create(
            nom="Plat", prix=1000, categorie=self.cat, disponible=True,
        )
        self.url = "/commandes/client/passer-commande/"

    def _payload(self):
        return json.dumps({
            "panier": [{"id": self.prod.id, "qte": 1}],
            "guest_nom": "Ali",
            "guest_telephone": "0600000000",
        })

    def test_guest(self):
        c = Client(enforce_csrf_checks=False)
        rep = c.post(self.url, data=self._payload(), content_type="application/json")
        self.assertEqual(rep.status_code, 200)

    def test_connecte_sans_token(self):
        c = Client(enforce_csrf_checks=True)
        c.force_login(self.user)
        rep = c.post(self.url, data=self._payload(), content_type="application/json")
        self.assertEqual(rep.status_code, 403)

    def test_connecte_avec_token(self):
        c = Client(enforce_csrf_checks=True)
        c.force_login(self.user)
        # La page de connexion pose le cookie csrftoken (formulaire + get_token)
        c.get("/accounts/login/")
        cookie = c.cookies.get("csrftoken")
        self.assertIsNotNone(cookie, "cookie csrftoken attendu")
        rep = c.post(self.url, data=self._payload(), content_type="application/json",
                     HTTP_X_CSRFTOKEN=cookie.value)
        self.assertEqual(rep.status_code, 200)

    def test_rate_limit(self):
        c = Client(enforce_csrf_checks=False)
        # 1re commande (guest) -> 200
        r1 = c.post(self.url, data=self._payload(), content_type="application/json")
        self.assertEqual(r1.status_code, 200)
        # 2e immédiate -> 429
        r2 = c.post(self.url, data=self._payload(), content_type="application/json")
        self.assertEqual(r2.status_code, 429)