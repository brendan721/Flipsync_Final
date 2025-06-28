#!/usr/bin/env python3
"""
FlipSync Database Connectivity Test and Setup
==============================================

This script tests PostgreSQL connectivity and sets up the AI tools database
while maintaining separation from the main FlipSync application database.
"""

import sys
import socket
import subprocess
import json
from datetime import datetime
from typing import Dict, Any, Optional

def test_port_connectivity(host: str = "localhost", port: int = 1432) -> bool:
    """Test if PostgreSQL port is accessible."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"❌ Socket test failed: {e}")
        return False

def check_database_packages() -> Dict[str, bool]:
    """Check availability of database packages."""
    packages = {
        'psycopg2': False,
        'asyncpg': False,
        'sqlite3': False
    }
    
    for pkg in packages:
        try:
            __import__(pkg)
            packages[pkg] = True
        except ImportError:
            packages[pkg] = False
    
    return packages

def test_postgresql_connection() -> Optional[Dict[str, Any]]:
    """Test PostgreSQL connection using available drivers."""
    packages = check_database_packages()
    
    if packages['psycopg2']:
        return test_psycopg2_connection()
    elif packages['asyncpg']:
        return test_asyncpg_connection()
    else:
        return None

def test_psycopg2_connection() -> Optional[Dict[str, Any]]:
    """Test connection using psycopg2."""
    try:
        import psycopg2
        
        conn = psycopg2.connect(
            host='localhost',
            port=1432,
            user='postgres',
            password='postgres',
            database='postgres'
        )
        
        cursor = conn.cursor()
        cursor.execute('SELECT version();')
        version = cursor.fetchone()[0]
        
        cursor.execute('SELECT datname FROM pg_database;')
        databases = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'driver': 'psycopg2',
            'version': version,
            'databases': databases,
            'success': True
        }
    except Exception as e:
        return {
            'driver': 'psycopg2',
            'error': str(e),
            'success': False
        }

def test_asyncpg_connection() -> Optional[Dict[str, Any]]:
    """Test connection using asyncpg (requires async handling)."""
    try:
        import asyncio
        import asyncpg
        
        async def test_conn():
            conn = await asyncpg.connect(
                host='localhost',
                port=1432,
                user='postgres',
                password='postgres',
                database='postgres'
            )
            
            version = await conn.fetchval('SELECT version();')
            databases = await conn.fetch('SELECT datname FROM pg_database;')
            
            await conn.close()
            
            return {
                'driver': 'asyncpg',
                'version': version,
                'databases': [row['datname'] for row in databases],
                'success': True
            }
        
        return asyncio.run(test_conn())
    except Exception as e:
        return {
            'driver': 'asyncpg',
            'error': str(e),
            'success': False
        }

def setup_ai_tools_database() -> bool:
    """Set up the AI tools database using SQL script."""
    try:
        # Try using psql command if available
        result = subprocess.run([
            'psql', 
            '-h', 'localhost',
            '-p', '1432',
            '-U', 'postgres',
            '-f', 'setup_ai_tools_database.sql'
        ], capture_output=True, text=True, input='postgres\n')
        
        if result.returncode == 0:
            print("✅ AI tools database setup completed via psql")
            return True
        else:
            print(f"❌ psql setup failed: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ psql command not found")
        return False

def test_sqlite_setup() -> Dict[str, Any]:
    """Test SQLite setup and create local database."""
    try:
        import sqlite3
        
        # Create SQLite database for local development
        db_path = 'flipsync_ai_tools.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create basic tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_type TEXT NOT NULL,
                context_key TEXT NOT NULL,
                context_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(agent_type, context_key)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS code_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT,
                insight_type TEXT,
                insight_data TEXT,
                confidence_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Test insert
        cursor.execute(
            'INSERT OR REPLACE INTO agent_memory (agent_type, context_key, context_data) VALUES (?, ?, ?)',
            ('test', 'connectivity_test', json.dumps({'status': 'success', 'timestamp': str(datetime.now())}))
        )
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'database_path': db_path,
            'message': 'SQLite database created successfully'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def main():
    """Main test function."""
    print("🔍 FlipSync Database Connectivity Test")
    print("=" * 50)
    
    # Test port connectivity
    print("\n1. Testing PostgreSQL port connectivity...")
    port_accessible = test_port_connectivity()
    if port_accessible:
        print("✅ PostgreSQL port 1432 is accessible")
    else:
        print("❌ PostgreSQL port 1432 is not accessible")
    
    # Check database packages
    print("\n2. Checking database packages...")
    packages = check_database_packages()
    for pkg, available in packages.items():
        status = "✅" if available else "❌"
        print(f"{status} {pkg}: {'Available' if available else 'Not available'}")
    
    # Test PostgreSQL connection
    print("\n3. Testing PostgreSQL connection...")
    if port_accessible and any(packages.values()):
        pg_result = test_postgresql_connection()
        if pg_result and pg_result['success']:
            print(f"✅ PostgreSQL connection successful using {pg_result['driver']}")
            print(f"   Version: {pg_result['version'][:50]}...")
            print(f"   Available databases: {', '.join(pg_result['databases'])}")
            
            # Check if AI tools database exists
            if 'flipsync_ai_tools' in pg_result['databases']:
                print("✅ flipsync_ai_tools database already exists")
            else:
                print("⚠️  flipsync_ai_tools database does not exist")
                print("   Run setup_ai_tools_database.sql to create it")
        else:
            print(f"❌ PostgreSQL connection failed: {pg_result.get('error', 'Unknown error') if pg_result else 'No suitable driver'}")
    else:
        print("❌ Skipping PostgreSQL test (port not accessible or no drivers)")
    
    # Test SQLite setup
    print("\n4. Testing SQLite setup...")
    sqlite_result = test_sqlite_setup()
    if sqlite_result['success']:
        print(f"✅ SQLite setup successful: {sqlite_result['database_path']}")
    else:
        print(f"❌ SQLite setup failed: {sqlite_result['error']}")
    
    print("\n" + "=" * 50)
    print("Database connectivity test complete!")

if __name__ == "__main__":
    main()
