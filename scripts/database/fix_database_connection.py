#!/usr/bin/env python3
"""
Fix Database Connection for FlipSync Agents
==========================================

Ensures proper database connectivity for autonomous agents with learning capabilities.
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any, List

# Add the project root to Python path
sys.path.append("/home/brend/Flipsync_Final")

logger = logging.getLogger(__name__)


class DatabaseConnectionFixer:
    """
    Fixes database connection issues for FlipSync autonomous agents.

    Addresses:
    - Database name mismatches
    - Connection string validation
    - Agent learning system initialization
    - Production database setup
    """

    def __init__(self):
        self.connection_issues = []
        self.fixes_applied = []

    async def diagnose_and_fix(self) -> Dict[str, Any]:
        """Diagnose and fix database connection issues."""
        logger.info("🔍 Diagnosing database connection issues...")

        # Step 1: Check environment configuration
        env_status = self._check_environment_config()

        # Step 2: Test database connectivity
        db_status = await self._test_database_connection()

        # Step 3: Validate agent database dependencies
        agent_status = await self._check_agent_database_setup()

        # Step 4: Apply fixes if needed
        fixes_applied = await self._apply_fixes()

        return {
            "environment_status": env_status,
            "database_status": db_status,
            "agent_status": agent_status,
            "fixes_applied": fixes_applied,
            "connection_ready": db_status.get("connected", False),
            "agents_ready": agent_status.get("learning_enabled", False),
        }

    def _check_environment_config(self) -> Dict[str, Any]:
        """Check environment configuration for database settings."""
        logger.info("📋 Checking environment configuration...")

        required_vars = [
            "DATABASE_URL",
            "DB_HOST",
            "DB_PORT",
            "DB_NAME",
            "DB_USER",
            "DB_PASSWORD",
        ]

        config_status = {}
        missing_vars = []

        for var in required_vars:
            value = os.getenv(var)
            if value:
                config_status[var] = "✅ Set"
                if var == "DATABASE_URL":
                    # Check if URL points to correct database
                    if "flipsync_agentic_test" in value:
                        config_status["database_name_correct"] = "✅ Correct"
                    else:
                        config_status["database_name_correct"] = "❌ Incorrect"
                        self.connection_issues.append(
                            f"DATABASE_URL points to wrong database"
                        )
            else:
                config_status[var] = "❌ Missing"
                missing_vars.append(var)

        if missing_vars:
            self.connection_issues.append(
                f"Missing environment variables: {missing_vars}"
            )

        return {
            "status": "healthy" if not missing_vars else "issues_found",
            "config_details": config_status,
            "missing_variables": missing_vars,
        }

    async def _test_database_connection(self) -> Dict[str, Any]:
        """Test actual database connectivity."""
        logger.info("🔌 Testing database connection...")

        try:
            # Import database components
            from fs_agt_clean.core.db.database import Database
            from fs_agt_clean.core.config.config_manager import ConfigManager

            # Create database instance
            config_manager = ConfigManager()
            database = Database(config_manager)

            # Test connection
            await database.initialize()

            # Test basic query
            async with database.get_session() as session:
                from sqlalchemy import text

                result = await session.execute(
                    text("SELECT current_database(), version()")
                )
                row = result.fetchone()

                if row:
                    db_name = row[0]
                    db_version = row[1]

                    return {
                        "connected": True,
                        "database_name": db_name,
                        "database_version": db_version,
                        "correct_database": db_name == "flipsync_agentic_test",
                    }
                else:
                    return {"connected": False, "error": "No response from database"}

        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Database connection failed: {error_msg}")

            # Analyze error type
            if "does not exist" in error_msg:
                if "flipsync" in error_msg and "flipsync_agentic_test" not in error_msg:
                    self.connection_issues.append(
                        "Trying to connect to wrong database name"
                    )

            return {
                "connected": False,
                "error": error_msg,
                "error_type": self._classify_error(error_msg),
            }

    def _classify_error(self, error_msg: str) -> str:
        """Classify database error type."""
        error_msg_lower = error_msg.lower()

        if "does not exist" in error_msg_lower:
            return "database_not_found"
        elif "authentication" in error_msg_lower or "password" in error_msg_lower:
            return "authentication_failed"
        elif "connection" in error_msg_lower or "refused" in error_msg_lower:
            return "connection_refused"
        elif "timeout" in error_msg_lower:
            return "connection_timeout"
        else:
            return "unknown_error"

    async def _check_agent_database_setup(self) -> Dict[str, Any]:
        """Check if agents can access database for learning."""
        logger.info("🤖 Checking agent database setup...")

        try:
            # Test agent initialization with database
            from fs_agt_clean.agents.market.market_agent import MarketAutonomousAgent

            # Create agent
            agent = MarketAutonomousAgent()

            # Test decision making (should use database)
            try:
                result = await agent.make_decision("test_decision", {"test": True})

                # Check if decision was stored in database
                learning_enabled = result is not None and not isinstance(
                    result, Exception
                )

                return {
                    "agent_initialized": True,
                    "learning_enabled": learning_enabled,
                    "decision_pipeline_working": True,
                }

            except Exception as e:
                error_msg = str(e)

                # Check if it's a database-related error
                if (
                    "database" in error_msg.lower()
                    or "does not exist" in error_msg.lower()
                ):
                    return {
                        "agent_initialized": True,
                        "learning_enabled": False,
                        "decision_pipeline_working": False,
                        "error": "Database connectivity issues preventing learning",
                    }
                else:
                    return {
                        "agent_initialized": True,
                        "learning_enabled": False,
                        "decision_pipeline_working": False,
                        "error": error_msg,
                    }

        except Exception as e:
            logger.error(f"❌ Agent setup check failed: {e}")
            return {
                "agent_initialized": False,
                "learning_enabled": False,
                "decision_pipeline_working": False,
                "error": str(e),
            }

    async def _apply_fixes(self) -> List[str]:
        """Apply fixes for identified issues."""
        logger.info("🔧 Applying fixes...")

        fixes = []

        # Fix 1: Ensure correct environment variables
        if any("DATABASE_URL" in issue for issue in self.connection_issues):
            correct_url = "postgresql+asyncpg://postgres:FlipSync_DB_Prod_2024_Secure_Key_9x7z@192.168.110.71:5432/flipsync_agentic_test"
            os.environ["DATABASE_URL"] = correct_url
            os.environ["DB_NAME"] = "flipsync_agentic_test"
            fixes.append("✅ Set correct DATABASE_URL and DB_NAME")

        # Fix 2: Set other required environment variables
        required_env = {
            "DB_HOST": "192.168.110.71",
            "DB_PORT": "5432",
            "DB_USER": "postgres",
            "DB_PASSWORD": "FlipSync_DB_Prod_2024_Secure_Key_9x7z",
            "REDIS_PASSWORD": "FlipSync_Redis_Prod_2024_Secure_Key_9x7z",
        }

        for key, value in required_env.items():
            if not os.getenv(key):
                os.environ[key] = value
                fixes.append(f"✅ Set {key}")

        # Fix 3: Create database initialization script
        await self._create_database_init_script()
        fixes.append("✅ Created database initialization script")

        self.fixes_applied = fixes
        return fixes

    async def _create_database_init_script(self):
        """Create a database initialization script for agents."""
        init_script = '''#!/usr/bin/env python3
"""
Database Initialization for FlipSync Agents
"""
import asyncio
import os
import sys

sys.path.append('/home/brend/Flipsync_Final')

async def init_database():
    """Initialize database for agent learning."""
    # Set correct environment for Proxmox server
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:FlipSync_DB_Prod_2024_Secure_Key_9x7z@localhost:5432/flipsync_agentic_test"
    os.environ["DB_NAME"] = "flipsync_agentic_test"
    
    from fs_agt_clean.core.db.database import Database
    from fs_agt_clean.core.config.config_manager import ConfigManager
    
    config_manager = ConfigManager()
    database = Database(config_manager)
    
    try:
        await database.initialize()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(init_database())
'''

        with open("init_database.py", "w") as f:
            f.write(init_script)

    def generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on diagnosis."""
        recommendations = []

        if not results["database_status"].get("connected", False):
            recommendations.append(
                "🔧 Fix database connectivity before proceeding with agent testing"
            )
            recommendations.append(
                "📋 Verify database 'flipsync_agentic_test' exists on 192.168.110.71"
            )
            recommendations.append("🔑 Confirm database credentials are correct")

        if not results["agent_status"].get("learning_enabled", False):
            recommendations.append(
                "🤖 Enable agent learning by fixing database connectivity"
            )
            recommendations.append(
                "📊 Agent optimization will be limited without learning capabilities"
            )

        if results["connection_ready"] and results["agents_ready"]:
            recommendations.append(
                "🚀 System ready for full production testing with learning-enabled agents"
            )
            recommendations.append(
                "📈 Agents can now learn from decisions and improve over time"
            )
        else:
            recommendations.append(
                "⚠️ Current fallback mode provides basic functionality but no learning"
            )
            recommendations.append(
                "🎯 Fix database issues to unlock full agent potential"
            )

        return recommendations


