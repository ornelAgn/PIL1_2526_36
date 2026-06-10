from django.db import models
from django.contrib.auth.models import User

# ---------- PROFIL UTILISATEUR ----------
class Profile(models.Model):
    NIVEAU_CHOICES = [
        ('L1', 'Licence 1'), ('L2', 'Licence 2'), ('L3', 'Licence 3'),
        ('M1', 'Master 1'), ('M2', 'Master 2'),
    ]
    
    FORMAT_CHOICES = [
        ('PRESENTIEL', 'Présentiel uniquement'),
        ('EN_LIGNE', 'En ligne uniquement'),
        ('LES_DEUX', 'Présentiel et En ligne'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, help_text="Courte présentation et centres d'intérêt académiques")
    
    # Remplacement de avatar_url par un vrai champ image
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True) 
    phone = models.CharField(max_length=20, blank=True, null=True)

    niveau_etude = models.CharField(max_length=2, choices=NIVEAU_CHOICES)
    filiere = models.CharField(max_length=100)
    matricule = models.CharField(max_length=20, unique=True, blank=True, null=True)

    # Nouveaux champs pour le cahier des charges
    disponibilites = models.CharField(max_length=255, blank=True, null=True, help_text="Ex: En soirée après 18h, le week-end...")
    format_preference = models.CharField(max_length=15, choices=FORMAT_CHOICES, default='LES_DEUX')

    is_mentor = models.BooleanField(default=False)
    is_mentee = models.BooleanField(default=True)

    total_sessions_as_mentor = models.IntegerField(default=0)
    total_sessions_as_mentee = models.IntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} ({self.niveau_etude} {self.filiere})"
    

# ---------- COMPÉTENCES ----------
class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100)          # Ex: "Programmation", "Réseaux"
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class MentorSkill(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='mentor_skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    years_experience = models.IntegerField(default=0)

    class Meta:
        unique_together = ('profile', 'skill')

    def __str__(self):
        return f"{self.profile.user.username} enseigne {self.skill.name}"


# ---------- COMPÉTENCES MENTORÉ (DEMANDE) ----------
class MenteeSkill(models.Model):
    PRIORITY_CHOICES = [
        ('LOW', 'Faible'),
        ('MEDIUM', 'Moyenne'),
        ('HIGH', 'Élevée'),
    ]
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='mentee_skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    priority_level = models.CharField(max_length=6, choices=PRIORITY_CHOICES, default='MEDIUM')

    class Meta:
        unique_together = ('profile', 'skill')

    def __str__(self):
        return f"{self.profile.user.username} cherche {self.skill.name}"
# ---------- MESSAGERIE ----------
class Conversation(models.Model):
    # Suppression du ManyToMany participants → on utilise ConversationMember
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation {self.id}"


class ConversationMember(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('conversation', 'user')   # un utilisateur ne peut rejoindre qu'une fois

    def __str__(self):
        return f"{self.user.username} dans la conversation {self.conversation.id}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message de {self.sender.username}"


# ---------- SESSIONS DE MENTORAT ----------
class MentorshipSession(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('ACCEPTED', 'Acceptée'),
        ('REJECTED', 'Refusée'),
        ('COMPLETED', 'Terminée'),
        ('CANCELLED', 'Annulée'),
    ]
    mentor = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='mentored_sessions')
    mentee = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='learnt_sessions')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)

    scheduled_at = models.DateTimeField()
    duration_minutes = models.IntegerField(default=60)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    meeting_link = models.URLField(blank=True, null=True)
    session_notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


# ---------- REVIEWS (ÉVALUATIONS) ----------
class Review(models.Model):
    session = models.OneToOneField(MentorshipSession, on_delete=models.CASCADE)
    mentor = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='reviews_received')
    mentee = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='reviews_given')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


# ---------- BADGES ----------
class Badge(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon_class = models.CharField(max_length=50, default='default-badge')


class UserBadge(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('profile', 'badge')

class Annonce(models.Model):
    TYPE_CHOICES = [
        ('OFFRE', 'Offre de Mentorat (Je propose mon aide / Mentor)'),
        ('DEMANDE', 'Demande de Mentorat (Je cherche de l\'aide / Apprenant)'),
    ]
    
    FORMAT_CHOICES = [
        ('PRESENTIEL', 'Présentiel'),
        ('EN_LIGNE', 'En ligne'),
        ('LES_DEUX', 'Présentiel et En ligne'),
    ]

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='annonces')
    type_annonce = models.CharField(max_length=10, choices=TYPE_CHOICES)
    matiere = models.CharField(max_length=100, help_text="Ex: Langage C, Administration Windows, Probabilités")
    disponibilites = models.CharField(max_length=255, help_text="Ex: Les week-ends, Soirs après 18h")
    format_cours = models.CharField(max_length=15, choices=FORMAT_CHOICES, default='LES_DEUX')
    description = models.TextField(blank=True, help_text="Précisez votre besoin ou vos compétences particulières...")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.type_annonce}] {self.matiere} par {self.profile.user.username}"