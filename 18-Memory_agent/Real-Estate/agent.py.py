import os
import json
import faiss
import warnings
from mem0 import MemoryClient
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from sentence_transformers import SentenceTransformer

# Supprimer les avertissements de dépréciation
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Charger les variables d'environnement
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MEM0_API_KEY = os.getenv("MEM0_API_KEY") 
USER_ID = "Ismo"

class MemoryTools:
    """Classe pour gérer la mémoire persistante et la recherche vectorielle"""
    
    def __init__(self):
        """Initialisation du client mémoire et des outils de recherche"""
        self.mem0_client = MemoryClient(MEM0_API_KEY)
        
        # Initialisation du modèle d'embedding et de l'index FAISS
        self._initialize_search_system()
    
    def _initialize_search_system(self):
        """Initialise le système de recherche vectorielle FAISS"""
        # Chargement des données JSON des propriétés
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        
        try:
            with open(os.path.join(BASE_DIR, "agency_property_data.json"), "r") as f:
                self.data = json.load(f)
        except FileNotFoundError:
            print("⚠️ Fichier de données immobilières non trouvé")
            self.data = []
        
        # Initialisation du modèle d'embedding
        self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Extraction des textes pour l'embedding
        self.texts = self._extract_property_texts()
        
        # Calcul des embeddings
        if self.texts:
            embeddings = self.embed_model.encode(self.texts, convert_to_numpy=True)
            
            # Création de l'index FAISS
            dim = embeddings.shape[1]
            self.faiss_index = faiss.IndexFlatL2(dim)
            self.faiss_index.add(embeddings)
        else:
            self.faiss_index = None
    
    def _extract_property_texts(self) -> list:
        """Extrait et formate les textes des propriétés pour l'embedding"""
        texts = []
        
        for item in self.data:
            # Création d'un texte descriptif complet pour chaque propriété
            property_text = (
                f"{item.get('title', '')} "
                f"{item.get('description', '')} "
                f"{item.get('location', '')} "
                f"{str(item.get('price', ''))} "
                f"{item.get('currency', '')} "
                f"{str(item.get('surface_area', ''))} "
                f"{str(item.get('rooms', ''))} "
                f"{str(item.get('bedrooms', ''))} "
                f"{str(item.get('bathrooms', ''))} "
                f"{' '.join(item.get('features', []))} "
                f"{item.get('status', '')}"
            )
            texts.append(property_text)
        
        return texts
    
    def save_info(self, information: str) -> dict:
        """Sauvegarde les préférences importantes du client en mémoire"""
        try:
            # Stockage dans Mem0
            response = self.mem0_client.add(
                [{"role": "user", "content": information}],
                user_id=USER_ID,
                run_id="real_estate_session",
                metadata={"type": "property_info"}
            )
            
            return {
                "status": "success",
                "message": "Informations client sauvegardées avec succès",
                "response": response
            }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erreur lors de la sauvegarde: {str(e)}"
            }
    
    def retrieve_info(self, query: str) -> dict:
        """Récupère les informations pertinentes du client depuis la mémoire"""
        try:
            # Recherche dans Mem0
            results = self.mem0_client.search(
                query,
                user_id=USER_ID,
                limit=5,
                threshold=0.7,  # Seuil plus élevé pour des résultats plus pertinents
                output_format="v1.1"
            )
            
            # Formatage et retour des résultats
            if results and len(results) > 0:
                memories = [memory["memory"] for memory in results.get("results", [])]
                return {
                    "status": "success", 
                    "memories": memories, 
                    "count": len(memories)
                }
            else:
                return {
                    "status": "no_results", 
                    "memories": [], 
                    "count": 0
                }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erreur lors de la récupération: {str(e)}",
                "memories": [],
                "count": 0
            }
    
    def search_faiss(self, query: str, top_k: int = 5) -> dict:
        """Recherche FAISS et retourne les top_k résultats"""
        try:
            if not self.faiss_index or not self.texts:
                return {
                    "status": "error",
                    "message": "Index FAISS non initialisé",
                    "results": [],
                    "count": 0
                }
            
            # Encodage de la requête
            query_vec = self.embed_model.encode([query], convert_to_numpy=True)
            
            # Recherche dans l'index FAISS
            D, I = self.faiss_index.search(query_vec, top_k)
            
            # Récupération des résultats originaux
            results = []
            for idx in I[0]:
                if idx < len(self.data):  # Vérification des limites
                    results.append(self.data[idx])
            
            return {
                "status": "success", 
                "results": results, 
                "count": len(results)
            }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erreur lors de la recherche: {str(e)}",
                "results": [],
                "count": 0
            }
    
    def schedule_appointment(self, date: str, time: str, reason: str) -> dict:
        """Programme un rendez-vous"""
        try:
            # Dans une vraie application, ceci se connecterait à un système de planification
            appointment_id = f"APPT-{hash(date + time) % 10000}"
            
            return {
                "status": "success",
                "appointment_id": appointment_id,
                "confirmation": f"Appointment scheduled for {date} at {time} for {reason}"
            }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erreur lors de la planification: {str(e)}"
            }
    
    def get_contact_info(self) -> dict:
        """Retourne les informations de contact de l'agence"""
        return {
            "status": "success",
            "contact_info": "You can contact the agency at +33 6 12 34 56 78 or by email at realestateagency@mail.com"
        }


