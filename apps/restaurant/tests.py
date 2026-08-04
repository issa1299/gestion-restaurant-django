from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from apps.restaurant.models import Temoignage, ContactMessage
from apps.parametres.models import ParametreRestaurant

User = get_user_model()


class TemoignageCRUDTests(TestCase):
    """CRUD complet des témoignages côté admin."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="adm_t", email="adm_t@test.com", password="Test12345", role="ADMIN",
        )
        self.serveur = User.objects.create_user(
            username="ser_t", email="ser_t@test.com", password="Test12345", role="SERVEUR",
        )
        self.temoignage = Temoignage.objects.create(
            nom="Awa", note=5, message="Excellent restaurant !",
        )

    def test_gestion_accessible_admin(self):
        c = Client()
        c.force_login(self.admin)
        resp = c.get("/temoignages/gestion/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Awa")

    def test_gestion_interdite_serveur(self):
        c = Client()
        c.force_login(self.serveur)
        resp = c.get("/temoignages/gestion/")
        self.assertEqual(resp.status_code, 302)

    def test_ajouter_temoignage(self):
        c = Client()
        c.force_login(self.admin)
        resp = c.post("/temoignages/ajouter/", {
            "nom": "Moussa",
            "note": "4",
            "message": "Très bon service",
            "actif": "on",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Temoignage.objects.filter(nom="Moussa", note=4).exists())

    def test_modifier_temoignage(self):
        c = Client()
        c.force_login(self.admin)
        resp = c.post("/temoignages/%d/modifier/" % self.temoignage.id, {
            "nom": "Awa D.",
            "note": "3",
            "message": "Bien",
            "actif": "",
        })
        self.assertEqual(resp.status_code, 302)
        self.temoignage.refresh_from_db()
        self.assertEqual(self.temoignage.nom, "Awa D.")
        self.assertEqual(self.temoignage.note, 3)
        self.assertFalse(self.temoignage.actif)

    def test_supprimer_temoignage(self):
        c = Client()
        c.force_login(self.admin)
        resp = c.post("/temoignages/%d/supprimer/" % self.temoignage.id)
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Temoignage.objects.filter(id=self.temoignage.id).exists())

    def test_toggle_actif(self):
        c = Client()
        c.force_login(self.admin)
        resp = c.post("/temoignages/%d/toggle/" % self.temoignage.id)
        self.assertEqual(resp.status_code, 302)
        self.temoignage.refresh_from_db()
        self.assertFalse(self.temoignage.actif)

    def test_toggle_refuse_sur_get(self):
        c = Client()
        c.force_login(self.admin)
        resp = c.get("/temoignages/%d/toggle/" % self.temoignage.id)
        self.assertEqual(resp.status_code, 405)
        self.temoignage.refresh_from_db()
        self.assertTrue(self.temoignage.actif)

    def test_page_publique_cache_inactifs(self):
        Temoignage.objects.create(nom="Caché", note=1, message="x", actif=False)
        resp = self.client.get("/temoignages/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Awa")
        self.assertNotContains(resp, "Caché")


class RepondreMessageTests(TestCase):
    """Répondre à un message de contact par e-mail."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="adm_r", email="adm_r@test.com", password="Test12345", role="ADMIN",
        )
        self.client_role = User.objects.create_user(
            username="cli_r", email="cli_r@test.com", password="Test12345", role="CLIENT",
        )
        self.message = ContactMessage.objects.create(
            nom="Client", email="client@test.com", sujet="Question", message="Bonjour",
        )

    def test_page_reponse_accessible_admin(self):
        c = Client()
        c.force_login(self.admin)
        resp = c.get("/message/%d/repondre/" % self.message.id)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "client@test.com")

    def test_page_reponse_interdite_client(self):
        c = Client()
        c.force_login(self.client_role)
        resp = c.get("/message/%d/repondre/" % self.message.id)
        self.assertEqual(resp.status_code, 302)

    def test_reponse_sans_smtp_configure(self):
        """Sans SMTP configuré, on affiche un message mais pas de crash."""
        ParametreRestaurant.load().smtp_host = ""
        ParametreRestaurant.load().smtp_user = ""
        ParametreRestaurant.load().smtp_password = ""
        ParametreRestaurant.load().save()
        c = Client()
        c.force_login(self.admin)
        resp = c.post("/message/%d/repondre/" % self.message.id, {"reponse": "Merci !"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "configuré")
