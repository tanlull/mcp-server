from linebot.v3.messaging import MessagingApi, TextMessage, ReplyMessageRequest, TextMessage
from utils.logger import setup_logger
import json
import os
from datetime import datetime

logger = setup_logger()

class LineMessageHandler:
    def __init__(self, line_api: MessagingApi):
        self.line_api = line_api
        self.messages_file = "messages.json"
        # Load existing messages or create empty structure
        if os.path.exists(self.messages_file):
            with open(self.messages_file, 'r') as f:
                self.messages = json.load(f)
        else:
            self.messages = {'messages': []}

    def save_messages(self):
        """Save messages to file"""
        with open(self.messages_file, 'w') as f:
            json.dump(self.messages, f, indent=2)

    def handle_message(self, event):
        """Process incoming messages from LINE"""
        try:
            # Extract message details
            timestamp = datetime.fromtimestamp(event["timestamp"] / 1000).strftime('%Y-%m-%d %H:%M:%S')
            user_id = event["source"]["userId"]
            
            if event["message"]["type"] == "text":
                message_text = event["message"]["text"]
                message_type = "text"
                content = message_text
            elif event["message"]["type"] == "sticker":
                sticker_id = event["message"]["stickerId"]
                package_id = event["message"]["packageId"]
                message_type = "sticker"
                content = f"sticker (ID: {sticker_id} from package {package_id})"
            else:
                message_type = event["message"]["type"]
                content = f"unsupported type: {message_type}"
            
            # Save message to file
            self.messages['messages'].append({
                'timestamp': timestamp,
                'user_id': user_id,
                'type': message_type,
                'content': content
            })
            self.save_messages()
            
            # Log the saved message
            logger.info(f"Saved message from {user_id}: {content}")
            
            # Create response
            response = f"Message received and saved."
            
            # Send response
            text_message = TextMessage(text=response)
            request = ReplyMessageRequest(
                replyToken=event["replyToken"],
                messages=[text_message]
            )
            
            # Send the response
            api_response = self.line_api.reply_message(request)
            logger.info(f"Message sent successfully: {api_response}")
            
        except Exception as e:
            logger.error(f"Error in message handler: {str(e)}")
            try:
                error_message = TextMessage(text="Sorry, there was an error processing your message.")
                error_request = ReplyMessageRequest(
                    replyToken=event["replyToken"],
                    messages=[error_message]
                )
                self.line_api.reply_message(error_request)
            except Exception as reply_error:
                logger.error(f"Error sending error message: {str(reply_error)}")

    def get_latest_messages(self, limit=10):
        """Get latest messages for Claude to read"""
        messages = self.messages['messages'][-limit:]
        return '\n'.join([f"{m['timestamp']} - {m['user_id']}: {m['content']}" for m in messages])