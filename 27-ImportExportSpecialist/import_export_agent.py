import os
from textwrap import dedent
from dotenv import load_dotenv
from mistralai import Mistral
from agno.models.openai import OpenAIChat
from agno.agent import Agent
from agno.tools.googlesearch import GoogleSearchTools

# 🔑 Load API keys from .env
load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")
mistral_key = os.getenv("MISTRAL_API_KEY")

# 🤖 Initialize Mistral client
client = Mistral(api_key=mistral_key)

# 📄 OCR PDF to Markdown
def ocr_pdf(pdf_path, pdf_name):
    if not os.path.exists(pdf_path):
        return False
    
    uploaded_pdf = client.files.upload(
        file={"file_name": pdf_path, "content": open(pdf_path, "rb")},
        purpose="ocr"
    )
    
    signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)
    
    ocr_response = client.ocr.process(
        model="mistral-ocr-latest",
        document={"type": "document_url", "document_url": signed_url.url},
        include_image_base64=True
    )
    
    with open(f"Documents/{pdf_name}.md", "w") as f:
        f.write("\n".join([page.markdown for page in ocr_response.pages]))
    
    return True

# 📚 Load OCR outputs
def export_law_document(agent, query, num_documents=None, **kwargs):
    with open("Documents/uk-export-law.md", "r") as f:
        return f.read()

def import_law_document(agent, query, num_documents=None, **kwargs):
    with open("Documents/morocco-import-law.md", "r") as f:
        return f.read()

# 🔄 Translation Agent
translation_agent = Agent(
    name="Translation Agent",
    model=OpenAIChat(api_key=openai_key, id="gpt-4o-mini"),
    instructions=dedent("""
    You are an expert in translation. You are given a text in markdown format in French and you need to translate it to English.
    IMPORTANT: Keep the same structure and content of the original text.
    """),
)

# 🎯 Export-Import Compliance Expert
specialist_agent = Agent(
    name="Specialist Agent",
    model=OpenAIChat(api_key=openai_key, id="gpt-4o-mini"),
    instructions=dedent("""
    You are an Export-Import Compliance Expert with access to two knowledge sources:
    - The official UK export law document for electronics (including licences, restrictions, taxes, fees).
    - The official Moroccan import law document for electronics (including permits, quantity limits, import duties, VAT, prohibited items, and customs procedures).
    
    You also have access to GoogleSearchTools() to find up-to-date, authoritative data when it is missing or unclear.
    
    Your task is: given detailed product info (type, quantity, raw materials) and the shipment route (UK to Morocco), provide a **full, precise, step-by-step explanation** of:
    
    1. **UK export process**:
    - Exact licence requirements by name and code,
    - Clear restrictions on product types or materials,
    - Specific export taxes, fees, or levies with exact amounts or percentages,
    - Necessary documentation, including official form names or codes,
    - Compliance rules and penalties with numbers and legal references.
    
    2. **Moroccan import process**:
    - Precise import permits and certifications required,
    - Exact quantity restrictions or exemptions,
    - Detailed import duties and VAT rates with percentages or fixed amounts,
    - List of prohibited or restricted items by name and code,
    - Required documents with official titles,
    - Customs clearance steps with timelines and fees.
    
    Use only **facts and figures extracted from your knowledge base or from live, authoritative sources**. Do not guess or be vague.
    
    If any data is missing in your knowledge, immediately perform a GoogleSearchTools() lookup for official government or customs sites and incorporate exact data found.
    
    Present the response in clear, professional language, with no filler text or disclaimers.
    
    Provide the output as a flowing narrative, but include concrete numbers, names, codes, and references wherever applicable.
    
    The goal is to give the user a complete, actionable export-import compliance report with real numbers and official requirements.
    
    If data is unavailable, explicitly state that you researched and could not find updated official info.
    """),
    expected_output=dedent("""
    ### UK Export Process
    
    [Explain if an export licence is required for the product. Specify licence type and official code if available.]
    [Mention any restrictions on product types, raw materials, or dual-use classifications found in the UK export law document.]
    [Provide specific export taxes or fees applicable, with exact amounts or percentages, citing the document.]
    [Describe required paperwork and compliance steps before shipment.]
    
    ### Moroccan Import Process
    
    [Detail import permits, licences, or certifications required for the product according to the Moroccan import law document.]
    [State any quantity limits or restrictions, quoting exact figures or thresholds.]
    [Specify prohibited items or materials mentioned in the document.]
    [Give import duties and VAT rates with percentages or fixed amounts, as documented.]
    [List all required customs documents and procedures.]
    
    ### Taxes and Compliance Details
    
    [Summarize how taxes and fees are calculated and at which stage (export or import) they apply, based on the findings.]
    [Explain compliance obligations and potential penalties for non-compliance extracted from the documents.]
    [Include any additional practical advice referenced in the documents for smooth customs clearance.]
    
    ### Summary and Recommendations
    
    [Provide a concise summary of the entire export-import process highlighting key points and actionable next steps based solely on the document contents.]
    """),
    knowledge=None,
    search_knowledge=True,
    retriever=[],
    tools=[GoogleSearchTools()],
)

