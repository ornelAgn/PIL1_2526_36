"""
Configuration Django pour le projet 'backend'.
"""
import os
from pathlib import Path

# Chemin de base du projet (backend/backend)
BASE_DIR = Path(__file__).resolve().parent.parent

# Clé secrète (à garder confidentielle en production)
SECRET_KEY = 'django-insecure-remplacez-par-une-vraie-clef'

# Mode debug (désactiver en production)
DEBUG = True

ALLOWED_HOSTS = []

# Applications installées
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',  # Notre application principale
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

# Configuration des templates : Django cherchera dans 'frontend/' (en dehors du dossier backend)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, '../frontend')],  # <-- dossier frontend
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

# --- Configuration de la base de données ---
# Choisissez votre SGBD et renseignez vos identifiants

# 2) MySQL (installez mysqlclient) :
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'projet_db',        # À remplacer par le vrai nom
        'USER': 'root',            # Votre utilisateur MySQL
        'PASSWORD': 'ruth2026',         # Votre mot de passe
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

# 1) SQLite (décommenter si besoin) :
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

# 3) PostgreSQL (décommenter si besoin) :
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'nom_de_la_base',
#         'USER': 'utilisateur',
#         'PASSWORD': 'motdepasse',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }

# Validation des mots de passe (configuration standard)
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

# Fichiers statiques (CSS, JS, images)
STATIC_URL = '/static/'
# Si vous placez vos CSS/JS dans frontend/static/
STATICFILES_DIRS = [os.path.join(BASE_DIR, '../frontend/static')]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# URLs de redirection pour l'authentification
LOGIN_URL = 'connexion'          # nom de l'URL de connexion
LOGIN_REDIRECT_URL = 'dash'      # après connexion, rediriger vers le tableau de bord
LOGOUT_REDIRECT_URL = 'accueil'  # après déconnexion, retour à l'accueil