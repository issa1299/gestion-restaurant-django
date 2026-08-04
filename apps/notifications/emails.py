from django.core.mail import send_mail
from django.conf import settings
from apps.parametres.models import ParametreRestaurant


def tester_connexion_smtp():
    """Teste la connexion SMTP configurée. Retourne (ok: bool, message: str)."""
    p = ParametreRestaurant.load()
    if not p.smtp_config_complete():
        return False, "Configuration SMTP incomplète : renseignez l'e-mail, l'hôte, l'utilisateur et le mot de passe."
    try:
        connexion = _connexion_smtp(p, forcer_smtp=True)
        connexion.open()
        connexion.close()
        return True, "Connexion SMTP réussie ! Vos e-mails aux clients seront envoyés via ce serveur."
    except Exception as e:
        return False, f"Échec de la connexion SMTP : {e}"


def config_email_disponible():
    """Retourne True si une configuration SMTP est renseignée dans les paramètres."""
    p = ParametreRestaurant.load()
    return p.smtp_config_complete()


def envoyer_email(destinataire, sujet, message_html, message_texte=""):
    """Envoie un e-mail au client via la configuration SMTP du restaurant."""
    p = ParametreRestaurant.load()
    if not config_email_disponible():
        return False

    try:
        from django.core.mail import EmailMultiAlternatives
        email = EmailMultiAlternatives(
            subject=sujet,
            body=message_texte or sujet,
            from_email=p.email_restaurant,
            to=[destinataire],
            connection=_connexion_smtp(p),
        )
        email.attach_alternative(message_html, "text/html")
        email.send(fail_silently=False)
        return True
    except Exception:
        return False


def envoyer_email_avec_erreur(destinataire, sujet, message_html, message_texte=""):
    """Comme envoyer_email mais renvoie (ok, message_d_erreur) avec le détail."""
    p = ParametreRestaurant.load()
    if not config_email_disponible():
        return False, "Configuration SMTP incomplète dans Paramètres."
    if not destinataire:
        return False, "Aucune adresse e-mail pour ce client."

    try:
        from django.core.mail import EmailMultiAlternatives
        email = EmailMultiAlternatives(
            subject=sujet,
            body=message_texte or sujet,
            from_email=p.email_restaurant,
            to=[destinataire],
            connection=_connexion_smtp(p),
        )
        email.attach_alternative(message_html, "text/html")
        email.send(fail_silently=False)
        return True, ""
    except Exception as e:
        return False, str(e)


def _connexion_smtp(p, forcer_smtp=False):
    from django.core.mail import get_connection
    kwargs = dict(
        host=p.smtp_host,
        port=p.smtp_port,
        username=p.smtp_user,
        password=p.smtp_password_clair(),
        use_tls=(p.smtp_port in (587, 465)),
    )
    if forcer_smtp:
        kwargs["backend"] = "django.core.mail.backends.smtp.EmailBackend"
    return get_connection(**kwargs)


def _cadre_html(contenu, p):
    return f"""
    <div style="font-family:Arial,Helvetica,sans-serif;max-width:600px;margin:0 auto;
                border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;">
      <div style="background:#f97316;color:#fff;padding:18px 24px;text-align:center;">
        <strong style="font-size:18px;">{p.nom or 'Restaurant'}</strong>
      </div>
      <div style="padding:24px;">
        {contenu}
      </div>
      <div style="background:#f9fafb;padding:12px 24px;text-align:center;font-size:12px;color:#9ca3af;">
        {p.nom or 'Restaurant'} — {p.telephone or ''} {('· ' + p.adresse) if p.adresse else ''}
      </div>
    </div>
    """


def email_confirmation_commande(commande):
    """Confirme au client la création de sa commande."""
    p = ParametreRestaurant.load()
    if not config_email_disponible():
        return False
    if not commande.client or not commande.client.email:
        return False

    lignes = "".join(
        f"<tr><td style='padding:6px 0;'>{ligne.produit.nom}</td>"
        f"<td style='padding:6px 0;text-align:center;'>{ligne.quantite}</td>"
        f"<td style='padding:6px 0;text-align:right;'>{ligne.sous_total:.0f} {p.devise}</td></tr>"
        for ligne in commande.lignes.all()
    )
    contenu = f"""
    <h2 style="color:#1f2937;margin-top:0;">Merci {commande.client.nom} !</h2>
    <p style="color:#4b5563;">Votre commande <strong>N° {commande.id}</strong> a bien été enregistrée.</p>
    <table style="width:100%;border-collapse:collapse;font-size:14px;color:#374151;">
      <tr><th style="text-align:left;padding:6px 0;">Produit</th>
          <th style="text-align:center;">Qté</th>
          <th style="text-align:right;">Prix</th></tr>
      {lignes}
      <tr><td colspan="2" style="border-top:2px solid #e5e7eb;padding-top:8px;font-weight:bold;">Total</td>
          <td style="border-top:2px solid #e5e7eb;padding-top:8px;text-align:right;font-weight:bold;">
            {commande.total:.0f} {p.devise}</td></tr>
    </table>
    <p style="color:#4b5563;margin-top:16px;">
      Statut actuel : <strong>{commande.get_statut_display()}</strong>. Nous vous préviendrons dès qu'elle sera prête.
    </p>
    <p style="color:#6b7280;font-size:13px;">
      Pour toute question, contactez-nous au <strong>{p.telephone}</strong>.
    </p>
    """
    return envoyer_email(
        commande.client.email,
        f"Commande N° {commande.id} — {p.nom}",
        _cadre_html(contenu, p),
    )


