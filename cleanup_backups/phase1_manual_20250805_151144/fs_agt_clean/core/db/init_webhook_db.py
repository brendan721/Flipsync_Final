"""
Initialize webhook database tables.

This module contains functions to initialize the webhook database tables.
"""

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def init_webhook_db(session: AsyncSession) -> None:
    """Initialize webhook database tables.

    Args:
        session: Database session
    """
    try:
        # Check if webhook tables exist
        result = await session.execute(
            text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'webhooks')"
            )
        )
        webhooks_exist = result.scalar()

        if not webhooks_exist:
            logger.info("Creating webhook tables")
            # Create webhook tables
            await session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS webhooks (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    url VARCHAR(1024) NOT NULL,
                    secret VARCHAR(255),
                    status VARCHAR(50) NOT NULL DEFAULT 'active',
                    event_types VARCHAR(1024) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
                """
                )
            )

            await session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS webhook_events (
                    id SERIAL PRIMARY KEY,
                    webhook_id INTEGER NOT NULL REFERENCES webhooks(id),
                    event_type VARCHAR(50) NOT NULL,
                    payload TEXT NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'pending',
                    attempts INTEGER DEFAULT 0,
                    last_attempt_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
                """
                )
            )

            await session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS webhook_responses (
                    id SERIAL PRIMARY KEY,
                    event_id INTEGER NOT NULL REFERENCES webhook_events(id),
                    status_code INTEGER,
                    response_body TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
                """
                )
            )

            # Create webhook_stats table for monitoring
            await session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS webhook_stats (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    total_deliveries INTEGER NOT NULL,
                    successful_deliveries INTEGER NOT NULL,
                    failed_deliveries INTEGER NOT NULL,
                    retry_attempts INTEGER NOT NULL,
                    retry_successes INTEGER NOT NULL,
                    success_rate FLOAT NOT NULL,
                    retry_success_rate FLOAT NOT NULL,
                    avg_response_time_ms FLOAT NOT NULL,
                    webhook_count INTEGER NOT NULL,
                    failed_webhook_count INTEGER NOT NULL
                )
                """
                )
            )

            # Create webhook_retries table for retry mechanism
            await session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS webhook_retries (
                    id SERIAL PRIMARY KEY,
                    webhook_id INTEGER NOT NULL,
                    url VARCHAR(1024) NOT NULL,
                    payload TEXT NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'pending',
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 5,
                    last_attempt_at TIMESTAMP WITH TIME ZONE,
                    next_attempt_at TIMESTAMP WITH TIME ZONE,
                    error_message TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
                """
                )
            )

            await session.commit()
            logger.info("Webhook tables created successfully")
        else:
            logger.info("Webhook tables already exist")

    except Exception as e:
        logger.error(f"Error initializing webhook database: {str(e)}")
        raise
