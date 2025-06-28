"""
Database initialization script for metrics tables.

This script creates the necessary tables for the enhanced monitoring system.
"""

import asyncio
import logging
import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


async def create_metrics_tables():
    """Create metrics tables in the database."""
    logger = logging.getLogger(__name__)

    # Get database URL from environment
    db_url = os.getenv(
        "DATABASE_URL", "postgresql+asyncpg://admin:admin@db:5432/flipsync"
    )

    # Create engine and session
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as session:
            # Create enums first
            await session.execute(
                text(
                    """
                DO $$ BEGIN
                    CREATE TYPE metrictype AS ENUM ('GAUGE', 'COUNTER', 'HISTOGRAM', 'SUMMARY');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """
                )
            )

            await session.execute(
                text(
                    """
                DO $$ BEGIN
                    CREATE TYPE metriccategory AS ENUM ('SYSTEM', 'PERFORMANCE', 'BUSINESS', 'SECURITY', 'AGENT', 'CONVERSATION', 'DECISION', 'MOBILE', 'API');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """
                )
            )

            await session.execute(
                text(
                    """
                DO $$ BEGIN
                    CREATE TYPE alertlevel AS ENUM ('INFO', 'WARNING', 'ERROR', 'CRITICAL');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """
                )
            )

            await session.execute(
                text(
                    """
                DO $$ BEGIN
                    CREATE TYPE alertcategory AS ENUM ('SYSTEM', 'PERFORMANCE', 'SECURITY', 'BUSINESS', 'AGENT', 'CONVERSATION', 'DECISION', 'MOBILE', 'API');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """
                )
            )

            await session.execute(
                text(
                    """
                DO $$ BEGIN
                    CREATE TYPE alertsource AS ENUM ('SYSTEM', 'USER', 'AGENT', 'MONITORING', 'SECURITY');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """
                )
            )

            # Create metric_data_points table
            await session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS metric_data_points (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(255) NOT NULL,
                    value FLOAT NOT NULL,
                    type metrictype NOT NULL DEFAULT 'GAUGE',
                    category metriccategory NOT NULL DEFAULT 'SYSTEM',
                    labels JSONB,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    agent_id VARCHAR(255),
                    service_name VARCHAR(255)
                );
            """
                )
            )

            # Create indexes for metric_data_points
            await session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_metric_name ON metric_data_points(name);
                CREATE INDEX IF NOT EXISTS idx_metric_timestamp ON metric_data_points(timestamp);
                CREATE INDEX IF NOT EXISTS idx_metric_agent_id ON metric_data_points(agent_id);
                CREATE INDEX IF NOT EXISTS idx_metric_service_name ON metric_data_points(service_name);
                CREATE INDEX IF NOT EXISTS idx_metric_name_timestamp ON metric_data_points(name, timestamp);
                CREATE INDEX IF NOT EXISTS idx_metric_category_timestamp ON metric_data_points(category, timestamp);
                CREATE INDEX IF NOT EXISTS idx_metric_agent_timestamp ON metric_data_points(agent_id, timestamp);
                CREATE INDEX IF NOT EXISTS idx_metric_service_timestamp ON metric_data_points(service_name, timestamp);
            """
                )
            )

            # Create system_metrics table
            await session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    cpu_usage_percent FLOAT,
                    memory_total_bytes BIGINT,
                    memory_used_bytes BIGINT,
                    memory_usage_percent FLOAT,
                    disk_total_bytes BIGINT,
                    disk_used_bytes BIGINT,
                    disk_usage_percent FLOAT,
                    network_bytes_sent BIGINT,
                    network_bytes_received BIGINT,
                    process_cpu_percent FLOAT,
                    process_memory_percent FLOAT,
                    process_memory_rss BIGINT,
                    process_memory_vms BIGINT,
                    process_num_threads INTEGER,
                    process_num_fds INTEGER,
                    hostname VARCHAR(255),
                    service_name VARCHAR(255)
                );
            """
                )
            )

            # Create indexes for system_metrics
            await session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp);
                CREATE INDEX IF NOT EXISTS idx_system_metrics_service_name ON system_metrics(service_name);
            """
                )
            )

            # Create agent_metrics table
            await session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS agent_metrics (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    agent_id VARCHAR(255) NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    status VARCHAR(50) NOT NULL,
                    uptime_seconds FLOAT,
                    error_count INTEGER NOT NULL DEFAULT 0,
                    last_error_time TIMESTAMPTZ,
                    last_success_time TIMESTAMPTZ,
                    requests_total INTEGER DEFAULT 0,
                    requests_success INTEGER DEFAULT 0,
                    requests_failed INTEGER DEFAULT 0,
                    avg_response_time_ms FLOAT,
                    peak_response_time_ms FLOAT,
                    cpu_usage_percent FLOAT,
                    memory_usage_percent FLOAT,
                    agent_metadata JSONB
                );
            """
                )
            )

            # Create indexes for agent_metrics
            await session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_agent_metrics_agent_id ON agent_metrics(agent_id);
                CREATE INDEX IF NOT EXISTS idx_agent_metrics_timestamp ON agent_metrics(timestamp);
                CREATE INDEX IF NOT EXISTS idx_agent_metrics_status ON agent_metrics(status);
                CREATE INDEX IF NOT EXISTS idx_agent_metrics_agent_timestamp ON agent_metrics(agent_id, timestamp);
                CREATE INDEX IF NOT EXISTS idx_agent_metrics_status_timestamp ON agent_metrics(status, timestamp);
            """
                )
            )

            # Create alert_records table
            await session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS alert_records (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    alert_id VARCHAR(255) NOT NULL UNIQUE,
                    title VARCHAR(500) NOT NULL,
                    message TEXT NOT NULL,
                    level alertlevel NOT NULL,
                    category alertcategory NOT NULL,
                    source alertsource NOT NULL,
                    details JSONB,
                    labels JSONB,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    acknowledged BOOLEAN NOT NULL DEFAULT FALSE,
                    acknowledged_time TIMESTAMPTZ,
                    acknowledged_by VARCHAR(255),
                    correlation_id VARCHAR(255),
                    fingerprint VARCHAR(255),
                    resolved BOOLEAN NOT NULL DEFAULT FALSE,
                    resolved_time TIMESTAMPTZ,
                    resolved_by VARCHAR(255),
                    resolution_notes TEXT
                );
            """
                )
            )

            # Create indexes for alert_records
            await session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_alert_records_alert_id ON alert_records(alert_id);
                CREATE INDEX IF NOT EXISTS idx_alert_records_level ON alert_records(level);
                CREATE INDEX IF NOT EXISTS idx_alert_records_category ON alert_records(category);
                CREATE INDEX IF NOT EXISTS idx_alert_records_source ON alert_records(source);
                CREATE INDEX IF NOT EXISTS idx_alert_records_timestamp ON alert_records(timestamp);
                CREATE INDEX IF NOT EXISTS idx_alert_records_acknowledged ON alert_records(acknowledged);
                CREATE INDEX IF NOT EXISTS idx_alert_records_resolved ON alert_records(resolved);
                CREATE INDEX IF NOT EXISTS idx_alert_records_correlation_id ON alert_records(correlation_id);
                CREATE INDEX IF NOT EXISTS idx_alert_records_fingerprint ON alert_records(fingerprint);
                CREATE INDEX IF NOT EXISTS idx_alert_level_timestamp ON alert_records(level, timestamp);
                CREATE INDEX IF NOT EXISTS idx_alert_category_timestamp ON alert_records(category, timestamp);
                CREATE INDEX IF NOT EXISTS idx_alert_source_timestamp ON alert_records(source, timestamp);
                CREATE INDEX IF NOT EXISTS idx_alert_acknowledged_timestamp ON alert_records(acknowledged, timestamp);
                CREATE INDEX IF NOT EXISTS idx_alert_resolved_timestamp ON alert_records(resolved, timestamp);
            """
                )
            )

            # Create metric_thresholds table
            await session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS metric_thresholds (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    metric_name VARCHAR(255) NOT NULL UNIQUE,
                    warning_threshold FLOAT,
                    critical_threshold FLOAT,
                    enabled BOOLEAN NOT NULL DEFAULT TRUE,
                    comparison_operator VARCHAR(10) NOT NULL DEFAULT '>=',
                    description TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    created_by VARCHAR(255),
                    updated_by VARCHAR(255)
                );
            """
                )
            )

            # Create indexes for metric_thresholds
            await session.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_metric_thresholds_metric_name ON metric_thresholds(metric_name);
                CREATE INDEX IF NOT EXISTS idx_metric_thresholds_enabled ON metric_thresholds(enabled);
            """
                )
            )

            await session.commit()
            logger.info("Successfully created all metrics tables and indexes")

    except Exception as e:
        logger.error(f"Error creating metrics tables: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_metrics_tables())
