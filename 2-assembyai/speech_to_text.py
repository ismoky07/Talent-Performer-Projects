import assemblyai as aai
import os
from openai import OpenAI
from fpdf import FPDF
from dotenv import load_dotenv

class AudioAgent:
    def __init__(self):
        """Initialise l'agent avec les clés API"""
        load_dotenv()
        aai.settings.api_key = os.getenv("ASSEMBLY_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=openai_api_key)
    
    def transcribe_audio(self, audio_file_path):
        """Transcrit un fichier audio avec AssemblyAI"""
        config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.best)
        transcript = aai.Transcriber(config=config).transcribe(audio_file_path)
        return transcript
    
    def process_with_gpt(self, transcript_text, choice):
        """Traite le texte avec GPT selon le choix (résumé ou explication)"""
        prompt = f"Summarize the following transcript:\n{transcript_text}" if choice == "🔍 Summarize" else f"Explain in detail the following transcript:\n{transcript_text}"
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert transcription assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    
    def create_transcript_pdf(self, transcript_text):
        """Crée un PDF de la transcription"""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, transcript_text)
        pdf.output("transcript.pdf")
        return "transcript.pdf"
    
    def create_gpt_pdf(self, gpt_output):
        """Crée un PDF de la sortie GPT"""
        pdf_gpt = FPDF()
        pdf_gpt.add_page()
        pdf_gpt.set_auto_page_break(auto=True, margin=15)
        pdf_gpt.set_font("Arial", size=12)
        pdf_gpt.multi_cell(0, 10, gpt_output)
        pdf_gpt.output("gpt_output.pdf")
        return "gpt_output.pdf"