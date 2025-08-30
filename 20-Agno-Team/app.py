import streamlit as st
import tempfile
from pathlib import Path
from utils import get_document, set_document_file
from contract_analysis import create_manager_team

def main():
    st.title("📄 Analyseur de Contrats")
    
    # Upload du fichier
    uploaded_file = st.file_uploader(
        "Choisir un contrat", 
        type=['pdf', 'docx', 'txt']
    )
    
    if uploaded_file:
        # Sauvegarder temporairement
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            temp_file_path = tmp_file.name
        
        # Bouton d'analyse
        if st.button("🚀 Analyser le contrat", type="primary"):
            
            with st.spinner("Analyse en cours..."):
                try:
                    # Charger le document
                    set_document_file(temp_file_path)
                    
                    # Créer l'équipe d'agents
                    manager_team = create_manager_team()
                    
                    # Lancer l'analyse
                    result = manager_team.run("Analysez ce contrat complètement.")
                    
                    # Afficher les résultats
                    st.success("✅ Analyse terminée!")
                    
                    if hasattr(result, 'content'):
                        analysis_text = result.content
                    else:
                        analysis_text = str(result)
                    
                    st.markdown(analysis_text)
                    
                    # Bouton de téléchargement
                    st.download_button(
                        "📥 Télécharger le rapport",
                        analysis_text,
                        file_name=f"analyse_{uploaded_file.name}.md",
                        mime="text/markdown"
                    )
                    
                except Exception as e:
                    st.error(f"❌ Erreur: {str(e)}")

if __name__ == "__main__":
    main()