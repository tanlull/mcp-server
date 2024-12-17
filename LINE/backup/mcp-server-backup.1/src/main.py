from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
import logging
import asyncio
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi
from linebot.v3.exceptions import InvalidSignatureError
from dotenv import load_dotenv
import os
from tools import tools

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize LINE API
configuration = Configuration(access_token=os.getenv('LINE_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
client = ApiClient(configuration)
line_api = MessagingApi(client)

# Create a server instance
server = Server("line-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return tools

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        if name == "line_send_message":
            if not arguments.get("target_id"):
                return [types.TextContent(
                    type="text",
                    text="Error: target_id is required"
                )]
            if not arguments.get("message"):
                return [types.TextContent(
                    type="text",
                    text="Error: message is required"
                )]
                
            response = await line_api.push_message(
                target_id=arguments["target_id"],
                messages=[{
                    "type": "text",
                    "text": arguments["message"]
                }]
            )
            
            return [types.TextContent(
                type="text",
                text=f"Message sent successfully: {response}"
            )]
            
        elif name == "line_get_group_info":
            if not arguments.get("group_id"):
                return [types.TextContent(
                    type="text",
                    text="Error: group_id is required"
                )]
                
            response = await line_api.get_group_summary(
                group_id=arguments["group_id"]
            )
            
            return [types.TextContent(
                type="text",
                text=f"Group info: {response}"
            )]
            
        else:
            return [types.TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
            
    except Exception as e:
        logger.error(f"Error executing {name}: {str(e)}")
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    return []

@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    return []

async def run():
    try:
        logger.info("Starting LINE MCP Server...")
        
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="line",
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
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # Handle graceful shutdown