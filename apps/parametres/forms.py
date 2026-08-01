from django import forms
from .models import ParametreRestaurant

class ParametreForm(forms.ModelForm):
    class Meta:
        model = ParametreRestaurant
        fields = ['nom', 'adresse', 'telephone', 'email', 'logo', 'devise', 'message_ticket']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none'}),
            'adresse': forms.Textarea(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none', 'rows': 2}),
            'telephone': forms.TextInput(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none'}),
            'email': forms.EmailInput(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none'}),
            'devise': forms.Select(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none bg-white'}, choices=[
                ('FCFA', 'Franc CFA (FCFA)'),
            ]),
            'message_ticket': forms.Textarea(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none', 'rows': 2}),
            'logo': forms.FileInput(attrs={'class': 'w-full rounded-xl border-2 border-gray-200 p-3 focus:border-orange-500 focus:outline-none'}),
        }
