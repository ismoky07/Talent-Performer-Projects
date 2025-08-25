import os
from dotenv import load_dotenv
import pandas as pd
from textwrap import dedent
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools
from arize.otel import register
from openinference.instrumentation.openai import OpenAIInstrumentor
from openinference.instrumentation.agno import AgnoInstrumentor
from phoenix.evals import OpenAIModel, llm_classify

# Charger les variables d'environnement
load_dotenv()

# -------- Configuration OpenTelemetry --------
tracer_provider = register(
    space_id=os.getenv("ARIZE_SPACE_ID"),
    api_key=os.getenv("ARIZE_API_KEY"),
    project_name="agent-politique-agricole",
)

# Récupération de la clé API OpenAI
openai_api_key = os.getenv("OPENAI_API_KEY")

# Configuration de l'instrumentation
AgnoInstrumentor().instrument(tracer_provider=tracer_provider)
OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)

# -------- Agent 1: Recherche --------
AgentRecherche = Agent(
    name="AgentRecherche",
    model=OpenAIChat(api_key=openai_api_key, id="gpt-4o"),
    tools=[DuckDuckGoTools()],
    description=dedent("""
        Vous êtes un assistant de recherche politique spécialisé dans la collecte de données récentes et crédibles sur :
        - Les politiques agricoles du Royaume-Uni, les programmes de subventions, les schémas de développement rural et les réglementations environnementales
        - Votre objectif est de récupérer des informations exploitables et des rapports vérifiés à partir de :
        
        • Publications DEFRA et NFU
        • Organismes de recherche scientifique et groupes de réflexion politique
        • Journaux commerciaux et journaux réputés du Royaume-Uni
        • Plateformes gouvernementales officielles (.gov.uk)
    """),
    instructions=dedent("""
        1. Découverte des Sources 🔍
           □ Rechercher les documents, rapports et articles les plus récents liés à la législation agricole britannique.
           □ Prioriser les données de DEFRA, études académiques, NFU et sources politiques de confiance.

        2. Filtrage des Informations ✅
           □ Éliminer le contenu dupliqué ou obsolète.
           □ Se concentrer sur les changements politiques les plus récents et régionalement pertinents.

        3. Extraction du Contexte Brut 📋
           □ Extraire les faits clés, mises à jour politiques et contexte pertinent en texte brut.
           □ Ne pas effectuer d'analyse - se concentrer uniquement sur la récupération d'informations.
    """),
    expected_output=dedent("""
        # {Résumé de la Politique Agricole du Royaume-Uni 📄 Contexte Brut} 📋

        ## Données Collectées
        - **Source 1:** {...}
        - **Source 2:** {...}
        - **Source 3:** {...}

        ## Politiques et Programmes Pertinents
        - Politique A: {...}
        - Politique B: {...}
        - Schéma C: {...}

        ## Notes Environnementales et Économiques
        - Mises à jour des initiatives climatiques: {...}
        - Tendances des revenus agricoles: {...}

        ---
        Compilé par l'Agent de Recherche • Dernière Vérification: {heure_actuelle}
    """),
    markdown=True,
    show_tool_calls=True,
)

# -------- Agent 2: Analyse --------
AgentAnalyse = Agent(
    name="AgentAnalyse",
    model=OpenAIChat(api_key=openai_api_key, id="gpt-4o"),
    description=dedent("""
        Vous êtes un analyste senior de politique agricole qui synthétise des évaluations structurées 
        basées sur des documents politiques et des données d'intervenants. Vous fournissez des perspectives 
        complètes, factuelles et régionalement conscientes couvrant :

        • Implications politiques sur l'agriculture et la biodiversité
        • Évaluations d'impact économique
        • Recommandations stratégiques pour le gouvernement et les parties prenantes
    """),
    instructions=dedent("""
        1. Révision Politique 📋
           □ Analyser les données brutes et identifier les principaux moteurs politiques.
           □ Relier les conclusions à la productivité agricole, au bien-être des exploitations et à la durabilité.

        2. Évaluation des Résultats 📊
           □ Quantifier l'impact sur les communautés rurales et les chaînes d'approvisionnement alimentaire.
           □ Intégrer les tendances environnementales, commerciales et économiques.

        3. Recommandations 💡
           □ Proposer des plans d'action multi-échelles (immédiat, moyen terme, long terme).
           □ Structurer les suggestions selon le type d'exploitation, la géographie et la zone prioritaire.

        4. Format et Clarté ✓
           □ Utiliser un formatage Markdown clair avec des en-têtes structurés.
           □ Assurer un flux logique de l'observation à la recommandation.
    """),
    expected_output=dedent("""
        # {Analyse de Politique Agricole du Royaume-Uni} 🌾

        ## Résumé Exécutif
        {Aperçu concis du paysage agricole actuel et des défis clés}

        | Région | Types d'Exploitations | Enjeux Clés | Schémas de Soutien |
        |--------|-------------|-------------|----------------|
        | Angleterre| ...        | ...         | ...            |
        | Pays de Galles | ...   | ...         | ...            |
        | ...    | ...         | ...         | ...            |

        ## Conclusions Clés
        - **Impact Environnemental:** {...}
        - **Viabilité Économique:** {...}
        - **Développement Rural:** {...}

        ## Analyse de Marché
        {Tendances actuelles de l'agriculture britannique et implications commerciales internationales}

        ## Recommandations
        1. **Actions Immédiates:** {...}
        2. **Stratégie à Moyen Terme:** {...}
        3. **Vision à Long Terme:** {...}

        ## Sources de Données
        {Liste numérotée des références avec dates et pertinence}

        ---
        Préparé par l'Analyste de Politique Agricole • Publié : {date_actuelle} • Dernière Mise à Jour : {heure_actuelle}
    """),
    markdown=True,
)

