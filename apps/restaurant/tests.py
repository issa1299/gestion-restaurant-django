from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from apps.restaurant.models import Temoignage

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
        resp = c.get("/temoignages/%d/toggle/" % self.temoignage.id)
        self.assertEqual(resp.status_code, 302)
        self.temoignage.refresh_from_db()
        self.assertFalse(self.temoignage.actif)

    def test_page_publique_cache_inactifs(self):
        Temoignage.objects.create(nom="Caché", note=1, message="x", actif=False)
        resp = self.client.get("/temoignages/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Awa")
        self.assertNotContains(resp, "Caché")
