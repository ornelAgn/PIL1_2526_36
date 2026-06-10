"""
Vues (controllers) : logique métier reliant les templates au backend.
"""
from django.shortcuts import render, redirect, get_object_or_404

from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import InscriptionForm, ConnexionForm
from .models import Profile, MentorshipSession, Conversation, ConversationMember, Message,Badge, UserBadge
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.forms import AuthenticationForm



def accueil(request):
    """Page d'accueil publique."""
    return render(request, 'accueil.html')

def inscription(request):
    """Vue d'inscription : crée un compte utilisateur."""
    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            user = form.save()                     # sauvegarde l'utilisateur en base
            login(request, user)                   # connecte automatiquement
            messages.success(request, "Compte créé avec succès !")
            return redirect('dash')                # redirige vers le tableau de bord
    else:
        form = InscriptionForm()
    return render(request, 'inscription.html', {'form': form})

def connexion(request):
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
def deconnexion(request):
    """Déconnecte l'utilisateur et retourne à l'accueil."""
    logout(request)
    messages.info(request, "Vous avez été déconnecté.")
    return redirect('accueil')

@login_required
def dash(request):
    profile = request.user.profile  # grâce au OneToOne

    # Récupérer tous les mentors actifs (pour l'affichage côté apprenant)
    mentors = Profile.objects.filter(is_mentor=True).select_related('user')[:8]  # limite 8

    # Sessions à venir pour l'utilisateur (qu'il soit mentor ou mentoré)
    upcoming_sessions = MentorshipSession.objects.filter(
        Q(mentor=profile) | Q(mentee=profile),
        status__in=['PENDING', 'ACCEPTED'],
        scheduled_at__gte=timezone.now()
    ).order_by('scheduled_at')[:5]

    # Nombre de mentors total (pour affichage)
    mentors_count = Profile.objects.filter(is_mentor=True).count()

    context = {
        'profile': profile,
        'mentors': mentors,
        'upcoming_sessions': upcoming_sessions,
        'mentors_count': mentors_count,
    }
    return render(request, 'dash.html', context)

@login_required
def messagerie(request):
    """Liste les conversations de l'utilisateur connecté"""
    conversations = Conversation.objects.filter(
        conversationmember__user=request.user
    ).distinct().order_by('-updated_at')

    return render(request, 'messagerie.html', {
        'conversations': conversations
    })

@login_required
def conversation_detail(request, conversation_id):
    """Affiche une conversation et ses messages"""
    conversation = get_object_or_404(Conversation, id=conversation_id)
    # Vérifier que l'utilisateur est membre
    if not ConversationMember.objects.filter(conversation=conversation, user=request.user).exists():
        return redirect('messagerie')
    
    messages_list = Message.objects.filter(conversation=conversation).order_by('created_at')
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
            return redirect('conversation_detail', conversation_id=conversation.id)

    return render(request, 'conversation_detail.html', {
        'conversation': conversation,
        'messages_list': messages_list
    })

@login_required
def badges_view(request):
    """Liste les badges gagnés par l'utilisateur"""
    profile = request.user.profile
    user_badges = UserBadge.objects.filter(profile=profile).select_related('badge')
    all_badges = Badge.objects.all()  # Pour afficher ceux non acquis

    return render(request, 'badges.html', {
        'user_badges': user_badges,
        'all_badges': all_badges,
    })

@login_required
def profil(request):
    profile = request.user.profile
    return render(request, 'profil.html', {'profile': profile})