#!/usr/bin/env python3
"""
Test Learning Models Import and Database Creation
===============================================

Quick test to validate that the converted learning models can be imported
and that the database initialization creates all the required tables.
"""

import asyncio
import logging
import os
import sys

# Add the project root to the Python path
sys.path.append("/home/brend/Flipsync_Final")

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Set environment variables for database connection
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://postgres:FlipSync_DB_Prod_2024_Secure_Key_9x7z@174.138.77.110:5432/flipsync_agentic_test"
)
os.environ["DB_NAME"] = "flipsync_agentic_test"


async def test_learning_models_import():
    """Test that learning models can be imported successfully."""
    try:
        logger.info("🧪 Testing learning models import...")

        from fs_agt_clean.core.learning.database.models import (
            PolicyOptimizationHistory,
            PolicyStrategyEvolution,
            LearningKnowledgeBase,
            LearningFeedbackHistory,
            LearningPerformanceMetrics,
            CrossAgentLearningInsights,
            CrossAgentCoordinationState,
            LearningConflictResolution,
        )

        logger.info("✅ All learning models imported successfully")

        # Check that models have the correct table names
        expected_tables = [
            "policy_optimization_history",
            "policy_strategy_evolution",
            "learning_knowledge_base",
            "learning_feedback_history",
            "learning_performance_metrics",
            "cross_agent_learning_insights",
            "cross_agent_coordination_state",
            "learning_conflict_resolution",
        ]

        actual_tables = [
            PolicyOptimizationHistory.__tablename__,
            PolicyStrategyEvolution.__tablename__,
            LearningKnowledgeBase.__tablename__,
            LearningFeedbackHistory.__tablename__,
            LearningPerformanceMetrics.__tablename__,
            CrossAgentLearningInsights.__tablename__,
            CrossAgentCoordinationState.__tablename__,
            LearningConflictResolution.__tablename__,
        ]

        for expected, actual in zip(expected_tables, actual_tables):
            if expected == actual:
                logger.info(f"✅ Table name correct: {actual}")
            else:
                logger.error(
                    f"❌ Table name mismatch: expected {expected}, got {actual}"
                )
                return False

        return True

    except Exception as e:
        logger.error(f"❌ Learning models import failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_database_initialization():
    """Test that database initialization creates all learning tables."""
    try:
        logger.info("🧪 Testing database initialization...")

        from fs_agt_clean.core.db.database import get_database

        # Initialize database
        database = get_database()
        await database.initialize()

        logger.info("✅ Database initialization completed")

        # Check that learning tables were created
        async with database.get_session() as session:
            # Check for learning tables
            from sqlalchemy import text

            learning_check = await session.execute(
                text(
                    """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_name IN (
                    'policy_optimization_history',
                    'policy_strategy_evolution',
                    'learning_knowledge_base',
                    'learning_feedback_history',
                    'learning_performance_metrics',
                    'cross_agent_learning_insights',
                    'cross_agent_coordination_state',
                    'learning_conflict_resolution'
                )
                ORDER BY table_name
                """
                )
            )
            learning_tables = [row[0] for row in learning_check.fetchall()]

            logger.info(f"📊 Learning tables found: {learning_tables}")

            expected_count = 8
            if len(learning_tables) == expected_count:
                logger.info(
                    f"✅ All {expected_count} learning tables created successfully"
                )
                return True
            else:
                logger.error(
                    f"❌ Expected {expected_count} learning tables, found {len(learning_tables)}"
                )
                return False

    except Exception as e:
        logger.error(f"❌ Database initialization test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    logger.info("🚀 Starting Learning Models Import and Database Test...")

    # Test 1: Learning models import
    import_success = await test_learning_models_import()

    # Test 2: Database initialization
    db_success = await test_database_initialization()

    overall_success = import_success and db_success

    if overall_success:
        print("\n🎉 LEARNING MODELS IMPORT AND DATABASE TEST PASSED!")
        print("✅ All learning models imported successfully")
        print("✅ All learning tables created in database")
        print("✅ Ready for agent integration testing")
    else:
        print("\n❌ LEARNING MODELS IMPORT AND DATABASE TEST FAILED")
        print("⚠️ Review logs for details")

    return overall_success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
