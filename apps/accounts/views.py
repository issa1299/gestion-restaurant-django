from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .forms import UserCreateForm, UserEditForm
from .models import CustomUser
from .decorators import ROLE_HOME, role_required


def _est_hote_local(request):
    """True si on est sur un hôte de test/développement ou un tunnel
    (localhost, 127.x, 192.168.x, .trycloudflare.com, .serveo.net...).
    Dans ce cas, la validation par sous-domaine est ignorée."""
    host = request.get_host().split(":")[0]
    if host in ("localhost", "127.0.0.1", "testserver"):
        return True
    if host.startswith("127.") or host.startswith("192.168.") or host.startswith("10."):
        return True
    return host.endswith(
        (".trycloudflare.com", ".serveo.net", ".ngrok.app", ".localhost", ".testserver")
    )


def login_view(request):

    error = None

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            # Refuser la connexion si le restaurant de l'utilisateur est désactivé
            if user.restaurant_id and not user.restaurant.actif:
                error = "Votre établissement a été désactivé. Contactez l'administrateur."
                user = None

            # Refuser si l'abonnement a expiré
            elif user.restaurant_id and user.restaurant.est_expire():
                error = "Votre abonnement a expiré. Contactez l'administrateur pour le renouveler."
                user = None

            # Refuser si l'utilisateur n'appartient pas au restaurant du sous-domaine
            elif (
                not user.is_superuser
                and request.restaurant is not None
                and user.restaurant_id != request.restaurant.id
                and not _est_hote_local(request)
            ):
                error = "Compte invalide pour cet établissement."
                user = None

        if user is not None:

            login(request, user)

            # Chaque rôle atterrit sur sa propre interface
            return redirect(ROLE_HOME.get(user.role, "dashboard:index"))

        else:
            if not error:
                error = "Identifiant ou mot de passe incorrect."

    return render(
        request,
        "accounts/login.html",
        {"error": error}
    )



@login_required
def logout_view(request):

    logout(request)

    return redirect("accounts:login")



@role_required(["ADMIN"])
def users_list(request):

    users = CustomUser.objects.all()

    # Recherche
    q = request.GET.get("q", "").strip()
    if q:
        users = users.filter(
            Q(username__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(email__icontains=q)
            | Q(telephone__icontains=q)
        )

    # Filtre par rôle
    role = request.GET.get("role", "").strip()
    roles = CustomUser._meta.get_field("role").choices
    if role in [r[0] for r in roles]:
        users = users.filter(role=role)

    return render(
        request,
        "accounts/users_list.html",
        {
            "users": users,
            "q": q,
            "role_selectionne": role,
            "roles": roles,
            "users_actifs": CustomUser.objects.filter(is_active=True).count(),
            "users_inactifs": CustomUser.objects.filter(is_active=False).count(),
            "users_admins": CustomUser.objects.filter(role="ADMIN").count(),
            "stats_roles": {
                r: CustomUser.objects.filter(role=r).count()
                for r, _ in roles
            },
        }
    )



@role_required(["ADMIN"])
def user_create(request):

    # Limite d'utilisateurs selon le plan d'abonnement
    restaurant = request.user.restaurant
    if (
        not request.user.is_superuser
        and restaurant is not None
        and not restaurant.autorise_utilisateur()
    ):
        messages.error(
            request,
            f"Votre plan « {restaurant.plan.nom if restaurant.plan else ''} » "
            f"ne permet plus de créer de compte utilisateur. "
            f"Passez à un plan supérieur.",
        )
        return redirect("accounts:users_list")

    if request.method == "POST":

        form = UserCreateForm(request.POST, request.FILES)

        if form.is_valid():

            form.save()

            messages.success(request, "Utilisateur créé avec succès.")

            return redirect("accounts:users_list")

    else:

        form = UserCreateForm()

    return render(
        request,
        "accounts/user_create.html",
        {
            "form": form
        }
    )



@role_required(["ADMIN"])
def user_edit(request, id):

    user = get_object_or_404(CustomUser, id=id)

    if request.method == "POST":

        form = UserEditForm(request.POST, request.FILES, instance=user)

        if form.is_valid():

            form.save()

            # Changer le mot de passe si fourni
            new_password = form.cleaned_data.get("new_password")

            if new_password:
                user.set_password(new_password)
                user.save()

            messages.success(request, "Utilisateur modifié avec succès.")

            return redirect("accounts:users_list")

    else:

        form = UserEditForm(instance=user)

    return render(
        request,
        "accounts/user_edit.html",
        {
            "form": form,
            "user_obj": user
        }
    )



@role_required(["ADMIN"])
def user_delete(request, id):

    user = get_object_or_404(CustomUser, id=id)

    if request.method == "POST":

        # Empêcher l'admin de se supprimer lui-même
        if user == request.user:
            messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
            return redirect("accounts:users_list")

        user.delete()

        messages.success(request, "Utilisateur supprimé avec succès.")

        return redirect("accounts:users_list")

    return render(
        request,
        "accounts/user_delete.html",
        {
            "user_obj": user
        }
    )



@role_required(["ADMIN"])
def user_toggle_active(request, id):

    user = get_object_or_404(CustomUser, id=id)

    if user == request.user:
        messages.error(request, "Vous ne pouvez pas désactiver votre propre compte.")
        return redirect("accounts:users_list")

    user.is_active = not user.is_active
    user.save()

    status = "activé" if user.is_active else "désactivé"
    messages.success(request, f"Compte de {user.username} {status}.")

    return redirect("accounts:users_list")