from django import forms
from django.forms import inlineformset_factory
from apps.commandes.models import Commande, LigneCommande
from apps.menu.models import Produit

class CommandeForm(forms.ModelForm):
    class Meta:
        model = Commande
        fields = ['type', 'client', 'table', 'serveur', 'adresse_livraison', 'telephone_livraison']
        widgets = {
            'type': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg'}),
            'client': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg'}),
            'table': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg'}),
            'serveur': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg'}),
            'adresse_livraison': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg', 'rows': 2, 'placeholder': 'Adresse de livraison (si à emporter)'}),
            'telephone_livraison': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg', 'placeholder': 'Téléphone de livraison'}),
        }

class LigneCommandeForm(forms.ModelForm):
    class Meta:
        model = LigneCommande
        fields = ['produit', 'quantite', 'prix']
        widgets = {
            'produit': forms.Select(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg'}),
            'quantite': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg', 'min': 1}),
            'prix': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg', 'step': 0.01}),
        }

LigneCommandeFormSet = inlineformset_factory(
    Commande, 
    LigneCommande, 
    form=LigneCommandeForm, 
    extra=0, 
    can_delete=True,
)
