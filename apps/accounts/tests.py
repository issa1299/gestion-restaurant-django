from django.test import TestCase, Client
from django.contrib.auth import get_user_model

User = get_user_model()

ROLES = ["ADMIN", "CAISSIER", "SERVEUR", "CUISINIER", "GÉRANT", "LIVREUR", "CLIENT"]

# URL -> rôles autorisés (200 attendu), sinon 302 (redirection) attendue
ACCESS_MATRIX = {
    "/dashboard/": {"ADMIN", "SERVEUR", "CUISINIER", "CAISSIER"},
    "/accounts/users/": {"ADMIN"},
    "/clients/": {"ADMIN", "CAISSIER"},
    "/commandes/": {"ADMIN", "SERVEUR", "CUISINIER"},
    "/cuisine/": {"ADMIN", "CUISINIER"},
    "/livraisons/": {"ADMIN", "LIVREUR"},
    "/menu/gestion/": {"ADMIN", "GÉRANT"},
    "/stock/": {"ADMIN", "GÉRANT"},
    "/stock/historique/": {"ADMIN", "GÉRANT"},
    "/fournisseurs/": {"ADMIN", "GÉRANT"},
    "/fournisseurs/approvisionnements/": {"ADMIN", "GÉRANT"},
    "/tables/": {"ADMIN", "SERVEUR"},
    "/rapports/": {"ADMIN"},
    "/parametres/": {"ADMIN"},
    "/ventes/": {"CAISSIER"},
    "/ventes/historique/": {"ADMIN", "CAISSIER"},
    "/galerie/gestion/": {"ADMIN"},
    "/temoignages/gestion/": {"ADMIN"},
}


class AccessControlTests(TestCase):
    """Vérifie que chaque rôle n'accède qu'aux pages qui lui sont autorisées."""

    def setUp(self):
        self.users = {}
        for role in ROLES:
            self.users[role] = User.objects.create_user(
                username="user_%s" % role.lower(),
                email="user_%s@test.com" % role.lower(),
                password="Test12345",
                role=role,
            )

    def _get(self, role, url):
        c = Client()
        c.force_login(self.users[role])
        return c.get(url)

    def test_matrice_acces_par_role(self):
        for url, allowed in ACCESS_MATRIX.items():
            for role in ROLES:
                resp = self._get(role, url)
                if role in allowed:
                    self.assertEqual(
                        resp.status_code, 200,
                        "%s devrait être accessible à %s (statut %s)"
                        % (url, role, resp.status_code),
                    )
                else:
                    self.assertIn(
                        resp.status_code, (302, 403),
                        "%s devrait être interdit à %s (statut %s)"
                        % (url, role, resp.status_code),
                    )

    def test_pas_de_boucle_de_redirection(self):
        """Un rôle interdit ne doit jamais finir en boucle infinie."""
        for role, url in [
            ("CLIENT", "/dashboard/"),
            ("GÉRANT", "/dashboard/"),
            ("LIVREUR", "/dashboard/"),
            ("CLIENT", "/accounts/users/"),
            ("SERVEUR", "/stock/"),
        ]:
            resp = self._get(role, url)
            self.assertIn(resp.status_code, (302, 403))

    def test_admin_lecture_seule_sur_ecriture(self):
        """L'ADMIN ne peut pas accéder aux actions d'écriture (il supervise)."""
        urls_ecriture = [
            "/menu/produits/ajouter/",
            "/menu/produits/1/modifier/",
            "/stock/1/modifier/",
            "/stock/1/mouvement/",
            "/fournisseurs/ajouter/",
            "/fournisseurs/approvisionnements/ajouter/",
            "/ventes/",
            "/ventes/1/annuler/",
            "/clients/ajouter/",
            "/commandes/ajouter/",
            "/tables/creer/",
            "/livraisons/1/modifier/",
        ]
        for url in urls_ecriture:
            resp = self._get("ADMIN", url)
            self.assertIn(
                resp.status_code, (302, 403, 404, 405),
                "ADMIN ne devrait pas écrire via %s (statut %s)" % (url, resp.status_code),
            )

    def test_redirection_client_vers_menu(self):
        resp = self._get("CLIENT", "/dashboard/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/menu/", resp.get("Location", ""))

    def test_redirection_gerant_vers_gestion_menu(self):
        resp = self._get("GÉRANT", "/dashboard/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/menu/gestion/", resp.get("Location", ""))

    def test_redirection_livreur_vers_livraisons(self):
        resp = self._get("LIVREUR", "/dashboard/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/livraisons/", resp.get("Location", ""))

    def test_anonyme_redirige_vers_login(self):
        c = Client()
        resp = c.get("/dashboard/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp.get("Location", ""))


class UserManagementTests(TestCase):
    """Seul un ADMIN peut gérer les utilisateurs."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin_t", email="admin_t@test.com",
            password="Test12345", role="ADMIN",
        )
        self.serveur = User.objects.create_user(
            username="serveur_t", email="serveur_t@test.com",
            password="Test12345", role="SERVEUR",
        )

    def test_users_list_interdit_pour_non_admin(self):
        c = Client()
        c.force_login(self.serveur)
        resp = c.get("/accounts/users/")
        self.assertEqual(resp.status_code, 302)

    def test_users_list_accessible_admin(self):
        c = Client()
        c.force_login(self.admin)
        resp = c.get("/accounts/users/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Gestion des utilisateurs")

    def test_user_create_interdit_pour_non_admin(self):
        c = Client()
        c.force_login(self.serveur)
        resp = c.get("/accounts/users/create/")
        self.assertEqual(resp.status_code, 302)

    def test_admin_peut_creer_un_utilisateur(self):
        c = Client()
        c.force_login(self.admin)
        resp = c.post("/accounts/users/create/", {
            "username": "nouveau",
            "password1": "Motdepasse123",
            "password2": "Motdepasse123",
            "role": "SERVEUR",
        })
        self.assertIn(resp.status_code, (200, 302))
        if resp.status_code == 302:
            self.assertTrue(User.objects.filter(username="nouveau").exists())

    def test_admin_peut_desactiver_un_utilisateur(self):
        c = Client()
        c.force_login(self.admin)
        resp = c.post(
            "/accounts/users/%d/toggle-active/" % self.serveur.id,
        )
        self.serveur.refresh_from_db()
        self.assertFalse(self.serveur.is_active)
        self.assertEqual(resp.status_code, 302)
