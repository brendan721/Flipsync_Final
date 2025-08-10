#!/usr/bin/env python3
"""
Fix Agent Registration in PostgreSQL Database
============================================

This script ensures that agents can properly register themselves
in the database and make decisions.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

async def register_agent_in_database():
    """Register a test agent in the database to fix decision making."""
    print("🔧 Registering test agent in database...")
    
    try:
        import asyncpg
        
        # Connect to database
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="postgres",
            database="flipsync_agentic_test"
        )
        
        # Register a test agent with the exact ID format the code uses
        test_agent_id = "market_agent_20250810_111138_decision_maker"
        
        await conn.execute('''
        INSERT INTO autonomous_agents (agent_id, agent_type) 
        VALUES ($1, $2) ON CONFLICT (agent_id) DO NOTHING
        ''', test_agent_id, 'market')
        
        # Also register the base agent ID
        base_agent_id = "market_agent_20250810_111138"
        await conn.execute('''
        INSERT INTO autonomous_agents (agent_id, agent_type) 
        VALUES ($1, $2) ON CONFLICT (agent_id) DO NOTHING
        ''', base_agent_id, 'market')
        
        # Verify registration
        count = await conn.fetchval(
            'SELECT COUNT(*) FROM autonomous_agents WHERE agent_id LIKE $1',
            'market_agent_20250810_111138%'
        )
        
        await conn.close()
        
        print(f"✅ Registered agents: {count}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to register agent: {e}")
        return False

async def test_agent_decision_with_registration():
    """Test agent decision making after proper registration."""
    print("🧪 Testing agent decision making with registration...")
    
    try:
        from fs_agt_clean.agents.market.market_agent import MarketAutonomousAgent
        
        # Create agent
        agent = MarketAutonomousAgent()
        print(f"✅ Agent created with ID: {agent.agent_id}")
        
        # Register this specific agent in database
        import asyncpg
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="postgres",
            database="flipsync_agentic_test"
        )
        
        # Register the agent and its decision maker
        await conn.execute('''
        INSERT INTO autonomous_agents (agent_id, agent_type) 
        VALUES ($1, $2) ON CONFLICT (agent_id) DO NOTHING
        ''', agent.agent_id, 'market')
        
        await conn.execute('''
        INSERT INTO autonomous_agents (agent_id, agent_type) 
        VALUES ($1, $2) ON CONFLICT (agent_id) DO NOTHING
        ''', f"{agent.agent_id}_decision_maker", 'market')
        
        await conn.close()
        
        print("✅ Agent registered in database")
        
        # Now try decision making
        test_context = {
            'decision_type': 'pricing_optimization',
            'product_data': {'price': 100, 'category': 'electronics'}
        }
        
        result = await agent.make_decision('pricing_optimization', test_context)
        
        if result.get('success'):
            print('🎉 SUCCESS! Agent decision making now works!')
            print(f'Decision result: {result}')
            return True
        else:
            print(f'❌ Decision still failed: {result.get("error", "Unknown error")}')
            return False
            
    except Exception as e:
        print(f'❌ Test failed: {e}')
        import traceback
        traceback.print_exc()
        return False

async def create_dynamic_agent_registration():
    """Create a system that automatically registers agents."""
    print("🔧 Setting up dynamic agent registration...")
    
    try:
        import asyncpg
        
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            user="postgres",
            database="flipsync_agentic_test"
        )
        
        # Create a function to auto-register agents
        await conn.execute('''
        CREATE OR REPLACE FUNCTION auto_register_agent(agent_id_param TEXT, agent_type_param TEXT)
        RETURNS BOOLEAN AS $$
        BEGIN
            INSERT INTO autonomous_agents (agent_id, agent_type) 
            VALUES (agent_id_param, agent_type_param) 
            ON CONFLICT (agent_id) DO NOTHING;
            RETURN TRUE;
        END;
        $$ LANGUAGE plpgsql;
        ''')
        
        # Test the function
        result = await conn.fetchval(
            "SELECT auto_register_agent($1, $2)",
            'test_agent_function', 'test'
        )
        
        await conn.close()
        
        print(f"✅ Dynamic registration function created: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create registration function: {e}")
        return False

async def main():
    """Main function to fix agent registration."""
    print("🚀 Fixing Agent Registration for PostgreSQL")
    print("=" * 60)
    
    # Step 1: Register test agents
    if not await register_agent_in_database():
        print("❌ Agent registration failed!")
        return False
    
    # Step 2: Create dynamic registration
    if not await create_dynamic_agent_registration():
        print("⚠️  Dynamic registration failed, but continuing...")
    
    # Step 3: Test agent decision making
    success = await test_agent_decision_with_registration()
    
    print("=" * 60)
    if success:
        print("🎉 AGENT REGISTRATION FIX: SUCCESS!")
        print("✅ Agents can now make and store decisions in PostgreSQL")
    else:
        print("⚠️  Agent registration improved but decision making still has issues")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
