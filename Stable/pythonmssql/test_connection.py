#!/usr/bin/env python3
"""
Test script to verify connectivity to the MSSQL database.
This script helps ensure your environment is properly configured
before running the MCP server.
"""

import pandas as pd
import pymssql
from sqlalchemy import create_engine, text

# MSSQL connection details
DB_SERVER = '34.134.173.24'
DB_NAME = 'Telco'
DB_USER = 'SA'
DB_PASSWORD = 'Passw0rd123456'

def test_connection():
    """Test connection to the MSSQL database."""
    print(f"Testing connection to {DB_NAME} database on {DB_SERVER}...")
    
    try:
        # Create SQLAlchemy engine
        engine = create_engine(f'mssql+pymssql://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}/{DB_NAME}')
        
        # Test connection by making a simple query
        with engine.connect() as conn:
            print("✅ Successfully connected to the database!")
            
            # Test querying the tables
            query = text("""
                SELECT TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """)
            
            result = conn.execute(query)
            tables = [row[0] for row in result]
            print(f"✅ Found {len(tables)} tables in the database.")
            print("\nAvailable tables:")
            for table in tables:
                print(f"  - {table}")
            
            # If we have tables, test querying one of them
            if tables:
                test_table = tables[0]
                print(f"\nTesting preview of table '{test_table}':")
                
                df = pd.read_sql(text(f"SELECT TOP 5 * FROM [{test_table}]"), conn)
                print(df.to_string(index=False))
            
        print("\n✅ Connection test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to the database: {e}")
        print("\nPossible solutions:")
        print("1. Verify the connection details (server, database, username, password)")
        print("2. Ensure the server is accessible from your network")
        print("3. Check if there's a firewall blocking the connection")
        return False

if __name__ == "__main__":
    test_connection()
