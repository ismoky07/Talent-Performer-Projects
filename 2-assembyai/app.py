import streamlit as st
from dotenv import load_dotenv
import os
from fpdf import FPDF
from speech_to_text import AudioAgent

# Load environment variables
load_dotenv()

# Initialize agent
agent = AudioAgent()

# Streamlit UI
st.title("🎤 Speech to Text + GPT Summary/Explanation")

uploaded_audio = st.file_uploader("Upload your audio file (.mp3, .wav)", type=["mp3", "wav"])
if uploaded_audio is not None:
    # Save temporary file
    with open("temp_audio_file", "wb") as f:
        f.write(uploaded_audio.getbuffer())
    
    # Transcription
    with st.spinner("🔊 Transcribing..."):
        transcript = agent.transcribe_audio("temp_audio_file")
        
    if transcript.status == "error":
        st.error(f"❌ Transcription failed: {transcript.error}")
    else:
        st.success("✅ Transcription complete")
        st.text_area("📝 Transcript:", transcript.text, height=200)
        
        # Export transcription to PDF
        if st.button("📄 Download transcript PDF"):
            pdf_path = agent.create_transcript_pdf(transcript.text)
            with open(pdf_path, "rb") as f:
                st.download_button("Download PDF", f, file_name="transcript.pdf")
        
        # GPT choice
        choice = st.radio("What do you want GPT to do?", ["🔍 Summarize", "📖 Explain in detail"])
        if st.button("Run GPT"):
            with st.spinner("🤖 GPT is thinking..."):
                gpt_output = agent.process_with_gpt(transcript.text, choice)
            
            st.success("✅ GPT response ready")
            st.text_area("🤖 GPT Output:", gpt_output, height=300)
            
            # Export GPT result to PDF
            if st.button("📑 Download GPT Output PDF"):
                pdf_path = agent.create_gpt_pdf(gpt_output)
                with open(pdf_path, "rb") as f:
                    st.download_button("Download GPT Output PDF", f, file_name="gpt_output.pdf")