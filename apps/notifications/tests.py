import datetime

# -*- coding: utf-8 -*-
from django.test import TestCase, override_settings
from django.core import mail
from django.contrib.auth import get_user_model

from apps.parametres.models import ParametreRestaurant
from apps.restaurant.models import Reservation, ContactMessage
from apps.clients.models import Client
from apps.menu.models import Categorie, Produit
from apps.commandes.models import Commande, LigneCommande
from apps.notifications.emails import (
    config_email_disponible,
    email_confirmation_commande,
    email_statut_commande,
    email_reservation,
    email_reponse_contact,
)

User = get_user_model()


def html_du_mail(email):
    for contenu, type_ in email.alternatives:
        if type_ == "text/html":
            return contenu
    return email.body


class EmailAutomatiqueTests(TestCase):

    def setUp(self):
        p = ParametreRestaurant.load()
        p.email_restaurant = "resto@test.com"
        p.smtp_host = "smtp.test.com"
        p.smtp_port = 587
        p.smtp_user = "resto@test.com"
        p.smtp_password = "secret"
        p.save()
        self.client = Client.objects.create(nom="Paul", email="paul@client.com", telephone="01")

    def test_config_email_disponible(self):
        self.assertTrue(config_email_disponible())

    def test_config_email_indisponible(self):
        p = ParametreRestaurant.load()
        p.smtp_password = ""
        p.save()
        self.assertFalse(config_email_disponible())

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_email_confirmation_commande(self):
        cat = Categorie.objects.create(nom="Cat Email")
        prod = Produit.objects.create(categorie=cat, nom="Plat", prix=1000)
        commande = Commande.objects.create(client=self.client, type="SUR_PLACE")
        LigneCommande.objects.create(commande=commande, produit=prod, quantite=2, prix=1000)

        ok = email_confirmation_commande(commande)
        self.assertTrue(ok)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["paul@client.com"])
        self.assertIn("Commande", mail.outbox[0].subject)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_email_statut_commande(self):
        commande = Commande.objects.create(client=self.client, type="SUR_PLACE", statut="PRETE")
        ok = email_statut_commande(commande)
        self.assertTrue(ok)
        self.assertIn("prête", html_du_mail(mail.outbox[0]))

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_email_reservation_confirmee(self):
        resa = Reservation.objects.create(
            nom="Awa", email="awa@test.com", telephone="01",
            date=datetime.date(2026, 8, 10), heure=datetime.time(19, 30), nombre_personnes=4,
        )
        ok = email_reservation(resa, annulation=False)
        self.assertTrue(ok)
        self.assertIn("confirmée", mail.outbox[0].subject)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_email_reponse_contact(self):
        msg = ContactMessage.objects.create(nom="Moussa", email="moussa@test.com", message="Bonjour")
        ok = email_reponse_contact(msg, "Merci de nous contacter !")
        self.assertTrue(ok)
        self.assertIn("Re:", mail.outbox[0].subject)
        self.assertIn("Merci", html_du_mail(mail.outbox[0]))
