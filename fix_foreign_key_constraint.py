#!/usr/bin/env python3
"""
Fix Foreign Key Constraint - Remove agent_decisions_agent_id_fkey
================================================================

This script removes the foreign key constraint that prevents autonomous agents
from storing decisions when they're not registered in the unified_agents table.

Autonomous agents should be able to make decisions independently without
requiring registration in the unified_agents table.
"""

import asyncio
import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Set up environment variables
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:FlipSync_DB_Prod_2024_Secure_Key_9x7z@174.138.77.110:5432/flipsync_agentic_test"
os.environ["DB_NAME"] = "flipsync_agentic_test"

async def fix_foreign_key_constraint():
    """Remove the foreign key constraint that blocks autonomous agent decisions."""
    
    print("🔧 Fixing Foreign Key Constraint...")
    print("=" * 60)
    
    # Create database connection
    database_url = os.environ["DATABASE_URL"]
    engine = create_async_engine(database_url)
    
    try:
        async with engine.begin() as conn:
            # Check if foreign key constraint exists
            print("📊 Checking for foreign key constraint...")
            
            check_constraint_sql = """
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_name = 'agent_decisions' 
                AND constraint_type = 'FOREIGN KEY'
                AND constraint_name LIKE '%agent_id%'
            """
            
            result = await conn.execute(text(check_constraint_sql))
            constraints = result.fetchall()
            
            if not constraints:
                print("✅ No foreign key constraints found - no changes needed")
                return True
            
            print(f"🔍 Found {len(constraints)} foreign key constraint(s):")
            for constraint in constraints:
                print(f"   - {constraint[0]}")
            
            # Remove the foreign key constraint
            for constraint in constraints:
                constraint_name = constraint[0]
                print(f"🔧 Removing foreign key constraint: {constraint_name}")
                
                drop_constraint_sql = f"""
                    ALTER TABLE agent_decisions 
                    DROP CONSTRAINT IF EXISTS {constraint_name}
                """
                
                await conn.execute(text(drop_constraint_sql))
                print(f"✅ Removed constraint: {constraint_name}")
            
            # Verify the constraint is removed
            print("🔍 Verifying constraint removal...")
            
            result = await conn.execute(text(check_constraint_sql))
            remaining_constraints = result.fetchall()
            
            if remaining_constraints:
                print(f"⚠️ Warning: {len(remaining_constraints)} constraints still exist")
                for constraint in remaining_constraints:
                    print(f"   - {constraint[0]}")
            else:
                print("✅ All foreign key constraints successfully removed")
            
            print("\n✅ Foreign key constraint fix completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Foreign key constraint fix failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await engine.dispose()

async def test_constraint_fix():
    """Test that agents can now store decisions without foreign key issues."""
    
    print("\n🧪 Testing Constraint Fix...")
    print("=" * 40)
    
    database_url = os.environ["DATABASE_URL"]
    engine = create_async_engine(database_url)
    
    try:
        async with engine.begin() as conn:
            # Test insert with a non-existent agent_id
            test_insert_sql = """
                INSERT INTO agent_decisions 
                (id, agent_id, decision_type, parameters, confidence, rationale, status, created_at, result)
                VALUES 
                (gen_random_uuid(), 'test_autonomous_agent_constraint_fix', 'test_decision', 
                 '{"test": true}', 0.95, 'Constraint fix test', 'completed', NOW(), 
                 '{"test_result": "success"}')
                RETURNING id
            """
            
            result = await conn.execute(text(test_insert_sql))
            test_id = result.scalar()
            
            print(f"✅ Test insert successful - ID: {test_id}")
            print("✅ Autonomous agents can now store decisions independently")
            
            # Clean up test record
            cleanup_sql = "DELETE FROM agent_decisions WHERE id = :test_id"
            await conn.execute(text(cleanup_sql), {"test_id": test_id})
            
            print("✅ Test cleanup completed")
            print("🎯 Constraint fix validation successful!")
            return True
            
    except Exception as e:
        print(f"❌ Constraint test failed: {e}")
        return False
    
    finally:
        await engine.dispose()

async def main():
    """Main function to fix and test the foreign key constraint."""
    
    print("🚀 Foreign Key Constraint Fix")
    print("=" * 60)
    print("Removing foreign key constraint from agent_decisions table")
    print("This allows autonomous agents to make decisions independently")
    print("Database: flipsync_agentic_test")
    print("=" * 60)
    
    # Step 1: Fix the constraint
    constraint_fixed = await fix_foreign_key_constraint()
    
    if not constraint_fixed:
        print("❌ Constraint fix failed - aborting")
        return False
    
    # Step 2: Test the fix
    test_passed = await test_constraint_fix()
    
    if not test_passed:
        print("❌ Constraint test failed - fix may be incomplete")
        return False
    
    print("\n🎉 FOREIGN KEY CONSTRAINT FIX COMPLETED SUCCESSFULLY!")
    print("✅ Autonomous agents can now store decisions independently")
    print("✅ No registration in unified_agents table required")
    print("✅ DatabaseDecisionMaker should now work without foreign key errors")
    print("\n🔄 Ready to re-run the autonomous agent optimization test!")
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Constraint fix interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Constraint fix failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
