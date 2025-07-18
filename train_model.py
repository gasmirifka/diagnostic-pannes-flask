
# === Importations ===
import os
import sqlite3
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
import joblib

# === Configuration ===
DB_PATH = "C:/Users/merci/OneDrive/Bureau/master/pannes.db"
MODEL_DIR = "C:/Users/merci/OneDrive/Bureau/master/models"

# === 1. Chargement des données ===
def charger_donnees():
    """Charge les données de pannes depuis la base SQLite."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM pannes", conn)
    conn.close()
    return df

# === 2. Entraînement du modèle KNN avec TF-IDF ===
def entrainer_modele(df):
    """
    Nettoie les données, vectorise le texte avec TF-IDF,
    puis entraîne un modèle KNN basé sur la distance cosinus.
    Ajoute des visualisations du processus.
    """
    df = df.dropna(subset=["Description_Panne"])  # Supprimer les lignes sans description
    
    # Vectorisation TF-IDF
    print("\n=== Vectorisation TF-IDF ===")
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(df["Description_Panne"])
    print(f"Matrice TF-IDF générée (shape: {X.shape})")
    
    # Exemple de features (mots) importants
    feature_names = vectorizer.get_feature_names_out()
    print(f"\nExemple de features (10 premiers): {feature_names[:10]}")
    
    # Entraînement KNN
    print("\n=== Entraînement KNN ===")
    model = NearestNeighbors(n_neighbors=1, metric='cosine')
    model.fit(X)
    
    # Exemple de calcul de distance
    print("\n=== Exemple de calcul de distance ===")
    sample_text = df["Description_Panne"].iloc[3]
    print(f"Texte exemple: '{sample_text[:50]}...'")
    
    vec = vectorizer.transform([sample_text])
    distances, indices = model.kneighbors(vec)
    
    print(f"\nDistance cosinus pour le texte exemple:")
    print(f"- Plus proche voisin: indice {indices[0][0]}")
    print(f"- Distance: {distances[0][0]:.4f}")
    print(f"- Texte similaire: '{df['Description_Panne'].iloc[indices[0][0]][:50]}...'")
    
    return model, vectorizer

# === 3. Sauvegarde du modèle ===
def sauvegarder_modele(model, vectorizer):
    """Sauvegarde le modèle KNN et le vectoriseur TF-IDF au format .pkl."""
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, os.path.join(MODEL_DIR, "knn_model.pkl"))
    joblib.dump(vectorizer, os.path.join(MODEL_DIR, "vectorizer.pkl"))
    print("✅ Modèle et vectoriseur sauvegardés avec succès.")

# === 4. Pipeline principal ===
def pipeline_entrainement():
    """Pipeline complet : chargement des données, entraînement et sauvegarde."""
    print("🔄 Chargement des données...")
    df = charger_donnees()

    print("🧠 Entraînement du modèle...")
    model, vectorizer = entrainer_modele(df)

    print("💾 Sauvegarde du modèle...")
    sauvegarder_modele(model, vectorizer)

    print("✅ Entraînement du modèle terminé avec succès.")

# === Point d'entrée ===
if __name__ == "__main__":
    pipeline_entrainement()
# === Fin du script ===
