import os
from exa_py import Exa
from textwrap import dedent
from typing import Iterator
from dotenv import load_dotenv
from agno.workflow import Workflow
from agno.agent import Agent, RunResponse
from agno.models.openai import OpenAIChat
from agno.tools.python import PythonTools
from agno.utils.pprint import pprint_run_response

load_dotenv()

### Exa Setup ###
exa_api_key = os.environ.get('EXA_API_KEY')

if not exa_api_key:
    raise ValueError("EXA_API_KEY environment variable is required")

exa = Exa(api_key=exa_api_key)

# Exa search function using basic search and contents
def exa_search(product_list: str, location: str):
    """
    Search for products and vendors using Exa's search and contents functionality
    """
    try:
        # Create a comprehensive search query
        search_query = f"vendors suppliers {product_list} {location} prices purchasing procurement"
        
        print(f"Searching for: {search_query}")
        
        # Perform search and get contents
        results = exa.search_and_contents(
            query=search_query,
            num_results=15,  # Get more results for better coverage
            text=True,  # Include full text content
            type="auto"  # Use auto type for best results
        )
        
        # Format the results for the procurement agent
        formatted_results = f"""
# Procurement Research Results for {location}

**Products searched:** {product_list}
**Location:** {location}
**Search performed:** {search_query}

## Search Results:

"""
        
        for i, result in enumerate(results.results, 1):
            formatted_results += f"""
### Result {i}: {result.title or 'No title'}

**URL:** {result.url}
**Author:** {result.author or 'Not specified'}
**Published Date:** {result.published_date or 'Not specified'}
**Score:** {result.score or 'N/A'}

**Content Preview:**
{result.text[:1500] if result.text else 'No content available'}...

---
"""
        
        print("-------------------------------- EXA SEARCH COMPLETION --------------------------------")
        print(f"Found {len(results.results)} results")
        print("------------------------------------------------------------------------------------------------")
        
        return formatted_results
        
    except Exception as e:
        print(f"Error in exa_search: {str(e)}")
        # Fallback to a simpler search
        try:
            print("Trying fallback search...")
            results = exa.search(
                query=f"{product_list} suppliers {location}",
                num_results=10
            )
            
            fallback_results = f"""
# Fallback Search Results for {location}

**Products searched:** {product_list}
**Location:** {location}

## Basic Search Results:

"""
            
            for i, result in enumerate(results.results, 1):
                fallback_results += f"""
### Result {i}: {result.title or 'No title'}
- **URL:** {result.url}
- **Score:** {result.score or 'N/A'}
- **Published:** {result.published_date or 'Not specified'}

"""
            
            return fallback_results
            
        except Exception as fallback_error:
            print(f"Fallback search also failed: {str(fallback_error)}")
            return f"""
# Search Error

Unable to perform search for products: {product_list} in location: {location}

Error details: {str(e)}

Please check your Exa API key and try again.
"""

class ProcurementAgent(Workflow):
    procurement_agent: Agent = Agent(
        name='Procurement Agent',
        model=OpenAIChat(id='gpt-4o'),
        instructions=dedent("""
        You are a procurement analysis agent.

        Your goal is to:
        1. Parse the search results from Exa containing information about vendors and suppliers.
        2. For each relevant product/vendor combination found, extract the following fields:
            - Product Name
            - Vendor Name
            - Product Title
            - Price (if mentioned, convert to numeric if possible)
            - Currency (if mentioned)
            - Vendor Website or Purchase Link
            - Short Product Description
            - Minimum Order Quantity (if available)
            - Shipping Time (if available)
            - Bulk Discounts or Deals (if available)
            - Vendor Location (if mentioned)

        3. After extracting the data, write and execute a Python script that creates a file named `data.csv`
            - Use the standard `csv` module
            - Make the columns in this order: Product Name, Vendor Name, Product Title, Price, Currency, Bulk Discounts or Deals, Vendor Website, Short Product Description, Minimum Order Quantity, Shipping Time, Vendor Location
            - The script should write a header row followed by one row per vendor/product combination
            - IMPORTANT: When opening the file, always use encoding='utf-8' in open(), e.g. open('data.csv', 'w', newline='', encoding='utf-8')
            - Then use the PythonTools tool to run the script and save the data
            - Create rows for each relevant data point found in the search results

        Then:

        4. Analyze the data across all products and vendors.
            - Compare vendors based on pricing, shipping times, minimum quantities, and available deals.
            - Prioritize vendors who:
                - Deliver to the specified location
                - Offer competitive prices
                - Have favorable shipping times or bulk deals
                - Appear reliable (from established marketplaces or verified sellers)

        5. Write an executive summary that includes:
            - Recommended vendor(s) per product (if clear recommendations can be made)
            - Reasons for the recommendation (price, location, delivery, etc.)
            - Any noteworthy observations (e.g. pricing differences, available options)
            - Limitations of the search results (if search quality was limited)

        IMPORTANT: 
        - Use PythonTools to write the extracted data to `data.csv`.
        - If search results are limited or don't contain specific pricing/vendor info, acknowledge this in your analysis.
        - Focus on extracting whatever relevant information is available from the search results.
        """),
        expected_output=dedent("""
        The output should include:

        1. 📊 Data Summary:
        - Number of relevant results processed
        - Total vendors/suppliers identified
        - Location considered for delivery: <city>, <country>
        - Data quality assessment and any limitations

        2. 🏆 Recommendations Per Product:
        For each product found (e.g., "banane", "pomme"), provide:

        ### Product: <Product Name>

        **Available Options Found:**
        - List the vendors/suppliers found with their key details

        **Best Option (if determinable):** <Vendor Business Name>  
        **Why Recommended:**  
        - Reason 1 (e.g. local supplier, competitive pricing mentioned)
        - Reason 2 (e.g. established marketplace presence)
        - Reason 3 (e.g. good shipping options or bulk availability)

        **Alternative Options:**
        - Mention other viable vendors if found

        **Data Quality Note:**
        - Acknowledge any limitations in the search results
        - Mention if specific pricing or delivery info was not available

        IMPORTANT: Confirm that the CSV file was created and contains the extracted data.
        """),
        tools=[PythonTools()],
        show_tool_calls=True,
        markdown=True
    )

    def run(self, product_list: str, location: str):
        research_response = exa_search(product_list, location)
        yield from self.procurement_agent.run(research_response, stream=True)

if __name__ == '__main__':
    from rich.prompt import Prompt
    
    # Check if API key is available
    if not os.environ.get('EXA_API_KEY'):
        print("❌ Error: EXA_API_KEY environment variable is not set.")
        print("Please set your Exa API key in your .env file:")
        print("EXA_API_KEY=your_api_key_here")
        exit(1)
    
    product_list = Prompt.ask('Enter your products list separated by commas')
    location = Prompt.ask('Enter your business location (city, country)')
    
    if product_list and location:
        try:
            workflow = ProcurementAgent()
            response: Iterator[RunResponse] = workflow.run(product_list=product_list, location=location)
            pprint_run_response(response, markdown=True)
        except Exception as e:
            print(f"❌ Error running procurement agent: {str(e)}")
            print("Please check your API keys and try again.")