# ==============================================================================
# CRÉATION DE L'AGENT IMMOBILIER
# ==============================================================================
def create_real_estate_agent():
    """Crée et configure l'agent IA immobilier professionnel"""
    
    # Initialisation des outils mémoire
    memory_tools = MemoryTools()
    
    # Création de l'agent avec LiteLlm pour OpenAI
    root_agent = LlmAgent(
        name="real_estate_assistant",
        model=LiteLlm(model="openai/gpt-4o-mini"),
        
        description="""
        AI-powered Real Estate Assistant for a reputable agency, supporting clients by recording preferences, 
        retrieving past inquiries, searching property listings, scheduling viewings, and providing professional guidance.
        """,
        
        instruction="""
        You are a professional Real Estate Assistant representing a top-tier agency in France. Always speak in a courteous, confident, and expert manner—just like a senior agent at our firm.

        When you greet a user:
        - Use a formal opening (e.g., "Good day. We are a Real Estate Agency. How may I assist you with finding your next property?")

        Core responsibilities:
        1. **Recording client preferences and details** using the `save_info` tool (e.g., preferred neighborhoods, budgets, must-have features).
        2. **Retrieving past inquiries or saved preferences** via `retrieve_info` so the conversation feels consistent and personalized.
        3. **Searching property listings** with `search_faiss` to provide concise summaries of matching properties, including location, price (formatted in EUR), surface area, bedrooms, and standout features.
        4. **Scheduling property viewings or appointments** via `schedule_appointment` once the client has identified properties of interest.
        5. **Providing agency contact information** by invoking `get_contact_info` whenever the user requests it or if you need them to have our phone/email.

        🔺 GUIDELINES & BEHAVIOR:
        - Maintain a professional, friendly, and helpful tone at all times—like a high-end real estate broker.
        - Do NOT offer legal, financial, or investment advice. Instead, suggest they consult qualified professionals for those matters.
        - Always ask for missing contact details of the client using `get_contact_info` when appropriate (e.g., "May I share our agency's phone number with you so you can call directly?").
        - Respect client privacy—never expose or share their personal info outside the scope of this conversation.
        - Before requesting any new information, check existing memory with `retrieve_info`.
        - Offer only the most relevant listings to avoid overwhelming the client.
        - Confirm actions (saving info, scheduling viewings, offering contact info) clearly and politely.

        🔒 COMPLIANCE & PRIVACY:
        - Treat all client data as strictly confidential.

        Your goal is to emulate a boutique real estate agency: knowledgeable, professional, and fully attentive to each client's needs.
        """,
        
        # Outils disponibles pour l'agent
        tools=[
            memory_tools.save_info,
            memory_tools.retrieve_info, 
            memory_tools.search_faiss,
            memory_tools.schedule_appointment,
            memory_tools.get_contact_info,
        ],
    )
    
    return root_agent


# ==============================================================================
# POINT D'ENTRÉE PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    try:
        # Initialisation des outils mémoire
        memory_tools = MemoryTools()
        
        # Créer l'agent immobilier
        real_estate_agent = create_real_estate_agent()
        
        print("🏠 Assistant IA Immobilier initialisé avec succès!")
        print(f"👤 Utilisateur: {USER_ID}")
        print("🚀 Prêt à accompagner vos clients...")
        
        # Informations sur les données chargées
        if hasattr(memory_tools, 'data') and memory_tools.data:
            print(f"📊 {len(memory_tools.data)} propriétés chargées dans la base")
        else:
            print("⚠️ Aucune donnée de propriété chargée")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        print("Vérifiez vos clés API et dépendances")