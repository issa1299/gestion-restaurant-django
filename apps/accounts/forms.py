from django import forms
from .models import CustomUser, Role


class UserCreateForm(forms.ModelForm):

    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(
            attrs={"class": "w-full rounded-xl border p-3", "placeholder": "Mot de passe"}
        )
    )

    password_confirm = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(
            attrs={"class": "w-full rounded-xl border p-3", "placeholder": "Confirmer le mot de passe"}
        )
    )

    class Meta:

        model = CustomUser

        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "telephone",
            "adresse",
            "photo",
            "role",
            "password",
            "password_confirm",
        ]

        widgets = {
            "username": forms.TextInput(attrs={"class": "w-full rounded-xl border p-3", "placeholder": "Nom d'utilisateur"}),
            "first_name": forms.TextInput(attrs={"class": "w-full rounded-xl border p-3", "placeholder": "Prénom"}),
            "last_name": forms.TextInput(attrs={"class": "w-full rounded-xl border p-3", "placeholder": "Nom"}),
            "email": forms.EmailInput(attrs={"class": "w-full rounded-xl border p-3", "placeholder": "Email"}),
            "telephone": forms.TextInput(attrs={"class": "w-full rounded-xl border p-3", "placeholder": "Téléphone"}),
            "adresse": forms.TextInput(attrs={"class": "w-full rounded-xl border p-3", "placeholder": "Adresse"}),
            "photo": forms.FileInput(attrs={"class": "w-full rounded-xl border p-3"}),
            "role": forms.Select(attrs={"class": "w-full rounded-xl border p-3"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].choices = [
            (value, label) for value, label in Role.choices
            if value != Role.CLIENT
        ]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")

        return cleaned_data

    def save(self, commit=True):

        user = super().save(commit=False)

        user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()

        return user


class UserEditForm(forms.ModelForm):

    new_password = forms.CharField(
        label="Nouveau mot de passe (laisser vide pour ne pas changer)",
        widget=forms.PasswordInput(
            attrs={"class": "w-full rounded-xl border p-3", "placeholder": "Laisser vide pour ne pas modifier"}
        ),
        required=False
    )

    class Meta:

        model = CustomUser

        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "telephone",
            "adresse",
            "photo",
            "role",
            "is_active",
        ]

        widgets = {
            "username": forms.TextInput(attrs={"class": "w-full rounded-xl border p-3"}),
            "first_name": forms.TextInput(attrs={"class": "w-full rounded-xl border p-3"}),
            "last_name": forms.TextInput(attrs={"class": "w-full rounded-xl border p-3"}),
            "email": forms.EmailInput(attrs={"class": "w-full rounded-xl border p-3"}),
            "telephone": forms.TextInput(attrs={"class": "w-full rounded-xl border p-3"}),
            "adresse": forms.TextInput(attrs={"class": "w-full rounded-xl border p-3"}),
            "photo": forms.FileInput(attrs={"class": "w-full rounded-xl border p-3"}),
            "role": forms.Select(attrs={"class": "w-full rounded-xl border p-3"}),
            "is_active": forms.CheckboxInput(attrs={"class": "h-5 w-5 accent-orange-500"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].choices = [
            (value, label) for value, label in Role.choices
            if value != Role.CLIENT
        ]