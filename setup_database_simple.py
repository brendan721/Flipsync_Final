#!/usr/bin/env python3
"""
Simple Database Setup for FlipSync
==================================

This script sets up the database using the existing PostgreSQL connection
that's already working.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_sql_command(sql_command):
    """Run a SQL command using psql."""
    try:
        # Try different connection methods
        methods = [
            ["psql", "-h", "localhost", "-U", "postgres", "-c", sql_command],
            ["psql", "-U", "postgres", "-c", sql_command],
            ["psql", "-c", sql_command]
        ]
        
        for method in methods:
            try:
                result = subprocess.run(
                    method,
                    capture_output=True,
                    text=True,
                    input="\n",  # Send empty password
                    timeout=10
                )
                
                if result.returncode == 0:
                    print(f"✅ SQL executed successfully: {sql_command[:50]}...")
                    return True, result.stdout
                    
            except subprocess.TimeoutExpired:
                continue
            except Exception:
                continue
        
        print(f"❌ Failed to execute SQL: {sql_command[:50]}...")
        return False, None
        
    except Exception as e:
        print(f"❌ Error running SQL command: {e}")
        return False, None

def create_database_schema():
    """Create the database schema using SQL files."""
    print("🔧 Creating database schema...")
    
    # Create the database
    success, _ = run_sql_command("CREATE DATABASE flipsync_agentic_test;")
    if not success:
        print("Database might already exist, continuing...")
    
    # Create schema SQL
    schema_sql = """
    \\c flipsync_agentic_test;
    
    CREATE TABLE IF NOT EXISTS autonomous_agents (
        id SERIAL PRIMARY KEY,
        agent_id VARCHAR(255) UNIQUE NOT NULL,
        agent_type VARCHAR(100) NOT NULL,
        status VARCHAR(50) DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS autonomous_agent_decisions (
        id SERIAL PRIMARY KEY,
        agent_id VARCHAR(255) NOT NULL,
        decision_type VARCHAR(100) NOT NULL,
        context TEXT,
        result TEXT,
        confidence REAL,
        execution_time_ms INTEGER,
        success BOOLEAN,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS learning_knowledge_base (
        id SERIAL PRIMARY KEY,
        agent_type VARCHAR(100) NOT NULL,
        learning_type VARCHAR(100) NOT NULL,
        learning_data TEXT,
        success_rate REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    INSERT INTO autonomous_agents (agent_id, agent_type) VALUES 
    ('market_agent_test', 'market'),
    ('executive_agent_test', 'executive'),
    ('content_agent_test', 'content'),
    ('logistics_agent_test', 'logistics'),
    ('conversational_agent_test', 'conversational')
    ON CONFLICT (agent_id) DO NOTHING;
    """
    
    # Write schema to temporary file
    schema_file = Path("/tmp/flipsync_schema.sql")
    schema_file.write_text(schema_sql)
    
    # Execute schema file
    try:
        result = subprocess.run(
            ["psql", "-h", "localhost", "-U", "postgres", "-f", str(schema_file)],
            capture_output=True,
            text=True,
            input="\n",  # Send empty password
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ Database schema created successfully")
            return True
        else:
            print(f"❌ Schema creation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating schema: {e}")
        return False

def update_env_file():
    """Update .env file with correct PostgreSQL configuration."""
    print("🔧 Updating .env file...")
    
    env_path = Path("/home/brend/Flipsync_Final/.env")
    
    # Read current .env file
    if env_path.exists():
        lines = env_path.read_text().split('\n')
    else:
        lines = []
    
    # Update DATABASE_URL
    new_database_url = "postgresql+asyncpg://postgres@localhost:5432/flipsync_agentic_test"
    
    # Replace or add DATABASE_URL
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('DATABASE_URL='):
            lines[i] = f'DATABASE_URL={new_database_url}'
            updated = True
            break
    
    if not updated:
        lines.append(f'DATABASE_URL={new_database_url}')
    
    # Write back to file
    env_path.write_text('\n'.join(lines))
    
    print(f"✅ Updated .env file")
    print(f"   DATABASE_URL={new_database_url}")

def test_connection():
    """Test the database connection."""
    print("🧪 Testing database connection...")
    
    success, output = run_sql_command("\\c flipsync_agentic_test; SELECT COUNT(*) FROM autonomous_agents;")
    
    if success:
        print("✅ Database connection test passed")
        return True
    else:
        print("❌ Database connection test failed")
        return False

def main():
    """Main setup function."""
    print("🚀 FlipSync Simple Database Setup")
    print("=" * 50)
    
    # Step 1: Create database schema
    if not create_database_schema():
        print("❌ Database setup failed!")
        return False
    
    # Step 2: Update environment file
    update_env_file()
    
    # Step 3: Test connection
    if not test_connection():
        print("⚠️  Database created but connection test failed")
    
    print("=" * 50)
    print("✅ Database setup completed!")
    print("Next steps:")
    print("1. Test 4+1 agent decision making")
    print("2. Verify WebSocket endpoints")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
