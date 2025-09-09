import streamlit as st
import requests
import json
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="HR Assistant",
    page_icon="👥",
    layout="centered"
)

# URL de votre API Flask
API_BASE_URL = "http://127.0.0.1:5000"

# Titre principal
st.title("HR Assistant System")

# Zone Employee ID
col1, col2 = st.columns([1, 2])
with col1:
    employee_id = st.number_input("Employee ID:", min_value=1, value=1)
with col2:
    st.write("")  # Espace vide

# Fonction pour appeler l'API
def call_hr_api(message):
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={"message": message},
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("response", "Pas de réponse")
        else:
            return f"Erreur API: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return "Erreur: Serveur HR non accessible"
    except Exception as e:
        return f"Erreur: {str(e)}"

# Zone de chat
st.subheader("Chat")

# Initialiser l'historique
if "messages" not in st.session_state:
    st.session_state.messages = []

# Afficher les messages
for message in st.session_state.messages:
    if message["role"] == "user":
        st.write(f"**Vous:** {message['content']}")
    else:
        st.write(f"**Assistant:** {message['content']}")

# Zone de saisie
user_input = st.text_input("Votre message:", placeholder="Ex: Combien de jours de congés me reste-t-il ?")

# Boutons
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Envoyer") and user_input:
        # Ajouter Employee ID au message
        full_message = f"Employee ID: {employee_id}. {user_input}"
        
        # Ajouter à l'historique
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Appeler l'API
        with st.spinner("En cours..."):
            response = call_hr_api(full_message)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

with col2:
    if st.button("Mes congés"):
        message = f"Employee ID: {employee_id}. Quel est mon solde de congés ?"
        st.session_state.messages.append({"role": "user", "content": "Mes congés"})
        
        with st.spinner("En cours..."):
            response = call_hr_api(message)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

with col3:
    if st.button("Mon projet"):
        message = f"Employee ID: {employee_id}. Quel est mon projet actuel ?"
        st.session_state.messages.append({"role": "user", "content": "Mon projet"})
        
        with st.spinner("En cours..."):
            response = call_hr_api(message)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

# Bouton pour vider l'historique
if st.button("Vider le chat"):
    st.session_state.messages = []
    st.rerun()

# Test de connexion
st.subheader("Test de connexion")
if st.button("Tester l'API"):
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        st.success("Connexion OK")
    except:
        st.error("Connexion échouée - Vérifiez que le serveur Flask est démarré")