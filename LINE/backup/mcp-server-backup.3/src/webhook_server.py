from fastapi import FastAPI, Request, HTTPException
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.exceptions import InvalidSignatureError
from dotenv import load_dotenv
import os
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message}',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
LINE_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')

if not LINE_CHANNEL_SECRET or not LINE_ACCESS_TOKEN:
    raise ValueError("LINE_CHANNEL_SECRET and LINE_ACCESS_TOKEN must be set in .env file")

# Initialize FastAPI app
app = FastAPI()

# Initialize LINE API
configuration = Configuration(access_token=LINE_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
line_api = MessagingApi(ApiClient(configuration))

def save_message(timestamp: str, user_id: str, message_type: str, content: str):
    """Save message to messages.json"""
    try:
        # Load existing messages
        messages = {'messages': []}
        if os.path.exists('messages.json'):
            with open('messages.json', 'r') as f:
                messages = json.load(f)
        
        # Add new message
        messages['messages'].append({
            'timestamp': timestamp,
            'user_id': user_id,
            'type': message_type,
            'content': content
        })
        
        # Save to file
        with open('messages.json', 'w') as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Message saved: {content}")
        return True
    except Exception as e:
        logger.error(f"Error saving message: {str(e)}")
        return False

@app.post("/webhook")
async def webhook(request: Request):
    try:
        # Get signature and body
        signature = request.headers.get('X-Line-Signature', '')
        body = await request.body()
        body_str = body.decode('utf-8')
        
        # Log request
        logger.info("Received webhook request")
        
        # Process message
        body_json = json.loads(body_str)
        events = body_json.get("events", [])
        
        if not events:
            return {"status": "OK", "message": "No events"}
            
        event = events[0]
        if event["type"] != "message":
            return {"status": "OK", "message": "Not a message event"}
            
        # Extract message details
        timestamp = datetime.fromtimestamp(event["timestamp"] / 1000).strftime('%Y-%m-%d %H:%M:%S')
        user_id = event["source"]["userId"]
        message_type = event["message"]["type"]
        content = event["message"].get("text", "") if message_type == "text" else f"[{message_type} message]"
        
        # Save message only
        save_message(timestamp, user_id, message_type, content)
        
        return {"status": "OK", "message": "Message processed"}
        
    except Exception as e:
        error_msg = f"Webhook error: {str(e)}"
        logger.error(error_msg)
        return {"status": "Error", "message": error_msg}

@app.get("/")
async def root():
    return {"status": "LINE Webhook Server is running"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('SERVER_PORT', 8000))
    uvicorn.run("webhook_server:app", host="0.0.0.0", port=port, reload=True)