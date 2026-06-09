-- =========================================================================
-- Schéma de Base de Données pour la Plateforme "IFRI Mentor"
-- Compatible MySQL / PostgreSQL (avec ajustements mineurs de types)
-- =========================================================================

-- 1. TABLE DES UTILISATEURS (COMPTE / AUTHENTIFICATION)
-- Note : Si vous utilisez Django, Django génère sa propre table `auth_user`.
-- Ce schéma est conçu pour s'y coupler via une clé étrangère.
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(150) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL, -- Stocke le mot de passe hashé (bcrypt/argon2)
    date_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    is_staff BOOLEAN DEFAULT FALSE
);

-- 2. TABLE DES PROFILS UTILISATEURS
-- Contient les informations académiques spécifiques à l'IFRI et les préférences de rôle.
CREATE TABLE IF NOT EXISTS profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    bio TEXT,
    avatar_url VARCHAR(255) NULL, -- Lien vers l'image de profil ou NULL pour utiliser les initiales
    phone VARCHAR(20) NULL,
    
    -- Informations Académiques IFRI
    niveau_etude ENUM('L1', 'L2', 'L3', 'M1', 'M2') NOT NULL, -- Licence 1 à Master 2
    filiere VARCHAR(100) NOT NULL, -- Ex: "Génie Logiciel", "Systèmes et Réseaux", "Sécurité"
    matricule VARCHAR(20) UNIQUE NULL, -- Optionnel : matricule étudiant de l'UAC
    
    -- Rôles (un étudiant peut être l'un, l'autre ou les deux)
    is_mentor BOOLEAN DEFAULT FALSE,
    is_mentee BOOLEAN DEFAULT TRUE,
    
    -- Statistiques pour l'algorithme et l'affichage
    total_sessions_as_mentor INT DEFAULT 0,
    total_sessions_as_mentee INT DEFAULT 0,
    average_rating DECIMAL(3, 2) DEFAULT 0.00, -- Moyenne des notes reçues sur 5.00
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 3. GESTION DES COMPÉTENCES ET MATIÈRES (SKILLS)
-- Table de référence des matières enseignées à l'IFRI (ex: Python, Algorithmique, SQL...)
CREATE TABLE IF NOT EXISTS skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(100) NOT NULL, -- Ex: "Programmation", "Base de données", "Mathématiques", "Réseaux"
    description TEXT NULL
);

