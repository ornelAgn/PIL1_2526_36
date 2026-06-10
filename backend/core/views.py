"""
Vues (controllers) : logique métier reliant les templates au backend.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse

from .forms import InscriptionForm, UserUpdateForm, ProfileUpdateForm, AnnonceForm
from .models import (
    Profile, MentorshipSession, Conversation, ConversationMember,
    Message, Badge, UserBadge, Annonce
)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGES PUBLIQUES
# ═══════════════════════════════════════════════════════════════════════════════

def accueil(request):
    """Page d'accueil publique."""
    return render(request, 'accueil.html')


# ═══════════════════════════════════════════════════════════════════════════════
# AUTHENTIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

def inscription(request):
    """Vue d'inscription : crée un compte utilisateur."""
    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Compte créé avec succès !")
            return redirect('dash')
    else:
        form = InscriptionForm()
    return render(request, 'inscription.html', {'form': form})


def connexion(request):
    """Vue de connexion."""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Bienvenue, {user.username} !")
            return redirect('dash')
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe invalide.")
    else:
        form = AuthenticationForm()
    return render(request, 'connexion.html', {'form': form})


@login_required
def deconnexion(request):
    """Déconnecte l'utilisateur et retourne à l'accueil."""
    logout(request)
    messages.info(request, "Vous avez été déconnecté.")
    return redirect('accueil')


# ═══════════════════════════════════════════════════════════════════════════════
# TABLEAU DE BORD
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def dash(request):
    """
    Tableau de bord principal avec switcher Apprenant / Mentor.
    """
    profile = request.user.profile

    # ─── TRAITEMENT DU FORMULAIRE : DEVENIR MENTOR ───
    if request.method == 'POST' and request.POST.get('action') == 'devenir_mentor':
        profile.is_mentor = True
        profile.save()
        messages.success(request, '🎉 Félicitations ! Votre profil mentor est maintenant actif.')
        return redirect('dash')

    # ─── RECHERCHE ───
    query = request.GET.get('q', '').strip()

    # ─── LISTE DES MENTORS ───
    mentors = Profile.objects.filter(
        is_mentor=True
    ).exclude(
        user=request.user
    ).select_related(
        'user'
    ).prefetch_related(
        'mentor_skills__skill'
    ).annotate(
        mentor_skill_count=Count('mentor_skills')
    )

    # Filtre par recherche textuelle
    if query:
        mentors = mentors.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(mentor_skills__skill__name__icontains=query) |
            Q(filiere__icontains=query)
        ).distinct()

    # ─── SESSIONS À VENIR ───
    upcoming_sessions = MentorshipSession.objects.filter(
        Q(mentor=profile) | Q(mentee=profile),
        status__in=['PENDING', 'ACCEPTED'],
        scheduled_at__gte=timezone.now()
    ).select_related(
        'skill', 'mentor__user', 'mentee__user'
    ).order_by('scheduled_at')[:10]

    # ─── COMPTEURS ───
    mentors_count = Profile.objects.filter(is_mentor=True).exclude(user=request.user).count()

    context = {
        'profile': profile,
        'mentors': mentors,
        'mentors_count': mentors_count,
        'upcoming_sessions': upcoming_sessions,
        'search_query': query,
    }
    return render(request, 'dash.html', context)


# ═══════════════════════════════════════════════════════════════════════════════
# MATCHING AVANCÉ
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def matching_avance(request):
    """
    Page de recherche avancée avec algorithme de matching.
    Affiche les mentors les plus compatibles avec l'apprenant connecté.
    """
    profile = request.user.profile

    # Vérifier que l'utilisateur est bien un apprenant
    if not profile.is_mentee:
        messages.warning(request, 'Vous devez être enregistré comme apprenant pour utiliser le matching.')
        return redirect('dash')

    # Récupérer les résultats du matching
    from .matching import trouver_meilleurs_mentors
    resultats = trouver_meilleurs_mentors(profile, limit=12, min_score=15.0)

    return render(request, 'matching_avance.html', {
        'profile': profile,
        'resultats': resultats,
        'total_mentors': len(resultats),
    })


@login_required
def matching_api(request):
    """
    API JSON pour le matching (pour AJAX ou applications externes).
    """
    profile = request.user.profile
    limit = int(request.GET.get('limit', 10))
    min_score = float(request.GET.get('min_score', 15.0))

    from .matching import trouver_meilleurs_mentors
    resultats = trouver_meilleurs_mentors(profile, limit=limit, min_score=min_score)

    data = []
    for mentor, matching in resultats:
        data.append({
            'mentor_id': mentor.user.id,
            'nom': mentor.user.last_name,
            'prenom': mentor.user.first_name,
            'username': mentor.user.username,
            'filiere': mentor.filiere,
            'niveau': mentor.niveau_etude,
            'avatar_initials': mentor.initials,
            'score_compatibilite': matching['score_total'],
            'competences_communes': matching['common_skills'],
            'disponibilites_communes': matching['common_dispos'],
            'details': matching['details'],
            'note': float(mentor.average_rating),
            'sessions': mentor.total_sessions_as_mentor,
        })

    return JsonResponse({
        'success': True,
        'count': len(data),
        'results': data,
    })


