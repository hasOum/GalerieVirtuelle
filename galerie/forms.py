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
