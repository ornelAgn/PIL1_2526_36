"""
Routes de l'application core : associe chaque URL à une vue.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.accueil, name='accueil'),
    path('connexion/', views.connexion, name='connexion'),
    path('inscription/', views.inscription, name='inscription'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    path('dash/', views.dash, name='dash'),
    path('messagerie/', views.messagerie, name='messagerie'),
    path('messagerie/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('badges/', views.badges_view, name='badges'),
    path('profil/', views.profil, name='profil'),
]