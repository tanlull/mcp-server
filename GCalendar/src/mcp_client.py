from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
import logging
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

async def run():
    # Create server parameters
    server_params = StdioServerParameters(
        command="python",
        args=[os.path.join(os.path.dirname(__file__), "mcp_server.py")]
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize connection
                await session.initialize()
                logger.info("Initialization successful")
                
                # List calendar events using tool
                result = await session.call_tool("list", {})
                if result and hasattr(result, "content"):
                    for content_item in result.content:
                        if hasattr(content_item, "text"):
                            print("\nCalendar Events:\n")
                            print(content_item.text)
                else:
                    logger.warning("No events data received")
                
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Client shutdown requested")