# -------- Agent 3: Évaluation --------
AgentEvaluateur = Agent(
    name="AgentEvaluateur",
    model=OpenAIChat(api_key=openai_api_key, id="gpt-4o"),
    description=dedent("""
        Vous êtes un auditeur d'impact politique évaluant si un rapport de politique agricole britannique 
        répond de manière significative aux besoins des "communautés agricoles". Vous évaluez si l'analyse 
        est impactante basée sur :

        • Pertinence et couverture des défis agricoles actuels
        • Profondeur des perspectives sur les résultats économiques et environnementaux
        • Qualité et réalisme des recommandations politiques proposées
    """),
    instructions=dedent("""
        1. Tâche d'Évaluation 🎯
           □ Évaluer l'utilité globale du rapport politique.
           □ Comparer le contenu aux préoccupations agricoles du monde réel.

        2. Décision d'Étiquetage 🏷️
           □ Utiliser uniquement "impactant" ou "non impactant" comme étiquette finale.
           □ Être strict : n'attribuer "impactant" que si l'analyse est approfondie et axée sur la communauté.

        3. Explication du Raisonnement 🧠
           □ Après l'étiquetage, rédiger une explication étape par étape.
           □ Souligner ce qui rend le rapport fort ou faible d'un point de vue d'impact politique.

        ⚠️ La sortie doit commencer par un seul mot : impactant ou non impactant. Aucun autre caractère sur la première ligne.
    """),
    expected_output=dedent("""
        impactant

        L'analyse démontre profondeur et pertinence. Elle couvre la biodiversité, l'économie rurale et les risques de chaîne d'approvisionnement.
        La structure s'aligne avec les formats politiques et inclut des recommandations basées sur des données.
        Les différences régionales et les impacts socioéconomiques sont correctement abordés.

        ---
        Évalué par l'Auditeur d'Impact Politique • Vérifié : {date_actuelle}
    """),
    markdown=True,
)

# -------- Agent 4: Gestionnaire --------
AgentGestionnaire = Agent(
    name="AgentGestionnaire",
    model=OpenAIChat(api_key=openai_api_key, id="gpt-4o"),
    tools=[AgentRecherche, AgentAnalyse, AgentEvaluateur],
    description="Un agent orchestrateur coordonnant le flux d'évaluation complet de la politique agricole britannique.",
    instructions=dedent("""
        Étapes :
        1. Appeler AgentRecherche pour rassembler le contexte pertinent de la politique agricole britannique.
        2. Transmettre le contexte brut à AgentAnalyse pour produire une analyse structurée.
        3. Demander à AgentEvaluateur d'évaluer l'impact du rapport politique.

        Ne pas générer de texte vous-même. Router chaque tâche vers l'agent correct.
    """),
    expected_output="Rapport politique complet suivi d'une étiquette d'évaluation d'impact formelle et d'une explication.",
    markdown=True,
    show_tool_calls=True,
)

# -------- Exécution multi-agents --------
saisie_utilisateur = "Analyser l'état actuel et les implications futures des politiques agricoles britanniques et leur impact sur les communautés agricoles"

print("Génération d'analyse politique multi-agents...")
print("=" * 80)

reponse_multi = AgentGestionnaire.run(saisie_utilisateur)
print("\n===== SORTIE FINALE =====")
print(reponse_multi.content)

# -------- Évaluation automatique --------
MODELE_EVAL_ROUTER = """
Vous êtes un bot d'aide IA qui vérifie l'impact de l'analyse de politique agricole britannique sur les communautés agricoles. Votre tâche est d'évaluer si l'analyse fournie est impactante.

Voici les données :
[DÉBUT DONNÉES]
************
[Input]: Ci-dessous se trouve l'entrée qui contient la saisie utilisateur et l'historique de conversation.
{input}

[Sortie Réelle]: Ci-dessous se trouve la sortie réelle générée par l'agent.
{actual_output}

[Sortie Attendue]: Ci-dessous se trouve le format de sortie attendu qui devrait contenir une analyse des politiques agricoles britanniques et leur impact sur les communautés agricoles.
{expected_output}
************
[FIN DONNÉES]

Déterminer si l'analyse est impactante ou non impactante basé sur l'entrée, la sortie réelle et le format attendu.
"""

# Préparation des données pour l'évaluation
donnees_reponse = {
    'input': [saisie_utilisateur],
    'actual_output': [reponse_multi.content],
    'expected_output': [AgentAnalyse.expected_output]
}

df_reponse = pd.DataFrame(donnees_reponse)

# Génération du prompt formaté
def format_template(row):
    return MODELE_EVAL_ROUTER.format(
        input=row['input'],
        actual_output=row['actual_output'],
        expected_output=row['expected_output']
    )

df_reponse['formatted_prompt'] = df_reponse.apply(format_template, axis=1)

# Lancement de l'évaluation
df_eval_router = llm_classify(
    dataframe=df_reponse,
    template=MODELE_EVAL_ROUTER,
    model=OpenAIModel(api_key=openai_api_key, model="gpt-4o"),
    rails=["not impactful", "impactful"],
    provide_explanation=True,
    concurrency=1
)

print("\n===== RÉSULTATS D'ÉVALUATION =====")
print(df_eval_router[['label', 'explanation']])
print("Résultats sauvegardés dans 'evaluation_analyse_politique.csv'")
df_eval_router.to_csv("evaluation_analyse_politique.csv", index=False)