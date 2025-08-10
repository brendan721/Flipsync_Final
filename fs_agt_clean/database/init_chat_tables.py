"""
Database Initialization Script for Chat and 4+1 Architecture Agent Tables
========================================================

This script initializes the database tables for chat conversations, messages,
agent status, and agent decisions.
"""

import asyncio
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from fs_agt_clean.database.models.autonomous_agent import (
    AutonomousAgent,
    AutonomousAgentDecision,
    AutonomousAgentStatus,
    AutonomousAgentType,
)
from fs_agt_clean.database.models.unified_base import Base
from fs_agt_clean.database.models.chat import (
    Conversation,
    Message,
)

logger = logging.getLogger(__name__)


async def create_chat_and_agent_tables(
    connection_string: str = "postgresql+asyncpg://postgres:FlipSync_DB_Prod_2024_Secure_Key_9x7z@174.138.77.110:5432/flipsync_agentic_test",
):
    """Create chat and agent tables in the database.

    Args:
        connection_string: Database connection string
    """
    try:
        # Create async engine
        engine = create_async_engine(
            connection_string,
            echo=True,  # Set to False in production
            pool_size=5,
            max_overflow=10,
        )

        logger.info("Creating chat and agent tables...")

        # Create all tables
        async with engine.begin() as conn:
            # Import all models to ensure they're registered
            logger.info("Importing models...")

            # Create tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Successfully created all tables")

        # Test the tables by creating a sample conversation
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            # Create a test conversation
            test_conversation = Conversation(
                user_id=uuid.UUID(
                    "550e8400-e29b-41d4-a716-446655440000"
                ),  # Sample UUID
                title="Test Conversation",
                extra_metadata={"test": True},
            )
            session.add(test_conversation)
            await session.commit()

            # Create a test message
            test_message = Message(
                conversation_id=test_conversation.id,
                content="Hello, this is a test message",
                sender="user",
                extra_metadata={"test": True},
            )
            session.add(test_message)

            # Create a test autonomous agent (using 4+1 architecture)
            test_agent = AutonomousAgent(
                agent_id="market_agent_001",
                agent_type=AutonomousAgentType.MARKET,
                agent_class="MarketAutonomousAgent",
                status=AutonomousAgentStatus.ACTIVE,
                llm_free=True,
                uses_standard_decision_pipeline=True,
                capabilities='["price_optimization", "market_analysis"]',
                optimization_config='{"max_concurrent_tasks": 10}',
            )
            session.add(test_agent)

            # Create a test agent decision (using 4+1 architecture)
            from datetime import datetime, timezone

            test_decision = AutonomousAgentDecision(
                decision_id="decision_001",
                agent_id=test_agent.id,  # Reference the created agent
                decision_type="pricing",
                context='{"product_id": "ASIN123456", "current_price": 29.99}',
                result='{"recommended_price": 27.99, "rationale": "Competitor analysis suggests lowering price by 7% to increase sales"}',
                execution_time_ms=150.5,
                confidence=0.85,
                status="completed",
                used_llm=False,  # 4+1 architecture compliance
                used_standard_pipeline=True,  # 4+1 architecture compliance
                algorithm_used="competitive_pricing_algorithm",
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
            )
            session.add(test_decision)

            await session.commit()

            logger.info("Successfully created test data")

            # Verify the data was created
            from sqlalchemy import text

            conversations = await session.execute(
                text("SELECT COUNT(*) FROM conversations")
            )
            messages = await session.execute(text("SELECT COUNT(*) FROM messages"))
            agent_statuses = await session.execute(
                text("SELECT COUNT(*) FROM agent_status")
            )
            agent_decisions = await session.execute(
                text("SELECT COUNT(*) FROM agent_decisions")
            )

            conv_count = conversations.scalar()
            msg_count = messages.scalar()
            status_count = agent_statuses.scalar()
            decision_count = agent_decisions.scalar()

            logger.info(f"Database verification:")
            logger.info(f"  Conversations: {conv_count}")
            logger.info(f"  Messages: {msg_count}")
            logger.info(f"  Autonomous Agents: {status_count}")
            logger.info(f"  Autonomous Agent Decisions: {decision_count}")

        await engine.dispose()
        logger.info("Database initialization completed successfully")

    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise


async def drop_chat_and_agent_tables(
    connection_string: str = "postgresql+asyncpg://postgres:FlipSync_DB_Prod_2024_Secure_Key_9x7z@174.138.77.110:5432/flipsync_agentic_test",
):
    """Drop chat and agent tables from the database.

    Args:
        connection_string: Database connection string
    """
    try:
        # Create async engine
        engine = create_async_engine(connection_string, echo=True)

        logger.info("Dropping chat and agent tables...")

        # Drop all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("Successfully dropped all tables")

        await engine.dispose()
        logger.info("Database cleanup completed successfully")

    except Exception as e:
        logger.error(f"Error dropping tables: {e}")
        raise


async def reset_database(
    connection_string: str = "postgresql+asyncpg://postgres:FlipSync_DB_Prod_2024_Secure_Key_9x7z@174.138.77.110:5432/flipsync_agentic_test",
):
    """Reset the database by dropping and recreating all tables.

    Args:
        connection_string: Database connection string
    """
    logger.info("Resetting database...")
    await drop_chat_and_agent_tables(connection_string)
    await create_chat_and_agent_tables(connection_string)
    logger.info("Database reset completed")


if __name__ == "__main__":
    import sys

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Get connection string from environment or use default
    import os

    connection_string = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:FlipSync_DB_Prod_2024_Secure_Key_9x7z@174.138.77.110:5432/flipsync_agentic_test",
    )

    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "create":
            asyncio.run(create_chat_and_agent_tables(connection_string))
        elif command == "drop":
            asyncio.run(drop_chat_and_agent_tables(connection_string))
        elif command == "reset":
            asyncio.run(reset_database(connection_string))
        else:
            print("Usage: python init_chat_tables.py [create|drop|reset]")
            sys.exit(1)
    else:
        # Default action is to create tables
        asyncio.run(create_chat_and_agent_tables(connection_string))
