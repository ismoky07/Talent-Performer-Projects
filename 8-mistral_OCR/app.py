import streamlit as st
import os
from legal_copilot import OCRService

st.set_page_config(page_title="Legal Copilot", layout="wide")
st.title("⚖️ Legal Copilot - PDF OCR and Legal QA")

ocr_service = OCRService()
uploaded_file = st.file_uploader("📁 Upload a legal PDF file", type=["pdf"])
ocr_performed = False

if uploaded_file:
    os.makedirs("pdf", exist_ok=True)
    file_path = f"pdf/{uploaded_file.name}"
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())
    
    if st.button("🔍 Run OCR"):
        ocr_service.ocr_pdf(file_path)
        ocr_performed = True

if uploaded_file and ocr_service.ocr_is_valid(file_path) and st.checkbox("📄 Show extracted OCR text"):
    try:
        text = ocr_service.read_markdown_file("ocr_response.md")
        st.markdown(text)
    except Exception:
        st.warning("Error reading OCR content.")
elif not uploaded_file:
    st.info("Upload a PDF file to enable OCR analysis.")

st.markdown("### 📝 Document Summary")
if uploaded_file and ocr_service.ocr_is_valid(file_path) and st.button("📝 Generate Summary"):
    text = ocr_service.read_markdown_file("ocr_response.md")
    prompt = f"Summarize this legal document clearly and concisely:\n\n{text}"
    try:
        summary = ocr_service.run_mistral(prompt)
        st.markdown("#### 🔍 Summary:")
        st.markdown(summary)
    except Exception as e:
        st.error(f"Error during summarization: {e}")

st.markdown("### ❓ Ask a question about the document content")
question = st.text_input("Your question:")

if question:
    if not os.path.exists("ocr_response.md") or not ocr_service.ocr_is_valid(file_path):
        st.error("❌ No valid OCR data found. Please run OCR first.")
    else:
        try:
            response = ocr_service.process_question(question, file_path)
            st.markdown("### 🤖 Response")
            st.markdown(response)
        except Exception as e:
            st.error(f"Error while processing: {e}")