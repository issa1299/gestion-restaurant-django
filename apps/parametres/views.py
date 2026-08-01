from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ParametreRestaurant
from .forms import ParametreForm

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
