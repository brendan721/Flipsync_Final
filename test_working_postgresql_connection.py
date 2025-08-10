#!/usr/bin/env python3
"""
Test Working PostgreSQL Connection
==================================

This script tests the PostgreSQL connection using the method that worked
when we successfully created the database earlier.
"""

import asyncio
import os
import subprocess
import sys
from pathlib import Path

async def test_postgresql_connection_methods():
    """Test different PostgreSQL connection methods."""
    print("🔍 Testing PostgreSQL Connection Methods")
    print("=" * 50)
    
    # Method that worked before - let's replicate it exactly
    print("🔄 Testing the method that worked when we created the database...")
    
    try:
        # This is the exact command that worked before
        env = os.environ.copy()
        env['PGPASSWORD'] = ''  # Empty password
        
        result = subprocess.run(
            ["psql", "-h", "localhost", "-U", "postgres", "-f", "/tmp/flipsync_setup.sql"],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
            input="\n"  # Send empty input for password prompt
        )
        
        if result.returncode == 0:
            print("✅ SQL script execution method works!")
            print("Output:", result.stdout[-200:])  # Show last 200 chars
            return True
        else:
            print(f"❌ SQL script method failed: {result.stderr[:100]}...")
            
    except Exception as e:
        print(f"❌ SQL script method error: {e}")
    
    # Try direct asyncpg connection with different parameters
    print("\n🔄 Testing asyncpg connection methods...")
    
    connection_params = [
        # Method 1: No password, explicit host
        {"host": "localhost", "port": 5432, "user": "postgres", "database": "flipsync_agentic_test"},
        # Method 2: Try with empty password
        {"host": "localhost", "port": 5432, "user": "postgres", "password": "", "database": "flipsync_agentic_test"},
        # Method 3: Try with current user
        {"host": "localhost", "port": 5432, "user": "brend", "database": "flipsync_agentic_test"},
        # Method 4: Try without explicit host (Unix socket)
        {"user": "postgres", "database": "flipsync_agentic_test"},
    ]
    
    for i, params in enumerate(connection_params, 1):
        print(f"\nMethod {i}: {params}")
        try:
            import asyncpg
            
            conn = await asyncpg.connect(**params)
            
            # Test basic query
            version = await conn.fetchval('SELECT version()')
            print(f"✅ Method {i} SUCCESS!")
            print(f"   Version: {version[:50]}...")
            
            # Test table access
            count = await conn.fetchval('SELECT COUNT(*) FROM autonomous_agents')
            print(f"   Agents in database: {count}")
            
            await conn.close()
            return True, params
            
        except Exception as e:
            print(f"❌ Method {i} failed: {e}")
    
    return False, None

async def test_agent_with_working_connection(connection_params):
    """Test agent functionality with working connection parameters."""
    print("\n🤖 Testing Agent with Working Connection")
    print("=" * 50)
    
    try:
        # Set up environment for the working connection
        if connection_params:
            if "password" in connection_params and connection_params["password"] == "":
                database_url = f"postgresql+asyncpg://{connection_params['user']}:@{connection_params['host']}:{connection_params['port']}/{connection_params['database']}"
            elif "password" not in connection_params:
                database_url = f"postgresql+asyncpg://{connection_params['user']}@{connection_params['host']}:{connection_params['port']}/{connection_params['database']}"
            else:
                database_url = f"postgresql+asyncpg://{connection_params['user']}:{connection_params['password']}@{connection_params['host']}:{connection_params['port']}/{connection_params['database']}"
            
            os.environ['DATABASE_URL'] = database_url
            print(f"✅ Set DATABASE_URL: {database_url}")
        
        from fs_agt_clean.agents.market.market_agent import MarketAutonomousAgent
        
        print("✅ Creating MarketAgent...")
        agent = MarketAutonomousAgent()
        print(f"✅ Agent created: {agent.agent_id}")
        
        # Test initialization
        print("🔄 Testing agent initialization...")
        success = await agent.initialize_async()
        
        if success:
            print("🎉 SUCCESS! Agent initialization completed")
            
            # Test decision making
            print("🔄 Testing decision making...")
            test_context = {
                'decision_type': 'pricing_optimization',
                'product_data': {'price': 100, 'category': 'electronics'}
            }
            
            result = await agent.make_decision('pricing_optimization', test_context)
            
            if result.get('success'):
                print("🎉 SUCCESS! Decision making works!")
                return True
            else:
                print(f"⚠️  Decision making failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print("❌ Agent initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    print("🚀 Testing Working PostgreSQL Connection for FlipSync")
    print("=" * 70)
    
    # Test connection methods
    success, working_params = await test_postgresql_connection_methods()
    
    if success:
        print(f"\n✅ Found working connection method: {working_params}")
        
        # Test agent with working connection
        agent_success = await test_agent_with_working_connection(working_params)
        
        if agent_success:
            print("\n🎉 COMPLETE SUCCESS!")
            print("✅ PostgreSQL connection: WORKING")
            print("✅ Agent registration: WORKING")
            print("✅ Decision making: WORKING")
            print("\n🚀 Ready to test full 4+1 architecture!")
            return 0
        else:
            print("\n⚠️  Connection works but agent functionality has issues")
            return 1
    else:
        print("\n❌ No working PostgreSQL connection method found")
        print("Need to investigate PostgreSQL configuration further")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
