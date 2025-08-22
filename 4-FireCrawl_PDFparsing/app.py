import streamlit as st
from pdf_analyzer import extract_pdf_content, analyze_question

# 🖥️ Interface utilisateur
st.set_page_config(page_title="Analyse PDF IA", layout="wide")
st.title("🔍 Analyse Intelligente de PDF")
st.markdown("Entrez l'URL d'un PDF public pour extraire et interroger son contenu.")

# 📥 URL de l'utilisateur
pdf_url = st.text_input("🔗 URL du PDF :", value="https://www.pwc.com/gx/en/issues/analytics/assets/pwc-ai-analysis-sizing-the-prize-report.pdf")

# ⚡ Traitement
if pdf_url:
    with st.spinner("⏳ Extraction du contenu en cours..."):
        extracted_text, error = extract_pdf_content(pdf_url)
        
        if error:
            st.error(f"❌ {error}")
        else:
            # ✅ Affichage
            st.success("✅ Contenu extrait avec succès.")
            with st.expander("📋 Voir le contenu extrait (nettoyé)", expanded=True):
                st.text_area("Contenu PDF", extracted_text, height=500)
            
            st.subheader("❓ Posez une question au sujet du PDF")
            question = st.text_input("Votre question :", placeholder="Ex: Quel est l'impact économique de l'IA ?")
            
            if question:
                with st.spinner("🤔 Analyse de la question par l'agent..."):
                    answer, error = analyze_question(question, extracted_text)
                    
                    if error:
                        st.error(f"❌ {error}")
                    else:
                        st.markdown("### 💬 Réponse de l'IA")
                        st.markdown(answer)