# ═══════════════════════════════════════════════════════════════════════════════
# MESSAGERIE
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def messagerie(request):
    """Liste les conversations de l'utilisateur connecté."""
    conversations = Conversation.objects.filter(
        members__user=request.user
    ).distinct().order_by('-updated_at')

    return render(request, 'messagerie.html', {
        'conversations': conversations
    })

@login_required
def conversation_detail(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk)

    # Vérifier que l'utilisateur est bien membre
    if not ConversationMember.objects.filter(
        conversation=conversation, user=request.user
    ).exists():
        return redirect('messagerie')

    messages_list = Message.objects.filter(
        conversation=conversation
    ).order_by('created_at')

    # Récupérer l'autre participant (pour le nom dans le header)
    other_member = ConversationMember.objects.filter(
        conversation=conversation
    ).exclude(user=request.user).first()
    other_participant = other_member.user if other_member else None

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
            return redirect('conversation_detail', pk=conversation.pk)

    return render(request, 'conversation_detail.html', {
        'conversation': conversation,
        'messages_list': messages_list,
        'other_participant': other_participant,
    })

@login_required
def conversation_start(request, user_id):
    """Démarre ou redirige vers une conversation existante entre l'utilisateur et un autre."""
    other_user = get_object_or_404(User, id=user_id)

    # Chercher une conversation existante contenant exactement les deux utilisateurs
    conversation = Conversation.objects.annotate(
        num_members=Count('members')
    ).filter(
        num_members=2,
        members__user=request.user
    ).filter(
        members__user=other_user
    ).first()

    if not conversation:
        conversation = Conversation.objects.create()
        ConversationMember.objects.create(conversation=conversation, user=request.user)
        ConversationMember.objects.create(conversation=conversation, user=other_user)

    return redirect('conversation_detail', pk=conversation.pk)
# ═══════════════════════════════════════════════════════════════════════════════
# BADGES
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def badges_view(request):
    """Liste les badges gagnés par l'utilisateur."""
    profile = request.user.profile
    user_badges = UserBadge.objects.filter(profile=profile).select_related('badge')
    all_badges = Badge.objects.all()

    return render(request, 'badges.html', {
        'user_badges': user_badges,
        'all_badges': all_badges,
    })


# ═══════════════════════════════════════════════════════════════════════════════
# PROFIL
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def profil(request):
    """Page de profil avec formulaire de modification."""
    # Sécurité : S'assurer que le profil existe, sinon le créer
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Votre profil a été mis à jour avec succès !')
            return redirect('profil')
        else:
            # Debug
            print("\n====== ERREURS DE VALIDATION ======")
            if u_form.errors:
                print("Erreurs User :", u_form.errors.as_data())
            if p_form.errors:
                print("Erreurs Profile :", p_form.errors.as_data())
            print("=====================================\n")
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=profile)

    context = {
        'u_form': u_form,
        'p_form': p_form,
        'profile': profile
    }
    return render(request, 'profil.html', context)


# ═══════════════════════════════════════════════════════════════════════════════
# ANNONCES (OFFRES & DEMANDES)
# ═══════════════════════════════════════════════════════════════════════════════

@login_required
def offres_demandes(request):
    """Page des annonces : création et liste des annonces de l'utilisateur."""
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = AnnonceForm(request.POST)
        if form.is_valid():
            annonce = form.save(commit=False)
            annonce.profile = profile
            annonce.save()
            messages.success(request, 'Annonce publiée avec succès !')
            return redirect('offres_demandes')
    else:
        form = AnnonceForm()

    # Récupérer uniquement les annonces publiées par l'utilisateur connecté
    mes_annonces = Annonce.objects.filter(profile=profile).order_by('-created_at')

    return render(request, 'offres_demandes.html', {
        'form': form,
        'mes_annonces': mes_annonces
    })


@login_required
def supprimer_annonce(request, annonce_id):
    """Supprime une annonce de l'utilisateur connecté."""
    profile = request.user.profile
    annonce = get_object_or_404(Annonce, id=annonce_id, profile=profile)
    annonce.delete()
    messages.success(request, 'Annonce supprimée.')
    return redirect('offres_demandes')