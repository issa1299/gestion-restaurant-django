from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from apps.accounts.decorators import role_required
from .models import Table


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
def toggle_table(request, id):
    table = get_object_or_404(Table, id=id)
    table.disponible = not table.disponible
    table.save()
    status = "disponible" if table.disponible else "occupée"
    messages.success(request, f"Table {table.numero} marquée comme {status}.")
    return redirect("tables:liste")
