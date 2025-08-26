import os
from agno.agent import Agent
from agno.memory.v2.db.postgres import PostgresMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.openai import OpenAIChat
from agno.storage.agent.postgres import PostgresAgentStorage
from agno.team.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.reasoning import ReasoningTools
from agno.tools.yfinance import YFinanceTools
from agno.playground import Playground, serve_playground_app
from dotenv import load_dotenv

load_dotenv()
OPENAI_KEY_API = os.getenv("OPENAI_API_KEY")

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "agno_finance_db")

if MYSQL_PASSWORD:
    db_url = f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
else:
    db_url = f"mysql+mysqlconnector://{MYSQL_USER}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

print(f"MySQL: {MYSQL_USER}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")

def test_mysql_connection():
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(db_url)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            result = connection.execute(text("SELECT DATABASE()"))
            current_db = result.fetchone()[0]
            print(f"MySQL OK - Base active: {current_db}")
        return True
    except Exception as e:
        print(f"Erreur MySQL: {e}")
        return False

if not test_mysql_connection():
    exit(1)

memory = Memory(
    model=OpenAIChat(api_key="OPENAI_API_KEY", id="gpt-4o"),
    db=PostgresMemoryDb(table_name="user_memories", db_url=db_url),
    delete_memories=False,
    clear_memories=False,
)

web_agent = Agent(
    name="Web Search Agent",
    role="Handle web search requests and general research",
    agent_id="web_agent",
    model=OpenAIChat(api_key="OPENAI_API_KEY", id="gpt-4o"),
    tools=[DuckDuckGoTools()],
    storage=PostgresAgentStorage(db_url=db_url, table_name="web_agent_sessions"),
    memory=memory,
    instructions=[
        "Search for current and relevant information on financial topics",
        "Always include sources and publication dates",
        "Focus on reputable financial news sources",
        "Provide context and background information",
        "Remember user preferences and previous searches",
    ],
    markdown=True,
    enable_agentic_memory=True,
    add_history_to_messages=True,
    add_datetime_to_instructions=True,
)

finance_agent = Agent(
    name="Finance Agent",
    role="Handle financial data requests and market analysis",
    agent_id="finance_agent",
    model=OpenAIChat(api_key="OPENAI_API_KEY", id="gpt-4o"),
    tools=[YFinanceTools(
        stock_price=True,
        company_info=True,
        stock_fundamentals=True,
        key_financial_ratios=True,
        analyst_recommendations=True,
    )],
    storage=PostgresAgentStorage(db_url=db_url, table_name="finance_agent_sessions"),
    memory=memory,
    instructions=[
        "You are a financial data specialist and your goal is to generate comprehensive and accurate financial reports.",
        "Use tables to display stock prices, fundamentals (P/E, Market Cap, Revenue), and recommendations.",
        "Clearly state the company name and ticker symbol.",
        "Include key financial ratios and metrics in your analysis.",
        "Focus on delivering actionable financial insights.",
        "Delegate tasks and run tools in parallel if needed.",
        "Remember user's investment preferences and risk tolerance.",
    ],
    markdown=True,
    enable_agentic_memory=True,
    add_history_to_messages=True,
    add_datetime_to_instructions=True,
)

reasoning_finance_team = Team(
    name="Reasoning Finance Team",
    mode="coordinate",
    team_id="reasoning_finance_team",
    model=OpenAIChat(api_key="OPENAI_API_KEY", id="gpt-4o"),
    members=[web_agent, finance_agent],
    tools=[ReasoningTools(add_instructions=True)],
    instructions=[
        "Collaborate to provide comprehensive financial and investment insights",
        "Consider both fundamental analysis and market sentiment",
        "Provide actionable investment recommendations with clear rationale",
        "Use tables and charts to display data clearly and professionally",
        "Ensure all claims are supported by data and sources",
        "Present findings in a structured format",
        "Only output the final consolidated analysis",
        "Don't use emojis in formal financial reports",
        "Build on previous team analyses and preferences stored in memory",
    ],
    storage=PostgresAgentStorage(db_url=db_url, table_name="reasoning_finance_team_sessions"),
    memory=memory,
    markdown=True,
    enable_agentic_memory=True,
    enable_agentic_context=True,
    add_datetime_to_instructions=True,
    enable_team_history=True,
    success_criteria="The team has provided a complete financial analysis with data, visualizations, risk assessment, and actionable recommendations.",
)

app = Playground(
    app_id="multi-agent-reasoning-app-mysql",
    name="Multi Agent Reasoning App (MySQL)",
    agents=[web_agent, finance_agent],
    teams=[reasoning_finance_team],
).get_app()

def show_database_info():
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(db_url)
        print("État DB MySQL:")
        with engine.connect() as connection:
            tables = connection.execute(text("SHOW TABLES")).fetchall()
            if tables:
                for table in tables:
                    table_name = table[0]
                    count = connection.execute(text(f"SELECT COUNT(*) FROM `{table_name}`")).fetchone()[0]
                    print(f"{table_name}: {count} enregistrements")
            else:
                print("Aucune table trouvée")
    except Exception as e:
        print(f"Impossible d'afficher la base: {e}")

if __name__ == "__main__":
    print("Démarrage Application Multi-Agents d'Analyse Financière")
    print(f"Interface: http://localhost:7777")
    print(f"Base: MySQL - {MYSQL_DATABASE}")
    show_database_info()
    serve_playground_app("__main__:app", port=7777)
