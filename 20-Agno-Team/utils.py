from pathlib import Path
import fitz  # PyMuPDF

# Variable globale
current_file_path = None

def set_document_file(file_path):
    """Définit le fichier à analyser"""
    global current_file_path
    current_file_path = file_path

def get_document():
    """Retourne le contenu du fichier"""
    global current_file_path
    
    if not current_file_path:
        return {"error": "Aucun fichier", "content": ""}
    
    file_path = Path(current_file_path)
    extension = file_path.suffix.lower()
    
    try:
        if extension == '.pdf':
            content = extract_pdf(file_path)
        elif extension in ['.docx', '.doc']:
            content = extract_word_simple(file_path)
        elif extension == '.txt':
            content = extract_text(file_path)
        else:
            return {"error": "Format non supporté", "content": ""}
        
        return {"content": content, "error": None}
    
    except Exception as e:
        return {"error": str(e), "content": ""}

def extract_pdf(file_path):
    """Extrait le texte d'un PDF"""
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def extract_word_simple(file_path):
    """Extrait le texte d'un fichier Word avec PyMuPDF"""
    try:
        # PyMuPDF peut aussi lire les fichiers Word !
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except:
        return "Erreur: Impossible de lire ce fichier Word. Convertissez-le en PDF."

def extract_text(file_path):
    """Extrait le texte d'un fichier texte"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()