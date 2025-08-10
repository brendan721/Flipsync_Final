#!/usr/bin/env python3
"""
Create Agent Feedback Table
===========================

This script creates the missing agent_feedback table that the autonomous agents
need for storing feedback data about their decisions.
"""

import asyncio
import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Set up environment variables
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:FlipSync_DB_Prod_2024_Secure_Key_9x7z@174.138.77.110:5432/flipsync_agentic_test"
os.environ["DB_NAME"] = "flipsync_agentic_test"

async def create_agent_feedback_table():
    """Create the missing agent_feedback table."""
    
    print("🔧 Creating Agent Feedback Table...")
    print("=" * 60)
    
    # Create database connection
    database_url = os.environ["DATABASE_URL"]
    engine = create_async_engine(database_url)
    
    try:
        async with engine.begin() as conn:
            # Check if table already exists
            print("📊 Checking if agent_feedback table exists...")
            
            check_table_sql = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'agent_feedback'
            """
            
            result = await conn.execute(text(check_table_sql))
            existing_table = result.fetchone()
            
            if existing_table:
                print("✅ Agent_feedback table already exists - no changes needed")
                return True
            
            # Create the agent_feedback table
            print("🔧 Creating agent_feedback table...")
            
            create_table_sql = """
                CREATE TABLE agent_feedback (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    decision_id UUID NOT NULL,
                    feedback_data JSONB,
                    quality_score DECIMAL(3,2),
                    outcome VARCHAR(50),
                    execution_time DECIMAL(10,3),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    processor_id VARCHAR(255)
                )
            """
            
            await conn.execute(text(create_table_sql))
            print("✅ Created agent_feedback table successfully")
            
            # Create index on decision_id for performance
            print("🔧 Creating index on decision_id...")
            
            create_index_sql = """
                CREATE INDEX idx_agent_feedback_decision_id 
                ON agent_feedback(decision_id)
            """
            
            await conn.execute(text(create_index_sql))
            print("✅ Created index on decision_id")
            
            # Verify the table structure
            print("🔍 Verifying table structure...")
            
            verify_sql = """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'agent_feedback'
                ORDER BY ordinal_position
            """
            
            result = await conn.execute(text(verify_sql))
            columns = result.fetchall()
            
            print("📊 Table structure:")
            for col in columns:
                print(f"   - {col[0]}: {col[1]} (nullable: {col[2]})")
            
            print("\n✅ Agent feedback table creation completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Table creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await engine.dispose()

async def test_table_creation():
    """Test that the agent_feedback table works correctly."""
    
    print("\n🧪 Testing Agent Feedback Table...")
    print("=" * 40)
    
    database_url = os.environ["DATABASE_URL"]
    engine = create_async_engine(database_url)
    
    try:
        async with engine.begin() as conn:
            # Test insert into agent_feedback table
            test_insert_sql = """
                INSERT INTO agent_feedback 
                (decision_id, feedback_data, quality_score, outcome, execution_time, processor_id)
                VALUES 
                (gen_random_uuid(), '{"test": true}', 0.85, 'success', 1.5, 'test_processor')
                RETURNING id
            """
            
            result = await conn.execute(text(test_insert_sql))
            test_id = result.scalar()
            
            print(f"✅ Test insert successful - ID: {test_id}")
            
            # Clean up test record
            cleanup_sql = "DELETE FROM agent_feedback WHERE id = :test_id"
            await conn.execute(text(cleanup_sql), {"test_id": test_id})
            
            print("✅ Test cleanup completed")
            print("🎯 Agent feedback table validation successful!")
            return True
            
    except Exception as e:
        print(f"❌ Table test failed: {e}")
        return False
    
    finally:
        await engine.dispose()

async def main():
    """Main function to create and test the agent_feedback table."""
    
    print("🚀 Agent Feedback Table Creation")
    print("=" * 60)
    print("Creating missing agent_feedback table for autonomous agents")
    print("Database: flipsync_agentic_test")
    print("=" * 60)
    
    # Step 1: Create the table
    table_created = await create_agent_feedback_table()
    
    if not table_created:
        print("❌ Table creation failed - aborting")
        return False
    
    # Step 2: Test the table
    test_passed = await test_table_creation()
    
    if not test_passed:
        print("❌ Table test failed - creation may be incomplete")
        return False
    
    print("\n🎉 AGENT FEEDBACK TABLE CREATION COMPLETED SUCCESSFULLY!")
    print("✅ Autonomous agents can now store feedback data")
    print("✅ Decision feedback loop is now functional")
    print("✅ Learning and optimization capabilities enabled")
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
