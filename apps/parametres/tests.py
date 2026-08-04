from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.parametres.models import ParametreRestaurant

User = get_user_model()


class TesterConnexionSmtpTests(TestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_t", email="admin_t@test.com", password="pass12345", role="ADMIN"
        )
        self.cais = User.objects.create_user(
            username="cais_t", email="cais_t@test.com", password="pass12345", role="CAISSIER"
        )
        self.client.force_login(self.admin)
        self.url = "/parametres/tester-connexion/"

    def _post(self, **kwargs):
        base = {
            "nom": "RestaurantPro",
            "devise": "FCFA",
            "smtp_port": "587",
            "message_ticket": "Merci",
        }
        base.update(kwargs)
        return self.client.post(self.url, base)

    def test_reserve_aux_admins(self):
        self.client.force_login(self.cais)
        rep = self._post()
        self.assertEqual(rep.status_code, 403)

    def test_config_incomplete(self):
        rep = self._post()
        self.assertEqual(rep.status_code, 200)
        self.assertFalse(rep.json()["ok"])
        self.assertIn("incomplète", rep.json()["message"])

    def test_doit_renvoyer_erreur(self):
        p = ParametreRestaurant.load()
        p.email_restaurant = "resto@test.com"
        p.smtp_host = "smtp.invalid.test"
        p.smtp_port = 587
        p.smtp_user = "resto@test.com"
        p.smtp_password = "secret"
        p.save()
        rep = self._post(
            email_restaurant="resto@test.com",
            smtp_host="smtp.invalid.test",
            smtp_port="587",
            smtp_user="resto@test.com",
            smtp_password="secret",
        )
        self.assertEqual(rep.status_code, 200)
        self.assertFalse(rep.json()["ok"])
