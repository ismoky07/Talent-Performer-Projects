import os
import requests
from datetime import datetime, timedelta
from textwrap import dedent
from agno.agent import Agent
from dotenv import load_dotenv
from agno.models.openai import OpenAIChat

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TODOIST_API_KEY = os.getenv("TODOIST_API_KEY")
HEADERS = {
    "Authorization": f"Bearer {TODOIST_API_KEY}",
    "Content-Type": "application/json"
}

def get_tasks():
    response = requests.get("https://api.todoist.com/rest/v2/tasks", headers=HEADERS)
    if response.ok:
        return response.json()
    return []

def add_task(content, due_datetime=None):
    payload = {"content": content}
    if due_datetime:
        payload["due_datetime"] = due_datetime
    response = requests.post("https://api.todoist.com/rest/v2/tasks", headers=HEADERS, json=payload)
    return response.ok

def get_current_datetime():
    url = 'https://timeapi.io/api/Time/current/zone?timeZone=Africa/Casablanca'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data["dateTime"]
    else:
        return None

# NOUVELLES FONCTIONS D'AIDE POUR L'AGENT
def get_tasks_for_date(date_str):
    """Récupère les tâches pour une date spécifique (format: 2025-08-30)"""
    all_tasks = get_tasks()
    tasks_for_date = []
    
    for task in all_tasks:
        if task.get("due") and task["due"].get("date") == date_str:
            tasks_for_date.append({
                "content": task["content"],
                "time": task["due"].get("datetime", "Pas d'heure spécifique")
            })
    
    return tasks_for_date

def get_today_date():
    """Retourne la date d'aujourd'hui au format 2025-08-29"""
    current_dt = get_current_datetime()
    if current_dt:
        # Extraire juste la date (YYYY-MM-DD)
        return current_dt.split("T")[0]
    return None

def get_tomorrow_date():
    """Retourne la date de demain au format 2025-08-30"""
    today = get_today_date()
    if today:
        # Convertir en date et ajouter 1 jour
        today_dt = datetime.strptime(today, "%Y-%m-%d")
        tomorrow_dt = today_dt + timedelta(days=1)
        return tomorrow_dt.strftime("%Y-%m-%d")
    return None

agent = Agent(
    model=OpenAIChat(id="gpt-4o", api_key=OPENAI_API_KEY),
    instructions = dedent("""
    Tu es un assistant personnel qui gère les tâches via WhatsApp.
    
    🔧 TES OUTILS DISPONIBLES:
    - get_current_datetime() : heure actuelle complète
    - get_today_date() : date d'aujourd'hui (format: 2025-08-29)  
    - get_tomorrow_date() : date de demain (format: 2025-08-30)
    - get_tasks() : toutes les tâches
    - get_tasks_for_date(date) : tâches pour une date précise
    - add_task(content, due_datetime) : ajouter une tâche
    
    📋 COMMENT RÉPONDRE:
    
    Pour "J'ai combien de tâches demain?":
    1. Appeler get_tomorrow_date()
    2. Appeler get_tasks_for_date(date_de_demain)  
    3. Compter et lister les tâches
    
    Pour "Mes tâches aujourd'hui":
    1. Appeler get_today_date()
    2. Appeler get_tasks_for_date(date_aujourd_hui)
    3. Lister les tâches
    
    Pour ajouter une tâche demain à 15h:
    1. Appeler get_tomorrow_date() → "2025-08-30"
    2. Créer datetime: "2025-08-30T15:00:00Z"
    3. Appeler add_task("contenu", "2025-08-30T15:00:00Z")
    
    ✅ EXEMPLES DE RÉPONSES:
    - "📅 Vous avez 2 tâches demain : 🛒 Courses (pas d'heure), 📞 Appel (15h)"
    - "✅ Tâche ajoutée pour demain !"
    - "🎉 Aucune tâche prévue demain"
    
    Sois simple, direct et utilise des emojis appropriés.
    """),
    markdown=True,
    tools=[get_current_datetime, get_today_date, get_tomorrow_date, get_tasks, get_tasks_for_date, add_task]
)

def get_response(message):
    response = agent.run(message)
    return response.content

if __name__ == "__main__":
    print(get_response("J'ai combien de tâches demain?"))