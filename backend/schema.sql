-- ==============================================================================
-- PROJET : Plateforme de Mentorat IFRI (Type Superprof)
-- SGBD Recommandé : PostgreSQL
-- ==============================================================================

-- Suppression des tables existantes pour repartir à zéro
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;
DROP TABLE IF EXISTS avis CASCADE;
DROP TABLE IF EXISTS sessions_mentorat CASCADE;
DROP TABLE IF EXISTS annonces CASCADE;
DROP TABLE IF EXISTS competences CASCADE;
DROP TABLE IF EXISTS matieres CASCADE;
DROP TABLE IF EXISTS utilisateurs CASCADE;

-- ==============================================================================
-- 1. TABLE UTILISATEURS (Étudiants de l'IFRI)
-- Modifiée pour faciliter la personnalisation du Dashboard
-- ==============================================================================
CREATE TABLE utilisateurs (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    mot_de_passe VARCHAR(255) NOT NULL, -- Géré et sécurisé par Django
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    matricule VARCHAR(50) UNIQUE, -- Spécifique IFRI
    filiere VARCHAR(50) CHECK (filiere IN ('GL', 'IM', 'SI', 'AS', 'Autre')), -- Filières de l'IFRI
    niveau_etude VARCHAR(10) CHECK (niveau_etude IN ('L1', 'L2', 'L3', 'M1', 'M2')),
    bio TEXT, 
    photo_profil VARCHAR(255), 
    
    -- Pour le Dashboard unique : permet de mémoriser le dernier mode utilisé
    mode_dashboard_prefere VARCHAR(20) DEFAULT 'MENTORE' CHECK (mode_dashboard_prefere IN ('MENTOR', 'MENTORE')),
    
    date_inscription TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    est_actif BOOLEAN DEFAULT TRUE
);

-- ==============================================================================
-- 2. TABLE MATIERES (Cours de l'IFRI)
-- ==============================================================================
CREATE TABLE matieres (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(150) UNIQUE NOT NULL, -- ex: "Architecture des Ordinateurs"
    code_ue VARCHAR(20), -- ex: "UE-GL310"
    description TEXT,
    semestre VARCHAR(10) CHECK (semestre IN ('S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9', 'S10'))
);

-- ==============================================================================
-- 3. TABLE COMPETENCES (Algorithme de filtrage avancé)
-- ==============================================================================
CREATE TABLE competences (
    id SERIAL PRIMARY KEY,
    utilisateur_id INT REFERENCES utilisateurs(id) ON DELETE CASCADE,
    matiere_id INT REFERENCES matieres(id) ON DELETE CASCADE,
    role VARCHAR(20) CHECK (role IN ('MENTOR', 'MENTORE')), -- Offre ou demande de l'aide
    niveau_maitrise INT CHECK (niveau_maitrise BETWEEN 1 AND 5), -- Échelle de niveau
    description_specifique TEXT,
    UNIQUE (utilisateur_id, matiere_id, role)
);

-- Index indispensable pour la recherche multicritère ultra-rapide
CREATE INDEX idx_recherche_competence ON competences(matiere_id, role, niveau_maitrise);

-- ==============================================================================
-- 4. TABLE ANNONCES (Offres de cours et demandes d'aide)
-- ==============================================================================
CREATE TABLE annonces (
    id SERIAL PRIMARY KEY,
    auteur_id INT REFERENCES utilisateurs(id) ON DELETE CASCADE,
    matiere_id INT REFERENCES matieres(id) ON DELETE CASCADE,
    type_annonce VARCHAR(20) CHECK (type_annonce IN ('OFFRE', 'DEMANDE')),
    titre VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    disponibilite TEXT, 
    tarif_horaire DECIMAL(10, 2) DEFAULT 0.00, -- Entraide gratuite (0.00) ou payante/jetons
    statut VARCHAR(20) DEFAULT 'ACTIVE' CHECK (statut IN ('ACTIVE', 'FERMEE')),
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_annonces_matiere ON annonces(matiere_id, statut);

-- ==============================================================================
-- 5. TABLE SESSIONS DE MENTORAT (Réservations de cours)
-- ==============================================================================
CREATE TABLE sessions_mentorat (
    id SERIAL PRIMARY KEY,
    annonce_id INT REFERENCES annonces(id) ON DELETE SET NULL,
    mentor_id INT REFERENCES utilisateurs(id) ON DELETE CASCADE,
    mentore_id INT REFERENCES utilisateurs(id) ON DELETE CASCADE,
    matiere_id INT REFERENCES matieres(id) ON DELETE CASCADE,
    statut VARCHAR(30) DEFAULT 'EN_ATTENTE' CHECK (statut IN ('EN_ATTENTE', 'ACCEPTEE', 'REFUSEE', 'TERMINEE', 'ANNULEE')),
    date_prevue TIMESTAMP NOT NULL,
    lieu_ou_lien VARCHAR(255), -- Ex: "Salle 3 IFRI" ou "Lien Google Meet"
    message_initial TEXT,
    date_demande TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_mentor_mentore_differents CHECK (mentor_id != mentore_id)
);

-- ==============================================================================
-- 6. TABLE AVIS ET NOTES (Réputation des mentors)
-- ==============================================================================
CREATE TABLE avis (
    id SERIAL PRIMARY KEY,
    session_id INT REFERENCES sessions_mentorat(id) ON DELETE CASCADE UNIQUE,
    auteur_id INT REFERENCES utilisateurs(id) ON DELETE CASCADE,
    destinataire_id INT REFERENCES utilisateurs(id) ON DELETE CASCADE,
    note INT NOT NULL CHECK (note BETWEEN 1 AND 5),
    commentaire TEXT,
    date_avis TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_auteur_destinataire_differents CHECK (auteur_id != destinataire_id)
);

CREATE INDEX idx_avis_destinataire ON avis(destinataire_id);

-- ==============================================================================
-- 7. NOUVELLE TABLE : CONVERSATIONS (Messagerie)
-- Regroupe les messages entre deux étudiants
-- ==============================================================================
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    utilisateur_un_id INT REFERENCES utilisateurs(id) ON DELETE CASCADE,
    utilisateur_deux_id INT REFERENCES utilisateurs(id) ON DELETE CASCADE,
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Empêche d'avoir des conversations doublées (ex: A-B et B-A)
    CONSTRAINT unique_conversation_duo UNIQUE (utilisateur_un_id, utilisateur_deux_id),
    CONSTRAINT chk_interlocuteurs_differents CHECK (utilisateur_un_id != utilisateur_deux_id)
);

-- ==============================================================================
-- 8. NOUVELLE TABLE : MESSAGES (Messagerie)
-- Contenu des discussions
-- ==============================================================================
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INT REFERENCES conversations(id) ON DELETE CASCADE,
    expediteur_id INT REFERENCES utilisateurs(id) ON DELETE CASCADE,
    contenu TEXT NOT NULL,
    lu BOOLEAN DEFAULT FALSE, -- Pratique pour afficher une notification "Nouveau message !" sur le dashboard
    date_envoi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour charger l'historique d'un chat très rapidement par ordre chronologique
CREATE INDEX idx_messages_conversation ON messages(conversation_id, date_envoi);