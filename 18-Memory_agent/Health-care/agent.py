import os
from mem0 import MemoryClient
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration
USER_ID = "Isma"
APP_NAME = "agent"
SESSION_ID_SCHEMA_AGENT = "session_agent"
MEM0_API_KEY = os.getenv("MEM0_API_KEY")  

class PatientService:
    """Service pour gérer les informations des patients avec mémoire persistante"""
    
    def __init__(self, user_id) -> None:
        """Initialise le service avec l'ID utilisateur"""
        self.user_id = user_id
        if MEM0_API_KEY:
            self.memo_client = MemoryClient(api_key=MEM0_API_KEY)
            self.use_mem0 = True
        else:
            self.memo_client = None
            self.use_mem0 = False
            self.local_memory = {}
    
    def save_patient_info(self, information: str) -> dict:
        """Sauvegarde les informations importantes du patient en mémoire."""
        try:
            if self.use_mem0 and self.memo_client:
                response = self.memo_client.add(
                    [{"role": "user", "content": information}],
                    user_id=self.user_id,
                    run_id="healthcare_session1",
                    metadata={"type": "patient_info"}
                )
                return {"status": "success", "message": "Information sauvegardée"}
            else:
                # Fallback local
                if self.user_id not in self.local_memory:
                    self.local_memory[self.user_id] = []
                self.local_memory[self.user_id].append(information)
                return {"status": "success", "message": "Information sauvegardée localement"}
        except Exception as e:
            return {"status": "error", "message": f"Erreur: {str(e)}"}
    
    def retrieve_patient_info(self, query: str) -> dict:
        """Récupère les informations pertinentes du patient depuis la mémoire."""
        try:
            if self.use_mem0 and self.memo_client:
                results = self.memo_client.search(
                    query,
                    user_id=self.user_id,
                    limit=5,
                    threshold=0.7,
                    output_format="v1.1"
                )
                
                if results and len(results) > 0:
                    memories = [memory["memory"] for memory in results.get("results", [])]
                    return {"status": "success", "memories": memories, "count": len(memories)}
                else:
                    return {"status": "no_results", "memories": [], "count": 0}
            else:
                # Fallback local
                if self.user_id in self.local_memory and self.local_memory[self.user_id]:
                    memories = self.local_memory[self.user_id]
                    return {"status": "success", "memories": memories, "count": len(memories)}
                else:
                    return {"status": "no_results", "memories": [], "count": 0}
        except Exception as e:
            return {"status": "error", "message": f"Erreur: {str(e)}", "memories": [], "count": 0}
    
    def schedule_appointment(self, date: str, time: str, reason: str) -> dict:
        """Programme un rendez-vous médical."""
        try:
            appointment_id = f"APPT-{hash(date + time) % 10000}"
            return {
                "status": "success",
                "appointment_id": appointment_id,
                "confirmation": f"Rendez-vous programmé le {date} à {time} pour {reason}",
                "message": "Merci d'arriver 15 minutes en avance."
            }
        except Exception as e:
            return {"status": "error", "message": f"Erreur: {str(e)}"}

# Initialiser le service
patient_service = PatientService(USER_ID)

# IMPORTANT: Créer l'agent au niveau du module pour ADK
root_agent = LlmAgent(
    name="healthcare_assistant",
    model=LiteLlm(model="openai/gpt-4o-mini"),
    description="Assistant IA Santé pour accompagner les patients",
    
    instruction="""
    Vous êtes un assistant IA de santé professionnel et bienveillant.
    
    Quand on vous salue, répondez chaleureusement en vous présentant.
    
    Vos responsabilités:
    1. Enregistrer les informations de santé avec save_patient_info
    2. Récupérer l'historique avec retrieve_patient_info  
    3. Programmer des rendez-vous avec schedule_appointment
    
    Comportement:
    - Ton empathique et professionnel
    - Ne donnez JAMAIS de diagnostic médical
    - Encouragez à consulter un professionnel pour les symptômes sérieux
    - Respectez la confidentialité
    
    Exemple de salutation: "Bonjour ! Je suis votre assistant santé IA. Comment puis-je vous aider aujourd'hui ?"
    """,
    
    tools=[
        patient_service.save_patient_info,
        patient_service.retrieve_patient_info,
        patient_service.schedule_appointment,
    ],
)

# Code d'initialisation optionnel
if __name__ == "__main__":
    print("Assistant IA Santé prêt")
    print(f"Utilisateur: {USER_ID}")