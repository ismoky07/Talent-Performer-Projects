import re
import os
from firecrawl import FirecrawlApp
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from textwrap import dedent
from dotenv import load_dotenv


load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

# 🔑 Initialisation de Firecrawl
firecrawl = FirecrawlApp(api_key=FIRECRAWL_API_KEY)

# 🤖 Définition de l'agent IA
pdf_agent = Agent(
    model=OpenAIChat(api_key=OPENAI_API_KEY, id="gpt-4o"),
    name="PDF Analysis Agent",
    role="Expert en analyse de documents PDF",
    instructions=dedent("""
    Vous êtes un expert en analyse de documents PDF. Votre rôle est :
    1. Répondre aux questions précises sur le document
    2. Identifier les thèmes clés et structure logique
    
    Règles strictes :
    - Pour les Q/R : citer les pages/paragraphes pertinents si possible
    - Toujours vérifier la cohérence interne du document
    - Maintenir un ton professionnel et neutre
    
    Format de réponse :
    🎯 Réponse concise
    💡 Contexte : [explication ou justification]
    📄 Source : [citation ou référence précise]
    """),
    markdown=True
)

def extract_pdf_content(pdf_url):
    try:
        # 🔍 Extraction via Firecrawl (essai des deux méthodes possibles)
        try:
            # Méthode v2 (nouvelle version)
            result = firecrawl.scrape(url=pdf_url, formats=['markdown'])
        except AttributeError:
            try:
                # Méthode v1 (ancienne version)
                result = firecrawl.scrape_url(url=pdf_url)
            except AttributeError:
                raise Exception("Méthode Firecrawl non trouvée. Vérifiez votre version de firecrawl-py")
        
        # 🔧 Accès au markdown dans result
        markdown_text = None
        
        # Pour la v2 de l'API
        if hasattr(result, 'markdown'):
            markdown_text = result.markdown
        # Pour la v1 de l'API ou structure différente
        elif hasattr(result, "data") and isinstance(result.data, list) and len(result.data) > 0:
            markdown_text = getattr(result.data[0], "markdown", None)
        # Autre structure possible
        elif isinstance(result, dict) and 'markdown' in result:
            markdown_text = result['markdown']
        
        if not markdown_text:
            return None, "Aucune donnée extraite. Vérifiez que le PDF n'est pas protégé."
        
        # 🧹 Nettoyage markdown
        cleaned = re.sub(r'!\[.*?\]\(.*?\)', '', markdown_text)  # supprime les images
        cleaned = re.sub(r'#+.*', '', cleaned, flags=re.MULTILINE)  # supprime les titres
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)  # lignes vides multiples
        extracted_text = cleaned.strip()
        
        if not extracted_text:
            return None, "Le contenu extrait est vide après nettoyage."
        
        return extracted_text, None
        
    except Exception as e:
        return None, f"Erreur lors de l'extraction: {e}"

def analyze_question(question, pdf_content):
    try:
        prompt = f"{question}\n\nContenu PDF extrait :\n{pdf_content[:6000]}"
        answer = pdf_agent.run(prompt)
        return answer.content, None
    except Exception as e:
        return None, f"Erreur lors de l'analyse: {e}"