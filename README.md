# IFRI MentorLink

Application web de mentorat académique pour les étudiants de l'IFRI.

## Installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/PIL1_2526_XX/IFRI_MentorLink.git
cd IFRI_MentorLink

# 2. Créer et activer l'environnement virtuel
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer la base de données PostgreSQL
# Créer une base nommée mentorlink_db, puis :
export DB_NAME=mentorlink_db
export DB_USER=postgres
export DB_PASSWORD=votre_mot_de_passe

# 5. Appliquer les migrations
python manage.py migrate

# 6. Lancer le serveur
python manage.py runserver
```

Ouvrir http://127.0.0.1:8000

## Structure du projet

```
apps/accounts/   → Gestion des comptes et profils
apps/matching/   → Algorithme de matching mentor/mentoré
apps/messaging/  → Messagerie instantanée (WebSocket)
database/        → schema.sql (livrable)
report/          → rapport HTML (livrable)
```

## Algorithme de matching

Le score de compatibilité est calculé selon trois critères :
- **50%** — Compatibilité des matières (lacunes du mentoré ∩ compétences du mentor)
- **30%** — Compatibilité horaire (créneaux communs / créneaux du mentoré)
- **20%** — Proximité de filière (même filière = 100, IA↔IM = 60, autres = 30)
