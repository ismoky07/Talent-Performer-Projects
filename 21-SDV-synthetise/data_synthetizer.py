import pandas as pd
import warnings
import os
from sdv.metadata import Metadata
from sdv.single_table import GaussianCopulaSynthesizer
from sdv.evaluation.single_table import run_diagnostic, evaluate_quality, get_column_plot
from transformers import pipeline

# Ignorer les messages d'avertissement pour garder une sortie propre
warnings.filterwarnings("ignore")

# Créer un dossier nommé "Data" s'il n'existe pas déjà
os.makedirs("Data", exist_ok=True)

# Charger le dataset original (premières 500 lignes pour la démo)
real_data = pd.read_csv("21-SDV-synthetise/Data/E-Commerce Dataset.csv", nrows=500)

# Initialiser les variables pour stocker les données et résultats
metadata = None
synthetic_data = None
quality_report_result = None

def synthetize_data(realism=False):
    """
    Générer des données synthétiques basées sur le dataset original
    
    Args:
        realism (bool): Si True, active le mode réalisme pour plus de variété
    """
    global metadata, synthetic_data
    
    # Détecter automatiquement la structure et les types depuis le dataset original
    metadata = Metadata.detect_from_dataframe(real_data)
    
    # Initialiser le synthétiseur avec les options sélectionnées
    synthesizer = GaussianCopulaSynthesizer(metadata)
    
    # Entraîner le synthétiseur sur le dataset réel
    synthesizer.fit(real_data)
    
    # Générer des échantillons synthétiques
    synthetic_data = synthesizer.sample(num_rows=500)
    
    # Sauvegarder les données générées dans un fichier CSV
    synthetic_data.to_csv("Data/synthetic_data.csv", index=False)
    print("\n✅ Données synthétiques sauvegardées dans Data/synthetic_data.csv")

def generate_narrative_data():
    """
    Générer des données narratives synthétiques en utilisant GPT-2
    """
    global narrative_data
    
    # Créer un pipeline de génération de texte
    generator = pipeline("text-generation", model="gpt2")
    
    # Générer des messages synthétiques
    prompts = ["Message support client:" for _ in range(10)]
    messages = [
        generator(prompt, max_new_tokens=40, truncation=True)[0]["generated_text"].replace(prompt, "").strip()
        for prompt in prompts
    ]
    
    # Créer et sauvegarder le DataFrame
    narrative_data = pd.DataFrame({
        "id": [f"MSG-{i+1}" for i in range(len(messages))],
        "message": messages
    })
    narrative_data.to_csv("Data/narrative_data.csv", index=False)
    print("\n✅ Données narratives synthétiques sauvegardées dans Data/narrative_data.csv")

def diagnostic_report():
    """
    Exécuter un diagnostic pour s'assurer que les données sont valides
    """
    diagnostic = run_diagnostic(
        real_data=real_data,
        synthetic_data=synthetic_data,
        metadata=metadata
    )
    print("\n📊 Rapport de diagnostic généré")
    return diagnostic

def quality_report():
    """
    Mesurer la qualité des données ou la similarité statistique entre les vraies et fausses données
    """
    global quality_report_result
    quality_report_result = evaluate_quality(
        real_data,
        synthetic_data,
        metadata
    )
    print("\n📈 Rapport de qualité généré")
    print(f"Score de qualité global: {quality_report_result.get_score():.3f}")

def column_plot():
    """
    Afficher les détails de qualité par colonne
    """
    global quality_report_result
    if quality_report_result is None:
        print("Rapport de qualité pas encore généré. Génération en cours...")
        quality_report()
    print("Colonnes classées de la meilleure à la moins bonne qualité:")
    print("--------------------------------------------------------")
    print(quality_report_result.get_details("Column Shapes"))

def visualize_data():
    """
    Visualiser la comparaison d'une colonne entre les données réelles et synthétiques
    """
    # Visualiser en comparant une colonne (PreferredOrderCat) des vraies données aux synthétiques
    fig = get_column_plot(
        real_data=real_data,
        synthetic_data=synthetic_data,
        column_name="PreferredOrderCat",
        metadata=metadata
    )
    fig.show()
    print("\n📊 Graphique de comparaison affiché")

def post_synthesis_menu():
    """
    Menu d'analyse post-synthèse permettant d'évaluer les résultats
    """
    print("\nDonnées synthétisées avec succès, consultez le fichier 'Data/synthetic_data.csv'")
    print("""
Que voulez-vous faire ensuite ?
1. Voir le rapport de diagnostic
2. Voir le rapport de qualité
3. Voir le graphique des colonnes
4. Visualiser les données
5. Quitter
""")
    
    while True:
        choice = input("Tapez votre choix : ").strip()
        if choice == "1":
            diagnostic_report()
        elif choice == "2":
            quality_report()
        elif choice == "3":
            column_plot()
        elif choice == "4":
            visualize_data()
        elif choice == "5":
            print("🟡 Fermeture du programme.")
            exit()
        else:
            print("❌ Entrée invalide. Veuillez entrer un nombre de 1 à 5.")

# Menu principal
if __name__ == "__main__":
    print("""
Quel est l'objectif des données que vous voulez synthétiser (tapez le numéro de l'objectif) :
1. Réplication de schéma
2. Réalisme + variété
3. Champs narratifs (Ex: avis, tickets de support)
Vous voulez connaître la différence entre les objectifs ? Tapez 'aide'
""")
    
    while True:
        user_input = input("Tapez votre choix : ")
        if user_input == "aide":
            print("""
1. Réplication de schéma : S'assure que les données synthétiques correspondent à la structure 
   (colonnes, types de données, contraintes) du dataset original.

2. Réalisme + variété : Se concentre sur la création de données synthétiques réalistes et 
   diversifiées, capturant les motifs et la variabilité observés dans les vraies données.

3. Champs narratifs : Implique la génération de texte cohérent et humain pour des champs 
   comme les avis ou tickets de support, nécessitant compréhension et génération du langage naturel.
""")
        elif user_input == "1":
            synthetize_data()
            post_synthesis_menu()
        elif user_input == "2":
            synthetize_data(realism=True)
            post_synthesis_menu()
        elif user_input == "3":
            generate_narrative_data()
            # Note: Pas de menu post-synthèse pour les données narratives dans le code original
            print("\nDonnées narratives générées. Tapez 'quit' pour quitter ou recommencez.")
        else:
            print("Entrée invalide. Veuillez entrer 1, 2, 3 ou 'aide'.")
            continue