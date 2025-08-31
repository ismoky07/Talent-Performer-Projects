import requests
import json
import logging
import re
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from agent_service import get_response
import os
from time import sleep

load_dotenv()

WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
VERSION = os.getenv('VERSION')
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")


def get_text_message_input(recipient, text):
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "text",
        "text": {"preview_url": False, "body": text},
    }


def generate_response(message):
    # Dummy response for now
    return message.upper()


def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
    }
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"

    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        response.raise_for_status()
        log_http_response(response)
        return response
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return JSONResponse({"status": "error", "message": "Request timed out"}, status_code=408)
    except requests.RequestException as e:
        logging.error(f"Request failed due to: {e}")
        return JSONResponse({"status": "error", "message": "Failed to send message"}, status_code=500)


def is_valid_whatsapp_message(body: dict):
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )


def process_whatsapp_message(body: dict):
    value = body["entry"][0]["changes"][0]["value"]
    wa_id = value["contacts"][0]["wa_id"]
    name = value["contacts"][0]["profile"]["name"]
    message = value["messages"][0]
    if message["type"] == "text":
        message_body = message["text"]["body"]
    elif message["type"] == "image":
        message_body = message["image"]
        id = message_body.get("id")
        headers = {
            "Content-type": "application/json",
            "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        }
        metadata_res = requests.get(f"https://graph.facebook.com/{VERSION}/{id}", headers=headers)
        image_url = metadata_res.json().get("url")
        image_res = requests.get(image_url, headers={"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"})
        with open(f"images/{id}.jpg", "wb") as f:
            f.write(image_res.content)
        if message_body.get("caption"):
            message_body = {'image_path': f'images/{id}.jpg', 'caption': message_body.get("caption")}
        else:
            message_body = {'image_path': f'images/{id}.jpg', 'caption': ''}

    response_text = get_response(message_body)
    data = get_text_message_input(wa_id, response_text)
    send_message(data)

