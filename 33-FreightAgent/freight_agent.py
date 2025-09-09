import os
from textwrap import dedent
from agno.agent import Agent
from mistralai import Mistral
from agno.models.openai import OpenAIChat
from agno.vectordb.lancedb import LanceDb, SearchType
from agno.tools.reasoning import ReasoningTools
from ddgs import DDGS
from agno.knowledge.markdown import MarkdownKnowledgeBase
from agno.embedder.openai import OpenAIEmbedder
from dotenv import load_dotenv
load_dotenv()

mistral_key = os.getenv("MISTRAL_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")

if mistral_key:
    client = Mistral(api_key=mistral_key)
else:
    print("ERREUR: MISTRAL_API_KEY requis pour OCR")
    exit()

if not openai_key:
    print("ERREUR: OPENAI_API_KEY requis")
    exit()

## OCR Function améliorée ###
def ocr_pdf(pdf_path, output_name=None):
    """Convertit un PDF en Markdown via OCR Mistral"""
    if not os.path.exists(pdf_path):
        print(f"ERREUR: PDF non trouvé - {pdf_path}")
        return False
    
    print(f"Traitement OCR de {pdf_path}...")
    
    try:
        # Upload du PDF
        uploaded_pdf = client.files.upload(
            file={
                "file_name": os.path.basename(pdf_path),
                "content": open(pdf_path, "rb"),
            },
            purpose="ocr"
        )

        # Obtenir URL signée
        signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)

        # Traitement OCR
        ocr_response = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "document_url",
                "document_url": signed_url.url,
            },
            include_image_base64=True
        )

        # Générer nom de sortie
        if output_name is None:
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            output_name = f"{base_name}.md"

        # Sauvegarder en Markdown
        os.makedirs("33-FreightAgent/Markdown", exist_ok=True)
        output_path = f"33-FreightAgent/Markdown/{output_name}"
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join([page.markdown for page in ocr_response.pages]))
        
        print(f"SUCCESS: {output_path} créé ({len(ocr_response.pages)} pages)")
        return True
        
    except Exception as e:
        print(f"ERREUR OCR {pdf_path}: {e}")
        return False
class DDGSTools:
    def __init__(self):
        self.ddgs = DDGS()
    
    def search(self, query, max_results=5):
        try:
            results = list(self.ddgs.text(query, max_results=max_results))
            return results
        except Exception as e:
            print(f"Erreur recherche: {e}")
            return []

# Dans votre agent
ddgs_tool = DDGSTools()

## Traitement de tous vos PDFs ###
def process_all_pdfs():
    """Traite tous les PDFs du dossier Document/"""
    document_folder = "33-FreightAgent/Document/"
    
    if not os.path.exists(document_folder):
        print(f"ERREUR: Dossier {document_folder} non trouvé")
        return
    
    # Lister tous les PDFs
    pdf_files = [f for f in os.listdir(document_folder) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("Aucun PDF trouvé dans Document/")
        return
    
    print(f"PDFs trouvés: {pdf_files}")
    
    success_count = 0
    for pdf_file in pdf_files:
        pdf_path = os.path.join(document_folder, pdf_file)
        if ocr_pdf(pdf_path):
            success_count += 1
    
    print(f"\nTraitement terminé: {success_count}/{len(pdf_files)} PDFs convertis")
    
    # Lister les Markdown créés
    if os.path.exists("33-FreightAgent/Markdown/"):
        md_files = [f for f in os.listdir("33-FreightAgent/Markdown/") if f.endswith('.md')]
        print(f"Fichiers Markdown créés: {md_files}")

## Configuration base de connaissances ###
knowledge_base = MarkdownKnowledgeBase(
    path="33-FreightAgent/Markdown/",
    vector_db=LanceDb(
        table_name="freight_documents",
        uri="33-FreightAgent/tmp/lancedb",
        search_type=SearchType.hybrid,
        embedder=OpenAIEmbedder(id="text-embedding-3-small", dimensions=1536),
    ),
)

freight_agent = Agent(
    name="Freight Agent",
    model=OpenAIChat(id="gpt-4o-mini", api_key=openai_key),
    instructions=dedent("""
    You are a Freight Cost Estimator Agent that helps small import/export businesses estimate and compare shipping costs and timelines across major carriers.

    You have access to:
    - A knowledge base built from 2024 rate guides and surcharge tables for UPS, FedEx, and DHL (converted from PDF via OCR)
    - DDGS search for live data and missing information

    When analyzing shipping requests, search your knowledge base FIRST for official rates, then supplement with web search if needed.
    
    Always provide detailed cost breakdowns, delivery estimates, and clear recommendations based on the specific product dimensions and requirements.
    """),
    tools=[ReasoningTools(add_instructions=True), ddgs_tool],
    knowledge=knowledge_base,
    search_knowledge=True,
)

def load_knowledge_base():
    """Charge la base de connaissances depuis les Markdown"""
    try:
        if os.path.exists("33-FreightAgent/Markdown/") and any(f.endswith('.md') for f in os.listdir("33-FreightAgent/Markdown/")):
            print("Chargement de la base de connaissances...")
            freight_agent.knowledge.load(recreate=False)
            print("Base de connaissances chargée avec succès")
        else:
            print("Aucun fichier Markdown trouvé - utilisation de DDGS uniquement")
    except Exception as e:
        print(f"Erreur lors du chargement: {e}")

def full_response(message):
    print('--------Freight Agent Triggered--------')
    try:
        response = freight_agent.run(message)
        return response.content
    except Exception as e:
        print(f"Erreur: {e}")
        return f"Erreur lors du traitement: {str(e)}"

if __name__ == '__main__':
    print("=== FREIGHT AGENT OCR SETUP ===")
    
    # Étape 1: Traiter les PDFs (décommentez pour exécuter)
    #process_all_pdfs()
    #exit()  # Arrête après traitement OCR
    
    # Étape 2: Charger la base de connaissances
    load_knowledge_base()
    
    # Test
    test_message = """
    User Question: Ship from Chicago, IL to Miami, FL
    Product Specifications: Machine parts, Weight: 300 lbs, Dimensions: 36"x24"x18", Industrial equipment
    """
    
    print("\nTest agent...")
    result = full_response(test_message)
    print(f"\nRésultat:\n{result}")