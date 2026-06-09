"""
Configuration des URLs du projet.
On inclut les URLs de l'application 'core' et celles d'authentification.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # toutes les pages de notre application
]