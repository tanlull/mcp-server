# Google Calendar MCP Server - Python Installation Guide

A Model Context Protocol server that provides access to Google Calendar API with support for asynchronous operations.

## Components

### Tools
- list
   • List calendar events from the past 2 years to 1 year in future
   • No input parameters required
   • Events are cached for optimal performance

- create-event
   • Input: `summary` (string): Event title
   • Input: `start_time` (string): Start time in YYYY-MM-DDTHH:MM:SS format or date in YYYY-MM-DD format
   • Input: `end_time` (string, optional): End time. If not provided, event will be 1 hour long
   • Input: `description` (string, optional): Event description

- delete-duplicates
   • Input: `target_date` (string): Target date in YYYY-MM-DD format
   • Input: `event_summary` (string): Event title to match

- delete-event
   • Input: `event_time` (string): Event time from list output
   • Input: `event_summary` (string): Event title to match

### Resources
- Token Management (`credentials/*.json`)
   • OAuth 2.0 authentication
   • Automatic token refresh
   • JSON token information
   • Automatically discovered at runtime

- Logging System (`logs/*.log`)
   • Detailed operation logs
   • Error tracking and reporting

## Installation (Conda Environment)

Prerequisites:
First, ensure you have Conda installed on your system:

# Verify installation
conda --version

Server Setup:
Clone the repository:

git clone https://github.com/yourusername/GCalendar.git

Environment Setup:
# Create conda environment
conda create -n mcp-gcalendar python=3.9

# Activate environment
conda activate mcp-gcalendar

# Install dependencies
pip install -r requirements.txt

## Usage with Claude Desktop

To use this server with the Claude Desktop app, add the following configuration to the "mcpServers" section of your `claude_desktop_config.json`:

{
  "mcpServers": {
    "gcalendar": {
      "command": "YOUR_CONDA_PATH/envs/mcp-gcalendar/bin/python",
      "args": [
        "YOUR_PATH/GCalendar/src/mcp_server.py"
      ]
    }
  }
}

Replace paths according to your system:
- YOUR_CONDA_PATH examples:
   • M1/M2 Mac with Miniforge: /opt/homebrew/Caskroom/miniforge/base
   • Miniconda: ~/miniconda3 or /opt/miniconda3
- YOUR_PATH: Full path to where you cloned the repository

## Configuration

Create required files that are not included in repository:

- Credentials Setup:
   • Create credentials directory
   • Add credentials.json from Google Cloud Console
   • Run create_token.py to generate token.json

- Connection Settings:
   • OAuth 2.0 authentication
   • Token auto-refresh
   • 60s default timeout
   • Automatic error retry
   • Event caching enabled

## License

This MCP server is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License. For more details, please see the LICENSE file in the project repository.
