import os
import base64
# from letta_client import Letta
from dotenv import load_dotenv
from agno.agent import Agent
from agno.media import Image
from agno.models.openai import OpenAIChat

load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")


# LETTA_TOKEN = os.getenv('LETTA_API_KEY')
# AGENT_ID = os.getenv('AGENT_ID')

# client = Letta(
#     token=LETTA_TOKEN,
#     # timeout=15,
# )

# create agent
# response = client.templates.agents.create(
#     project="default-project",
#     template_version="Companion:latest",
# )

# message agent
def get_response(message):
    message = message
    image_data = None
    print('--------------Agent triggered--------------')
    if isinstance(message, dict):
        with open(message.get("image_path"), "rb") as f:
            image_data = f.read()
        message = message.get('caption')

    print('---message---', message)
    agent = Agent(
        model=OpenAIChat(id="gpt-4o-mini", api_key=openai_key),
        instructions="""
        If an image is given, you are responsible for defining the object on the image, (if it's a product define what is it in details),
        along with it's name, dimensions and material.
        IMPORTANT: Do not ask back, only give product specifications, dimensions and material!
        """,
    )
    if image_data:
        response = agent.run('Please define the object on the image, along with it\'s name, dimensions and material.', images=[Image(content=image_data)])
    else:
        response = agent.run(message)
    print('---response---', response.content)
    full_response = f"""
    User Question: {message}
    Product Specifications: {response.content}
    """
    return full_response


if __name__ == '__main__':
    print(get_response('hello'))