"""
═══════════════════════════════════════════════════════════════════════════════
ALGORITHME DE MATCHING IFRI MENTOR
═══════════════════════════════════════════════════════════════════════════════

Calcule un score de compatibilité entre un apprenant (mentee) et un mentor
basé sur :
  1. Compétences / matières en commun (40%)
  2. Disponibilités communes (30%)
  3. Proximité filière & niveau d'étude (20%)
  4. Popularité / expérience du mentor (10%)

Score final : 0 à 100
"""

from difflib import SequenceMatcher
import math


# ─── Pondération des critères ───
WEIGHTS = {
    'skills': 0.40,       # Compétences en commun
    'availability': 0.30,  # Disponibilités communes
    'academic': 0.20,      # Filière + niveau
    'experience': 0.10,    # Sessions & note
}


def normalize_text(text):
    """Normalise un texte pour comparaison."""
    if not text:
        return ""
    return text.lower().strip().replace(" ", "_").replace("-", "_")


def jaccard_similarity(set_a, set_b):
    """Calcule la similarité de Jaccard entre deux ensembles."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def string_similarity(str1, str2):
    """Similarité entre deux chaînes (0 à 1)."""
    if not str1 or not str2:
        return 0.0
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def parse_disponibilites(dispo_str):
    """
    Parse une chaîne de disponibilités en ensemble normalisé.
    Ex: "Lundi Soir, Mercredi Aprem" -> {"lundi_soir", "mercredi_aprem"}
    """
    if not dispo_str:
        return set()

    result = set()
    for part in dispo_str.lower().split(','):
        part = part.strip()
        if not part:
            continue
        normalized = part.replace(" ", "_").replace("-", "_")
        result.add(normalized)

    return result


def calculer_score_skills(mentee_skills, mentor_skills):
    """
    Score basé sur les compétences en commun.
    mentee_skills : QuerySet de MenteeSkill
    mentor_skills : QuerySet de MentorSkill
    """
    if not mentee_skills.exists() or not mentor_skills.exists():
        return 0.0

    # Ensemble des noms de compétences
    mentee_set = set(normalize_text(ms.skill.name) for ms in mentee_skills)
    mentor_set = set(normalize_text(ms.skill.name) for ms in mentor_skills)

    # Similarité de Jaccard
    similarity = jaccard_similarity(mentee_set, mentor_set)

    # Bonus si correspondance exacte sur une compétence recherchée en HIGH priority
    high_priority_skills = set(
        normalize_text(ms.skill.name) 
        for ms in mentee_skills.filter(priority_level='HIGH')
    )
    if high_priority_skills & mentor_set:
        similarity = min(1.0, similarity + 0.15)

    return similarity


def calculer_score_disponibilites(mentee_dispo, mentor_dispo):
    """
    Score basé sur les disponibilités communes.
    """
    mentee_set = parse_disponibilites(mentee_dispo)
    mentor_set = parse_disponibilites(mentor_dispo)

    if not mentee_set or not mentor_set:
        return 0.5  # Neutre si pas renseigné

    return jaccard_similarity(mentee_set, mentor_set)


def calculer_score_academic(mentee_profile, mentor_profile):
    """
    Score basé sur la proximité académique (filière + niveau).
    """
    score = 0.0

    # Filière (60% du score académique)
    filiere_sim = string_similarity(mentee_profile.filiere, mentor_profile.filiere)
    score += filiere_sim * 0.6

    # Niveau d'étude (40% du score académique)
    niveau_order = {'L1': 1, 'L2': 2, 'L3': 3, 'M1': 4, 'M2': 5}
    mentee_niveau = niveau_order.get(mentee_profile.niveau_etude, 0)
    mentor_niveau = niveau_order.get(mentor_profile.niveau_etude, 0)

    if mentee_niveau and mentor_niveau:
        niveau_diff = abs(mentee_niveau - mentor_niveau)
        if mentor_niveau > mentee_niveau:
            # Mentor plus avancé = idéal
            niveau_score = max(0, 1.0 - (niveau_diff * 0.2))
        else:
            # Mentor au même niveau ou moins = moins idéal
            niveau_score = max(0, 0.6 - (niveau_diff * 0.3))
        score += niveau_score * 0.4
    else:
        score += 0.2

    return score


def calculer_score_experience(mentor_profile):
    """
    Score basé sur l'expérience du mentor (sessions + note).
    """
    score = 0.0

    # Note moyenne (0-5) -> normalisé sur 0-0.6
    rating = float(mentor_profile.average_rating or 0)
    score += min(rating / 5.0, 1.0) * 0.6

    # Nombre de sessions (logarithmique)
    sessions = mentor_profile.total_sessions_as_mentor or 0
    score += min(math.log10(sessions + 1) / 2.0, 1.0) * 0.4

    return score


def calculer_score_matching(mentee_profile, mentor_profile):
    """
    Calcule le score global de matching entre un apprenant et un mentor.

    Retourne un dictionnaire avec :
        - score_total : score global (0-100)
        - details : détail par critère
        - common_skills : liste des compétences en commun
        - common_dispos : liste des disponibilités communes
    """
    # ─── Skills ───
    mentee_skills = mentee_profile.mentee_skills.select_related('skill')
    mentor_skills = mentor_profile.mentor_skills.select_related('skill')
    score_skills = calculer_score_skills(mentee_skills, mentor_skills)

    # Compétences communes pour affichage
    mentee_skill_names = {normalize_text(ms.skill.name): ms.skill.name for ms in mentee_skills}
    mentor_skill_names = {normalize_text(ms.skill.name): ms.skill.name for ms in mentor_skills}
    common_skills = [
        mentee_skill_names[k] 
        for k in set(mentee_skill_names.keys()) & set(mentor_skill_names.keys())
    ]

    # ─── Disponibilités ───
    score_dispo = calculer_score_disponibilites(
        mentee_profile.disponibilites,
        mentor_profile.disponibilites
    )

    mentee_dispos = parse_disponibilites(mentee_profile.disponibilites)
    mentor_dispos = parse_disponibilites(mentor_profile.disponibilites)
    common_dispos = list(mentee_dispos & mentor_dispos)

    # ─── Académique ───
    score_academic = calculer_score_academic(mentee_profile, mentor_profile)

    # ─── Expérience ───
    score_exp = calculer_score_experience(mentor_profile)

    # ─── Score global pondéré ───
    score_total = (
        score_skills * WEIGHTS['skills'] +
        score_dispo * WEIGHTS['availability'] +
        score_academic * WEIGHTS['academic'] +
        score_exp * WEIGHTS['experience']
    )

    # Convertir en pourcentage (0-100)
    score_total = round(score_total * 100, 1)

    return {
        'score_total': score_total,
        'details': {
            'skills': {
                'score': round(score_skills * 100, 1),
                'weight': WEIGHTS['skills'],
                'contribution': round(score_skills * WEIGHTS['skills'] * 100, 1),
            },
            'availability': {
                'score': round(score_dispo * 100, 1),
                'weight': WEIGHTS['availability'],
                'contribution': round(score_dispo * WEIGHTS['availability'] * 100, 1),
            },
            'academic': {
                'score': round(score_academic * 100, 1),
                'weight': WEIGHTS['academic'],
                'contribution': round(score_academic * WEIGHTS['academic'] * 100, 1),
            },
            'experience': {
                'score': round(score_exp * 100, 1),
                'weight': WEIGHTS['experience'],
                'contribution': round(score_exp * WEIGHTS['experience'] * 100, 1),
            },
        },
        'common_skills': common_skills,
        'common_dispos': common_dispos,
    }


def trouver_meilleurs_mentors(mentee_profile, limit=10, min_score=20.0):
    """
    Trouve les meilleurs mentors pour un apprenant donné.

    Args:
        mentee_profile : Profile de l'apprenant
        limit : Nombre maximum de résultats
        min_score : Score minimum pour être inclus (0-100)

    Returns:
        Liste de tuples (mentor_profile, resultat_matching) triée par score décroissant
    """
    from .models import Profile

    # Récupérer tous les mentors actifs (sauf soi-même)
    mentors = Profile.objects.filter(
        is_mentor=True
    ).exclude(
        user=mentee_profile.user
    ).select_related(
        'user'
    ).prefetch_related(
        'mentor_skills__skill'
    )

    resultats = []
    for mentor in mentors:
        matching = calculer_score_matching(mentee_profile, mentor)
        if matching['score_total'] >= min_score:
            resultats.append((mentor, matching))

    # Trier par score décroissant
    resultats.sort(key=lambda x: x[1]['score_total'], reverse=True)

    return resultats[:limit]