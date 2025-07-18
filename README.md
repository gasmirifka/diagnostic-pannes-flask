# diagnostic-pannes-flask
# 🛠️ Système intelligent de diagnostic des pannes — Application Web Flask

## 📘 Présentation

Ce projet consiste à développer une application web intelligente permettant de diagnostiquer automatiquement des pannes industrielles à partir de données mesurées. Il s’inscrit dans la logique de l’industrie 4.0 en intégrant des mécanismes d’automatisation, d’analyse intelligente et de visualisation web.

L’application utilise **Flask** pour l’interface web, un modèle de **machine learning (KNN)** pour la détection des pannes, et envoie des **alertes par email** en cas de panne .

## 🛠 Technologies utilisées
- **Backend** : Flask (Python)
- **IA / NLP** : TfidfVectorizer + Nearest Neighbors (sklearn)
- **Base de données** : SQLite
- **Front-end** : HTML / css
- **Multilingue** : dictionnaire statique (fr / en / ja)
- **Visualisation PDF / Emailing** : xhtml2pdf, smtplib
- **Modèle enregistré** : `knn_model.pkl`, `vectorizer.pkl`

## 📂 Structure du projet

**mon_app.py** 	    Application web principale (authentification, rôles, diagnostic)
**train_model.py**	Script d’entraînement KNN + TF-IDF
**translations.py**	Dictionnaire multilingue (français, anglais, japonais)
**models/**         Modèle KNN et vectoriseur (fichiers .pkl)
**templates/**      Interfaces HTML  

## 🧪 Fonctionnalités principales
- Signalement de panne par les opérateurs

- Diagnostic automatisé par similarité

- Interface dédiée par rôle (admin / technicien / opérateur)

- Tableau de bord avec statistiques

- Génération de rapport PDF

- Envoi d’alertes par e‑mail

## 🏷 Auteur
Gasmi Rifka – 2025
Master Robotique & IA – ISET Bizerte
📧 gasmirifka5@gmail.com
