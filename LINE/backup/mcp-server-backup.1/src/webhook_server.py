from fastapi import FastAPI, Request, HTTPException
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.exceptions import InvalidSignatureError
from dotenv import load_dotenv
import os
import json
from datetime import datetime

from modules.line_handler import LineMessageHandler
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="LINE Webhook Server")

# Initialize LINE API
configuration = Configuration(access_token=os.getenv('LINE_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
client = ApiClient(configuration)
line_api = MessagingApi(client)
message_handler = LineMessageHandler(line_api)

# Setup logging
logger = setup_logger()

@app.get("/")
async def root():
    return {"status": "LINE Webhook Server is running"}

@app.post("/webhook")
async def webhook(request: Request):
    try:
        # Get signature and body
        signature = request.headers.get('X-Line-Signature', '')
        body = await request.body()
        body_str = body.decode('utf-8')
        
        # Log request details
        logger.info("Request headers:")
        for header, value in request.headers.items():
            logger.info(f"{header}: {value}")
        
        logger.info(f"Request body: {body_str}")
        
        # Process message
        try:
            body_json = json.loads(body_str)
            if body_json.get("events"):
                event = body_json["events"][0]
                if event["type"] == "message":
                    message_handler.handle_message(event)
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
        
        return {"status": "OK"}

    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return {"status": "OK"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('SERVER_PORT', 8000))
    uvicorn.run("webhook_server:app", host="0.0.0.0", port=port, reload=True)