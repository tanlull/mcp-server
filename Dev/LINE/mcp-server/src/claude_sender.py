from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from linebot.v3.messaging import (
    Configuration, 
    ApiClient, 
    MessagingApi, 
    ReplyMessageRequest,
    TextMessage
)
import os
import logging
import uvicorn

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')

if not ACCESS_TOKEN:
    raise ValueError("LINE_ACCESS_TOKEN must be set in .env file")

# Initialize FastAPI
app = FastAPI()

# Initialize LINE API client
configuration = Configuration(access_token=ACCESS_TOKEN)
client = ApiClient(configuration)
line_api = MessagingApi(client)

class Message(BaseModel):
    reply_token: str
    text: str

@app.post("/send")
async def send_message(message: Message):
    try:
        # Create TextMessage object
        text_message = TextMessage(type='text', text=message.text)
        
        # Create ReplyMessageRequest
        request = ReplyMessageRequest(
            reply_token=message.reply_token,
            messages=[text_message]
        )
        
        # Send message
        response = line_api.reply_message(request)
        logger.info(f"Message replied successfully using token: {message.reply_token}")
        return {"status": "success", "message": "Message sent successfully"}
        
    except Exception as e:
        error_msg = f"Error sending message: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/")
async def root():
    return {"status": "Claude Sender Service is running"}

if __name__ == "__main__":
    port = int(os.getenv('SENDER_PORT', 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)