```markdown
# Google Calendar MCP Server - Python Installation Guide

A Model Context Protocol server that provides access to Google Calendar API with support for asynchronous operations.

# Components

## Tools

### list
- Execute queries to list calendar events from the past 2 years to 1 year in future
- No input parameters required
- Events are cached in memory for optimal performance

### create-event
- Create new calendar events with specified parameters
- Input: `summary` (string): Event title
- Input: `start_time` (string): Start time in YYYY-MM-DDTHH:MM:SS format or date in YYYY-MM-DD format
- Input: `end_time` (string, optional): End time. If not provided, event will be 1 hour long
- Input: `description` (string, optional): Event description

### delete-duplicates
- Remove duplicate events on a specific date
- Input: `target_date` (string): Target date in YYYY-MM-DD format
- Input: `event_summary` (string): Event title to match

### delete-event
- Delete a single calendar event
- Input: `event_time` (string): Event time from list output
- Input: `event_summary` (string): Event title to match

# Installation (Conda Environment)

## Prerequisites

First, ensure you have Conda installed on your system:

```bash
# Install Conda using Homebrew
brew install miniforge

# Verify Conda installation
conda --version

# Create dedicated conda environment
conda create -n mcp-gcalendar python=3.9

# Activate the environment
conda activate mcp-gcalendar

# Install required packages
pip install -r requirements.txt
```

# Server Setup

Clone the repository and set up the required directories:

```bash
# Clone repository
git clone https://github.com/yourusername/GCalendar.git
cd GCalendar
mkdir -p credentials logs
```

# Usage with Claude Desktop

Add the following configuration to your `claude_desktop_config.json`:

```json
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
```

Replace path placeholders:
- YOUR_CONDA_PATH examples:
  - M1/M2 Mac with Miniforge: `/opt/homebrew/Caskroom/miniforge/base`
  - Miniconda: `~/miniconda3` or `/opt/miniconda3`
- YOUR_PATH: Full path to your cloned repository location

# Connection Configuration

## Credentials Setup
- Create a credentials directory
- Download credentials.json from Google Cloud Console
- Generate token.json using create_token.py script

## Connection Settings
- OAuth 2.0 authentication protocol
- Automatic token refresh mechanism
- 60-second default timeout
- Automatic retry on transient errors
- Event caching enabled by default

# License

This project is licensed under the MIT License. See LICENSE file for details.
```
