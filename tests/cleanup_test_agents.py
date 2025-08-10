#!/usr/bin/env python3
"""
FlipSync Agent Database Cleanup Script
=====================================
Removes test agents and ensures proper 4+1 architecture compliance.
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import List, Set

# Add the project root to Python path
sys.path.append("/home/brend/Flipsync_Final")


async def cleanup_test_agents():
    """Remove test agents from database and ensure 4+1 architecture compliance."""
    try:
        # Set environment variables for database connection
        os.environ["DATABASE_URL"] = (
            "sqlite:///flipsync_local.db"
        )
        os.environ["DB_NAME"] = "flipsync_agentic_test"
        os.environ["DB_HOST"] = "localhost"
        os.environ["DB_PORT"] = "5432"
        os.environ["DB_USER"] = "postgres"
        os.environ["DB_PASSWORD"] = "FlipSync_DB_Prod_2024_Secure_Key_9x7z"

        from fs_agt_clean.core.db.database import Database
        from fs_agt_clean.core.config.config_manager import ConfigManager
        from fs_agt_clean.database.repositories.autonomous_agent_repository import (
            AutonomousAgentRepository,
        )

        print("🧹 FlipSync Agent Database Cleanup Script")
        print("=" * 50)

        # Initialize database connection
        config = ConfigManager()
        database_url = "sqlite:///flipsync_local.db"
        database = Database(config, connection_string=database_url)

        print("📡 Connecting to database...")
        await database.initialize()

        repository = AutonomousAgentRepository()

        # Define the exact 4 production agents that should remain
        production_agents: Set[str] = {
            "market_autonomous_agent",
            "content_autonomous_agent",
            "executive_autonomous_agent",
            "logistics_autonomous_agent",
        }

        print(f"✅ Expected production agents: {len(production_agents)}")
        for agent_id in sorted(production_agents):
            print(f"   - {agent_id}")

        async with database.get_session() as session:
            # Get all agents from database
            print("\n🔍 Scanning database for agents...")
            all_agents = await repository.get_all_autonomous_agents(session)

            print(f"📊 Found {len(all_agents)} total agents in database")

            # Categorize agents
            production_found = []
            test_agents = []

            for agent in all_agents:
                if agent.agent_id in production_agents:
                    production_found.append(agent)
                else:
                    test_agents.append(agent)

            print(f"\n📈 Analysis Results:")
            print(f"   Production agents found: {len(production_found)}")
            print(f"   Test agents found: {len(test_agents)}")

            # Show production agents
            if production_found:
                print(f"\n✅ Production agents (keeping these):")
                for agent in production_found:
                    print(
                        f"   - {agent.agent_id} (type: {agent.agent_type}, status: {agent.status})"
                    )

            # Show test agents to be removed
            if test_agents:
                print(f"\n🗑️  Test agents to remove:")
                for agent in test_agents:
                    created_str = (
                        agent.created_at.strftime("%Y-%m-%d %H:%M:%S")
                        if agent.created_at
                        else "Unknown"
                    )
                    print(f"   - {agent.agent_id}")
                    print(f"     Type: {agent.agent_type}")
                    print(f"     Status: {agent.status}")
                    print(f"     Created: {created_str}")
                    print()

                # Confirm removal
                print(
                    f"⚠️  WARNING: This will permanently delete {len(test_agents)} test agents!"
                )
                confirm = (
                    input(f"Remove {len(test_agents)} test agents? (y/N): ")
                    .strip()
                    .lower()
                )

                if confirm == "y":
                    print(f"\n🗑️  Removing {len(test_agents)} test agents...")

                    removed_count = 0
                    for agent in test_agents:
                        try:
                            await session.delete(agent)
                            removed_count += 1
                            print(f"   ✅ Removed: {agent.agent_id}")
                        except Exception as e:
                            print(f"   ❌ Failed to remove {agent.agent_id}: {e}")

                    # Commit changes
                    await session.commit()
                    print(f"\n✅ Successfully removed {removed_count} test agents")

                else:
                    print("❌ Cleanup cancelled by user")
                    return False
            else:
                print("\n✅ No test agents found - database is already clean!")

            # Verify final state
            print(f"\n🔍 Verifying final database state...")
            remaining_agents = await repository.get_all_autonomous_agents(session)

            print(f"📊 Final state: {len(remaining_agents)} agents remaining")

            if len(remaining_agents) == 4:
                print("✅ Perfect! Exactly 4 autonomous agents remain")

                # Verify they are the correct production agents
                remaining_ids = {agent.agent_id for agent in remaining_agents}
                if remaining_ids == production_agents:
                    print("✅ All remaining agents are correct production agents")

                    print(f"\n📋 Final agent list:")
                    for agent in sorted(remaining_agents, key=lambda x: x.agent_id):
                        print(f"   - {agent.agent_id} ({agent.agent_type})")

                    print(f"\n🎉 Database cleanup completed successfully!")
                    print(f"   - 4+1 Architecture compliance: READY")
                    print(f"   - Production agents: {len(remaining_agents)}")
                    print(f"   - Test agents: 0")

                    return True
                else:
                    print(
                        "❌ ERROR: Remaining agents don't match expected production agents"
                    )
                    missing = production_agents - remaining_ids
                    extra = remaining_ids - production_agents
                    if missing:
                        print(f"   Missing: {missing}")
                    if extra:
                        print(f"   Extra: {extra}")
                    return False
            else:
                print(
                    f"❌ ERROR: Expected 4 agents, but {len(remaining_agents)} remain"
                )
                return False

    except Exception as e:
        print(f"❌ Database cleanup failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main execution function."""
    print(f"🚀 Starting FlipSync Agent Database Cleanup")
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    success = await cleanup_test_agents()

    if success:
        print(f"\n✅ CLEANUP SUCCESSFUL - 4+1 Architecture Ready!")
        return 0
    else:
        print(f"\n❌ CLEANUP FAILED - Manual intervention required")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
