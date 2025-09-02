import streamlit as st
from import_export_agent import *

# Streamlit UI
if __name__ == "__main__":
    st.title("Import Export Specialist Multi-Agent System")

    product_details = st.text_input("Enter product and shipment details")

    if st.button("Submit"):
        with st.spinner("Running multi-agent workflow..."):
            # Get PDFs and process them
            ocr_pdf("Documents/uk-export-law.pdf", "uk-export-law")
            ocr_pdf("Documents/morocco-import-law.pdf", "morocco-import-law")
            
            # Translation step
            translation_response = translation_agent.run(import_law_document(None, None))
            with open("Documents/morocco-import-law-en.md", "w") as f:
                f.write(translation_response.content)
            
            # Specialist analysis
            specialist_agent.retriever = [export_law_document, import_law_document]
            specialist_response = specialist_agent.run(product_details)
            
            # Display specialist report
            st.subheader("📋 Specialist Compliance Report")
            st.markdown(specialist_response.content)
            
            # Verification step
            verification_response = verification_agent.run(specialist_response.content)
            st.subheader("✅ Verification Feedback")
            st.markdown(verification_response.content)
            
            # Risk analysis
            risk_response = risk_agent.run(specialist_response.content)
            st.subheader("⚠️ Risk Analysis")
            st.markdown(risk_response.content)