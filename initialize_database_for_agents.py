#!/usr/bin/env python3
"""
Initialize Database for 4+1 Agent Architecture
==============================================

This script properly initializes the PostgreSQL database using the existing
FlipSync database initialization system, ensuring that agents can register
themselves properly.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

async def initialize_database_properly():
    """Initialize database using the existing FlipSync database system."""
    print("🚀 Initializing Database for 4+1 Agent Architecture")
    print("=" * 60)
    
    try:
        # Import the existing database initialization system
        from fs_agt_clean.core.db.database import Database, get_database
        from fs_agt_clean.core.config.config_manager import ConfigManager
        
        print("✅ Imported database modules")
        
        # Create config manager
        config_manager = ConfigManager()
        
        # Get database connection string from environment
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ DATABASE_URL not found in environment")
            return False
        
        print(f"✅ Database URL: {database_url}")
        
        # Create database instance
        database = Database(
            config_manager=config_manager,
            connection_string=database_url,
            pool_size=10,
            max_overflow=20,
            echo=False
        )
        
        print("✅ Database instance created")
        
        # Initialize database connection
        await database.initialize()
        print("✅ Database connection initialized")
        
        # Create all tables using the existing system
        await database.create_tables()
        print("✅ Database tables created")
        
        # Verify the autonomous_agents table exists
        async with database.get_session() as session:
            from sqlalchemy import text
            
            # Check if autonomous_agents table exists
            result = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'autonomous_agents'
            """))
            
            table_exists = result.fetchone() is not None
            
            if table_exists:
                print("✅ autonomous_agents table exists")
                
                # Check table structure
                result = await session.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'autonomous_agents'
                    ORDER BY ordinal_position
                """))
                
                columns = result.fetchall()
                print(f"✅ Table has {len(columns)} columns:")
                for col in columns:
                    print(f"   - {col[0]}: {col[1]}")
                    
            else:
                print("❌ autonomous_agents table does not exist")
                return False
        
        await database.close()
        print("✅ Database connection closed")
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_agent_registration():
    """Test that agents can now register properly."""
    print("\n🧪 Testing Agent Registration")
    print("=" * 40)
    
    try:
        from fs_agt_clean.agents.market.market_agent import MarketAutonomousAgent
        
        print("✅ Creating MarketAgent...")
        agent = MarketAutonomousAgent()
        
        print(f"✅ Agent created with ID: {agent.agent_id}")
        
        # Test the registration process
        print("🔄 Testing agent registration...")
        
        # The agent should register itself during initialization
        success = await agent.initialize_async()
        
        if success:
            print("🎉 SUCCESS! Agent registered successfully")
            
            # Test decision making
            print("🔄 Testing decision making...")
            test_context = {
                'decision_type': 'pricing_optimization',
                'product_data': {'price': 100, 'category': 'electronics'}
            }
            
            result = await agent.make_decision('pricing_optimization', test_context)
            
            if result.get('success'):
                print("🎉 SUCCESS! Agent decision making works!")
                return True
            else:
                print(f"⚠️  Decision making failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print("❌ Agent registration failed")
            return False
            
    except Exception as e:
        print(f"❌ Agent registration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def verify_all_agents():
    """Verify all 4 agents can initialize properly."""
    print("\n🔄 Testing All 4+1 Agents")
    print("=" * 40)
    
    agents_to_test = [
        ('Market', 'fs_agt_clean.agents.market.market_agent', 'MarketAutonomousAgent'),
        ('Executive', 'fs_agt_clean.agents.executive.executive_agent', 'ExecutiveAutonomousAgent'),
        ('Content', 'fs_agt_clean.agents.content.content_agent', 'ContentAutonomousAgent'),
        ('Logistics', 'fs_agt_clean.agents.logistics.logistics_agent', 'LogisticsAutonomousAgent')
    ]
    
    successful_agents = 0
    
    for agent_name, module_path, class_name in agents_to_test:
        try:
            print(f"\n🔄 Testing {agent_name}Agent...")
            
            # Dynamic import
            module = __import__(module_path, fromlist=[class_name])
            agent_class = getattr(module, class_name)
            
            agent = agent_class()
            print(f"✅ {agent_name}Agent created: {agent.agent_id}")
            
            # Test initialization
            success = await agent.initialize_async()
            
            if success:
                print(f"✅ {agent_name}Agent registered successfully")
                successful_agents += 1
            else:
                print(f"⚠️  {agent_name}Agent registration failed")
                
        except Exception as e:
            print(f"❌ {agent_name}Agent failed: {e}")
    
    print(f"\n📊 Results: {successful_agents}/4 agents successful")
    return successful_agents

async def main():
    """Main function."""
    
    # Step 1: Initialize database
    db_success = await initialize_database_properly()
    
    if not db_success:
        print("\n❌ Database initialization failed!")
        return False
    
    # Step 2: Test agent registration
    agent_success = await test_agent_registration()
    
    # Step 3: Verify all agents
    agent_count = await verify_all_agents()
    
    print("\n" + "=" * 60)
    print("🎯 FINAL RESULTS:")
    print(f"✅ Database initialization: {'SUCCESS' if db_success else 'FAILED'}")
    print(f"✅ Agent registration: {'SUCCESS' if agent_success else 'FAILED'}")
    print(f"✅ All agents working: {agent_count}/4")
    
    if db_success and agent_success and agent_count >= 3:
        print("\n🎉 PROXMOX POSTGRESQL SETUP COMPLETE!")
        print("The 4+1 architecture is ready for production deployment")
        print("\nNext steps:")
        print("1. Start the FastAPI server")
        print("2. Test WebSocket endpoints")
        print("3. Verify full system integration")
        return True
    else:
        print("\n⚠️  Some issues remain, but progress has been made")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
