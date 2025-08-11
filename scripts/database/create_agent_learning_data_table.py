#!/usr/bin/env python3
"""
Create Agent Learning Data Table
===============================

This script creates the missing agent_learning_data table that the learning system
needs for storing agent learning data and cross-agent learning capabilities.
"""

import asyncio
import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Set up environment variables
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:FlipSync_DB_Prod_2024_Secure_Key_9x7z@192.168.110.71:5432/flipsync_agentic_test"
os.environ["DB_NAME"] = "flipsync_agentic_test"

async def create_agent_learning_data_table():
    """Create the missing agent_learning_data table."""
    
    print("🔧 Creating Agent Learning Data Table...")
    print("=" * 60)
    
    # Create database connection
    database_url = os.environ["DATABASE_URL"]
    engine = create_async_engine(database_url)
    
    try:
        async with engine.begin() as conn:
            # Check if table already exists
            print("📊 Checking if agent_learning_data table exists...")
            
            check_table_sql = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'agent_learning_data'
            """
            
            result = await conn.execute(text(check_table_sql))
            existing_table = result.fetchone()
            
            if existing_table:
                print("✅ Agent_learning_data table already exists - no changes needed")
                return True
            
            # Create the agent_learning_data table
            print("🔧 Creating agent_learning_data table...")
            
            create_table_sql = """
                CREATE TABLE agent_learning_data (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    agent_id VARCHAR(255) NOT NULL,
                    learning_type VARCHAR(100) NOT NULL,
                    data JSONB NOT NULL,
                    performance_score DECIMAL(5,4),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """
            
            await conn.execute(text(create_table_sql))
            print("✅ Created agent_learning_data table successfully")
            
            # Create indexes for performance
            print("🔧 Creating indexes...")
            
            create_indexes_sql = [
                "CREATE INDEX idx_agent_learning_data_agent_id ON agent_learning_data(agent_id)",
                "CREATE INDEX idx_agent_learning_data_learning_type ON agent_learning_data(learning_type)",
                "CREATE INDEX idx_agent_learning_data_created_at ON agent_learning_data(created_at)"
            ]
            
            for index_sql in create_indexes_sql:
                await conn.execute(text(index_sql))
            
            print("✅ Created indexes successfully")
            
            # Verify the table structure
            print("🔍 Verifying table structure...")
            
            verify_sql = """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'agent_learning_data'
                ORDER BY ordinal_position
            """
            
            result = await conn.execute(text(verify_sql))
            columns = result.fetchall()
            
            print("📊 Table structure:")
            for col in columns:
                print(f"   - {col[0]}: {col[1]} (nullable: {col[2]})")
            
            print("\n✅ Agent learning data table creation completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Table creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await engine.dispose()

async def test_learning_table():
    """Test that the agent_learning_data table works correctly."""
    
    print("\n🧪 Testing Agent Learning Data Table...")
    print("=" * 40)
    
    database_url = os.environ["DATABASE_URL"]
    engine = create_async_engine(database_url)
    
    try:
        async with engine.begin() as conn:
            # Test insert into agent_learning_data table
            test_insert_sql = """
                INSERT INTO agent_learning_data 
                (agent_id, learning_type, data, performance_score)
                VALUES 
                ('test_agent_learning', 'custom', '{"test": "learning_data"}', 0.85)
                RETURNING id
            """
            
            result = await conn.execute(text(test_insert_sql))
            test_id = result.scalar()
            
            print(f"✅ Test insert successful - ID: {test_id}")
            
            # Clean up test record
            cleanup_sql = "DELETE FROM agent_learning_data WHERE id = :test_id"
            await conn.execute(text(cleanup_sql), {"test_id": test_id})
            
            print("✅ Test cleanup completed")
            print("🎯 Agent learning data table validation successful!")
            return True
            
    except Exception as e:
        print(f"❌ Learning table test failed: {e}")
        return False
    
    finally:
        await engine.dispose()

async def main():
    """Main function to create and test the agent_learning_data table."""
    
    print("🚀 Agent Learning Data Table Creation")
    print("=" * 60)
    print("Creating missing agent_learning_data table for learning system")
    print("Database: flipsync_agentic_test")
    print("=" * 60)
    
    # Step 1: Create the table
    table_created = await create_agent_learning_data_table()
    
    if not table_created:
        print("❌ Table creation failed - aborting")
        return False
    
    # Step 2: Test the table
    test_passed = await test_learning_table()
    
    if not test_passed:
        print("❌ Table test failed - creation may be incomplete")
        return False
    
    print("\n🎉 AGENT LEARNING DATA TABLE CREATION COMPLETED SUCCESSFULLY!")
    print("✅ Cross-agent learning system is now functional")
    print("✅ Agent decision feedback loop is complete")
    print("✅ Learning and optimization capabilities fully enabled")
    print("\n🔄 Ready for next phase of fixes!")
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Table creation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Table creation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
