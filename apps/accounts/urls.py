from django.urls import path
from . import views

app_name = "accounts"


urlpatterns = [

    path(
        "login/",
        views.login_view,
        name="login"
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout"
    ),

    # Gestion utilisateurs
    path(
        "users/",
        views.users_list,
        name="users_list"
    ),

    path(
        "users/create/",
        views.user_create,
        name="user_create"
    ),

    path(
        "users/<int:id>/edit/",
        views.user_edit,
        name="user_edit"
    ),

    path(
        "users/<int:id>/delete/",
        views.user_delete,
        name="user_delete"
    ),

    path(
        "users/<int:id>/toggle-active/",
        views.user_toggle_active,
        name="user_toggle_active"
    ),

]