"""
Routes de l'application core : associe chaque URL à une vue.
"""
from django.urls import path
from . import views

urlpatterns = [
    # === Pages publiques & Authentification ===
    path('', views.accueil, name='accueil'),
    path('connexion/', views.connexion, name='connexion'),
    path('inscription/', views.inscription, name='inscription'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),

    # === Tableau de bord & Profil ===
    path('dash/', views.dash, name='dash'),
    path('profil/', views.profil, name='profil'),

    # === Offres et Demandes de Mentorat ===
    path('annonces/', views.offres_demandes, name='offres_demandes'),
    path('annonces/supprimer/<int:annonce_id>/', views.supprimer_annonce, name='supprimer_annonce'),

    # === Messagerie & Conversations ===
    path('messagerie/', views.messagerie, name='messagerie'),
    path('messagerie/<int:pk>/', views.conversation_detail, name='conversation_detail'),
    path('messagerie/start/<int:user_id>/', views.conversation_start, name='conversation_start'),

    # ─── Matching Avancé ───
    path('matching/', views.matching_avance, name='matching_avance'),
    path('api/matching/', views.matching_api, name='matching_api'),

    # === Gamification (Badges) ===
    path('badges/', views.badges_view, name='badges'),
]