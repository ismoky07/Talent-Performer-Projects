import os
from dotenv import load_dotenv
from agno.agent import Agent
from agno.team.team import Team
from agno.models.openai import OpenAIChat
from textwrap import dedent
from datetime import datetime
import utils  

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def get_document():
    """
    Récupère le document à analyser depuis le module utils
    """
    return utils.get_document()

def create_structure_agent():
    """
    Crée l'agent spécialisé dans l'analyse structurelle des contrats
    """
    return Agent(
        model=OpenAIChat(id="gpt-4o", api_key=OPENAI_API_KEY),
        name='Agent Structure',
        role='Expert en Structuration de Contrats',
        instructions=dedent("""
            Vous êtes un Expert en Structuration de Contrats. Votre rôle est d'évaluer la structure 
            d'un contrat et de suggérer des améliorations ou de construire une structure appropriée 
            à partir de zéro.
            
            Vous utiliserez l'outil `get_document` pour récupérer le texte complet du contrat.
            Votre tâche est d'analyser le contrat et de déterminer s'il est structuré de manière 
            claire, complète et juridiquement appropriée.
            
            Vous devez identifier les sections manquantes ou peu claires :
            - S'il manque de structure, suggérez une structure complète en utilisant des en-têtes 
              de section standard (ex: Définitions, Conditions, Obligations, Résiliation, Loi applicable).
            - Évitez l'interprétation juridique - concentrez-vous uniquement sur l'organisation, 
              la clarté et le flux logique.
            - Soyez concis mais clair dans votre analyse.
            
            Produisez une structure au format markdown si vous créez une nouvelle structure, 
            ou des commentaires sous forme de puces si vous évaluez une structure existante.
            
            
        """),
        tools=[get_document],
        markdown=True,
    )

def create_legal_agent():
    """
    Crée l'agent spécialisé dans l'analyse juridique des contrats
    """
    return Agent(
        model=OpenAIChat(id="gpt-4o", api_key=OPENAI_API_KEY),
        name='Agent Juridique',
        role='Analyste des Questions Juridiques',
        instructions=dedent("""
            Vous êtes un Analyste du Cadre Juridique chargé d'identifier les problèmes juridiques, 
            les risques et les principes juridiques clés dans le contrat téléchargé.
            
            Utilisez l'outil `get_document` pour accéder au texte complet du contrat. 
            Pour chaque problème juridique ou observation, vous DEVEZ :
            
            - Citer la clause, phrase ou paragraphe exact du contrat sur lequel votre point est basé.
            - Commencer une nouvelle ligne avec 'Problème :' suivi d'une explication courte 
              et claire de la préoccupation ou du principe juridique.
            - Faire clairement référence au titre de section, en-tête ou numéro de paragraphe 
              si disponible. Sinon, décrire son emplacement (ex: "section commençant par [texte]...").
            - NE PAS faire d'évaluation ou commentaire juridique à moins qu'il ne soit directement 
              soutenu par une citation du contrat.
            
            Votre tâche :
            - Identifier le domaine juridique du contrat (ex: droit commercial, emploi, NDA, etc.)
            - Déterminer la juridiction probable ou la loi applicable
            - Souligner tout problème juridique potentiel ou clause problématique
            - Vérifier la conformité RGPD si applicable
            - Identifier les déséquilibres de responsabilité et de responsabilité
            
            Formatez chaque constatation comme suit :
            📄 Clause :
            "Texte cité du contrat ici."
                            
            📍 Section : (Titre de section ou emplacement)
                            
            ⚠️ Problème :
            Votre brève analyse de pourquoi cette clause peut présenter une préoccupation juridique.
            
        """),
        tools=[get_document],
        show_tool_calls=False,
        markdown=True,
    )

def create_negotiation_agent():
    """
    Crée l'agent spécialisé dans les stratégies de négociation contractuelle
    """
    return Agent(
        model=OpenAIChat(id="gpt-4o", api_key=OPENAI_API_KEY),
        name='Agent Négociation',
        role='Stratège en Négociation de Contrats',
        instructions=dedent("""
            Vous êtes un Stratège en Négociation de Contrats.
            
            Votre travail est d'identifier les parties d'un contrat qui sont couramment négociables 
            ou potentiellement déséquilibrées. Vous DEVEZ :
            
            - Toujours citer le paragraphe ou la clause exacte à laquelle vous faites référence.
            - Expliquer clairement pourquoi elle peut être négociable ou nécessite un ajustement.
            - Suggérer une contre-offre ou une formulation alternative.
            
            Structurez votre analyse comme ceci :
            1. **Clause Citée** (texte exact du contrat)
            2. **Pourquoi elle est négociable ou problématique**
            3. **Exemple de stratégie ou contre-suggestion**
            
            NE FAITES PAS de commentaires généraux. Chaque point que vous faites doit être soutenu 
            par une citation directe du contrat, et votre sortie doit clairement montrer quelle 
            partie du contrat vous analysez.
           
        """),
        tools=[get_document],
        show_tool_calls=False,
        markdown=True,
    )

def create_manager_team():
    """
    Crée l'équipe de management qui coordonne tous les agents spécialisés
    
    Returns:
        Team: Équipe coordonnée d'agents pour l'analyse complète de contrats
    """
    
    # Création des agents spécialisés
    structure_agent = create_structure_agent()
    legal_agent = create_legal_agent()
    negotiate_agent = create_negotiation_agent()
    
    # Équipe coordonnée par un agent manager
    manager_agent = Team(
        members=[structure_agent, legal_agent, negotiate_agent],
        model=OpenAIChat(id="gpt-4o", api_key=OPENAI_API_KEY),
        mode='coordinate',
        success_criteria=dedent("""
            Un résumé bien organisé et traçable du contrat qui inclut :
            - Contexte juridique soulignant les problèmes juridiques potentiels avec le texte 
              du contrat cité comme preuve
            - Revue structurelle avec des suggestions de clarté et de formatage  
            - Stratégies de négociation directement liées à des paragraphes ou clauses spécifiques
            - Évaluation des risques consolidée avec des recommandations actionnables
            - Classement de priorité clair de tous les problèmes identifiés
        """),
        instructions=dedent("""
            Vous êtes le Coordinateur principal et résumeur. Vous devez combiner les apports de :
            1. Agent Structure  
            2. Agent Juridique
            3. Agent Négociation
            
            Note : L'extraction de document est gérée automatiquement par get_document() - 
            les agents reçoivent un texte propre.
            
            Exigences clés :
            - Pour tous les points juridiques et de négociation, préservez les clauses citées 
              du contrat comme preuve.
            - L'Agent Juridique devrait souligner des problèmes juridiques spécifiques, 
              suivis d'une courte explication 'Problème :'.
            - Chaque extrait cité doit être suivi de l'explication ou recommandation de l'agent.
            - Consolidez tous les scores en une évaluation globale des risques
            - Fournissez un résumé exécutif clair avec des étapes actionnables suivantes
            - Assurez-vous de la traçabilité complète de toutes les contributions des agents
            
            Format final :
            1. Résumé Exécutif
            2. Contexte Juridique (Avec clauses citées et explications des problèmes)
            3. Retours sur la Structure du Contrat
            4. Recommandations de Négociation
        """),
        show_tool_calls=True,
        markdown=True,
    )
    
    return manager_agent