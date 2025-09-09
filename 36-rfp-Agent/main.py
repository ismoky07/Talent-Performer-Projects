import os
import pygsheets
import pandas as pd
from agno.tools import tool
from textwrap import dedent
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.vectordb.pgvector import PgVector
from agno.tools.reasoning import ReasoningTools
from agno.knowledge.markdown import MarkdownKnowledgeBase
from agno.vectordb.qdrant import Qdrant
from dotenv import load_dotenv
import json
from io import StringIO

# Charger les variables d'environnement
load_dotenv()

# Récupération des variables d'environnement
qdrant_api_key = os.getenv("QDRANT_API_KEY")
qdrant_url = os.getenv("QDRANT_URL")
openai_api_key = os.getenv("OPENAI_API_KEY")

# Autorisation Google Sheets
gc = pygsheets.authorize(service_account_file='36-rfp-Agent/client_secret.json')

### Setup Knowledge Base ###
vector_db = Qdrant(
    collection="docs_markdown",
    api_key=qdrant_api_key,
    url=qdrant_url,
)

knowledge_base = MarkdownKnowledgeBase(
    path="36-rfp-Agent/docs/markdown/",
    vector_db=vector_db,
    num_documents=5,
)

@tool(
    name="list_worksheets",
    description="List all available worksheets in the Google Sheet.",
    show_result=True,
)
def list_worksheets(sheet_id: str) -> str:
    """
    List all available worksheets in a Google Sheet.
    
    Args:
        sheet_id (str): The unique ID of the Google Sheet.
    
    Returns:
        str: List of available worksheet titles.
    """
    try:
        sh = gc.open_by_key(sheet_id)
        worksheets = sh.worksheets()
        titles = [ws.title for ws in worksheets]
        return f"Available worksheets: {', '.join(titles)}"
    except Exception as e:
        return f"Error listing worksheets: {str(e)}"

@tool(
    name="read_sheet_as_df",
    description="Read an entire Google Sheets worksheet as a pandas DataFrame.",
    show_result=True,
)
def read_sheet_as_df(sheet_id: str, worksheet_title: str) -> str:
    """
    Use this function to read an entire Google Sheets worksheet and return its data as a JSON-formatted DataFrame.
    
    Args:
        sheet_id (str): The unique ID of the Google Sheet (from the URL).
        worksheet_title (str): The tab name of the worksheet within the Google Sheet.
    
    Returns:
        str: A JSON string representing the DataFrame containing the worksheet's data.
    """
    try:
        sh = gc.open_by_key(sheet_id)
        
        # Vérifier si l'onglet existe
        try:
            wks = sh.worksheet_by_title(worksheet_title)
        except:
            # Lister les onglets disponibles si celui demandé n'existe pas
            worksheets = sh.worksheets()
            available = [ws.title for ws in worksheets]
            return f"Worksheet '{worksheet_title}' not found. Available worksheets: {', '.join(available)}"
        
        df = wks.get_as_df()
        return df.to_json(orient="records")
    except Exception as e:
        return f"Error reading sheet: {str(e)}"

@tool(
    name="write_df_to_sheet",
    description="Write a DataFrame to a Google Sheets worksheet using the sheet ID.",
    show_result=True,
)
def write_df_to_sheet(
    df_json: str, sheet_id: str, worksheet_title: str, start_cell: list[int] = [1, 1]
) -> str:
    """
    Use this function to write a DataFrame (as JSON) to a Google Sheets worksheet.
    
    Args:
        df_json (str): JSON string representing the DataFrame to write.
        sheet_id (str): The unique ID of the Google Sheet (from the URL).
        worksheet_title (str): The tab name of the worksheet.
        start_cell (list[int], optional): [row, column] location to start writing. Defaults to [1, 1].
    
    Returns:
        str: Confirmation message upon successful write.
    """
    try:
        # Gestion améliorée du JSON
        if isinstance(df_json, str):
            # Nettoyer le JSON si nécessaire
            df_json = df_json.strip()
            if df_json.startswith("```json"):
                df_json = df_json.replace("```json", "").replace("```", "").strip()
            
            # Parser le JSON avec StringIO pour éviter le warning
            df = pd.read_json(StringIO(df_json))
        else:
            # Si ce n'est pas une string, essayer de convertir
            df = pd.DataFrame(df_json)
        
        sh = gc.open_by_key(sheet_id)
        try:
            wks = sh.worksheet_by_title(worksheet_title)
        except pygsheets.WorksheetNotFound:
            wks = sh.add_worksheet(worksheet_title)
        
        wks.clear()
        wks.set_dataframe(df, start=tuple(start_cell))
        return f"Successfully wrote DataFrame to worksheet '{worksheet_title}' in sheet '{sheet_id}'. Rows: {len(df)}, Columns: {len(df.columns)}"
        
    except json.JSONDecodeError as e:
        return f"JSON parsing error: {str(e)}. Please provide valid JSON format."
    except Exception as e:
        return f"Error writing to sheet: {str(e)}"