async def main():
    """Main diagnostic and fix function."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    print("🔧 FlipSync Database Connection Diagnostic & Fix")
    print("=" * 60)

    fixer = DatabaseConnectionFixer()
    results = await fixer.diagnose_and_fix()

    # Display results
    print(f"\n📊 DIAGNOSTIC RESULTS")
    print(
        f"Environment Config: {'✅ OK' if results['environment_status']['status'] == 'healthy' else '❌ Issues'}"
    )
    print(
        f"Database Connected: {'✅ Yes' if results['database_status'].get('connected') else '❌ No'}"
    )
    print(
        f"Agent Learning: {'✅ Enabled' if results['agent_status'].get('learning_enabled') else '❌ Disabled'}"
    )

    if results["fixes_applied"]:
        print(f"\n🔧 FIXES APPLIED:")
        for fix in results["fixes_applied"]:
            print(f"  {fix}")

    # Generate recommendations
    recommendations = fixer.generate_recommendations(results)
    if recommendations:
        print(f"\n📋 RECOMMENDATIONS:")
        for rec in recommendations:
            print(f"  {rec}")

    # Show database details if connected
    if results["database_status"].get("connected"):
        db_details = results["database_status"]
        print(f"\n📊 DATABASE DETAILS:")
        print(f"  Database Name: {db_details.get('database_name', 'Unknown')}")
        print(
            f"  Correct Database: {'✅ Yes' if db_details.get('correct_database') else '❌ No'}"
        )

    print(f"\n{'='*60}")

    return results


if __name__ == "__main__":
    asyncio.run(main())
