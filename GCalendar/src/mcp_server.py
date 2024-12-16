from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
import logging
import asyncio
from calendar_service import CalendarService
import os
import signal
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Create a server instance
server = Server("gcalendar-server")
calendar_service = None

# Signal handler for graceful shutdown
def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}")
    if calendar_service:
        calendar_service.close()
    raise KeyboardInterrupt

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list",
            description="List calendar events",
            arguments={},
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="create-event",
            description="Create a new calendar event",
            arguments={},
            inputSchema={
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Event title"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Start time in YYYY-MM-DDTHH:MM:SS format or date in YYYY-MM-DD format"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "End time (optional). If not provided, event will be 1 hour long"
                    },
                    "description": {
                        "type": "string",
                        "description": "Event description (optional)"
                    }
                },
                "required": ["summary", "start_time"]
            }
        ),
        types.Tool(
            name="delete-duplicates",
            description="Delete duplicate events on a specific date",
            arguments={},
            inputSchema={
                "type": "object",
                "properties": {
                    "target_date": {
                        "type": "string",
                        "description": "Target date in YYYY-MM-DD format"
                    },
                    "event_summary": {
                        "type": "string",
                        "description": "Event title to match"
                    }
                },
                "required": ["target_date", "event_summary"]
            }
        ),
        types.Tool(
            name="delete-event",
            description="Delete a single calendar event",
            arguments={},
            inputSchema={
                "type": "object",
                "properties": {
                    "event_time": {
                        "type": "string",
                        "description": "Event time from list output"
                    },
                    "event_summary": {
                        "type": "string",
                        "description": "Event title to match"
                    }
                },
                "required": ["event_time", "event_summary"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        if name == "list":
            formatted_text = await asyncio.wait_for(
                calendar_service.list_events(),
                timeout=60
            )
            return [types.TextContent(
                type="text",
                text=formatted_text
            )]
            
        elif name == "create-event":
            if not arguments.get("summary"):
                return [types.TextContent(
                    type="text",
                    text="Error: Event title (summary) is required"
                )]
            
            if not arguments.get("start_time"):
                return [types.TextContent(
                    type="text",
                    text="Error: Start time is required"
                )]
            
            result = await asyncio.wait_for(
                calendar_service.create_event(
                    summary=arguments["summary"],
                    start_time=arguments["start_time"],
                    end_time=arguments.get("end_time"),
                    description=arguments.get("description")
                ),
                timeout=60
            )
            
            return [types.TextContent(
                type="text",
                text=result
            )]
            
        elif name == "delete-duplicates":
            if not arguments.get("target_date"):
                return [types.TextContent(
                    type="text",
                    text="Error: Target date is required"
                )]
            
            if not arguments.get("event_summary"):
                return [types.TextContent(
                    type="text",
                    text="Error: Event title is required"
                )]
            
            result = await asyncio.wait_for(
                calendar_service.delete_duplicate_events(
                    target_date=arguments["target_date"],
                    event_summary=arguments["event_summary"]
                ),
                timeout=60
            )
            
            return [types.TextContent(
                type="text",
                text=result
            )]

        elif name == "delete-event":
            if not arguments.get("event_time"):
                return [types.TextContent(
                    type="text",
                    text="Error: Event time is required"
                )]
            
            if not arguments.get("event_summary"):
                return [types.TextContent(
                    type="text",
                    text="Error: Event title is required"
                )]
            
            result = await asyncio.wait_for(
                calendar_service.delete_single_event(
                    event_time=arguments["event_time"],
                    event_summary=arguments["event_summary"]
                ),
                timeout=60
            )
            
            return [types.TextContent(
                type="text",
                text=result
            )]
        
        else:
            return [types.TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
            
    except asyncio.TimeoutError:
        error_msg = f"Operation timed out while executing {name}"
        logger.error(error_msg)
        return [types.TextContent(
            type="text",
            text=error_msg
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
    global calendar_service
    
    try:
        # Initialize calendar service
        logger.info("Starting Calendar Server...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        calendar_service = CalendarService(
            credentials_path=os.path.join(script_dir, "..", "credentials", "credentials.json"),
            token_path=os.path.join(script_dir, "..", "credentials", "token.json")
        )
        
        # Authentication with longer timeout
        try:
            await asyncio.wait_for(calendar_service.authenticate(), timeout=60)
            logger.info("Authentication successful")
        except asyncio.TimeoutError:
            logger.error("Authentication timed out")
            raise
        
        # Run the server
        logger.info("Calendar Server is ready")
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="gcalendar",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    )
                )
            )
    except ConnectionError as e:
        logger.error(f"Connection error: {str(e)}")
        raise
    except IOError as e:
        logger.error(f"IO error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error in run: {str(e)}")
        raise
    finally:
        if calendar_service:
            logger.info("Closing calendar service...")
            calendar_service.close()

async def main():
    try:
        await run()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
    finally:
        if calendar_service:
            calendar_service.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # Handle graceful shutdown