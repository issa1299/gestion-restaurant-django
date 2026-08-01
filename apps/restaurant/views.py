from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.accounts.decorators import role_required
from apps.notifications.utils import envoyer_notification_broadcast
from .models import Reservation, ContactMessage, PhotoGalerie, Temoignage


def bienvenue(request):
    """Page de bienvenue (splash) affichée avant d'entrer sur le site."""
    return render(request, "site/bienvenue.html")


def accueil(request):
    """Page d'accueil publique du restaurant"""
    return render(request, "site/accueil.html")


def a_propos(request):
    """Page de présentation du restaurant"""
    return render(request, "site/a_propos.html")


def galerie(request):
    """Galerie de photos"""
    photos = PhotoGalerie.objects.all()
    return render(request, "site/galerie.html", {"photos": photos})


def livraison(request):
    """Informations sur la livraison"""
    return render(request, "site/livraison.html")


def temoignages(request):
    """Avis des clients"""
    temoignages = Temoignage.objects.filter(actif=True)
    return render(request, "site/temoignages.html", {"temoignages": temoignages})


def contact(request):
    """Page contact avec formulaire"""
    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        email = request.POST.get("email", "").strip()
        telephone = request.POST.get("telephone", "").strip()
        sujet = request.POST.get("sujet", "").strip()
        message = request.POST.get("message", "").strip()

        if not nom or not email or not message:
            messages.error(request, "Nom, email et message sont requis.")
            return redirect("restaurant:contact")

        ContactMessage.objects.create(
            nom=nom,
            email=email,
            telephone=telephone,
            sujet=sujet,
            message=message,
        )
        messages.success(request, "Votre message a bien été envoyé. Merci !")
        envoyer_notification_broadcast("dashboard", "nouveau_message", {
            "nom": nom,
            "email": email,
            "sujet": sujet or "Message de contact",
        })
        return redirect("restaurant:contact")

    return render(request, "site/contact.html")


def reserver(request):
    """Page de réservation de table"""
    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        telephone = request.POST.get("telephone", "").strip()
        email = request.POST.get("email", "").strip()
        date = request.POST.get("date", "")
        heure = request.POST.get("heure", "")
        personnes = request.POST.get("nombre_personnes", "2")
        message = request.POST.get("message", "").strip()

        if not nom or not telephone or not date or not heure:
            messages.error(request, "Nom, téléphone, date et heure sont requis.")
            return redirect("restaurant:reserver")

        try:
            personnes = int(personnes)
            if personnes < 1:
                raise ValueError
        except (ValueError, TypeError):
            personnes = 2

        Reservation.objects.create(
            nom=nom,
            telephone=telephone,
            email=email,
            date=date,
            heure=heure,
            nombre_personnes=personnes,
            message=message,
        )
        messages.success(
            request,
            f"Votre réservation du {date} à {heure} a bien été enregistrée. "
            f"Nous vous attendons !",
        )
        envoyer_notification_broadcast("dashboard", "nouvelle_reservation", {
            "nom": nom,
            "telephone": telephone,
            "date": date,
            "heure": str(heure),
            "personnes": personnes,
        })
        return redirect("restaurant:reserver")

    return render(request, "site/reserver.html")


@role_required(["ADMIN", "SERVEUR", "CAISSIER"])
def changer_statut_reservation(request, pk):
    """Confirmer ou annuler une réservation depuis le dashboard"""
    reservation = get_object_or_404(Reservation, pk=pk)
    statut = request.POST.get("statut")
    source = request.POST.get("source", "dashboard")

    if statut in (Reservation.CONFIRMEE, Reservation.ANNULEE):
        ancien = reservation.statut
        reservation.statut = statut
        reservation.save()
        libelles = dict(Reservation.STATUTS)
        messages.success(
            request,
            f"Réservation de {reservation.nom} : "
            f"{libelles.get(ancien, ancien)} → {libelles.get(statut)}.",
        )
        envoyer_notification_broadcast("dashboard", "statut_reservation", {
            "id": reservation.id,
            "nom": reservation.nom,
            "statut": libelles.get(statut),
        })
    else:
        messages.error(request, "Statut invalide.")

    if source == "reservations":
        return redirect("restaurant:reservations")
    return redirect("dashboard:index")


@role_required(["ADMIN", "SERVEUR", "CAISSIER"])
def marquer_message_lu(request, pk):
    """Marquer un message de contact comme lu (ou non lu)"""
    message = get_object_or_404(ContactMessage, pk=pk)
    lu = request.POST.get("lu", "1") == "1"
    message.lu = lu
    message.save()
    if lu:
        messages.success(request, f"Message de {message.nom} marqué comme lu.")
    else:
        messages.success(request, f"Message de {message.nom} marqué comme non lu.")
    if request.POST.get("source") == "messages":
        return redirect("restaurant:messages")
    return redirect("dashboard:index")


@role_required(["ADMIN", "SERVEUR", "CAISSIER"])
def liste_reservations(request):
    """Historique complet des réservations avec filtre par statut"""
    statut = request.GET.get("statut", "")
    reservations = Reservation.objects.all()
    if statut in dict(Reservation.STATUTS):
        reservations = reservations.filter(statut=statut)
    return render(request, "restaurant/reservations.html", {
        "reservations": reservations,
        "statuts": Reservation.STATUTS,
        "statut_selectionne": statut,
        "groupe": "dashboard",
    })


