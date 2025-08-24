import asyncio
import os
import pandas as pd
from dotenv import load_dotenv
from uqlm import BlackBoxUQ
from uqlm.utils import load_example_dataset, math_postprocessor
from langchain_openai import ChatOpenAI

# 🧠 AGENT AGNO
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.python import PythonTools

# ✅ Chargement des variables d'environnement depuis le fichier .env
load_dotenv()

# ✅ Vérification que la clé API OpenAI est disponible
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY non trouvée dans le fichier .env. Veuillez l'ajouter.")

# ✅ Définition de l'agent Agno
agent_hallucination = Agent(
    name="AgentDetectionHallucination",
    role="Analyser les réponses incertaines et proposer une action appropriée.",
    model=OpenAIChat(id="gpt-4o"),
    tools=[PythonTools()],
    show_tool_calls=False,
    markdown=False,
    description="""
Vous êtes un agent spécialisé dans l'analyse des réponses générées par un modèle de langage.
Votre rôle est de détecter les réponses avec un risque élevé d'hallucination basé uniquement sur le score d'incertitude fourni par une méthode de quantification d'incertitude (UQ).
Vous n'avez pas accès à la vérité terrain et devez vous fier exclusivement au niveau d'incertitude pour décider s'il faut ACCEPTER, REFORMULER, ou REFUSER la réponse.
Vous opérez selon une logique basée sur des seuils et êtes censé fournir des sorties normalisées et cohérentes dans un format de décision clair.
""",
    instructions="""
🎯 Objectif:
Vous êtes un expert agent dans la détection d'hallucinations potentielles dans les réponses générées par un modèle de langage (ex. GPT-3.5-turbo) pour des questions mathématiques simples du jeu de données SVAMP.

📝 Entrée (fournie dans le prompt en texte brut):
1. La **question** mathématique posée (ex. "Tom a 3 pommes et achète 2 de plus...")
2. La **réponse** générée par le modèle (ex. "La réponse est 5.")
3. Le **score d'incertitude** associé (ex. 0.47), un flottant entre 0 et 1 fourni par la bibliothèque BlackBoxUQ.

🎯 Tâche:
Basé **uniquement** sur la valeur d'incertitude, déterminer l'action la plus appropriée selon ces règles:
🟢 Si incertitude < 0.2 → **ACCEPTER**
🟠 Si 0.2 ≤ incertitude ≤ 0.5 → **REFORMULER**
🔴 Si incertitude > 0.5 → **REFUSER**

📋 Format de Réponse (strictement requis):
Toujours répondre sur **une seule ligne**, commençant par l'action (**ACCEPTER**, **REFORMULER**, ou **REFUSER**) en **MAJUSCULES**, suivi d'une **justification concise en une phrase claire**.
⚠️ Ne pas inclure de texte supplémentaire ou de sauts de ligne.

🔴 Exemple:
REFORMULER L'incertitude est modérée (0.43), reformuler la réponse est recommandé.
"""
)

def calculer_incertitude(row):
    """
    Calculer le score d'incertitude à partir des métriques BlackBoxUQ.
    Une entropie_semantique plus faible = incertitude plus élevée
    """
    incertitude_semantique = 1 - row.get('semantic_negentropy', 0)
    incertitude_correspondance_exacte = 1 - row.get('exact_match', 0)  
    incertitude_cosinus = 1 - row.get('cosine_sim', 0)
    incertitude_contradiction = 1 - row.get('noncontradiction', 0)
    
    incertitude_primaire = incertitude_semantique
    incertitude_combinee = (incertitude_semantique + incertitude_correspondance_exacte + incertitude_cosinus) / 3
    
    return incertitude_primaire, {
        'semantique': incertitude_semantique,
        'correspondance_exacte': incertitude_correspondance_exacte, 
        'cosinus': incertitude_cosinus,
        'contradiction': incertitude_contradiction,
        'combinee': incertitude_combinee
    }

async def main():
    # 📊 1. Charger le jeu de données SVAMP
    svamp = load_example_dataset("svamp", n=5)
    print('------------------------📊 Questions------------------------')
    for idx, q in enumerate(svamp['question'], 1):
        print(f"{idx}. {q}")
    print('-----------------------------------------------------------')
    
    # 📝 2. Préparer les prompts
    INSTRUCTION_MATH = "Lorsque vous résolvez ce problème mathématique, ne retournez que la réponse sans texte supplémentaire.\n"
    prompts = [INSTRUCTION_MATH + q for q in svamp.question]
    
    # 🧠 3. Initialiser le modèle LLM
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    
    # 🔍 4. Génération avec incertitude via BlackBoxUQ
    bbuq = BlackBoxUQ(llm=llm)
    results = await bbuq.generate_and_score(prompts)
    df = results.to_df()
    
    print("\n✅ Colonnes disponibles :", df.columns.tolist())
    print(df.head())
    
    # 🧹 5. Nettoyage des réponses
    if "response" in df.columns:
        df['sortie_traitee'] = df['response'].apply(math_postprocessor)
    elif "generation" in df.columns:
        df['sortie_traitee'] = df['generation'].apply(math_postprocessor)
    else:
        print("⚠️ Aucun champ 'response' ou 'generation' trouvé.")
        df['sortie_traitee'] = None
    
    # 📊 6. Calculer les scores d'incertitude
    donnees_incertitude = []
    for i, row in df.iterrows():
        incertitude, detail_incertitude = calculer_incertitude(row)
        donnees_incertitude.append({
            'incertitude': incertitude,
            **detail_incertitude
        })
    
    df_incertitude = pd.DataFrame(donnees_incertitude)
    df = pd.concat([df, df_incertitude], axis=1)
    
    print("\n📊 Scores d'incertitude calculés:")
    print(df[['response', 'incertitude', 'semantique', 'correspondance_exacte', 'cosinus', 'combinee']].head())
    
    # 🧠 7. Analyser intelligemment par Agent Agno
    resultats_analyse = []
    for i, row in df.iterrows():
        question = row.get('question', 'N/A')
        response = row.get('response') or row.get('generation', '')
        incertitude = row.get('incertitude', 1.0)
        
        contexte_prompt = f"""
Question : {question}
Réponse : {response}
Incertitude : {incertitude:.3f}
"""
        
        try:
            reponse_agent = agent_hallucination.run(contexte_prompt.strip())
            decision_agent = reponse_agent.content if hasattr(reponse_agent, "content") else str(reponse_agent)
            print(f"🤖 Décision agent    : {decision_agent}")
        except Exception as e:
            decision_agent = f"ERREUR: {str(e)}"
        
        resultats_analyse.append(decision_agent)
        print(f"🧠 Q{i+1} → Incertitude: {incertitude:.3f} → {decision_agent}")
    
    df['decision_agent'] = resultats_analyse
    
    # 💾 8. Sauvegarder dans un fichier CSV
    df.to_csv("resultats_math_uq_corrige.csv", index=False)
    print("\n📁 Résultats sauvegardés dans resultats_math_uq_corrige.csv")
    
    # 📊 9. Résumé des décisions
    print("\n📊 Résumé des décisions:")
    decisions = [result.split()[0] for result in resultats_analyse if result.split()]
    comptes_decisions = pd.Series(decisions).value_counts()
    print(comptes_decisions)

if __name__ == "__main__":
    asyncio.run(main())