# ✅ Agent 4 — Compliance Verification
verification_agent = Agent(
    name="Compliance Verification Agent",
    model=OpenAIChat(api_key=openai_key, id="gpt-4o"),
    instructions=dedent("""
    You are a regulatory compliance auditor specializing in international trade.
    
    Your job is to audit an export-import compliance report that was generated by another expert agent. You must carefully review the content and assess:
    
    1. **Legal consistency**:
    - Are the legal steps and procedures correctly sequenced?
    - Are licenses, permits, and document names aligned with real trade practice?
    
    2. **Accuracy of references**:
    - Are any numbers, codes, rates or penalties properly supported?
    - Are there unsupported claims, vague terms, or approximations?
    
    3. **Completeness**:
    - Are all sections fully covered: UK export, Moroccan import, taxes, and summary?
    - Are essential steps or legal documents missing?
    
    Your output should:
    - Clearly identify each issue, grouped by section,
    - Suggest accurate corrections where needed,
    - Confirm when a section is compliant.
    
    You must use markdown to organize your response under:
    - UK Export Section
    - Moroccan Import Section
    - Taxation Section
    - General Observations
    
    Be precise, legal, and concise — no filler or speculation.
    """),
    expected_output=dedent("""
    ### UK Export Section
    [✓ or X Summary of findings with details and line references]
    
    ### Moroccan Import Section
    [✓ or X Summary of findings with suggested corrections]
    
    ### Taxation Section
    [✓ or X Breakdown of duties, VAT accuracy, correction if needed]
    
    ### General Observations
    [Highlight formatting, clarity, completeness, and red flags if any]
    """),
    knowledge=None,
    search_knowledge=False,
    retriever=[],
    tools=[],
)

# 🎯 Agent 5 — Risk Analysis Agent
risk_agent = Agent(
    name="Risk Analysis Agent",
    model=OpenAIChat(api_key=openai_key, id="gpt-4o"),
    instructions=dedent("""
    You are a senior risk analysis advisor for international trade operations between the UK and Morocco.
    
    Based on a complete export-import compliance report, your task is to identify and evaluate potential risks across three main areas:
    
    1. **Legal Risks**:
    - Missing or ambiguous license requirements
    - Penalties for non-compliance
    - Contradictions or lack of jurisdiction clarity
    
    2. **Operational Risks**:
    - Risks of shipment delay due to customs, documents, unclear timelines
    - Problems with quantity limits, permit validation, or procedural bottlenecks
    
    3. **Financial Risks**:
    - Unexpected taxes, fees, or duties
    - Currency conversion, VAT surprises, or payment processing complications
    
    You must respond in clear markdown format, with bold headers for each section.
    Use concrete details from the report to justify your findings.
    Do not invent risks — base your output only on what is found in the report.
    
    You may recommend mitigation strategies if applicable.
    """),
    expected_output=dedent("""
    ### Legal Risks
    [Bullet list of legal vulnerabilities based on the report]
    
    ### Operational Risks
    [Bullet list of logistics, customs or documentation-related risks]
    """),
    knowledge=None,
    search_knowledge=False,
    retriever=[],
    tools=[],
)