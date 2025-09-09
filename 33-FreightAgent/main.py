import os
import json
import uvicorn
import logging
import requests
from threading import Thread
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from whatsapp_utils import process_whatsapp_message, is_valid_whatsapp_message

load_dotenv()

VERSION = os.getenv('VERSION')
PHONE_NUMBER_ID = os.getenv('PHONE_NUMBER_ID')
WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
RECIPIENT_PHONE_NUMBER = os.getenv('RECIPIENT_PHONE_NUMBER')
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the portal!"}

# Required webhook verifictaion for WhatsApp
async def verify(request: Request):
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            logging.info("WEBHOOK_VERIFIED")
            return PlainTextResponse(content=challenge, status_code=200)
        else:
            logging.warning("VERIFICATION_FAILED")
            raise HTTPException(status_code=403, detail="Verification failed")
    else:
        logging.warning("MISSING_PARAMETER")
        raise HTTPException(status_code=400, detail="Missing parameters")

async def handle_message(request: Request):
    try:
        body = await request.json()
    except json.JSONDecodeError:
        logging.error("Failed to decode JSON")
        return JSONResponse(status_code=400, content={"status": "error", "message": "Invalid JSON provided"})

    if (
        body.get("entry", [{}])[0]
        .get("changes", [{}])[0]
        .get("value", {})
        .get("statuses")
    ):
        logging.info("Received a WhatsApp status update.")
        return JSONResponse(content={"status": "ok"})

    if is_valid_whatsapp_message(body):
        try:
            # Run message processing in a background thread
            Thread(target=process_whatsapp_message, args=(body,)).start()
        except Exception as e:
            logging.error(f"Error starting background message thread: {e}")
        return JSONResponse(content={"status": "ok"})
    else:
        return JSONResponse(status_code=404, content={"status": "error", "message": "Not a WhatsApp API event"})



@app.get("/test")
def test():
    url = f'https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages'
    headers = {
        'Authorization': f'Bearer {WHATSAPP_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        'messaging_product': 'whatsapp',
        'to': RECIPIENT_PHONE_NUMBER,
        'type': 'template',
        'template': {
            'name': 'hello_world',
            'language': {
                'code': 'en_US'
            }
        }
    }
    response = requests.post(url, headers=headers, json=data)
    return {"message": "Test successful!", "response": response.json()}

@app.get("/send_message")
def send_message():
    url = f'https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages'
    headers = {
        'Authorization': f'Bearer {WHATSAPP_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        'messaging_product': 'whatsapp',
        'to': RECIPIENT_PHONE_NUMBER,
        'type': 'text',
        'text': {
            'body': 'Hello, how are you?'
        }
    }
    response = requests.post(url, headers=headers, json=data)
    return {"message": "Message sent successfully!", "response": response.json()}

# @app.get("/webhook")
# async def webhook(request: Request):
#     return await verify(request)

@app.get("/webhook")
async def webhook_verify(request: Request):
    return await verify(request)

@app.post("/webhook")
async def webhook_message(request: Request):
    return await handle_message(request)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)