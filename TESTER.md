Voici le contenu à placer dans un fichier **README.md** à la racine du projet. Il explique toutes les étapes pour installer et lancer l’application, même pour une personne qui découvre le projet.

```markdown
# IFRI Mentor - Plateforme de mentorat académique

Projet Django de mise en relation des étudiants de l'IFRI pour du mentorat entre pairs (entraide bénévole).

---

## 📋 Prérequis techniques

- **Python** 3.10 ou supérieur
- **pip** (gestionnaire de paquets Python)
- **MySQL** (ou MariaDB) installé et en cours d’exécution
- Un client MySQL (ligne de commande ou outil graphique) pour créer la base de données
- (Optionnel) Un environnement virtuel Python (`venv`)

> **Remarque** : Le projet est configuré pour MySQL. Si vous préférez utiliser SQLite (plus simple, sans installation), modifiez `backend/backend/settings.py` (voir section « Configuration de la base de données »).

---

## 🚀 Installation pas à pas

### 1. Récupérer le projet

Placez-vous dans le dossier où vous souhaitez installer le projet, puis clonez ou copiez les fichiers.  
Par exemple, si le projet est déjà sur votre machine, ouvrez un terminal dans le dossier racine `PIL_2526_36/`.

### 2. Créer un environnement virtuel (recommandé)

```bash
python -m venv venv
```
Ouvrez un terminal PowerShell en tant qu’administrateur et exécutez :

Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

Activez-le :
- **Windows** : `.\venv\Scripts\activate`
- **macOS/Linux** : `source venv/bin/activate`

### 3. Installer les dépendances
va dans :  cd backend 
```bash
pip install -r requirements.txt

ou

python.exe -m pip install --upgrade pip
```

Le fichier `requirements.txt` contient :
```
Django==4.2
djangorestframework==3.14
djangorestframework-simplejwt==5.3
django-cors-headers==4.3
mysqlclient==2.2
python-dotenv==1.0
    
```


### 4. Configurer la base de données

#### 4.1 Créer la base MySQL

Connectez-vous à MySQL et créez la base :

```bash
mysql -u root -p
```

Puis dans l'invite MySQL :
```sql
CREATE DATABASE projet_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

#### 4.2 Adapter `settings.py` (si nécessaire)

Ouvrez `backend/backend/settings.py` et vérifiez la section `DATABASES`. Par défaut, elle est configurée pour MySQL :

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'projet_db',      # nom de la base créée
        'USER': 'root',            # votre utilisateur MySQL
        'PASSWORD': 'votre_mdp',   # votre mot de passe MySQL
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

**Pour utiliser SQLite** (base de données fichier, pas de MySQL nécessaire), remplacez ce bloc par :

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### 5. Appliquer les migrations (création des tables)

Placez-vous dans le dossier `backend/` :


pip install django

pip show django
pip install pymysql
```bash

Assurez-vous que votre base MySQL existe et que les identifiants dans settings.py sont corrects :

python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'projet_db',      # nom de votre base
        'USER': 'root',            # votre utilisateur MySQL
        'PASSWORD': 'votre_mot_de_passe',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

cd backend
python manage.py makemigrations core
python manage.py migrate
```

Cela va créer toutes les tables nécessaires (utilisateurs, profils, compétences, sessions, etc.) dans la base de données.

### 6. (Optionnel) Importer le schéma SQL personnalisé

Si vous avez un fichier `database/schema.sql` contenant des tables supplémentaires (en dehors des modèles Django), vous pouvez l'importer **avant ou après** les migrations.  
Depuis le dossier `backend/` :

```bash
mysql -u root -p projet_db < ../database/schema.sql
```

> Note : Les modèles Django couvrent déjà les tables principales, cette étape n’est normalement pas nécessaire.

### 7. Lancer le serveur de développement

Toujours dans `backend/`, exécutez :

```bash
python manage.py runserver
```

Ouvrez votre navigateur à l'adresse : **http://127.0.0.1:8000/**

---

## 🧭 Structure du projet

```
PIL_2526_36/
├── backend/                   # Projet Django
│   ├── manage.py
│   ├── backend/               # Configuration (settings, urls, wsgi)
│   │   ├── settings.py
│   │   └── urls.py
│   └── core/                  # Application principale
│       ├── models.py          # Modèles (User, Profile, Skill, etc.)
│       ├── views.py           # Vues (accueil, inscription, dash, etc.)
│       ├── forms.py           # Formulaires (inscription, connexion)
│       └── urls.py            # URLs de l'application
├── frontend/                  # Templates HTML
│   ├── base.html              # Layout public (accueil, etc.)
│   ├── dashboard_base.html    # Layout connecté (dashboard)
│   ├── accueil.html
│   ├── connexion.html
│   ├── inscription.html
│   ├── dash.html
│   ├── messagerie.html
│   ├── conversation_detail.html
│   ├── badges.html
│   ├── profil.html
│   └── static/                # CSS, JS, images
│       └── css/
│           └── style.css
├── database/
│   └── schema.sql             # Schéma SQL (si utilisé)
└── requirements.txt
```

---

## 🔑 Comptes de test (à créer après installation)

Pour vous connecter, créez un compte via la page d'inscription (`/inscription/`).  
Le premier utilisateur créé sera un simple étudiant (mentoré). Pour devenir mentor, vous pouvez modifier le profil dans l'administration Django.

Créez un superutilisateur pour accéder à l'administration :

```bash
cd backend
python manage.py createsuperuser
```

Puis connectez-vous sur `http://127.0.0.1:8000/admin/`.

---

## 📌 Remarques

- Si vous rencontrez l'erreur `mysqlclient` non installé, assurez-vous d'avoir les outils de compilation nécessaires (sous Windows, installez `mysqlclient` via une roue précompilée : `pip install mysqlclient‑2.2.0‑cp312‑cp312‑win_amd64.whl`).
- Les fichiers statiques (CSS) sont servis automatiquement en mode développement (`DEBUG=True`).
- La messagerie et les badges sont fonctionnels, mais nécessitent que des données existent dans la base.

---

## 📧 Contact

Projet développé dans le cadre de la plateforme IFRI Mentor – entraide académique.
```

Ce guide couvre toutes les étapes nécessaires pour qu'une nouvelle personne puisse installer et lancer le projet sans difficulté. Vous pouvez le placer dans un fichier `README.md` à la racine.