import os
from dotenv import load_dotenv
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, PushMessageRequest
import logging

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

# Initialize LINE API client
configuration = Configuration(access_token=ACCESS_TOKEN)
client = ApiClient(configuration)
line_api = MessagingApi(client)

async def push_message(user_id: str, message: str):
    try:
        request = PushMessageRequest(
            to=user_id,
            messages=[{
                "type": "text",
                "text": message
            }]
        )
        response = await line_api.push_message(request)
        logger.info(f"Message sent successfully: {response}")
        return response
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise

if __name__ == "__main__":
    import asyncio

    async def main():
        user_id = "U83c2834ae9ed6a4df9fad1b741617ed6"  # User ID from messages.json
        message = "ทดสอบครับผม"
        await push_message(user_id, message)

    asyncio.run(main())