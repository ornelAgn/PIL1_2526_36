from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Profile

class InscriptionForm(UserCreationForm):
    # Champs User
    email = forms.EmailField(required=True, label="Adresse email")

    # Champs Profile
    niveau_etude = forms.ChoiceField(choices=Profile.NIVEAU_CHOICES, label="Niveau d'étude")
    filiere = forms.CharField(max_length=100, label="Filière")
    matricule = forms.CharField(max_length=20, required=False, label="Matricule (optionnel)")
    phone = forms.CharField(max_length=20, required=False, label="Téléphone")
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False, label="Bio")

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            Profile.objects.create(
                user=user,
                niveau_etude=self.cleaned_data['niveau_etude'],
                filiere=self.cleaned_data['filiere'],
                matricule=self.cleaned_data.get('matricule'),
                phone=self.cleaned_data.get('phone'),
                bio=self.cleaned_data.get('bio'),
                is_mentee=True,
                is_mentor=False,
            )
        return user


class ConnexionForm(AuthenticationForm):
    """Formulaire de connexion standard, avec des labels personnalisés si besoin."""
    username = forms.CharField(label="Nom d'utilisateur", widget=forms.TextInput(attrs={'autofocus': True}))
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)