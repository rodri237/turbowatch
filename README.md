# 🚀 Guide de Déploiement — TurboWatch

> Application de Maintenance Prédictive des Turbines Hydrauliques  
> Déploiement **gratuit** sur Streamlit Cloud

---

## 📁 Structure du Projet

```
predictive_maintenance/
├── app.py              ← Application principale Streamlit
├── models.py           ← Modèles de validation (Pydantic)
├── database.py         ← Couche d'accès aux données (SQLite)
├── requirements.txt    ← Dépendances Python
├── .gitignore          ← Fichiers à exclure de Git
└── README.md           ← Ce guide
```

---

## 🔧 Exécution Locale (Test avant déploiement)

### Étape 1 — Créer un environnement virtuel
```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

### Étape 2 — Installer les dépendances
```bash
pip install -r requirements.txt
```

### Étape 3 — Lancer l'application
```bash
streamlit run app.py
```

L'application est accessible sur : **http://localhost:8501**

---

## ☁️ Déploiement Gratuit sur Streamlit Cloud

### Pré-requis
- Un compte **GitHub** (gratuit)
- Un compte **Streamlit Cloud** : https://streamlit.io/cloud (gratuit)

---

### Étape 1 — Préparer le dépôt GitHub

1. Créez un fichier `.gitignore` :
```
venv/
data/
__pycache__/
*.pyc
*.db
.env
```

2. Initialisez et poussez le code :
```bash
git init
git add .
git commit -m "feat: application TurboWatch maintenance prédictive"
git branch -M main
git remote add origin https://github.com/VOTRE_NOM/turbowatch.git
git push -u origin main
```

---

### Étape 2 — Connecter à Streamlit Cloud

1. Rendez-vous sur **https://share.streamlit.io**
2. Cliquez sur **"New app"**
3. Connectez votre compte GitHub
4. Remplissez le formulaire :
   - **Repository** : `VOTRE_NOM/turbowatch`
   - **Branch** : `main`
   - **Main file path** : `app.py`
5. Cliquez sur **"Deploy!"**

⏳ Le déploiement prend 2 à 5 minutes.

---

### Étape 3 — Obtenir le lien exécutable

Après déploiement, vous obtenez une URL publique du type :
```
https://VOTRE_NOM-turbowatch-app-XXXX.streamlit.app
```

✅ Ce lien est partageable et accessible par votre enseignant.

---

## ☁️ Alternative : Déploiement sur Render

### Étape 1 — Créer un compte sur Render
Rendez-vous sur https://render.com (gratuit)

### Étape 2 — Créer un fichier `Procfile`
```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

### Étape 3 — Déployer
1. Sur Render → **New Web Service**
2. Connectez votre dépôt GitHub
3. Runtime : **Python 3**
4. Start command : `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
5. Cliquez sur **Create Web Service**

---

## 🗄️ Structure de la Base de Données

### Table `releves_capteurs`
| Colonne       | Type    | Description                        |
|---------------|---------|------------------------------------|
| id            | INTEGER | Clé primaire auto-incrémentée      |
| turbine_id    | TEXT    | Identifiant de la turbine          |
| technicien    | TEXT    | Nom du technicien                  |
| temperature   | REAL    | Température en °C                  |
| vibration     | REAL    | Vibration en mm/s                  |
| pression      | REAL    | Pression en bar                    |
| debit         | REAL    | Débit en m³/h (optionnel)          |
| notes         | TEXT    | Observations libres (optionnel)    |
| horodatage    | TEXT    | Date/heure ISO 8601                |
| statut_alerte | TEXT    | Normal / Avertissement / Critique  |

### Table `journal_alertes`
| Colonne       | Type    | Description                        |
|---------------|---------|------------------------------------|
| id            | INTEGER | Clé primaire auto-incrémentée      |
| releve_id     | INTEGER | Référence vers `releves_capteurs`  |
| turbine_id    | TEXT    | Identifiant de la turbine          |
| niveau_alerte | TEXT    | Avertissement / Critique           |
| message       | TEXT    | Description de l'alerte            |
| horodatage    | TEXT    | Date/heure ISO 8601                |

---

## 🔒 Seuils de sécurité industriels

| Capteur      | Plage normale   | Avertissement   | Critique        |
|--------------|-----------------|-----------------|-----------------|
| Température  | 20°C – 80°C     | > 80°C          | > 120°C         |
| Vibration    | 0 – 10 mm/s     | > 10 mm/s       | > 20 mm/s       |
| Pression     | 0 – 200 bar     | > 200 bar       | > 350 bar       |

---

## 🛡️ Fonctionnalités de Robustesse

- ✅ **Validation Pydantic** : validation stricte des types et plages
- ✅ **Try/Except** : gestion de toutes les erreurs base de données
- ✅ **WAL Mode SQLite** : écriture sécurisée et concurrente
- ✅ **Journal d'alertes** : traçabilité complète des événements critiques
- ✅ **Validation croisée** : règles métier inter-capteurs
- ✅ **Index BDD** : performances optimisées sur les grandes tables

---

*Développé avec Python 3.11 · Streamlit · Pydantic v2 · SQLite · Plotly*
