#!/usr/bin/env python3
"""
Debug script for troubleshooting MSSQL connection issues.
This script provides detailed information about connection attempts.
"""

import sys
import socket
import platform
import pandas as pd
import traceback
from sqlalchemy import create_engine, text
from time import sleep

# MSSQL connection details
DB_SERVER = '35.239.50.206'
DB_NAME = 'Telco'
DB_USER = 'SA'
DB_PASSWORD = 'Passw0rd123456'

def check_network_connectivity():
    """Test basic network connectivity to the server."""
    print(f"\n🔍 Testing network connectivity to {DB_SERVER}:1433...")
    
    try:
        # Check if we can reach the server
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        result = s.connect_ex((DB_SERVER, 1433))
        if result == 0:
            print(f"✅ Successfully connected to {DB_SERVER} on port 1433")
            s.close()
            return True
        else:
            print(f"❌ Failed to connect to {DB_SERVER} on port 1433")
            s.close()
            return False
    except Exception as e:
        print(f"❌ Network connection error: {e}")
        return False

def print_system_info():
    """Print information about the system."""
    print("\n🔍 System Information:")
    print(f"  Python version: {sys.version}")
    print(f"  Operating system: {platform.system()} {platform.release()}")
    print(f"  Platform: {platform.platform()}")

def test_connection_verbose():
    """Test connection to the MSSQL database with verbose output."""
    print("\n🔍 Testing database connection with SQLAlchemy...")
    print(f"  Server: {DB_SERVER}")
    print(f"  Database: {DB_NAME}")
    print(f"  Username: {DB_USER}")
    print(f"  Password: {'*' * len(DB_PASSWORD)}")
    
    try:
        # Create connection string
        connection_url = f'mssql+pymssql://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}/{DB_NAME}'
        print(f"\nConnection URL: {connection_url.replace(DB_PASSWORD, '*' * len(DB_PASSWORD))}")
        
        # Create engine
        print("Creating SQLAlchemy engine...")
        engine = create_engine(connection_url)
        
        # Connect and test
        print("Opening connection...")
        with engine.connect() as conn:
            print("✅ Successfully connected to the database!")
            
            # Test basic query
            print("\nTesting simple query...")
            query = text("SELECT @@VERSION")
            result = conn.execute(query)
            version = result.fetchone()[0]
            print(f"✅ Server version: {version}")
            
            # Test querying the tables
            print("\nQuerying table list...")
            query = text("""
                SELECT TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """)
            
            result = conn.execute(query)
            tables = [row[0] for row in result]
            print(f"✅ Found {len(tables)} tables in the database.")
            
            if tables:
                print("\nAvailable tables:")
                for table in tables:
                    print(f"  - {table}")
                
                # If we have tables, test querying one of them
                test_table = tables[0]
                print(f"\nTesting preview of table '{test_table}'...")
                
                try:
                    df = pd.read_sql(text(f"SELECT TOP 5 * FROM [{test_table}]"), conn)
                    print("✅ Successfully queried table data")
                    print(df.to_string(index=False))
                except Exception as e:
                    print(f"❌ Error querying table: {e}")
                    traceback.print_exc()
        
        print("\n✅ Connection test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Connection error: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("MSSQL Connection Debugging Tool (SQLAlchemy)")
    print("=" * 60)
    
    print_system_info()
    
    # Check network connectivity
    network_ok = check_network_connectivity()
    if not network_ok:
        print("\n⚠️  Network connectivity issue detected!")
        print("   Possible causes:")
        print("   - Firewall blocking connection")
        print("   - Server is not accepting connections from your IP")
        print("   - SQL Server not running on the target server")
        print("   - Incorrect server address or port")
    
    # Test database connection
    print("\nTesting database connection in 3 seconds...")
    sleep(3)  # Give time to see network results
    connection_ok = test_connection_verbose()
    
    print("\n" + "=" * 60)
    if connection_ok:
        print("✅ All tests passed! Your connection is working correctly.")
    else:
        print("❌ Connection test failed. Please check the errors above.")
        print("\nPossible solutions:")
        print("1. Verify server address, database name, username, and password")
        print("2. Check if SQL Server is configured to accept remote connections")
        print("3. Ensure the database user has appropriate permissions")
        print("4. Check firewall settings on both client and server")
        print("5. Try connecting from a different network to isolate network issues")
    print("=" * 60)
