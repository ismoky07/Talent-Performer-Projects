import os
from exa_py import Exa
from textwrap import dedent
from typing import Iterator
from dotenv import load_dotenv
from agno.workflow import Workflow
from agno.agent import Agent, RunResponse
from agno.models.openai import OpenAIChat
from agno.utils.pprint import pprint_run_response
from openai import OpenAI

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
exa_api_key = os.getenv("EXA_API_KEY")

# Initialiser les clients
exa = Exa(api_key=exa_api_key) if exa_api_key else None
openai_client = OpenAI(api_key=openai_api_key) if openai_api_key else None

def exa_search(search_term: str):
    """Fonction de recherche Exa """
    try:
        if not exa:
            raise Exception("Clé API Exa non configurée")
            
        # Utilisation de l'API Exa standard pour la recherche
        search_results = exa.search(
            query=f"Amazon {search_term} product reviews price",
            type="neural",  # Recherche sémantique
            num_results=10,
            include_domains=["amazon.com", "amazon.fr"],
            use_autoprompt=True
        )
        
        # Obtenir le contenu des pages
        content_results = exa.get_contents(
            urls=[result.url for result in search_results.results[:5]],
            text=True
        )
        
        # Formater les résultats pour l'agent
        formatted_content = f"""
        Résultats de recherche pour "{search_term}":
        
        """
        
        for i, (result, content) in enumerate(zip(search_results.results[:5], content_results.results)):
            formatted_content += f"""
            ## Produit {i+1}
            **Titre**: {result.title}
            **URL**: {result.url}
            **Score**: {result.score}
            **Contenu**: {content.text[:1000] if content.text else "Contenu non disponible"}...
            
            """
        
        # Utiliser OpenAI pour analyser les résultats Exa
        if not openai_client:
            raise Exception("Clé API OpenAI non configurée")
            
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """Tu es un expert en recherche de produits Amazon. 
                Analyse les résultats de recherche fournis et extrait 3 produits pertinents avec:
                - Nom du produit
                - Prix (si disponible)
                - Description courte
                - Points négatifs mentionnés (ou crée des exemples réalistes d'avis négatifs basés sur le type de produit)
                
                Format en markdown propre."""},
                {"role": "user", "content": f"""
                Analyse ces résultats de recherche pour "{search_term}" et extrait 3 produits Amazon pertinents:
                
                {formatted_content}
                
                Si les prix ne sont pas visibles, estime des prix réalistes pour ce type de produit.
                Pour les avis négatifs, soit utilise ceux trouvés, soit crée des exemples réalistes basés sur les problèmes courants de ce type de produit.
                """}
            ],
            temperature=0.7
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        print(f"Erreur lors de la recherche Exa: {e}")
        print("🔄 Utilisation du mode fallback (OpenAI seulement)...")
        
        # Fallback : utiliser uniquement OpenAI avec des connaissances générales
        if not openai_client:
            return f"❌ Erreur: Clé API OpenAI requise. Veuillez configurer OPENAI_API_KEY dans votre fichier .env"
        
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": f"""
                Crée une analyse de marché fictive mais réaliste pour le produit suivant: {search_term}
                
                Inclus 3 produits concurrents avec:
                - Nom du produit
                - Prix estimé réaliste
                - Description courte
                - 3 avis clients négatifs réalistes pour chaque produit
                
                Base-toi sur ta connaissance des produits similaires sur Amazon.
                Format en markdown propre et détaillé.
                """}
            ],
            temperature=0.7
        )
        
        return completion.choices[0].message.content

class ProductPriceAndPositioning(Workflow):
    pricing_and_positioning_strategist: Agent = Agent(
        name='Pricing Strategist',
        model=OpenAIChat(id='gpt-4o-mini'),
        instructions=dedent("""
        You are a pricing and product strategy expert.

        You will receive structured market research data about 3 competitor products, including for each:  
        - Competitor name  
        - Price  
        - Product description summary  
        - 3 negative customer reviews highlighting product complaints  

        Your tasks:

        1. Analyze the competitor prices and product positioning (budget, midrange, premium).  
        2. Pay special attention to the competitors' negative reviews to identify common product issues and customer pain points.  
        3. Based on the competitive pricing landscape and product differentiation, propose a recommended price range for your product:  
        - Classify it as Budget (< $30), Midrange ($30–$50), or Premium (> $50).  
        - Justify why this price range is appropriate, referencing competitors and market conditions.  
        4. Under **Key Competitors**, list each competitor with:  
        - Name and price  
        - A brief note on how it compares to your product  
        - Include the 3 bad reviews associated with that competitor, quoting customer complaints  
        5. Based on the negative reviews, suggest 2–4 tactical recommendations to improve your product and stand out, such as product improvements, bundles, discounts, or unique positioning strategies. Tie each recommendation directly to the competitor complaints you analyzed.
        """),
        expected_output=dedent("""
        Return your output exactly in this markdown format:

        ---

        ## 💰 Recommended Price Range

        **Range**: `$XX – $YY`  
        **Tier**: _Budget / Midrange / Premium_

        ---

        ## 🏷️ Key Competitors

        - **[Competitor Name]** – `$XX.XX`: _Short comparison note_  
        - Bad Reviews:  
            1. "..."  
            2. "..."  
            3. "..."

        - **[Competitor Name]** – `$XX.XX`: _Short comparison note_  
        - Bad Reviews:  
            1. "..."  
            2. "..."  
            3. "..."

        - _(Add more competitors if applicable)_

        ---

        ## 📊 Rationale

        _Explain why this price range fits your product and market, referencing competitor prices, positioning, and demand._

        ---

        ## 🎯 Tactical Recommendations

        - **[Recommendation 1]**: _Based on competitor complaints, e.g. "Improve pump mechanism to fix frequent failures."_  
        - **[Recommendation 2]**: _E.g. "Offer a cleaning brush bundle addressing cleaning difficulties customers mention."_  
        - _(Add more as relevant)_

        ---

        Keep your analysis specific, actionable, and tied closely to the competitor data and customer feedback.
        """),
        markdown=True
    )

    def run(self, product_details: str):
        print(f"🔍 Recherche de données de marché pour: {product_details}")
        research_response = exa_search(product_details)
        print('=== DONNÉES DE RECHERCHE ===')
        print(research_response)
        print('============================')
        yield from self.pricing_and_positioning_strategist.run(research_response, stream=True)

if __name__ == '__main__':

    from rich.prompt import Prompt
    product = Prompt.ask('Enter your product details')
    if product:
        workflow = ProductPriceAndPositioning()
        response: Iterator[RunResponse] = workflow.run(product_details=product)
        pprint_run_response(response, markdown=True)