#!/bin/bash
# Script to run the SQLAlchemy connection test

# Ensure the script is executable
chmod +x debug_connection_sqlalchemy.py

# Activate the conda environment if using conda
if command -v conda &> /dev/null; then
    eval "$(conda shell.bash hook)"
    if conda env list | grep -q "mssql-mcp"; then
        echo "Activating mssql-mcp conda environment..."
        conda activate mssql-mcp
    fi
fi

# Run the debug connection script
python debug_connection_sqlalchemy.py
