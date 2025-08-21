import os
import faiss
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from pypdf import PdfReader
import numpy as np

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

pdf = PdfReader("1-Agno/PDF/pwc-ai-analysis.pdf")
chunks = [page.extract_text() for page in pdf.pages if page.extract_text()]

all_chunks = []
for page in chunks:
    for paragraph in page.split('\n'):
        clean = paragraph.strip()
        if len(clean) > 50:
            all_chunks.append(clean)

embedder = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = embedder.encode(all_chunks, convert_to_numpy=True)

dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# CORRECTION : Gestion des paramètres None
def retrieve_from_vectorstore(agent, query, num_documents=3, **kwargs):
    if not query or len(query.strip()) == 0:
        return []
    
    # CORRECTION : Assurer que num_documents n'est jamais None
    if num_documents is None:
        num_documents = 3
    
    num_docs = min(num_documents, len(all_chunks))
    
    query_vec = embedder.encode([query])
    D, I = index.search(np.array(query_vec), num_docs)
    
    results = []
    for idx in I[0]:
        if 0 <= idx < len(all_chunks):
            results.append({
                "content": all_chunks[idx],
                "meta_data": {"source": f"PDF/pwc-ai-analysis.pdf - chunk {idx}"}
            })
    return results

full_text = "".join(page.extract_text() or "" for page in pdf.pages)
def always_return_full_pdf(agent, query, num_documents=None, **kwargs):
    return [{"content": full_text, "meta_data": {"source": "PDF/pwc-ai-analysis.pdf"}}]

USE_VECTORSTORE = True

agent = Agent(
    model=OpenAIChat(api_key=OPENAI_API_KEY, id="gpt-4o-mini"),
    knowledge=None,
    search_knowledge=True,
    retriever=retrieve_from_vectorstore if USE_VECTORSTORE else always_return_full_pdf
)

print(f"Agent RAG prêt! {len(all_chunks)} chunks chargés.")

while True:
    prompt = input("\nQuestion: ").strip()
    if prompt.lower() in ['quit', 'q', 'exit']:
        break
    if prompt:
        try:
            agent.print_response(prompt)
        except Exception as e:
            print(f"Erreur: {e}")
            print("Essayez une autre question.")