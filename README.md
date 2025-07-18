# diagnostic-pannes-flask
# 🛠️ Système intelligent de diagnostic des pannes — Application Web Flask

## 📘 Présentation

Ce projet consiste à développer une application web intelligente permettant de diagnostiquer automatiquement des pannes industrielles à partir de données mesurées. Il s’inscrit dans la logique de l’industrie 4.0 en intégrant des mécanismes d’automatisation, d’analyse intelligente et de visualisation web.

L’application utilise **Flask** pour l’interface web, un modèle de **machine learning (KNN)** pour la détection des pannes, et envoie des **alertes par email** en cas de panne .

<img width="1648" height="683" alt="accueil" src="https://github.com/user-attachments/assets/085028fb-824f-4aaa-bd71-121a3b84a281" />

## 🛠 Technologies utilisées
- **Backend** : Flask (Python)
- **IA / NLP** : TfidfVectorizer + Nearest Neighbors (sklearn)
- **Base de données** : SQLite
- **Front-end** : HTML / css
- **Multilingue** : dictionnaire statique (fr / en / ja)
- **Visualisation PDF / Emailing** : xhtml2pdf, smtplib
- **Modèle enregistré** : `knn_model.pkl`, `vectorizer.pkl`

## 📂 Structure du projet
système intelligent/
│
├── mon_app.py      # Application web principale (authentification, rôles, diagnostic)

│── train_model.py          # Python script d’entraînement KNN + TF-IDF

│── translations.py 	      # Dictionnaire multilingue (français, anglais, japonais)

├── data/

│ ├── pannes.db

│
├── templates/

│ ├── layout.html # Template principal

│ ├── index.html # Page de formulaire

│ └── result.html # Page de résultats

│── models/      

| └── knn_model.pkl      #Modèle KNN

| └──vectorizer.pkl      # vectoriseur

├── static/

│ └── style.css # Style CSS

│── data_email.txt          # Sample email 

├── requirements.txt # Liste des dépendances Python

├── .gitignore # Fichiers à ignorer dans Git

└── README.md # Documentation du projet


## ⚙️ Installation
Python 3.x
 Python libraries: pip install smtplib pandas flask
### 1. Cloner le projet
git clone  https://github.com/gasmirifka/diagnostic-pannes-flask.git
cd système intelligent

## Installer les dépendances
pip install -r requirements.txt
## 🚀 Lancer l'application
python mon_app.py
Puis ouvre ton navigateur sur :
🔗 http://127.0.0.1:5000
## 🧪 Fonctionnalités principales
- Signalement de panne par les opérateurs

- Diagnostic automatisé par similarité

- Interface dédiée par rôle (admin / technicien / opérateur)

- Tableau de bord avec statistiques

- Génération de rapport PDF

- Envoi d’alertes par e‑mail
## 📜 Licence
Projet open-source sous licence MIT.
## 🏷 Auteur
Gasmi Rifka – 2025
Master Robotique & IA – ISET Bizerte
📧 gasmirifka5@gmail.com
## 🤝 Contributions
Contributions bienvenues via issues ou pull requests.
