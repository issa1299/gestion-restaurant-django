from django import forms
from .models import Client


class ClientForm(forms.ModelForm):

    class Meta:
        model = Client

        fields = [
            "nom",
            "telephone",
            "email",
            "adresse",
            "photo",
            "date_naissance",
        ]

        widgets = {

            "nom": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 rounded-xl border",
                    "placeholder": "Nom du client"
                }
            ),

            "telephone": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 rounded-xl border",
                    "placeholder": "Téléphone"
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "class": "w-full px-4 py-2 rounded-xl border",
                    "placeholder": "Email"
                }
            ),

            "adresse": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-2 rounded-xl border",
                    "placeholder": "Adresse"
                }
            ),

            "date_naissance": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full px-4 py-2 rounded-xl border"
                }
            ),
        }