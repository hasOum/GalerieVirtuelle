from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from .models import Utilisateur, Oeuvre, Artiste


class RegisterForm(UserCreationForm):
    is_artiste = forms.BooleanField(required=False)

    # champs artiste
    nationalite = forms.CharField(required=False)
    date_naissance = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    biographie = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    class Meta:
        model = Utilisateur
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
        )

    def save(self, commit=True):
        user = super().save(commit=False)

        if self.cleaned_data.get("is_artiste"):
            user.role = "artiste"
        else:
            user.role = "visiteur"

        if commit:
            user.save()

            if user.role == "artiste":
                nom = (user.get_full_name() or user.username).strip()
                Artiste.objects.create(
                    user=user,
                    nom=nom,
                    nationalite=self.cleaned_data.get("nationalite", ""),
                    date_naissance=self.cleaned_data.get("date_naissance"),
                    biographie=self.cleaned_data.get("biographie", ""),
                )

        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"placeholder": "Username"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Password"})
    )


class OeuvreForm(forms.ModelForm):
    class Meta:
        model = Oeuvre
        fields = [
            "titre",
            "description",
            "image",
            "technique",
            "annee_creation",
            "categorie",
            "prix",
            "stock",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }


class PaiementForm(forms.Form):
    """Formulaire pour les informations de paiement"""
    
    # Adresse de facturation
    adresse = forms.CharField(
        label="Adresse",
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "123 Rue de la Paix",
            "type": "text"
        })
    )
    
    code_postal = forms.CharField(
        label="Code Postal",
        max_length=10,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "75001",
            "type": "text"
        })
    )
    
    ville = forms.CharField(
        label="Ville",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Paris",
            "type": "text"
        })
    )
    
    pays = forms.CharField(
        label="Pays",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "France",
            "type": "text"
        })
    )
    
    # Informations de paiement (Carte bancaire)
    numero_carte = forms.CharField(
        label="Numéro de carte",
        max_length=16,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "1234 5678 9012 3456",
            "maxlength": "16",
            "type": "text"
        })
    )
    
    nom_titulaire = forms.CharField(
        label="Nom du titulaire",
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Jean Dupont",
            "type": "text"
        })
    )
    
    date_expiration = forms.CharField(
        label="Date d'expiration (MM/YY)",
        max_length=5,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "12/25",
            "maxlength": "5",
            "type": "text"
        })
    )
    
    cvv = forms.CharField(
        label="CVV",
        max_length=4,
        required=True,
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "123",
            "maxlength": "4"
        })
    )
    
    # Conditions
    accepte_conditions = forms.BooleanField(
        label="J'accepte les conditions de paiement",
        required=True,
        widget=forms.CheckboxInput(attrs={
            "class": "form-check-input"
        })
    )
