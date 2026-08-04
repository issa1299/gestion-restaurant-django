from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
import qrcode
from io import BytesIO
from apps.accounts.decorators import role_required
from apps.parametres.models import ParametreRestaurant
from .models import Table


def url_menu_table(numero, base_url=""):
    """Construit l'URL du menu pour une table donnée.
    - base_url fournie (paramètre url_site) : utilisée telle quelle
    - sinon : relative, à compléter par request.build_absolute_uri
    """
    chemin = reverse("menu:accueil") + f"?table={numero}"
    if base_url:
        return f"{base_url.rstrip('/')}{chemin}"
    return chemin


@role_required(["ADMIN", "SERVEUR"])
def liste_tables(request):
    tables = Table.objects.all()
    total = tables.count()
    disponibles = tables.filter(disponible=True).count()
    occupees = tables.filter(disponible=False).count()

    return render(request, "tables/liste.html", {
        "tables": tables,
        "total": total,
        "disponibles": disponibles,
        "occupees": occupees,
    })


@role_required(["ADMIN", "SERVEUR"])
def qr_print(request):
    """Page imprimable avec les QR codes de toutes les tables"""
    tables = Table.objects.all()
    base = ParametreRestaurant.load().url_site

    qr_data = []
    for table in tables:
        url = url_menu_table(table.numero, base)
        if not base:
            url = request.build_absolute_uri(url)

        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        import base64
        data_uri = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()

        qr_data.append({"id": table.id, "numero": table.numero, "data_uri": data_uri})

    return render(request, "tables/qr_print.html", {"qr_data": qr_data})


def qr_table(request, id):
    """Génère le QR code de la table, pointant vers le menu avec le n° de table"""
    table = get_object_or_404(Table, id=id)

    base = ParametreRestaurant.load().url_site
    url = url_menu_table(table.numero, base)
    if not base:
        url = request.build_absolute_uri(url)

    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")

    return HttpResponse(
        buffer.getvalue(),
        content_type="image/png",
        headers={"Content-Disposition": f'inline; filename="table_{table.numero}_qr.png"'},
    )


@role_required(["SERVEUR"])
def creer_table(request):
    if request.method == "POST":
        numero = request.POST.get("numero")
        capacite = request.POST.get("capacite", 4)

        if Table.objects.filter(numero=numero).exists():
            messages.error(request, f"La table numéro {numero} existe déjà.")
            return redirect("tables:creer")

        Table.objects.create(numero=numero, capacite=capacite)
        messages.success(request, f"Table {numero} créée avec succès.")
        return redirect("tables:liste")

    return render(request, "tables/form.html", {"action": "Créer", "table": None})


@role_required(["SERVEUR"])
def modifier_table(request, id):
    table = get_object_or_404(Table, id=id)

    if request.method == "POST":
        table.numero = request.POST.get("numero")
        table.capacite = request.POST.get("capacite", 4)
        table.save()
        messages.success(request, f"Table {table.numero} modifiée.")
        return redirect("tables:liste")

    return render(request, "tables/form.html", {"action": "Modifier", "table": table})


@role_required(["SERVEUR"])
def supprimer_table(request, id):
    table = get_object_or_404(Table, id=id)

    if request.method == "POST":
        num = table.numero
        table.delete()
        messages.success(request, f"Table {num} supprimée.")
        return redirect("tables:liste")

    return render(request, "tables/supprimer.html", {"table": table})


@role_required(["SERVEUR"])
@require_POST
def toggle_table(request, id):
    table = get_object_or_404(Table, id=id)
    table.disponible = not table.disponible
    table.save()
    status = "disponible" if table.disponible else "occupée"
    messages.success(request, f"Table {table.numero} marquée comme {status}.")
    return redirect("tables:liste")
