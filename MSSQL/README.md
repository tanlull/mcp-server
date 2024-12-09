# Microsoft SQL Server MCP Server - M1 Mac Installation Guide

A Model Context Protocol server that provides read-only access to Microsoft SQL Server databases. This installation guide is specifically for Apple Silicon (M1) Macs.

## Components

### Tools

- query 
 - Execute read-only SQL queries against the connected database
 - Input: `sql` (string): The SQL query to execute  
 - All queries are executed within a connection pool for optimal performance

### Resources

The server provides schema information for each table in the database:

- Table Schemas (`mssql://<table>/schema`)
  - JSON schema information for each table 
  - Includes column names and data types
  - Automatically discovered from database metadata

## Installation (M1 Mac Only)

### Prerequisites 

First, ensure you have the required dependencies installed on your M1 Mac:

```bash 
# Install Node.js using Homebrew
brew install node

# Verify Node.js and npm installation
node --version  
npm --version

# Install additional required dependencies
brew install uv git sqlite3
```
### Server Setup

Clone the repository:

```bash
git clone https://github.com/aekanun2020/mcp-server.git
```

## Usage with Claude Desktop

To use this server with the Claude Desktop app, add the following configuration to the "mcpServers" section of your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mssql": {
      "command": "node",
      "args": [
        "/YOUR PATH/mcp-server-main/Bangkok-MCP-Server/src/mssql/dist/index.js",
        "{\"server\":\"MSSQL IP ADDRESS\",\"database\":\"DATABASE NAME\",\"user\":\"USERNAME\",\"password\":\"PASSWORD\",\"options\":{\"trustServerCertificate\":true}}"
      ]
    }
  }
}
```
Replace the connection string with your database credentials.

## Connection Configuration

The server supports the following connection options:

- User authentication
- Connection pooling (max 10 connections)
- TLS/SSL encryption (configurable) 
- Idle timeout management
- Trust server certificate options

## License

This MCP server is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License. For more details, please see the LICENSE file in the project repository.