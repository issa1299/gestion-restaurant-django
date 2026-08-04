from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import ParametreRestaurant
from .forms import ParametreForm
from apps.notifications.emails import tester_connexion_smtp

@login_required
def index(request):
    if request.user.role != "ADMIN":
        return render(request, "base/403.html", status=403)

    parametre = ParametreRestaurant.load()

    if request.method == "POST":
        form = ParametreForm(request.POST, request.FILES, instance=parametre)
        if form.is_valid():
            form.save()
            messages.success(request, "Paramètres enregistrés avec succès.")
            return redirect("parametres:index")
    else:
        form = ParametreForm(instance=parametre)

    return render(request, "parametres/index.html", {"form": form})


@login_required
def tester_connexion(request):
    if request.user.role != "ADMIN":
        return JsonResponse({"ok": False, "message": "Accès refusé."}, status=403)

    parametre = ParametreRestaurant.load()
    if request.method == "POST":
        form = ParametreForm(request.POST, request.FILES, instance=parametre)
        if form.is_valid():
            form.save()
            ok, message = tester_connexion_smtp()
            return JsonResponse({"ok": ok, "message": message})
        return JsonResponse(
            {"ok": False, "message": "Formulaire invalide : vérifiez les champs SMTP."},
            status=400,
        )
    return JsonResponse({"ok": False, "message": "Méthode non autorisée."}, status=405)