-- 4. TABLE D'ASSOCIATION : COMPÉTENCES PROPOSÉES PAR LES MENTORS (OFFRE)
-- Les matières dans lesquelles l'étudiant excelle et souhaite aider.
CREATE TABLE IF NOT EXISTS profile_mentor_skills (
    profile_id INT NOT NULL,
    skill_id INT NOT NULL,
    years_experience INT DEFAULT 0, -- Niveau d'expérience ou aisance dans la matière
    PRIMARY KEY (profile_id, skill_id),
    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

-- 5. TABLE D'ASSOCIATION : COMPÉTENCES RECHERCHÉES PAR LES MENTORÉS (DEMANDE)
-- Les matières pour lesquelles l'étudiant a besoin d'assistance.
CREATE TABLE IF NOT EXISTS profile_mentee_skills (
    profile_id INT NOT NULL,
    skill_id INT NOT NULL,
    priority_level ENUM('LOW', 'MEDIUM', 'HIGH') DEFAULT 'MEDIUM', -- Degré d'urgence du besoin
    PRIMARY KEY (profile_id, skill_id),
    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

-- =========================================================================
-- SYSTÈME DE MESSAGERIE ET CONVERSATIONS (MESSAGING)
-- =========================================================================

-- 6. TABLE DES CONVERSATIONS (CANAUX)
-- Regroupe deux ou plusieurs utilisateurs pour discuter.
CREATE TABLE IF NOT EXISTS conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 7. TABLE DES MEMBRES D'UNE CONVERSATION
-- Permet de lier les utilisateurs aux conversations (gère le chat direct et les groupes potentiels)
CREATE TABLE IF NOT EXISTS conversation_members (
    conversation_id INT NOT NULL,
    user_id INT NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (conversation_id, user_id),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 8. TABLE DES MESSAGES
-- Contient l'historique complet des messages envoyés au sein des conversations.
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conversation_id INT NOT NULL,
    sender_id INT NOT NULL,
    content TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE, -- Statut de lecture par le destinataire
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
);

-- =========================================================================
-- SYSTÈME DE MENTORAT, SESSIONS ET EVALUATIONS
-- =========================================================================

-- 9. SESSIONS DE MENTORAT (RENDEZ-VOUS ACADÉMIQUES)
CREATE TABLE IF NOT EXISTS mentorship_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mentor_id INT NOT NULL, -- Référence au profil du Mentor
    mentee_id INT NOT NULL, -- Référence au profil de l'Apprenant/Mentoré
    skill_id INT NOT NULL,  -- La matière concernée par cette session spécifique
    
    scheduled_at DATETIME NOT NULL, -- Date et heure programmée du cours/session
    duration_minutes INT DEFAULT 60, -- Durée estimée en minutes
    
    -- État de la session
    status ENUM('PENDING', 'ACCEPTED', 'REJECTED', 'COMPLETED', 'CANCELLED') DEFAULT 'PENDING',
    
    meeting_link VARCHAR(255) NULL, -- Lien de visioconférence (Google Meet, Teams, Zoom...)
    session_notes TEXT NULL,        -- Compte rendu ou notes prises par le mentor pour l'étudiant
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (mentor_id) REFERENCES profiles(id) ON DELETE CASCADE,
    FOREIGN KEY (mentee_id) REFERENCES profiles(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

-- 10. REVIEWS (ÉVALUATIONS ET AVIS)
-- Permet aux mentorés de noter et de laisser un avis sur leur session avec un mentor.
CREATE TABLE IF NOT EXISTS reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL UNIQUE, -- Une seule évaluation autorisée par session de mentorat
    mentor_id INT NOT NULL,         -- Stockage direct pour optimiser les requêtes d'agrégation de notes
    mentee_id INT NOT NULL,
    
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5), -- Note de 1 à 5 étoiles
    comment TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (session_id) REFERENCES mentorship_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (mentor_id) REFERENCES profiles(id) ON DELETE CASCADE,
    FOREIGN KEY (mentee_id) REFERENCES profiles(id) ON DELETE CASCADE
);

-- =========================================================================
-- GAMIFICATION ET RÉCOMPENSES (SYSTÈME DE BADGES)
-- =========================================================================

-- 11. TABLE DES BADGES DISPONIBLES
CREATE TABLE IF NOT EXISTS badges (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE, -- Ex: "Super Mentor", "Code Guru", "Toujours Ponctuel"
    description TEXT NOT NULL,
    icon_class VARCHAR(50) DEFAULT 'default-badge', -- Classe CSS ou icône SVG à afficher
    points_required INT DEFAULT 0 -- Si vous utilisez un système de points d'expérience (XP)
);

-- 12. ASSIGNATION DES BADGES AUX PROFILÉS (ACQUISITIONS)
CREATE TABLE IF NOT EXISTS user_badges (
    profile_id INT NOT NULL,
    badge_id INT NOT NULL,
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (profile_id, badge_id),
    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE,
    FOREIGN KEY (badge_id) REFERENCES badges(id) ON DELETE CASCADE
);

-- =========================================================================
-- INDEX DE PERFORMANCE (OPTIMISATION DU FILTRAGE ET DE LA RECHERCHE AVANCÉE)
-- =========================================================================

-- Index pour accélérer la recherche des mentors par matière enseignée
CREATE INDEX idx_mentor_skills_skill ON profile_mentor_skills(skill_id);
CREATE INDEX idx_mentor_skills_profile ON profile_mentor_skills(profile_id);

-- Index pour accélérer la recherche par niveau d'étude ou filière (pour l'algorithme)
CREATE INDEX idx_profile_academic_info ON profiles(niveau_etude, filiere);

-- Index pour la recherche rapide des rôles
CREATE INDEX idx_profile_roles ON profiles(is_mentor, is_mentee);

-- Index pour trier rapidement les mentors par popularité/note
CREATE INDEX idx_profile_ratings ON profiles(average_rating, total_sessions_as_mentor);

-- Index pour accélérer le chargement de l'historique des messages par date
CREATE INDEX idx_messages_conversation_date ON messages(conversation_id, created_at DESC);