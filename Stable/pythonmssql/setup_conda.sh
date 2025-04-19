#!/bin/bash
# This script sets up the MSSQL MCP server environment with Conda and Python 3.12

# Check if conda is installed
if ! command -v conda &> /dev/null; then
    echo "Conda is not installed. Please install Miniconda or Anaconda first."
    echo "Visit: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "Detected macOS system"
    echo "Checking for Homebrew..."
    if ! command -v brew &> /dev/null; then
        echo "Homebrew not found. Please install Homebrew first:"
        echo "/bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    
    echo "Installing ODBC Driver for SQL Server..."
    brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
    brew update
    brew install msodbcsql17 mssql-tools
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "Detected Linux system"
    echo "Installing ODBC Driver for SQL Server..."
    
    # Check if we're on Ubuntu/Debian
    if command -v apt-get &> /dev/null; then
        curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
        curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
        sudo apt-get update
        ACCEPT_EULA=Y sudo apt-get install -y msodbcsql17 mssql-tools
    else
        echo "Unsupported Linux distribution. Please install the ODBC driver manually."
        echo "See: https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server"
    fi
    
else
    echo "Unsupported operating system: $OSTYPE"
    echo "Please install the ODBC driver manually."
    echo "See: https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server"
fi

# Create and activate conda environment
echo "Creating conda environment with Python 3.12..."
conda env create -f environment.yml
echo "Activating conda environment..."
eval "$(conda shell.bash hook)"
conda activate mssql-mcp

# Make the scripts executable
chmod +x test_connection.py
chmod +x mssql_server.py

# Test the database connection
echo "Testing the database connection..."
python test_connection.py

# Instructions for Claude for Desktop configuration
echo ""
echo "To configure Claude for Desktop:"
echo "1. Edit the Claude for Desktop config file:"
echo "   • macOS: nano ~/Library/Application\ Support/Claude/claude_desktop_config.json"
echo "   • Windows: notepad %APPDATA%\Claude\claude_desktop_config.json"
echo ""
echo "2. Add the following configuration:"
echo "{" 
echo "  \"mcpServers\": {"
echo "    \"mssql-server\": {"
echo "      \"command\": \"$(conda info --base)/envs/mssql-mcp/bin/python\","
echo "      \"args\": [\"$(pwd)/mssql_server.py\"]"
echo "    }"
echo "  }"
echo "}"
echo ""
echo "3. Restart Claude for Desktop"
echo ""
echo "Setup complete!"
