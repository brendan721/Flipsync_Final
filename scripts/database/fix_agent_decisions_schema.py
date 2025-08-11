#!/usr/bin/env python3
"""
Fix Agent Decisions Schema - Add Missing Result Column
=====================================================

This script fixes the agent_decisions table schema by adding the missing 'result' column
that the DatabaseDecisionMaker expects but doesn't exist in the current schema.

The table currently has 'execution_result' but the code expects 'result'.
"""

import asyncio
import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Set up environment variables
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://postgres:FlipSync_DB_Prod_2024_Secure_Key_9x7z@192.168.110.71:5432/flipsync_agentic_test"
)
os.environ["DB_NAME"] = "flipsync_agentic_test"


async def fix_agent_decisions_schema():
    """Fix the agent_decisions table schema by adding the missing result column."""

    print("🔧 Fixing Agent Decisions Schema...")
    print("=" * 60)

    # Create database connection
    database_url = os.environ["DATABASE_URL"]
    engine = create_async_engine(database_url)

    try:
        async with engine.begin() as conn:
            # Check if result column already exists
            print("📊 Checking current table schema...")

            check_column_sql = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'agent_decisions' 
                AND column_name = 'result'
            """

            result = await conn.execute(text(check_column_sql))
            existing_column = result.fetchone()

            if existing_column:
                print("✅ Result column already exists - no changes needed")
                return True

            # Add the missing result column
            print("🔧 Adding missing 'result' column...")

            add_column_sql = """
                ALTER TABLE agent_decisions 
                ADD COLUMN result JSONB
            """

            await conn.execute(text(add_column_sql))
            print("✅ Added 'result' column to agent_decisions table")

            # Copy data from execution_result to result for existing records
            print("📋 Copying existing data from execution_result to result...")

            copy_data_sql = """
                UPDATE agent_decisions
                SET result = execution_result::jsonb
                WHERE execution_result IS NOT NULL
                AND result IS NULL
            """

            result = await conn.execute(text(copy_data_sql))
            rows_updated = result.rowcount
            print(f"✅ Copied data for {rows_updated} existing records")

            # Verify the fix
            print("🔍 Verifying schema fix...")

            verify_sql = """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'agent_decisions' 
                AND column_name IN ('result', 'execution_result')
                ORDER BY column_name
            """

            result = await conn.execute(text(verify_sql))
            columns = result.fetchall()

            print("📊 Current schema:")
            for col in columns:
                print(f"   - {col[0]}: {col[1]} (nullable: {col[2]})")

            print("\n✅ Schema fix completed successfully!")
            return True

    except Exception as e:
        print(f"❌ Schema fix failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        await engine.dispose()


async def test_schema_fix():
    """Test that the schema fix works by checking column existence."""

    print("\n🧪 Testing Schema Fix...")
    print("=" * 40)

    database_url = os.environ["DATABASE_URL"]
    engine = create_async_engine(database_url)

    try:
        async with engine.begin() as conn:
            # Test that result column exists and is accessible
            test_column_sql = """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'agent_decisions'
                AND column_name = 'result'
            """

            result = await conn.execute(text(test_column_sql))
            column_info = result.fetchone()

            if column_info:
                print(
                    f"✅ Result column found: {column_info[0]} ({column_info[1]}, nullable: {column_info[2]})"
                )
                print("🎯 Schema fix validation successful!")
                return True
            else:
                print("❌ Result column not found")
                return False

    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        return False

    finally:
        await engine.dispose()


async def main():
    """Main function to fix and test the schema."""

    print("🚀 Agent Decisions Schema Fix")
    print("=" * 60)
    print("Fixing missing 'result' column in agent_decisions table")
    print("Database: flipsync_agentic_test")
    print("=" * 60)

    # Step 1: Fix the schema
    schema_fixed = await fix_agent_decisions_schema()

    if not schema_fixed:
        print("❌ Schema fix failed - aborting")
        return False

    # Step 2: Test the fix
    test_passed = await test_schema_fix()

    if not test_passed:
        print("❌ Schema test failed - fix may be incomplete")
        return False

    print("\n🎉 SCHEMA FIX COMPLETED SUCCESSFULLY!")
    print("✅ The agent_decisions table now has the required 'result' column")
    print("✅ Existing data has been preserved")
    print("✅ DatabaseDecisionMaker should now work correctly")
    print("\n🔄 Ready to re-run the autonomous agent optimization test!")

    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Schema fix interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Schema fix failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
