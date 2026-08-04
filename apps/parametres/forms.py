from django import forms
from .models import ParametreRestaurant

class ParametreForm(forms.ModelForm):
    class Meta:
        model = ParametreRestaurant
        fields = ['nom', 'adresse', 'telephone', 'email', 'logo', 'devise', 'url_site',
                  'email_restaurant', 'smtp_host', 'smtp_port', 'smtp_user', 'smtp_password',
                  'message_ticket']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none'}),
            'adresse': forms.Textarea(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none', 'rows': 2}),
            'telephone': forms.TextInput(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none'}),
            'email': forms.EmailInput(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none'}),
            'devise': forms.Select(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none bg-white'}, choices=[
                ('FCFA', 'Franc CFA (FCFA)'),
            ]),
            'url_site': forms.URLInput(attrs={
                'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none',
                'placeholder': 'http://192.168.1.156:8000',
                'help_text': 'URL publique utilisée pour les QR codes des tables.',
            }),
            'email_restaurant': forms.EmailInput(attrs={
                'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none',
                'placeholder': 'restaurant@exemple.com',
            }),
            'smtp_host': forms.TextInput(attrs={
                'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none',
                'placeholder': 'smtp.gmail.com',
            }),
            'smtp_port': forms.NumberInput(attrs={
                'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none',
                'placeholder': '587',
            }),
            'smtp_user': forms.TextInput(attrs={
                'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none',
                'placeholder': 'votre@email.com',
            }),
            'smtp_password': forms.PasswordInput(attrs={
                'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none',
                'placeholder': 'mot de passe / mot de passe d\'application',
            }),
            'message_ticket': forms.Textarea(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none', 'rows': 2}),
            'logo': forms.FileInput(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none'}),
        }

    def clean_smtp_password(self):
        """Si le champ mot de passe est vide, conserver l'existant (chiffré)."""
        valeur = self.cleaned_data.get("smtp_password", "")
        if not valeur:
            existant = ParametreRestaurant.load().smtp_password
            return existant
        return valeur