rfp_agent = Agent(
    name="RFP Agent",
    model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
    knowledge=knowledge_base,
    search_knowledge=True,
    show_tool_calls=True,
    tools=[ReasoningTools(add_instructions=True), list_worksheets, read_sheet_as_df, write_df_to_sheet],
    instructions=dedent(
        """
        You are an RFP (Request-for-Proposal) agent.
        
        Your role is to assist with completing RFP spreadsheets. You receive partially filled RFP sheets and use the company knowledge base to fill in the missing fields accurately.
        
        ---
        
        🔧 Tools You Have Access To:
        
        1. list_worksheets(sheet_id: str)
           - Lists all available worksheets in a Google Sheet
           - Use this FIRST to check available worksheet names
        
        2. read_sheet_as_df(sheet_id: str, worksheet_title: str)
           - Reads an entire Google Sheets worksheet and returns its contents as a pandas DataFrame (serialized as JSON).
           - Use this to:
             • Load the current contents of an RFP sheet
             • Inspect which fields are already filled and which are missing
        
        3. write_df_to_sheet(df_json: str, sheet_id: str, worksheet_title: str, start_cell: List[int] = [1, 1])
           - Writes a pandas DataFrame (provided as a JSON string) to a specific worksheet in a Google Sheet, replacing all existing content.
           - IMPORTANT: df_json must be valid JSON format
           - Use this to:
             • Write the filled RFP sheet back to Google Sheets
             • Overwrite the worksheet with the completed version
        
        📋 Sheet Identification Notes:
        - `sheet_id` is the unique identifier found in the Google Sheets URL:
        Example: For `https://docs.google.com/spreadsheets/d/1yg8MQ7bocOlgURlQqZcX2fcY7AqjVlfQM8ZntwtbizA/edit?gid=0#gid=0`, the `sheet_id` is `1yg8MQ7bocOlgURlQqZcX2fcY7AqjVlfQM8ZntwtbizA`
        - `worksheet_title` refers to the tab name within the sheet, such as "Sheet1" or "RFP".
        
        ---
        
        🎯 Your Objective:
        
        1. FIRST: Use list_worksheets to see available worksheet names
        2. Read the data using read_sheet_as_df with the correct worksheet name
        3. Analyze the user's instructions and the structure of the RFP sheet
        4. Use the company knowledge base to fill in missing fields. If no relevant information is found in the knowledge base, leave the field blank.
        5. Fill in missing values using logic derived from the knowledge base or prompts
        6. Write the updated data using write_df_to_sheet with proper JSON format
        
        ---
        
        🗣️ How to Answer When Filling Fields:
        
        For each field you attempt to fill, explain your result in **natural language** using one of the following formats:
        
        - **Yes ✓** followed by a short explanation.
          - Example: *Yes ✓ We support integration with Salesforce and Slack out of the box.*
        
        - **No ✗** followed by a short explanation.
          - Example: *No ✗ Our platform does not currently support HIPAA compliance.*
        
        - **Partial ⚡** followed by a short explanation.
          - Example: *Partial ⚡ We offer 24/7 support via email and chat, but phone support is limited to business hours.*
        
        This phrasing should be used inline as part of your reasoning and field-filling process — not just as a summary label.
        
        ---
        
        IMPORTANT: Always start by listing available worksheets to avoid WorksheetNotFound errors.
        
        Respond like a knowledgeable and trustworthy analyst. Be clear, helpful, and direct.
        ---
        """
    ),
)

rfp_agent.knowledge.load(recreate=True)

# Démarrage avec vérification des onglets disponibles
rfp_agent.print_response(
    """
    Answer all the questions in the RFP spreadsheet based on our company knowledge base. only the 'Response / Answer' column should be updated.
    Sheet ID: '1yg8MQ7bocOlgURlQqZcX2fcY7AqjVlfQM8ZntwtbizA'
    
    IMPORTANT: First check what worksheets are available in this sheet, then use the correct worksheet name.
    """,
    stream=True,
)