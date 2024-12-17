# LINE MCP Server - Python Installation Guide

📘 **Overview**
A Model Context Protocol (MCP) server implementation that enables LLM applications to read text messages from LINE. This server captures LINE messages through webhooks and provides a standardized interface for message retrieval.

🔑 **Key Components**

### API Tools
- line_read_messages: Access message history with configurable limits
- http_request: Generic HTTP interface for LINE API

### Core Resources
- Message Management System (messages.json)
  - Chronological message storage
  - User ID tracking
  - Text message content
  - Message type indicators (text/sticker/image)
  - Sticker metadata (package and sticker IDs)
- Logging System (mcp_server.log)
  - Webhook event tracking
  - Message processing status
  - Error capture and diagnostics

### Current Limitations
- Stickers: Only records sticker ID and package ID, not the actual sticker image
- Images: Only records that an image was sent, without storing the image
- Non-text content: Limited to metadata and type identification only

💡 **Implementation Steps**

### Conda Environment Setup
1. Install Miniforge or Miniconda:
```bash
# For M1/M2 Mac (using Homebrew)
brew install --cask miniforge

# For other systems, download from:
# https://docs.conda.io/en/latest/miniconda.html
```

2. Create and activate conda environment:
```bash
# Create new environment
conda create -n mcp-line python=3.10

# Activate environment
conda activate mcp-line
```

3. Verify installation:
```bash
# Check Python version
python --version  # Should show Python 3.10.x

# Check conda environment
conda env list  # Should show mcp-line as active
```

### Prerequisites
```bash
# Install required Python packages
pip install -r requirements.txt
```

Dependencies:
```python
fastapi==0.100.0
linebot==3.5.0
python-dotenv==1.0.0
uvicorn==0.22.0
aiohttp==3.8.5
mcp-server-sdk==0.1.0
```

### Initial Setup
```bash
# Clone repository
git clone https://github.com/yourusername/LINE.git
cd LINE

# Create required directories and files
mkdir -p src/config src/modules
touch src/config/line_config.py
touch src/modules/line_handler.py
```

### Authentication Setup
1. Create LINE Business Account
2. Set up Messaging API channel
3. Enable Webhook setting in LINE Developers Console
4. Configure .env file:
```bash
LINE_CHANNEL_SECRET=your_channel_secret
LINE_ACCESS_TOKEN=your_access_token
SERVER_PORT=8000
```

⚙️ **Technical Configuration**

### Service Startup
Run these services in separate terminals:

1. Start the MCP server (for message reading):
```bash
python src/line_mcp_server.py
```

2. Start webhook server (port 8000, for message capturing):
```bash
python src/webhook_server.py
```

Verify services are running:
- Webhook server: http://localhost:8000 should return "LINE Webhook Server is running"

### Server Configuration
Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "line": {
      "command": "YOUR_CONDA_PATH/envs/mcp-line/bin/python",
      "args": [
        "YOUR_PATH/LINE/src/line_mcp_server.py"
      ]
    }
  }
}
```

### Path Configuration
Replace placeholders:
• YOUR_CONDA_PATH options:
  - M1/M2 Mac: `/opt/homebrew/Caskroom/miniforge/base`
  - Miniconda: `~/miniconda3` or `/opt/miniconda3`
• YOUR_PATH: Full repository clone path

### Error Handling and Security
- Webhook signature verification
- Message format validation
- JSON schema validation
- Secure message storage

### Project Structure
```
LINE/
├── mcp-server/
│   ├── src/
│   │   ├── config/
│   │   │   └── line_config.py     # Environment and webhook config
│   │   ├── modules/
│   │   │   └── line_handler.py    # Message processing logic
│   │   ├── line_mcp_server.py     # Main MCP server implementation
│   │   └── webhook_server.py      # LINE webhook endpoint (port 8000)
│   ├── messages.json              # Message storage
│   └── mcp_server.log            # Operation logs
├── requirements.txt
└── README.md
```

### System Requirements
- Python 3.10 or higher
- LINE Business Account with Messaging API enabled
- Valid LINE channel credentials
- Properly configured webhook endpoint
- Asia/Bangkok timezone for timestamp synchronization
- Public HTTPS endpoint for webhook
- Stable network connection
- Available port: 8000

## Security Notes
- Store credentials securely using environment variables
- Keep messages.json in a secure location
- Monitor webhook access logs

## License
This project is licensed under the MIT License. See LICENSE file for details.