from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.db import transaction
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

    def clean_matricule(self):
        """Convertit une chaîne vide en None pour éviter les doublons de chaînes vides."""
        matricule = self.cleaned_data.get('matricule')
        if matricule == '':
            return None
        return matricule

    @transaction.atomic
    def save(self, commit=True):
        # Sauvegarde l'utilisateur
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Création du profil dans la même transaction
            # Si une exception survient (ex: matricule en doublon), tout est annulé
            Profile.objects.create(
                user=user,
                niveau_etude=self.cleaned_data['niveau_etude'],
                filiere=self.cleaned_data['filiere'],
                matricule=self.cleaned_data.get('matricule'),  # None si champ vide
                phone=self.cleaned_data.get('phone'),
                bio=self.cleaned_data.get('bio'),
                is_mentee=True,
                is_mentor=False,
            )
        return user


class ConnexionForm(AuthenticationForm):
    """
    Formulaire de connexion qui accepte le nom d'utilisateur OU l'email.
    Hérite de AuthenticationForm pour conserver toute la logique de sécurité.
    """
    # On remplace le champ 'username' pour l'étendre (on garde le même nom)
    username = forms.CharField(
        label="Nom d'utilisateur ou email",
        widget=forms.TextInput(attrs={'autofocus': True})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # On peut personnaliser les labels si nécessaire
        self.fields['password'].label = "Mot de passe"

    def clean(self):
        # Appel de la validation standard (vérifie que les champs sont remplis)
        cleaned_data = super().clean()
        username_or_email = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username_or_email and password:
            # Tente d'authentifier avec le username
            from django.contrib.auth import authenticate
            user = authenticate(username=username_or_email, password=password)

            # Si échec, essaie de chercher l'utilisateur par email
            if user is None:
                try:
                    user_obj = User.objects.get(email=username_or_email)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass

            if user is None:
                raise forms.ValidationError(
                    "Nom d'utilisateur/email ou mot de passe incorrect.",
                    code='invalid_login'
                )

            # Stocke l'utilisateur trouvé pour get_user()
            self.user_cache = user

        return cleaned_data