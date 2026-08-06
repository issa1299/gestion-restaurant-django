"""Génération du reçu de paiement en PDF (ReportLab)."""

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

_COULEURS = {
    "encre": colors.HexColor("#1e293b"),
    "gris": colors.HexColor("#64748b"),
    "accent": colors.HexColor("#0ea5e9"),
    "vert": colors.HexColor("#16a34a"),
    "ligne": colors.HexColor("#e2e8f0"),
    "fond": colors.HexColor("#f8fafc"),
}


def _statut_libelle(statut):
    return {
        "SUCCES": "Paiement réussi",
        "EN_ATTENTE": "En attente",
        "ECHEC": "Échoué",
        "ANNULE": "Annulé",
        "REFUSE": "Refusé",
    }.get(statut, statut)


def _montant_fr(n):
    return f"{n:,}".replace(",", " ")


def generer_recu_pdf(paiement, parametres):
    """Retourne un BytesIO contenant le PDF du reçu."""
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A5)
    largeur, hauteur = A5
    marge = 12 * mm

    # --- En-tête ---
    c.setFillColor(_COULEURS["accent"])
    c.setFont("Helvetica-Bold", 10)
    c.drawString(marge, hauteur - 16 * mm, "RECU DE PAIEMENT")

    c.setFillColor(_COULEURS["gris"])
    c.setFont("Helvetica", 8)
    c.drawString(marge, hauteur - 21 * mm, parametres.nom_plateforme or "RestaurantPro")
    if parametres.telephone_paiement:
        c.drawString(marge, hauteur - 25 * mm, parametres.telephone_paiement)

    c.setFillColor(_COULEURS["encre"])
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(largeur - marge, hauteur - 16 * mm, paiement.transaction_id)
    c.setFont("Helvetica", 8)
    c.setFillColor(_COULEURS["gris"])
    c.drawRightString(
        largeur - marge,
        hauteur - 21 * mm,
        paiement.date_creation.strftime("%d/%m/%Y %H:%M"),
    )

    # --- Ligne de séparation ---
    c.setStrokeColor(_COULEURS["ligne"])
    c.line(marge, hauteur - 30 * mm, largeur - marge, hauteur - 30 * mm)

    # --- Statut ---
    y = hauteur - 38 * mm
    c.setFont("Helvetica-Bold", 9)
    statut = _statut_libelle(paiement.statut)
    if paiement.statut == "SUCCES":
        c.setFillColor(_COULEURS["vert"])
    else:
        c.setFillColor(_COULEURS["gris"])
    c.drawString(marge, y, statut)

    # --- Tableau de détails ---
    details = [
        ("Client", paiement.restaurant.nom if paiement.restaurant else "—"),
        ("Téléphone", paiement.restaurant.telephone if paiement.restaurant and paiement.restaurant.telephone else "—"),
        ("Motif", f"Abonnement mensuel — {paiement.restaurant.plan.nom if paiement.restaurant and paiement.restaurant.plan else 'Plateforme'}"),
        ("Numéro de paiement", paiement.telephone or "—"),
        ("Référence PayDunya", paiement.paydunya_token or "—"),
    ]
    if paiement.description:
        details.append(("Description", paiement.description))

    ligne_h = 7.5 * mm
    debut_tableau = hauteur - 46 * mm
    for i, (label, valeur) in enumerate(details):
        y1 = debut_tableau - i * ligne_h
        y2 = y1 - ligne_h
        if i % 2 == 0:
            c.setFillColor(_COULEURS["fond"])
            c.rect(marge, y2, largeur - 2 * marge, ligne_h, stroke=0, fill=1)
        c.setStrokeColor(_COULEURS["ligne"])
        c.setFillColor(_COULEURS["gris"])
        c.setFont("Helvetica", 8)
        c.drawString(marge + 4 * mm, y2 + 2 * mm, label)
        c.setFillColor(_COULEURS["encre"])
        c.setFont("Helvetica-Bold", 8)
        c.drawString(60 * mm, y2 + 2 * mm, str(valeur)[:42])

    # --- Montant ---
    montant_y = debut_tableau - len(details) * ligne_h - 14 * mm
    c.setFillColor(_COULEURS["encre"])
    c.setFont("Helvetica-Bold", 9)
    c.drawString(marge, montant_y, "Montant payé")
    c.setFillColor(_COULEURS["accent"])
    c.setFont("Helvetica-Bold", 16)
    c.drawRightString(
        largeur - marge,
        montant_y - 2 * mm,
        f"{_montant_fr(paiement.montant)} {paiement.devise}",
    )

    # --- Encaisse par ---
    encaisse_y = montant_y - 12 * mm
    c.setFillColor(_COULEURS["gris"])
    c.setFont("Helvetica", 8)
    c.drawString(marge, encaisse_y, f"Encaissé par : {parametres.nom_beneficiaire or parametres.nom_plateforme}")

    # --- Pied de page ---
    c.setFillColor(_COULEURS["gris"])
    c.setFont("Helvetica", 7)
    c.drawCentredString(
        largeur / 2,
        8 * mm,
        f"Merci pour votre confiance — {parametres.nom_plateforme or 'RestaurantPro'}",
    )

    c.showPage()
    c.save()
    buf.seek(0)
    return buf