from dotenv import load_dotenv
import os

load_dotenv()

LINE_CONFIG = {
    'CHANNEL_SECRET': os.getenv('LINE_CHANNEL_SECRET'),
    'ACCESS_TOKEN': os.getenv('LINE_ACCESS_TOKEN'),
    'SERVER_PORT': int(os.getenv('SERVER_PORT', 8000))
}

# Webhook configuration
WEBHOOK_HANDLER = {
    'ENDPOINT': '/webhook',
    'METHODS': ['POST']
}