import os
import requests
import streamlit as st
from textwrap import dedent
from agno.agent import Agent
from mistralai import Mistral
from agno.models.openai import OpenAIChat
from agno.vectordb.pgvector import PgVector
from agno.tools.reasoning import ReasoningTools
from agno.tools.googlesearch import GoogleSearchTools
from agno.knowledge.markdown import MarkdownKnowledgeBase
from dotenv import load_dotenv
load_dotenv()

mistral_key = os.getenv("MISTRAL_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")
client = Mistral(api_key=mistral_key)

## OCR the pdf ###
def ocr_pdf(pdf_path):
    # check if the file exists
    if not os.path.exists(pdf_path):
        st.error("PDF file not found")
        return
    
    uploaded_pdf = client.files.upload(
        file={
            "file_name": pdf_path,
            "content": open(pdf_path, "rb"),
        },
        purpose="ocr"
    )

    signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)

    ocr_response = client.ocr.process(
        model="mistral-ocr-latest",
        document={
            "type": "document_url",
            "document_url": signed_url.url,
        },
        include_image_base64=True
    )

    with open(f"DocumentMarkdown/ocr_document.md", "w") as f:
        f.write("\n".join([page.markdown for page in ocr_response.pages]))

def knowledge_base_setup():
    ### Setup Knowledge Base ###
    knowledge_base = MarkdownKnowledgeBase(
        path="DocumentMarkdown/ocr_document.md",
        vector_db=PgVector(
            table_name="markdown_documents",
            db_url="postgresql+psycopg://ai:ai@localhost:5532/ai",
        ),
    )
    return knowledge_base

def semantic_scholar_search(query):
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {"query": query}
    headers = {"x-api-key": "1234567890"}
    response = requests.get(url, params=params, headers=headers)
    return response.json()

def summary_agent():
    knowledge_base = knowledge_base_setup()
    summary_agent = Agent(
        name="Summary Agent",
        model=OpenAIChat(id="gpt-4o-mini", api_key="openai_key"),
        instructions=dedent("""
        You are a summary agent designed to summarize the document.
        Read the entire document stored in the knowledge base (in markdown format) and produce a concise summary in plain English. Keep it focused on the paper’s objective, methodology, and key findings.
        """),
        knowledge=knowledge_base,
        search_knowledge=True,
    )
    summary_agent.knowledge.load(recreate=False)
    return summary_agent

def agent_setup():
    knowledge_base = knowledge_base_setup()
    research_agent = Agent(
        name="Research Agent",
        model=OpenAIChat(id="gpt-4o-mini", api_key=openai_key),
        instructions=dedent("""
        You are a research assistant designed to simplify and answer questions about academic papers. Your behavior follows this logic:

        1. **Answering Questions**:
        - When a user asks a question, try to answer it using the internal knowledge base first.
        - If you find an answer, cite the **exact source** from the markdown document (quote the relevant sentence or paragraph).
        - Format the answer clearly and showably: include the answer, the citation snippet, and its section or approximate heading if available.

        2. **Fallback to External Tools**:
        - If the knowledge base doesn't contain enough information to answer:
            - Use `semantic_shcolar_search(query)` to look for external answers.
            - If that fails, retry once.
            - If it still fails, use `GoogleSearchTool(query)` as a backup.
        - When using external tools, always show the **source link** or citation (title, author if possible, and source URL).
        - Keep external answers clean, brief, and properly attributed.

        3. **Formatting**:
        - Always use clean markdown formatting.
        - Highlight the **source** of every answer clearly.
        - Avoid hallucinating—if you don’t know, say you’ll look it up.

        Your top priorities are accuracy, traceability (always show the source), and clarity.
        """),
        knowledge=knowledge_base,
        search_knowledge=True,
        tools=[ReasoningTools(add_instructions=True), semantic_scholar_search, GoogleSearchTools()],
    )
    research_agent.knowledge.load(recreate=False)

    return research_agent

if __name__ == "__main__":
    if "ocr_done" not in st.session_state:
        st.session_state.ocr_done = False

    if "knowledge_base" not in st.session_state:
        st.session_state.knowledge_base = None

    if "summary_agent" not in st.session_state:
        st.session_state.summary_agent = None

    if "agent" not in st.session_state:
        st.session_state.agent = None

    st.title("Advanced Research Assistant")
    uploaded_file = st.file_uploader("Upload your research paper", type=["pdf"])
    if uploaded_file and not st.session_state.ocr_done:
        with open(f"DocumentMarkdown/{uploaded_file.name}", "wb") as f:
            f.write(uploaded_file.read())
        with st.spinner("Performing OCR..."):
            ocr_pdf(f"DocumentMarkdown/{uploaded_file.name}")
        st.success("OCR completed successfully")
        st.session_state.ocr_done = True
        st.session_state.summary_agent = summary_agent()
        with st.spinner("Generating summary..."):
            summary_response = st.session_state.summary_agent.run("Summarize the document")
            st.write(summary_response.content)
        # st.session_state.knowledge_base = knowledge_base_setup()
        st.session_state.agent = agent_setup()

    if st.session_state.ocr_done:
        user_input = st.text_input("Enter a question: ")
        if st.button("Submit"):
            with st.spinner('Response is being generated in your terminal'):
                st.session_state.agent.print_response(
                    user_input,
                    stream=True,
                    show_full_reasoning=True,
                    stream_intermediate_steps=True
                )
            st.success('Response generated successfully')
            # response = research_agent.run(user_input)
            # st.write(response)


## How the pipeline-based approach decomposes the document parsing workflow