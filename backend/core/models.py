from django.db import models
from django.contrib.auth.models import User  # On garde le User Django

# ---------- PROFIL UTILISATEUR ----------
class Profile(models.Model):
    NIVEAU_CHOICES = [
        ('L1', 'Licence 1'),
        ('L2', 'Licence 2'),
        ('L3', 'Licence 3'),
        ('M1', 'Master 1'),
        ('M2', 'Master 2'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    avatar_url = models.URLField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    niveau_etude = models.CharField(max_length=2, choices=NIVEAU_CHOICES)
    filiere = models.CharField(max_length=100)          # Ex: "Génie Logiciel"
    matricule = models.CharField(max_length=20, unique=True, blank=True, null=True)

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


# ---------- COMPÉTENCES MENTOR (OFFRE) ----------
class MentorSkill(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
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
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    priority_level = models.CharField(max_length=6, choices=PRIORITY_CHOICES, default='MEDIUM')

    class Meta:
        unique_together = ('profile', 'skill')

    def __str__(self):
        return f"{self.profile.user.username} cherche {self.skill.name}"


# ---------- MESSAGERIE ----------
class Conversation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ConversationMember(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('conversation', 'user')

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]


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