import os
import base64
from letta_client import Letta
from dotenv import load_dotenv

load_dotenv()


LETTA_TOKEN = os.getenv('LETTA_API_KEY')
AGENT_ID = os.getenv('AGENT_ID')

client = Letta(
    token=LETTA_TOKEN,
    # timeout=15,
)

# create agent
# response = client.templates.agents.create(
#     project="default-project",
#     template_version="Companion:latest",
# )

# message agent
def get_response(message):
    message = message
    print('--------------Agent triggered--------------')
    if isinstance(message, dict):
        with open(message.get("image_path"), "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        message = [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": encoded_string,
                    },
                },
                {
                    "type": "text",
                    "text": message.get("caption")
                }
            ]
    try:
        answer = client.agents.messages.create(
            agent_id=AGENT_ID,
            messages=[{"role": "user", "content": message}],
        )
        for msg in answer.messages:        
            if hasattr(msg, "content") and msg.content:
                return msg.content
        return "Agent responded with no content."
    except Exception as e:
        print("ERROR:", e)
        return "Sorry, I ran into an issue. Please try again! 💔"


if __name__ == '__main__':
    print(get_response('hello'))