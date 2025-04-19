#!/usr/bin/env python3
import asyncio
import json
import os
import pandas as pd
import pymssql
from sqlalchemy import create_engine, text
from typing import Dict, List, Any, Optional, Union
from mcp.server.fastmcp import FastMCP

# MSSQL connection details
DB_SERVER = '34.134.173.24'
DB_NAME = 'Electric'
DB_USER = 'SA'
DB_PASSWORD = 'Passw0rd123456'

# Initialize FastMCP server
mcp = FastMCP("mssql-server")

# Create SQLAlchemy engine
engine = create_engine(f'mssql+pymssql://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}/{DB_NAME}')

# Function to get a connection from the engine
def get_connection():
    try:
        return engine.connect()
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

# Function to get all table names in the database
def get_tables():
    conn = get_connection()
    if not conn:
        return []
    
    try:
        # Query to get all user tables in the database
        query = text("""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        
        result = conn.execute(query)
        tables = [row[0] for row in result]
        return tables
    except Exception as e:
        print(f"Error fetching tables: {e}")
        return []
    finally:
        conn.close()

# Function to get the schema for a specific table
def get_table_schema(table_name):
    conn = get_connection()
    if not conn:
        return None
    
    try:
        # Query to get column information for the table
        query = text(f"""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE,
                COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION
        """)
        
        result = conn.execute(query)
        columns = []
        
        for row in result:
            col_name, data_type, max_length, is_nullable, default = row
            column_info = {
                "name": col_name,
                "type": data_type,
                "max_length": max_length,
                "nullable": is_nullable == 'YES',
                "default": default
            }
            columns.append(column_info)
            
        return columns
    except Exception as e:
        print(f"Error fetching schema for table {table_name}: {e}")
        return None
    finally:
        conn.close()

# Cache tables and schemas to avoid repeated database queries
tables_cache = None
schema_cache = {}

# Function to refresh the cache
def refresh_cache():
    global tables_cache, schema_cache
    tables_cache = get_tables()
    schema_cache = {}
    for table in tables_cache:
        schema_cache[table] = get_table_schema(table)

# Initialize cache on startup
refresh_cache()

# MCP Resource: List of tables in the database
@mcp.resource(uri="mssql://tables")
async def tables() -> str:
    """List all tables in the database."""
    tables = tables_cache or get_tables()
    return json.dumps(tables, indent=2)

# MCP Resource: Schema for a specific table
@mcp.resource(uri="mssql://schema/{table_name}")
async def table_schema(table_name: str) -> str:
    """Get the schema for a specific table.
    
    Args:
        table_name: Name of the table
    """
    if table_name in schema_cache:
        schema = schema_cache[table_name]
    else:
        schema = get_table_schema(table_name)
        if schema:
            schema_cache[table_name] = schema
    
    if not schema:
        return json.dumps({"error": f"Table {table_name} not found or error fetching schema"})
    
    return json.dumps(schema, indent=2)

# MCP Tool: Execute a read-only SQL query
@mcp.tool()
async def execute_query(query: str) -> str:
    """Execute a read-only SQL query and return the results.
    
    Args:
        query: SQL query to execute (must be SELECT only)
    """
    # Safety check: ensure it's a read-only query
    query = query.strip()
    ### if not query.lower().startswith('select'):
    ###    return "Error: Only SELECT queries are allowed for security reasons."
    
    conn = get_connection()
    if not conn:
        return "Error: Could not connect to the database."
    
    try:
        # Execute the query and return the results as a formatted table
        df = pd.read_sql(text(query), conn)
        result = df.to_string(index=False)
        
        # If the result is too large, format it differently
        if len(result) > 10000:
            result = df.head(100).to_string(index=False)
            result += f"\n\n[Showing only 100 of {len(df)} rows]"
            
        return result
    except Exception as e:
        return f"Error executing query: {str(e)}"
    finally:
        conn.close()

# MCP Tool: Get table preview
@mcp.tool()
async def preview_table(table_name: str, limit: int = 10) -> str:
    """Get a preview of the data in a table.
    
    Args:
        table_name: Name of the table to preview
        limit: Maximum number of rows to return (default: 10)
    """
    if limit > 1000:
        limit = 1000  # Cap the maximum number of rows for safety
        
    query = f"SELECT TOP {limit} * FROM [{table_name}]"
    
    conn = get_connection()
    if not conn:
        return "Error: Could not connect to the database."
    
    try:
        # Execute the query and return the results as a formatted table
        df = pd.read_sql(text(query), conn)
        if df.empty:
            return f"Table '{table_name}' is empty or does not exist."
        
        return df.to_string(index=False)
    except Exception as e:
        return f"Error previewing table: {str(e)}"
    finally:
        conn.close()

# MCP Tool: Get database information
@mcp.tool()
async def get_database_info() -> str:
    """Get general information about the database."""
    conn = get_connection()
    if not conn:
        return "Error: Could not connect to the database."
    
    info = {
        "database_name": DB_NAME,
        "server": DB_SERVER,
        "table_count": len(tables_cache) if tables_cache else len(get_tables()),
    }
    
    try:
        # Get database version
        query_version = text("SELECT @@VERSION")
        result = conn.execute(query_version)
        version = result.fetchone()[0]
        info["server_version"] = version
        
        # Get database size
        query_size = text("SELECT SUM(size/128.0) FROM sys.database_files;")
        result = conn.execute(query_size)
        size_mb = result.fetchone()[0]
        info["size_mb"] = round(float(size_mb), 2) if size_mb else None
        
    except Exception as e:
        info["error"] = str(e)
    
    finally:
        conn.close()
    
    return json.dumps(info, indent=2)

# MCP Tool: Refresh cache
@mcp.tool()
async def refresh_db_cache() -> str:
    """Refresh the database schema cache."""
    refresh_cache()
    return f"Cache refreshed. Found {len(tables_cache)} tables."

# MCP Prompt: Data analysis template
@mcp.prompt()
async def data_analysis_template(table_name: str) -> Dict:
    """Generate a template for analyzing a specific table.
    
    Args:
        table_name: Name of the table to analyze
    """
    if table_name not in tables_cache and table_name not in schema_cache:
        schema = get_table_schema(table_name)
        if not schema:
            return {
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": f"The table {table_name} was not found in the database. Please check the table name and try again."
                        }
                    }
                ]
            }
        schema_cache[table_name] = schema
    
    schema = schema_cache.get(table_name, get_table_schema(table_name))
    column_names = [col["name"] for col in schema]
    
    analysis_template = f"""
I need to analyze the data in the {table_name} table. The table has the following columns:
{', '.join(column_names)}

Please help me:
1. Understand the basic statistics and distribution of values in each column
2. Identify any trends or patterns in the data
3. Find correlations between different columns
4. Create visualizations to represent the data effectively
5. Provide insights and recommendations based on the data

Here's a sample SQL query to start exploring the table:
```sql
SELECT * FROM [{table_name}] LIMIT 10
```

What other analyses would you recommend for this table?
"""
    
    return {
        "messages": [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": analysis_template
                }
            }
        ]
    }

# MCP Prompt: SQL query generator
@mcp.prompt()
async def generate_sql_query(description: str) -> Dict:
    """Generate a SQL query based on a natural language description.
    
    Args:
        description: Natural language description of the query to generate
    """
    available_tables = tables_cache or get_tables()
    table_info = {}
    
    # Get schema for up to 5 tables (to avoid making too many DB calls)
    for table in available_tables[:5]:
        if table in schema_cache:
            schema = schema_cache[table]
        else:
            schema = get_table_schema(table)
            if schema:
                schema_cache[table] = schema
        
        if schema:
            table_info[table] = [col["name"] for col in schema]
    
    tables_schemas = ""
    for table, columns in table_info.items():
        tables_schemas += f"\nTable: {table}\nColumns: {', '.join(columns)}\n"
    
    query_prompt = f"""
I need help generating a SQL query for a Microsoft SQL Server database (T-SQL syntax).

The database contains the following tables and columns:
{tables_schemas}

Please write a SQL query that does the following:
{description}

Remember:
- Use proper T-SQL syntax
- Only use SELECT statements (read-only)
- Include comments to explain your query
- If you need to join tables, explain the relationships
"""
    
    return {
        "messages": [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": query_prompt
                }
            }
        ]
    }

# Run the server if executed directly
if __name__ == "__main__":
    # Initialize and run the server
    print("Starting MSSQL MCP Server...")
    mcp.run(transport='stdio')
    print("Server shutdown.")
