from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
from dotenv import load_dotenv
import os
import logging
import json

from linebot.v3 import WebhookHandler
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi
from linebot.v3.exceptions import InvalidSignatureError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class LineClient:
    def __init__(self, channel_secret: str, access_token: str):
        self.configuration = Configuration(access_token=access_token)
        self.handler = WebhookHandler(channel_secret)
        self.client = ApiClient(self.configuration)
        self.line_api = MessagingApi(self.client)

    def read_messages(self, limit: int = 10) -> str:
        """Read messages from messages.json"""
        try:
            with open("messages.json", "r") as f:
                data = json.load(f)
                messages = data.get("messages", [])
                # Get last N messages
                recent_messages = messages[-limit:]
                # Format messages
                formatted = "\n".join([
                    f"[{m['timestamp']}] {m['user_id']}: {m['content']}"
                    for m in recent_messages
                ])
                return formatted if formatted else "No messages found"
        except FileNotFoundError:
            return "No message history found"
        except Exception as e:
            return f"Error reading messages: {str(e)}"

    async def send_message(self, channel_id: str, text: str) -> dict:
        """Send a message to a LINE channel"""
        try:
            response = await self.line_api.reply_message({
                "replyToken": channel_id,
                "messages": [{"type": "text", "text": text}]
            })
            return {"success": True, "response": response}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_profile(self, user_id: str) -> dict:
        """Get a user's profile information"""
        try:
            response = await self.line_api.get_profile(user_id)
            return {"success": True, "profile": response}
        except Exception as e:
            return {"success": False, "error": str(e)}

# Create a server instance
server = Server("line-server")
line_client = None

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="line_read_messages",
            description="Read messages from LINE chat history",
            arguments={},
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of recent messages to read (default: 10)",
                        "default": 10
                    }
                }
            }
        ),
        types.Tool(
            name="line_send_message",
            description="Send a message to a LINE channel",
            arguments={},
            inputSchema={
                "type": "object",
                "properties": {
                    "channel_id": {
                        "type": "string",
                        "description": "The ID of the channel to send to"
                    },
                    "text": {
                        "type": "string",
                        "description": "The message text to send"
                    }
                },
                "required": ["channel_id", "text"]
            }
        ),
        types.Tool(
            name="line_get_profile",
            description="Get a LINE user's profile information",
            arguments={},
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "The user's LINE ID"
                    }
                },
                "required": ["user_id"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        if name == "line_read_messages":
            limit = arguments.get("limit", 10)
            messages = line_client.read_messages(limit)
            return [types.TextContent(
                type="text",
                text=messages
            )]
            
        elif name == "line_send_message":
            if not arguments.get("channel_id"):
                return [types.TextContent(
                    type="text",
                    text="Error: channel_id is required"
                )]
            
            if not arguments.get("text"):
                return [types.TextContent(
                    type="text",
                    text="Error: text is required"
                )]
            
            result = await line_client.send_message(
                channel_id=arguments["channel_id"],
                text=arguments["text"]
            )
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result)
            )]
        
        elif name == "line_get_profile":
            if not arguments.get("user_id"):
                return [types.TextContent(
                    type="text",
                    text="Error: user_id is required"
                )]
            
            result = await line_client.get_profile(
                user_id=arguments["user_id"]
            )
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result)
            )]
        
        else:
            return [types.TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
            
    except Exception as e:
        error_msg = f"Error executing {name}: {str(e)}"
        logger.error(error_msg)
        return [types.TextContent(
            type="text",
            text=error_msg
        )]

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    return []

@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    return []

async def run():
    global line_client
    
    try:
        # Load environment variables
        load_dotenv()
        channel_secret = os.getenv('LINE_CHANNEL_SECRET')
        access_token = os.getenv('LINE_ACCESS_TOKEN')

        if not channel_secret or not access_token:
            raise ValueError("LINE_CHANNEL_SECRET and LINE_ACCESS_TOKEN must be set")

        # Initialize LINE client
        logger.info("Starting LINE MCP Server...")
        line_client = LineClient(channel_secret, access_token)
        
        # Run the server
        logger.info("LINE MCP Server is ready")
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="line-mcp",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    )
                )
            )
    except Exception as e:
        logger.error(f"Error in run: {str(e)}")
        raise

async def main():
    try:
        await run()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass