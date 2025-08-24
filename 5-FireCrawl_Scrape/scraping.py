import os
import requests
from bs4 import BeautifulSoup
from firecrawl import Firecrawl
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from textwrap import dedent
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration API depuis les variables d'environnement
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")  
AIRTABLE_TABLE_ID = os.getenv("AIRTABLE_TABLE_ID")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configuration FireCrawl  
firecrawl = Firecrawl(api_key=FIRECRAWL_API_KEY)

# Agent IA
listing_agent = Agent(
    model=OpenAIChat(api_key=OPENAI_API_KEY, id="gpt-4o"),
    name="Listing Analyzer",
    role="Expert immobilier ",
    instructions=dedent("""
    Vous êtes un expert immobilier.
    
    Votre mission pour chaque annonce est :
    - Générer un résumé clair et concis du bien.
    - Identifier les atouts principaux (emplacement, prix, surface, transports, etc.).
    - Identifier les risques potentiels (prix élevé, manque d'information, incohérences, localisation douteuse).
    
    ⚠️ Règles strictes :
    - Si le quartier mentionné dans la description (ex : Gambetta/Pelleport) n'est PAS cohérent avec l'arrondissement dans le champ "location" (ex : 75015), signalez-le explicitement.
    - Ne jamais faire d'affirmation sur la localisation sans confirmation croisée.
    - Si une information importante est absente (surface, charges, etc.), mentionnez-le dans les risques.
    
    📝 Format de sortie obligatoire en Markdown clair :
    **Résumé** : ...
    
    ✅ **Atouts** :
    
    ⚠️ **Risques / Incohérences** :
    
    ⚡ Répondez uniquement en markdown bien formaté. Ne sortez jamais de ce format.
    """),
    show_tool_calls=False,
    markdown=True
)

# Fonctions de parsing
def clean_text_block(text_block):
    lines = [line.strip() for line in text_block.splitlines()]
    return "\n".join([line for line in lines if line])

def simple_parse(text):
    listings = text.split("Ref :")
    records = []
    
    for listing in listings[1:]:
        lines = listing.strip().split('\n')
        record = {}
        record['ref'] = lines[0].strip()
        
        price_line = next((l for l in lines if '€' in l), '')
        record['price'] = price_line.strip()
        
        location_line = next((l for l in lines if 'PARIS' in l.upper()), '')
        record['location'] = location_line.strip()
        
        try:
            price_index = lines.index(price_line)
            detail_index = lines.index(next((l for l in lines if 'Voir le détail du bien' in l)))
            record['description'] = ' '.join(line.strip() for line in lines[price_index+1:detail_index])
        except:
            record['description'] = ''
            
        records.append(record)
    
    return records

def scrape_and_parse(url):
    """Scrape une URL et retourne les annonces parsées"""
    try:
        # Debug: voir ce que retourne FireCrawl
        scrape_result = firecrawl.scrape(url, formats=["html", "markdown"])
        print(f"Debug - Type du résultat: {type(scrape_result)}")
        
        # Essayer d'accéder au contenu HTML
        if hasattr(scrape_result, 'html'):
            html_content = scrape_result.html
        elif hasattr(scrape_result, 'content'):
            html_content = scrape_result.content
        elif isinstance(scrape_result, dict) and 'html' in scrape_result:
            html_content = scrape_result['html']
        else:
            print(f"Debug - Structure du résultat: {scrape_result}")
            # Fallback: essayer le markdown
            if hasattr(scrape_result, 'markdown'):
                return parse_markdown(scrape_result.markdown)
            elif isinstance(scrape_result, dict) and 'markdown' in scrape_result:
                return parse_markdown(scrape_result['markdown'])
            else:
                raise ValueError("Impossible d'extraire le contenu HTML ou Markdown")
        
        # Parser le HTML
        soup = BeautifulSoup(html_content, "html.parser")
        plain_text = soup.get_text()
        
        # Debug: afficher un échantillon du texte
        print(f"Debug - Échantillon du texte (200 premiers caractères): {plain_text[:200]}...")
        
        # Essayer différentes méthodes de parsing
        records = simple_parse(plain_text)
        if not records:
            # Méthode alternative de parsing
            records = alternative_parse(plain_text)
        
        return records
        
    except Exception as e:
        print(f"Erreur dans scrape_and_parse: {e}")
        raise

def parse_markdown(markdown_content):
    """Parse le contenu Markdown pour extraire les annonces"""
    print(f"Debug - Parsing Markdown (200 premiers caractères): {markdown_content[:200]}...")
    # Adapter selon le format Markdown retourné
    return simple_parse(markdown_content)

def alternative_parse(text):
    """Méthode alternative de parsing si la première échoue"""
    print("Debug - Tentative de parsing alternatif...")
    
    # Rechercher d'autres patterns possibles
    patterns = ["Réf.", "REF:", "Ref.", "Reference:", "Prix", "€"]
    
    for pattern in patterns:
        if pattern in text:
            print(f"Debug - Pattern trouvé: {pattern}")
            # Essayer de parser avec ce pattern
            listings = text.split(pattern)
            if len(listings) > 1:
                print(f"Debug - {len(listings)-1} segments trouvés avec le pattern {pattern}")
                # Adapter le parsing selon le pattern
                return parse_with_pattern(listings, pattern)
    
    print("Debug - Aucun pattern reconnu trouvé")
    return []

def parse_with_pattern(listings, pattern):
    """Parse les annonces selon le pattern détecté"""
    records = []
    
    for i, listing in enumerate(listings[1:], 1):  # Skip le premier segment
        lines = listing.strip().split('\n')[:10]  # Limiter aux 10 premières lignes
        
        record = {}
        record['ref'] = f"{pattern}{lines[0].strip()}" if lines else f"Annonce_{i}"
        
        # Chercher le prix
        price_line = ""
        for line in lines:
            if '€' in line or 'EUR' in line:
                price_line = line.strip()
                break
        record['price'] = price_line
        
        # Chercher la localisation
        location_line = ""
        for line in lines:
            if any(word in line.upper() for word in ['PARIS', 'ARRONDISSEMENT', '75']):
                location_line = line.strip()
                break
        record['location'] = location_line
        
        # Description = les premières lignes
        record['description'] = ' '.join(lines[:5])
        
        records.append(record)
        
        if len(records) >= 10:  # Limiter pour éviter trop de résultats
            break
    
    print(f"Debug - {len(records)} annonces parsées avec pattern {pattern}")
    return records

def get_ai_summary(record):
    """Génère le résumé IA pour une annonce"""
    prompt = f"""Voici une annonce immobilière :
    
Référence : {record.get('ref')}
Prix : {record.get('price')}
Localisation : {record.get('location')}
Description : {record.get('description')}
"""
    
    summary = listing_agent.run(prompt)
    return summary.content

def save_to_airtable(record):
    """Sauvegarde un enregistrement dans Airtable"""
    
    enriched_record = {
        "ref": str(record.get("ref", "")),
        "price": str(record.get("price", "")),
        "location": str(record.get("location", "")),
        "description": str(record.get("description", "")),
        "summary": str(record.get("summary", ""))  # ✅ Maintenant que la colonne existe
    }
    
    response = requests.post(
        f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}",
        headers={
            "Authorization": f"Bearer {AIRTABLE_API_KEY}",
            "Content-Type": "application/json"
        },
        json={"fields": enriched_record}
    )
    
    return response.status_code == 200, response.text