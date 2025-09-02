import streamlit as st
import json
import os
import warnings
from textwrap import dedent
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from inference import InferencePipeline
from twilio.rest import Client

warnings.filterwarnings("ignore")

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Global setup
roboflow_key = os.getenv('ROBOFLOW_API_KEY')
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
client = Client(account_sid, auth_token)

MAX_FRAMES = 60
PLATES_FOUND = []
DONE_PLATES = []
data = []

# Load the violations database
try:
    with open('vehicle_violations.json', 'r') as file:
        data = json.load(file)
except FileNotFoundError:
    st.error("❌ 'vehicle_violations.json' not found.")
except json.JSONDecodeError:
    st.error("❌ JSON format error in 'vehicle_violations.json'.")

# Send alert via Twilio
def send_alert(plate_info: str):
    st.info(f"📤 Sending alert: {plate_info}")
    message = client.messages.create(
        from_=os.getenv('TWILIO_FROM_NUMBER'),
        to=os.getenv('TWILIO_TO_NUMBER'),
        body=plate_info
    )
    return message.sid

# Agent setup
agent = Agent(
    model=OpenAIChat(id='gpt-4o'),
    instructions=dedent("""
        You are a license plate alert system. You receive JSON input with full violation data for a detected vehicle.

        Your task is:
        1. Extract the actual values from the JSON input:
        - license_plate
        - crime
        - date
        - location
        - severity
        - fine_amount

        2. Format a single alert message exactly like this:
        "🚨 ALERT: Vehicle [license_plate] detected on [location] | VIOLATION RECORD: [crime] | Original incident: [date] | Severity: [severity] | Fine: £[fine_amount] | Vehicle with known violation history spotted"

        3. Use the `send_alert` tool to send this message as a string.

        Return a JSON response in this format:
        {
        "status": "success",
        "message": "Alert sent for license plate [license_plate]",
        "alert_sent": "[full_alert_message]"
        }
        If anything fails, return:
        {
        "status": "failed",
        "message": "Failed to send alert",
        "error": "[error_details]"
        }

        IMPORTANT:
        - Do NOT invent or guess any data. Only use what's provided in the input.
        - NEVER use placeholder values like ABC123 or Speeding.
    """),
    tools=[send_alert]
)

# Lookup violation
def plate_detection(plate: str):
    for d in data:
        if plate == d['license_plate'] and plate not in DONE_PLATES:
            return d
    return False

# Display + process detected plates
def my_sink(result, video_frame):
    if video_frame.frame_id == MAX_FRAMES:
        pipeline.terminate()
        return

    frame_plates = set()
    for group in result['open_ai']:
        for res in group:
            if res.get('output'):
                frame_plates.add(res['output'].strip())

    for plate in frame_plates:
        plate_info = plate_detection(plate)
        if plate_info:
            if plate_info['license_plate'] not in DONE_PLATES:
                DONE_PLATES.append(plate_info['license_plate'])
                st.success(f"✅ Match found: {plate}")
                agent_response = agent.run(json.dumps(plate_info))
                final_agent_output = None
                for msg in reversed(agent_response.messages):
                    if msg.role == 'assistant' and msg.content:
                        final_agent_output = msg.content
                        break
                if final_agent_output:
                    try:
                        st.json(json.loads(final_agent_output))
                    except json.JSONDecodeError as e:
                        st.error(f"⚠ Agent returned non-JSON content:\n{final_agent_output}")
                else:
                    st.warning("⚠ No assistant response received.")


# Streamlit UI
st.title("🚓 License Plate Violation Detection")

if st.button("▶ Start Detection from Video"):
    with st.spinner("Processing video..."):
        pipeline = InferencePipeline.init_with_workflow(
            api_key=roboflow_key,
            workspace_name="tp-qpwtk",
            workflow_id="custom-workflow",
            video_reference='video/traffic-3.mp4',
            max_fps=30,
            on_prediction=my_sink
        )
        pipeline.start()
        pipeline.join()
    st.success("✅ Finished processing video.")
