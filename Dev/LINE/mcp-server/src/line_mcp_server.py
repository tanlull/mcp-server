from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
from dotenv import load_dotenv
import os
import logging
import json
import aiohttp
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
                recent_messages = messages[-limit:]
                formatted = "\n".join([
                    f"[{m['timestamp']}] {m['user_id']}: {m['content']}"
                    for m in recent_messages
                ])
                return formatted if formatted else "No messages found"
        except FileNotFoundError:
            return "No message history found"
        except Exception as e:
            return f"Error reading messages: {str(e)}"

async def make_request(method: str, url: str, json_data: dict = None) -> str:
    """Make HTTP request"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, json=json_data) as response:
                return await response.text()
    except Exception as e:
        return f"Error making request: {str(e)}"

# Create a server instance
server = Server("line-server")
line_client = None

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="http_request",
            description="Send HTTP request",
            arguments={},
            inputSchema={
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "description": "HTTP method (GET, POST)"
                    },
                    "url": {
                        "type": "string",
                        "description": "Target URL"
                    },
                    "json_data": {
                        "type": "object",
                        "description": "JSON data for POST request"
                    }
                },
                "required": ["method", "url"]
            }
        ),
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
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        if name == "http_request":
            result = await make_request(
                method=arguments.get("method"),
                url=arguments.get("url"),
                json_data=arguments.get("json_data")
            )
            return [types.TextContent(type="text", text=str(result))]
            
        elif name == "line_read_messages":
            limit = arguments.get("limit", 10)
            messages = line_client.read_messages(limit)
            return [types.TextContent(type="text", text=messages)]
            
        else:
            return [types.TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
            
    except Exception as e:
        error_msg = f"Error executing {name}: {str(e)}"
        logger.error(error_msg)
        return [types.TextContent(type="text", text=error_msg)]

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    return []

@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    return []

async def run():
    global line_client
    
    try:
        load_dotenv()
        channel_secret = os.getenv('LINE_CHANNEL_SECRET')
        access_token = os.getenv('LINE_ACCESS_TOKEN')

        if not channel_secret or not access_token:
            raise ValueError("LINE_CHANNEL_SECRET and LINE_ACCESS_TOKEN must be set")

        logger.info("Starting LINE MCP Server...")
        line_client = LineClient(channel_secret, access_token)
        
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