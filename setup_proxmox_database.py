#!/usr/bin/env python3
"""
Setup Proxmox Database for FlipSync Agents
==========================================

This script sets up the database properly for the 4+1 agent architecture
after migration from DigitalOcean to Proxmox.
"""

import sqlite3
import os
import sys
from pathlib import Path

def setup_sqlite_database():
    """Set up SQLite database with proper schema and test data."""
    
    db_path = Path("/home/brend/Flipsync_Final/flipsync_local.db")
    
    print(f"🔧 Setting up SQLite database at {db_path}")
    
    # Create connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create autonomous_agents table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS autonomous_agents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT UNIQUE NOT NULL,
        agent_type TEXT NOT NULL,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create autonomous_agent_decisions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS autonomous_agent_decisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT NOT NULL,
        decision_type TEXT NOT NULL,
        context TEXT,
        result TEXT,
        confidence REAL,
        execution_time_ms INTEGER,
        success BOOLEAN,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create learning_knowledge_base table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS learning_knowledge_base (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_type TEXT NOT NULL,
        learning_type TEXT NOT NULL,
        learning_data TEXT,
        success_rate REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Insert test agents for the 4+1 architecture
    test_agents = [
        ('market_agent_test', 'market'),
        ('executive_agent_test', 'executive'),
        ('content_agent_test', 'content'),
        ('logistics_agent_test', 'logistics'),
        ('conversational_agent_test', 'conversational')
    ]
    
    for agent_id, agent_type in test_agents:
        cursor.execute('''
        INSERT OR IGNORE INTO autonomous_agents (agent_id, agent_type) 
        VALUES (?, ?)
        ''', (agent_id, agent_type))
    
    # Insert some test learning data
    cursor.execute('''
    INSERT OR IGNORE INTO learning_knowledge_base 
    (agent_type, learning_type, learning_data, success_rate) 
    VALUES ('market', 'pricing_optimization', '{"test": "data"}', 0.85)
    ''')
    
    conn.commit()
    
    # Verify the setup
    cursor.execute('SELECT COUNT(*) FROM autonomous_agents')
    agent_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM learning_knowledge_base')
    learning_count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"✅ Database setup complete:")
    print(f"   - Agents: {agent_count}")
    print(f"   - Learning records: {learning_count}")
    
    return db_path

def test_agent_with_proper_db():
    """Test agent functionality with properly set up database."""
    
    print("\n🧪 Testing agent with proper database setup...")
    
    # Set environment variables
    os.environ['DATABASE_URL'] = 'sqlite:///flipsync_local.db'
    os.environ['JWT_SECRET'] = 'FlipSync_JWT_Prod_2024_Secure_Key_7NaznE9ddVcN_Lq0LVHIFBKa9taUQnVOWZU6IjcV7Ww'
    os.environ['AUTH_SERVICE_TYPE'] = 'database'
    os.environ['GEMINI_API_KEY'] = 'AIzaSyC-6wbp5dPG1I4tEmmFbb9irZcwdB0oqVA'
    
    try:
        # Test direct SQLite connection
        conn = sqlite3.connect('flipsync_local.db')
        cursor = conn.cursor()
        
        # Insert a test agent that matches what the code will look for
        test_agent_id = 'market_agent_20250810_test'
        cursor.execute('''
        INSERT OR IGNORE INTO autonomous_agents (agent_id, agent_type) 
        VALUES (?, ?)
        ''', (test_agent_id, 'market'))
        
        # Insert a test decision
        cursor.execute('''
        INSERT INTO autonomous_agent_decisions 
        (agent_id, decision_type, context, result, confidence, execution_time_ms, success) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (test_agent_id, 'pricing_optimization', '{"test": "context"}', 
              '{"test": "result"}', 0.95, 150, True))
        
        conn.commit()
        conn.close()
        
        print("✅ Test data inserted successfully")
        
        # Verify the data
        conn = sqlite3.connect('flipsync_local.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM autonomous_agents')
        agents = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM autonomous_agent_decisions')
        decisions = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"✅ Database verification:")
        print(f"   - Total agents: {agents}")
        print(f"   - Total decisions: {decisions}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def main():
    """Main setup function."""
    
    print("🚀 FlipSync Proxmox Database Setup")
    print("=" * 50)
    
    # Step 1: Set up database
    db_path = setup_sqlite_database()
    
    # Step 2: Test database functionality
    success = test_agent_with_proper_db()
    
    if success:
        print("\n✅ Database setup completed successfully!")
        print(f"Database location: {db_path}")
        print("\nNext steps:")
        print("1. Test agent decision making")
        print("2. Verify WebSocket connectivity")
        print("3. Test full 4+1 architecture")
    else:
        print("\n❌ Database setup failed!")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
