from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.db import transaction
from .models import Profile, Annonce


# ═══════════════════════════════════════════════════════════════════════════════
# FORMULAIRE D'INSCRIPTION
# ═══════════════════════════════════════════════════════════════════════════════

class InscriptionForm(UserCreationForm):
    """
    Formulaire d'inscription complet qui crée simultanément :
    - Un compte User (Django auth)
    - Un profil Profile lié (IFRI Mentor)
    """

    # ─── Champs User ───
    email = forms.EmailField(
        required=True,
        label="Adresse email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'prenom.nom@ifri.uac.bj'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        label="Prénom",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Jean'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label="Nom de famille",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'DUPONT'
        })
    )

    # ─── Champs Profile ───
    niveau_etude = forms.ChoiceField(
        choices=Profile.NIVEAU_CHOICES,
        label="Niveau d'étude",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    filiere = forms.CharField(
        max_length=100,
        label="Filière",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Génie Logiciel'
        })
    )
    matricule = forms.CharField(
        max_length=20,
        required=False,
        label="Matricule (optionnel)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: IFRI20250001'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        label="Téléphone",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+229 XX XX XX XX'
        })
    )
    bio = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Parlez un peu de vous, vos passions, vos compétences...'
        }),
        required=False,
        label="Bio"
    )
    is_mentor = forms.BooleanField(
        required=False,
        label="Je souhaite être mentor",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'jdupont'
            }),
        }

    def clean_matricule(self):
        """Convertit une chaîne vide en None pour éviter les doublons."""
        matricule = self.cleaned_data.get('matricule')
        if matricule == '':
            return None
        return matricule

    def clean_email(self):
        """Vérifie que l'email n'est pas déjà utilisé."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cette adresse email est déjà utilisée.")
        return email

    @transaction.atomic
    def save(self, commit=True):
        """
        Crée l'utilisateur et son profil dans une transaction atomique.
        Si une erreur survient, tout est annulé.
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

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
                is_mentor=self.cleaned_data.get('is_mentor', False),
            )
        return user


# ═══════════════════════════════════════════════════════════════════════════════
# FORMULAIRE DE CONNEXION
# ═══════════════════════════════════════════════════════════════════════════════

class ConnexionForm(AuthenticationForm):
    """
    Formulaire de connexion qui accepte :
    - Le nom d'utilisateur
    - OU l'adresse email
    """

    username = forms.CharField(
        label="Nom d'utilisateur ou email",
        widget=forms.TextInput(attrs={
            'autofocus': True,
            'class': 'form-control',
            'placeholder': 'Utilisateur ou email'
        })
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnalisation des messages d'erreur
        self.error_messages['invalid_login'] = (
            "Nom d'utilisateur/email ou mot de passe incorrect."
        )

    def clean(self):
        cleaned_data = super().clean()
        username_or_email = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username_or_email and password:
            from django.contrib.auth import authenticate

            # Essai 1 : authentification par username
            user = authenticate(username=username_or_email, password=password)

            # Essai 2 : recherche par email puis authentification
            if user is None:
                try:
                    user_obj = User.objects.get(email=username_or_email)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass

            if user is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login'
                )

            if not user.is_active:
                raise forms.ValidationError(
                    "Ce compte est désactivé.",
                    code='inactive'
                )

            self.user_cache = user

        return cleaned_data

    def get_user(self):
        return getattr(self, 'user_cache', None)


# ═══════════════════════════════════════════════════════════════════════════════
# FORMULAIRE DE MISE À JOUR DU PROFIL (User)
# ═══════════════════════════════════════════════════════════════════════════════

class UserUpdateForm(forms.ModelForm):
    """
    Permet de modifier les informations de base du compte utilisateur.
    """

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre prénom'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre nom'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'prenom.nom@ifri.uac.bj'
            }),
        }

    def clean_email(self):
        """Vérifie l'unicité de l'email (sauf pour l'utilisateur actuel)."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Cette adresse email est déjà utilisée par un autre compte.")
        return email


# ═══════════════════════════════════════════════════════════════════════════════
# FORMULAIRE DE MISE À JOUR DU PROFIL (Profile)
# ═══════════════════════════════════════════════════════════════════════════════

class ProfileUpdateForm(forms.ModelForm):
    """
    Permet de modifier les informations académiques et préférences du profil.
    """

    class Meta:
        model = Profile
        fields = [
            'avatar',
            'niveau_etude',
            'filiere',
            'phone',
            'bio',
            'disponibilites',
            'format_preference',
            'is_mentor',
            'is_mentee',
        ]
        widgets = {
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'niveau_etude': forms.Select(attrs={'class': 'form-control'}),
            'filiere': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Génie Logiciel, Systèmes et Réseaux...'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+229 XX XX XX XX'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': "Parlez de vos centres d'intérêt académiques, vos compétences, ce que vous aimez partager..."
            }),
            'disponibilites': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Samedi matin, tous les soirs après 19h, vacances...'
            }),
            'format_preference': forms.Select(attrs={'class': 'form-control'}),
            'is_mentor': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_mentee': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'avatar': 'Photo de profil',
            'niveau_etude': "Niveau d'étude (IFRI)",
            'filiere': 'Filière',
            'phone': 'Téléphone',
            'bio': 'À propos de moi',
            'disponibilites': 'Disponibilités',
            'format_preference': 'Format de session préféré',
            'is_mentor': 'Je suis mentor',
            'is_mentee': 'Je suis apprenant',
        }
        help_texts = {
            'avatar': 'Image au format JPG, PNG (max 2Mo)',
            'bio': 'Cette description sera visible par les autres utilisateurs',
            'disponibilites': 'Indiquez vos créneaux disponibles pour les sessions',
        }


# ═══════════════════════════════════════════════════════════════════════════════
# FORMULAIRE DE CRÉATION D'ANNONCE
# ═══════════════════════════════════════════════════════════════════════════════

class AnnonceForm(forms.ModelForm):
    """
    Permet aux utilisateurs de créer une annonce
    (recherche de mentor ou proposition de mentorat).
    """

    class Meta:
        model = Annonce
        fields = [
            'type_annonce',
            'matiere',
            'disponibilites',
            'format_cours',
            'description',
        ]
        widgets = {
            'type_annonce': forms.Select(attrs={
                'class': 'form-control'
            }),
            'matiere': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Langage C, Réseau OSI, Base de données SQL...'
            }),
            'disponibilites': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Samedi matin, Mercredi après-midi, tous les soirs...'
            }),
            'format_cours': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Décrivez ce que vous maîtrisez ou ce que vous recherchez en détail...'
            }),
        }
        labels = {
            'type_annonce': "Type d'annonce",
            'matiere': 'Matière / Compétence',
            'disponibilites': 'Vos disponibilités',
            'format_cours': 'Format préféré',
            'description': 'Description détaillée',
        }
        help_texts = {
            'matiere': 'Soyez précis pour faciliter la mise en relation',
            'description': "Plus votre description est détaillée, plus vous avez de chances d'être contacté",
        }