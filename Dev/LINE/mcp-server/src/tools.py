from mcp.types import Tool

# Tool definitions for LINE integration
tools = [
    Tool(
        name="line_get_message",
        description="Get messages from LINE group or user",
        arguments={},
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "number",
                    "description": "Maximum number of messages to return (default 10)",
                    "default": 10
                }
            }
        }
    ),
    Tool(
        name="line_send_message",
        description="Send a message to LINE group or user",
        arguments={},
        inputSchema={
            "type": "object",
            "properties": {
                "target_id": {
                    "type": "string",
                    "description": "ID of the target group or user"
                },
                "message": {
                    "type": "string",
                    "description": "Message text to send"
                }
            },
            "required": ["target_id", "message"]
        }
    ),
    Tool(
        name="line_get_group_info",
        description="Get information about a LINE group",
        arguments={},
        inputSchema={
            "type": "object",
            "properties": {
                "group_id": {
                    "type": "string",
                    "description": "ID of the LINE group"
                }
            },
            "required": ["group_id"]
        }
    )
]