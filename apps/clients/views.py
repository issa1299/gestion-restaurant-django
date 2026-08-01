from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from apps.accounts.decorators import role_required
from .models import Client

@role_required(["ADMIN", "CAISSIER"])
def liste_clients(request):
    q = request.GET.get("q")
    clients = Client.objects.all()
    
    if q:
        clients = clients.filter(nom__icontains=q)
    
    total_clients = Client.objects.count()
    clients_aujourdhui = Client.objects.filter(
        created_at__date=timezone.now().date()
    ).count()
    avec_email = Client.objects.exclude(email="").count()
    avec_telephone = Client.objects.exclude(telephone="").count()

    return render(
        request,
        "clients/liste.html",
        {
            "clients": clients,
            "q": q,
            "total_clients": total_clients,
            "clients_aujourdhui": clients_aujourdhui,
            "avec_email": avec_email,
            "avec_telephone": avec_telephone,
            "groupe": "clients"  # ← Ajouter
        }
    )
    
    
@role_required(["CAISSIER"])
def ajouter_client(request):

    if request.method == "POST":

        Client.objects.create(

            nom=request.POST.get("nom"),

            telephone=request.POST.get("telephone", ""),

            email=request.POST.get("email", ""),

            adresse=request.POST.get("adresse", "")

        )

        messages.success(
            request,
            "Client ajouté avec succès."
        )

        return redirect("clients:list")

    return render(
        request,
        "clients/add.html"
    )
    
@role_required(["CAISSIER"])
def modifier_client(request, pk):

    client = get_object_or_404(Client, pk=pk)

    if request.method == "POST":

        client.nom = request.POST.get("nom")
        client.telephone = request.POST.get("telephone", "")
        client.email = request.POST.get("email", "")
        client.adresse = request.POST.get("adresse", "")

        client.save()

        messages.success(
            request,
            "Client modifié avec succès."
        )

        return redirect("clients:list")

    return render(
        request,
        "clients/edit.html",
        {
            "client": client
        }
    )
    
@role_required(["CAISSIER"])
def supprimer_client(request, pk):

    client = get_object_or_404(Client, pk=pk)

    client.delete()

    messages.success(
        request,
        "Client supprimé avec succès."
    )

    return redirect("clients:list")

@role_required(["ADMIN", "CAISSIER"])
def detail_client(request, pk):

    client = get_object_or_404(Client, pk=pk)

    return render(
        request,
        "clients/detail.html",
        {
            "client": client
        }
    )