@role_required(["ADMIN", "SERVEUR", "CAISSIER"])
def liste_messages(request):
    """Liste des messages de contact avec filtre lu / non lu"""
    filtre = request.GET.get("filtre", "")
    messages_list = ContactMessage.objects.all()
    if filtre == "lus":
        messages_list = messages_list.filter(lu=True)
    elif filtre == "non_lus":
        messages_list = messages_list.filter(lu=False)
    return render(request, "restaurant/messages.html", {
        "messages_list": messages_list,
        "filtre": filtre,
        "groupe": "dashboard",
    })


@role_required(["ADMIN"])
def galerie_gestion(request):
    """Gestion interne des photos de la galerie"""
    if request.method == "POST":
        image = request.FILES.get("image")
        if not image:
            messages.error(request, "Veuillez sélectionner une image.")
        else:
            PhotoGalerie.objects.create(
                titre=request.POST.get("titre", "").strip(),
                image=image,
                description=request.POST.get("description", "").strip(),
            )
            messages.success(request, "Photo ajoutée à la galerie.")
        return redirect("restaurant:galerie_gestion")

    photos = PhotoGalerie.objects.all()
    return render(request, "restaurant/galerie_gestion.html", {
        "photos": photos,
        "photos_avec_titre": photos.exclude(titre="").count(),
        "groupe": "dashboard",
    })


@role_required(["ADMIN"])
def galerie_supprimer(request, pk):
    """Supprimer une photo de la galerie"""
    photo = get_object_or_404(PhotoGalerie, pk=pk)
    titre = photo.titre or f"Photo {photo.id}"
    photo.delete()
    messages.success(request, f"Photo « {titre} » supprimée.")
    return redirect("restaurant:galerie_gestion")


@role_required(["ADMIN"])
def temoignages_gestion(request):
    """Liste et gestion des témoignages (admin)"""
    temoignages_list = Temoignage.objects.all()
    actifs = Temoignage.objects.filter(actif=True).count()
    inactifs = Temoignage.objects.filter(actif=False).count()

    return render(request, "restaurant/temoignages_gestion.html", {
        "temoignages_list": temoignages_list,
        "actifs": actifs,
        "inactifs": inactifs,
        "total": temoignages_list.count(),
        "groupe": "dashboard",
    })


@role_required(["ADMIN"])
def temoignage_ajouter(request):
    """Créer un témoignage"""
    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        note = request.POST.get("note", "5")
        message = request.POST.get("message", "").strip()
        actif = request.POST.get("actif") == "on"

        if not nom or not message:
            messages.error(request, "Le nom et le message sont requis.")
            return redirect("restaurant:temoignage_ajouter")

        try:
            note = int(note)
            if note < 1 or note > 5:
                raise ValueError
        except (ValueError, TypeError):
            note = 5

        Temoignage.objects.create(
            nom=nom,
            note=note,
            message=message,
            actif=actif,
        )
        messages.success(request, "Témoignage ajouté avec succès.")
        return redirect("restaurant:temoignages_gestion")

    return render(request, "restaurant/temoignage_form.html", {"edition": False})


@role_required(["ADMIN"])
def temoignage_modifier(request, pk):
    """Modifier un témoignage"""
    temoignage = get_object_or_404(Temoignage, pk=pk)

    if request.method == "POST":
        nom = request.POST.get("nom", "").strip()
        note = request.POST.get("note", "5")
        message = request.POST.get("message", "").strip()
        actif = request.POST.get("actif") == "on"

        if not nom or not message:
            messages.error(request, "Le nom et le message sont requis.")
            return redirect("restaurant:temoignage_modifier", pk=pk)

        try:
            note = int(note)
            if note < 1 or note > 5:
                raise ValueError
        except (ValueError, TypeError):
            note = 5

        temoignage.nom = nom
        temoignage.note = note
        temoignage.message = message
        temoignage.actif = actif
        temoignage.save()

        messages.success(request, "Témoignage modifié avec succès.")
        return redirect("restaurant:temoignages_gestion")

    return render(request, "restaurant/temoignage_form.html", {
        "temoignage": temoignage,
        "edition": True,
    })


@role_required(["ADMIN"])
def temoignage_supprimer(request, pk):
    """Supprimer un témoignage"""
    temoignage = get_object_or_404(Temoignage, pk=pk)

    if request.method == "POST":
        nom = temoignage.nom
        temoignage.delete()
        messages.success(request, f"Témoignage de « {nom} » supprimé.")
        return redirect("restaurant:temoignages_gestion")

    return render(request, "restaurant/temoignage_supprimer.html", {
        "temoignage": temoignage,
    })


@role_required(["ADMIN"])
def temoignage_toggle(request, pk):
    """Activer / désactiver un témoignage"""
    temoignage = get_object_or_404(Temoignage, pk=pk)
    temoignage.actif = not temoignage.actif
    temoignage.save()
    statut = "activé" if temoignage.actif else "désactivé"
    messages.success(request, f"Témoignage de « {temoignage.nom} » {statut}.")
    return redirect("restaurant:temoignages_gestion")
