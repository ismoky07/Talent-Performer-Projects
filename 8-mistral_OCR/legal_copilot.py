
import os
from dotenv import load_dotenv
import time
import faiss
import numpy as np
import chardet
from mistralai import Mistral
import os

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
class OCRService:
    def __init__(self):
        self.client = Mistral(api_key=MISTRAL_API_KEY)
    
    def ocr_pdf(self, file_path):
        uploaded_pdf = self.client.files.upload(
            file={
                "file_name": file_path.split("/")[-1],
                "content": open(file_path, "rb"),
            },
            purpose="ocr"
        )
        
        signed_url = self.client.files.get_signed_url(file_id=uploaded_pdf.id)
        
        ocr_response = self.client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "document_url",
                "document_url": signed_url.url,
            },
            include_image_base64=True
        )
        
        with open("ocr_response.md", "w", encoding="utf-8") as f:
            f.write("\n".join([page.markdown for page in ocr_response.pages]))
        
        with open("ocr_meta.txt", "w") as meta:
            meta.write(file_path)
    
    def read_markdown_file(self, path):
        with open(path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']
        return raw_data.decode(encoding, errors='replace')
    
    def get_text_embedding(self, input):
        embeddings_batch_response = self.client.embeddings.create(
            model="mistral-embed",
            inputs=input
        )
        return embeddings_batch_response.data[0].embedding
    
    def run_mistral(self, user_message, model="mistral-large-latest"):
        messages = [{"role": "user", "content": user_message}]
        chat_response = self.client.chat.complete(model=model, messages=messages)
        return chat_response.choices[0].message.content
    
    def ocr_is_valid(self, file_path):
        if not os.path.exists("ocr_meta.txt"):
            return False
        with open("ocr_meta.txt", "r") as meta:
            last_file = meta.read().strip()
        return file_path == last_file
    
    def process_question(self, question, file_path):
        text = self.read_markdown_file("ocr_response.md")
        chunk_size = 2048
        chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
        
        text_embeddings = []
        for chunk in chunks:
            embedding = self.get_text_embedding(chunk)
            text_embeddings.append(embedding)
            time.sleep(2)
        
        text_embeddings = np.array(text_embeddings)
        question_embedding = np.array([self.get_text_embedding(question)])
        
        d = text_embeddings.shape[1]
        index = faiss.IndexFlatL2(d)
        index.add(text_embeddings)
        
        D, I = index.search(question_embedding, k=2)
        retrieved_chunk = [chunks[i] for i in I.tolist()[0]]
        
        prompt = f"""
Context information is below.
-------------------
{retrieved_chunk}
-------------------
Given the context information and not prior knowledge, answer the query.
Query: {question}
Answer:
"""
        
        return self.run_mistral(prompt)