# app.py
"""
Interface Streamlit pour l'application de scraping immobilier
"""

import streamlit as st
from scraping import scrape_and_parse, get_ai_summary, save_to_airtable

# Interface utilisateur
st.set_page_config(page_title="Scraping Immobilier IA", layout="wide")
st.title("🏠 Scraping Immobilier avec Analyse IA")
st.markdown("Ce projet extrait les annonces immobilières et les analyse via un agent IA.")

# Session state
if "records" not in st.session_state:
    st.session_state.records = []

if "summaries" not in st.session_state:
    st.session_state.summaries = {}

# URL cible
url = st.text_input("URL à scraper :", value="https://www.century21.fr/annonces/achat-maison/v-bordeaux/")

# Scraper & analyser
if st.button("Lancer l'extraction et l'analyse"):
    with st.spinner("🔄 Récupération des données..."):
        try:
            st.session_state.records = scrape_and_parse(url)
            
            if st.session_state.records:
                st.success(f"✅ {len(st.session_state.records)} annonces trouvées !")
            else:
                st.warning("⚠️ Aucune annonce trouvée. Vérifiez les logs de debug ci-dessous.")
                st.info("💡 Conseils de dépannage:")
                st.markdown("""
                - L'URL est-elle accessible ?
                - Le site a-t-il changé de structure ?
                - Consultez les logs de debug dans la console/terminal
                """)
            
        except Exception as e:
            st.error(f"❌ Erreur : {e}")
            st.code(str(e), language="python")

# Affichage et IA
if st.session_state.records:
    for i, record in enumerate(st.session_state.records, 1):
        with st.expander(f"Annonce {i} - {record['ref']}"):
            st.write(f"**Prix :** {record['price']}")
            st.write(f"**Localisation :** {record['location']}")
            st.write(f"**Description :** {record['description']}")
            
            # Résumé IA avec cache
            if record['ref'] not in st.session_state.summaries:
                with st.spinner("🤖 Génération de l'analyse..."):
                    summary = get_ai_summary(record)
                    st.session_state.summaries[record['ref']] = summary
            
            st.markdown("### 🤖 Résumé IA")
            st.markdown(st.session_state.summaries[record['ref']])
            
            # Envoi à Airtable
            if st.button(f"📊 Enregistrer annonce {i} dans Airtable", key=f"btn_{i}"):
                record_with_summary = {
                    **record,
                    "summary": st.session_state.summaries[record['ref']]
                }
                
                success, message = save_to_airtable(record_with_summary)
                
                if success:
                    st.success("✅ Enregistré dans Airtable")
                else:
                    st.error("❌ Échec Airtable")
                    st.code(message, language="json")