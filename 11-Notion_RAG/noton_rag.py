import os
from notion_client import Client
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from dotenv import load_dotenv

load_dotenv()

OPENAI_KEY_API = os.getenv("OPENAI_KEY_API")

class NotionRAG:
    def __init__(self):
        self.notion = Client(auth=os.getenv("NOTION_TOKEN"))
        self.database_id = os.getenv("NOTION_DATABASE_ID")
        self.agent = self._create_agent() 
    
    def _create_agent(self):
        """Create agent with Notion retriever"""
        return Agent(
            model=OpenAIChat(id="gpt-4o", api_key=os.getenv("OPENAI_KEY_API")),
            knowledge=None,
            search_knowledge=True,
            retriever=self._notion_retriever
        )
    
    def _notion_retriever(self, agent, query, num_documents=None, **kwargs):
        """Search Notion database for relevant Q&A pairs"""
        try:
            results = self.notion.databases.query(database_id=self.database_id)
            
            matching_documents = []
            query_words = set(query.lower().split())
            
            for page in results["results"]:
                # Récupérer la question (gérer différentes casses)
                question_data = None
                if "Question" in page["properties"]:
                    question_data = page["properties"]["Question"]["title"]
                elif "question" in page["properties"]:
                    question_data = page["properties"]["question"]["title"]
                
                question = question_data[0]["plain_text"] if question_data and question_data else ""
                
                # Récupérer la réponse (gérer différentes casses)
                answer_data = None
                if "Response" in page["properties"]:
                    answer_data = page["properties"]["Response"]["rich_text"]
                elif "response" in page["properties"]:
                    answer_data = page["properties"]["response"]["rich_text"]
                elif "answer" in page["properties"]:
                    answer_data = page["properties"]["answer"]["rich_text"]
                
                answer = answer_data[0]["plain_text"] if answer_data and answer_data else ""
                
                # Better matching: check if most query words are in question or answer
                question_words = set(question.lower().split())
                answer_words = set(answer.lower().split())
                all_words = question_words.union(answer_words)
                
                # If at least 60% of query words match, it's a hit
                matches = len(query_words.intersection(all_words))
                match_ratio = matches / len(query_words) if query_words else 0
                
                if match_ratio >= 0.6:  # 60% match threshold
                    # Récupérer les métadonnées (gérer différentes casses)
                    department_data = None
                    if "Departement" in page["properties"]:
                        department_data = page["properties"]["Departement"]["select"]
                    elif "departement" in page["properties"]:
                        department_data = page["properties"]["departement"]["select"]
                    elif "Department" in page["properties"]:
                        department_data = page["properties"]["Department"]["select"]
                    
                    department = department_data["name"] if department_data else "Unknown"
                    
                    tags_data = None
                    if "Tags" in page["properties"]:
                        tags_data = page["properties"]["Tags"]["multi_select"]
                    elif "tags" in page["properties"]:
                        tags_data = page["properties"]["tags"]["multi_select"]
                    
                    tags = [tag["name"] for tag in tags_data] if tags_data else []
                    
                    content = f"Q: {question}\nA: {answer}"
                    if tags:
                        content += f"\nTags: {', '.join(tags)}"
                    
                    matching_documents.append({
                        "content": content,
                        "meta_data": {
                            "source": "Company Knowledge Base",
                            "department": department,
                            "tags": tags,
                            "match_score": match_ratio
                        }
                    })
            
            # Sort by match score (best matches first)
            matching_documents.sort(key=lambda x: x["meta_data"]["match_score"], reverse=True)
            
            print(f"Found {len(matching_documents)} matching documents")
            
            if matching_documents:
                return matching_documents[:num_documents] if num_documents else matching_documents
            else:
                return [{"content": "No matching entry found in the knowledge base.",
                        "meta_data": {"source": "Company Knowledge Base"}}]
                        
        except Exception as e:
            print(f"Error: {e}")
            return [{"content": f"Error: {str(e)}", "meta_data": {"source": "Error"}}]
    
    def ask(self, question):
        """Ask a question to the knowledge base"""
        print(f"🔍 Searching knowledge base for: {question}")
        self.agent.print_response(question)
    
    def chat(self):
        """Interactive chat mode"""
        print("🤖 Notion Knowledge Base Chat")
        print("Type 'quit' to exit")
        
        while True:
            question = input("\nYour question: ")
            if question.lower() in ["quit", "exit", "q"]:
                break
            
            self.ask(question)

def main():
    """Simple main function"""
    print("🚀 Notion RAG Knowledge Base")
    print("-" * 40)
    
    try:
        # Initialize the system
        rag = NotionRAG()
        
        # Interactive chat
        rag.chat()
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have:")
        print("1. NOTION_TOKEN in .env")
        print("2. NOTION_DATABASE_ID in .env")
        print("3. OPENAI_API_KEY in .env")

if __name__ == "__main__":
    main()