def email_statut_commande(commande):
    """Prévient le client d'un changement de statut de sa commande."""
    p = ParametreRestaurant.load()
    if not config_email_disponible():
        return False
    if not commande.client or not commande.client.email:
        return False

    messages_statut = {
        "EN_PREPARATION": "votre commande est actuellement en préparation en cuisine.",
        "PRETE": "votre commande est prête ! Vous pouvez venir la récupérer.",
        "LIVREE": "votre commande a été livrée. Bon appétit !",
        "ANNULEE": "votre commande a été annulée. Contactez-nous pour plus d'informations.",
    }
    phrase = messages_statut.get(commande.statut, f"votre commande a changé de statut : {commande.get_statut_display()}.")
    contenu = f"""
    <h2 style="color:#1f2937;margin-top:0;">Votre commande N° {commande.id}</h2>
    <p style="color:#4b5563;">Bonjour {commande.client.nom},<br>{phrase}</p>
    <p style="color:#6b7280;font-size:13px;">
      Total : <strong>{commande.total:.0f} {p.devise}</strong><br>
      Pour toute question : <strong>{p.telephone}</strong>
    </p>
    """
    return envoyer_email(
        commande.client.email,
        f"Statut de votre commande N° {commande.id} — {p.nom}",
        _cadre_html(contenu, p),
    )


def email_reservation(reservation, annulation=False):
    """Prévient le client de la confirmation ou de l'annulation de sa réservation."""
    p = ParametreRestaurant.load()
    if not config_email_disponible():
        return False
    if not reservation.email:
        return False

    if annulation:
        titre = "Réservation annulée"
        contenu = f"""
        <h2 style="color:#1f2937;margin-top:0;">Votre réservation a été annulée</h2>
        <p style="color:#4b5563;">Bonjour {reservation.nom},<br>
        Nous sommes désolés, votre réservation du
        <strong>{reservation.date:%d/%m/%Y} à {reservation.heure:%H:%M}</strong>
        pour {reservation.nombre_personnes} personne(s) n'a pas pu être confirmée.</p>
        <p style="color:#6b7280;font-size:13px;">Contactez-nous au <strong>{p.telephone}</strong> pour réserver à un autre moment.</p>
        """
    else:
        titre = "Réservation confirmée"
        contenu = f"""
        <h2 style="color:#1f2937;margin-top:0;">Réservation confirmée ✓</h2>
        <p style="color:#4b5563;">Bonjour {reservation.nom},</p>
        <table style="width:100%;font-size:14px;color:#374151;">
          <tr><td style="padding:4px 0;">📅 Date</td><td style="font-weight:bold;">{reservation.date:%d/%m/%Y}</td></tr>
          <tr><td style="padding:4px 0;">🕒 Heure</td><td style="font-weight:bold;">{reservation.heure:%H:%M}</td></tr>
          <tr><td style="padding:4px 0;">👥 Personnes</td><td style="font-weight:bold;">{reservation.nombre_personnes}</td></tr>
        </table>
        <p style="color:#4b5563;margin-top:12px;">Nous vous attendons avec plaisir !</p>
        <p style="color:#6b7280;font-size:13px;">Pour toute question : <strong>{p.telephone}</strong></p>
        """
    return envoyer_email(
        reservation.email,
        f"{titre} — {p.nom}",
        _cadre_html(contenu, p),
    )


def email_reponse_contact(message_contact, reponse):
    """Envoie la réponse du restaurant au client ayant envoyé un message."""
    p = ParametreRestaurant.load()
    if not config_email_disponible():
        return False

    contenu = f"""
    <h2 style="color:#1f2937;margin-top:0;">Réponse à votre message</h2>
    <p style="color:#4b5563;">Bonjour {message_contact.nom},</p>
    <blockquote style="border-left:3px solid #f97316;padding-left:12px;margin:12px 0;color:#6b7280;font-style:italic;">
      {message_contact.message}
    </blockquote>
    <p style="color:#4b5563;">{reponse}</p>
    <p style="color:#6b7280;font-size:13px;">L'équipe {p.nom}</p>
    """
    return envoyer_email(
        message_contact.email,
        f"Re: {message_contact.sujet or 'Votre message'} — {p.nom}",
        _cadre_html(contenu, p),
    )


def email_reponse_contact_avec_erreur(message_contact, reponse):
    """Comme email_reponse_contact mais renvoie (ok, message_d_erreur)."""
    p = ParametreRestaurant.load()
    contenu = f"""
    <h2 style="color:#1f2937;margin-top:0;">Réponse à votre message</h2>
    <p style="color:#4b5563;">Bonjour {message_contact.nom},</p>
    <blockquote style="border-left:3px solid #f97316;padding-left:12px;margin:12px 0;color:#6b7280;font-style:italic;">
      {message_contact.message}
    </blockquote>
    <p style="color:#4b5563;">{reponse}</p>
    <p style="color:#6b7280;font-size:13px;">L'équipe {p.nom}</p>
    """
    return envoyer_email_avec_erreur(
        message_contact.email,
        f"Re: {message_contact.sujet or 'Votre message'} — {p.nom}",
        _cadre_html(contenu, p),
    )
