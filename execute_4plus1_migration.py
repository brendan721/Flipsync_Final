#!/usr/bin/env python3
"""
Execute 4+1 Architecture Database Migration
==========================================

This script executes the database migration to add the 4+1 architecture tables:
- autonomous_agents (4 autonomous agents)
- conversational_interfaces (1 conversational interface)
- autonomous_agent_decisions (LLM-free decision tracking)

Features:
- Production-safe migration with rollback capability
- Comprehensive validation and error handling
- Performance optimization with proper indexes
- 4+1 architecture compliance enforcement
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Add the project root to the Python path
sys.path.append("/home/brend/Flipsync_Final")

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_CONFIG = {
    "host": "174.138.77.110",
    "port": 5432,
    "database": "flipsync_agentic_test",
    "user": "postgres",
    "password": "FlipSync_DB_Prod_2024_Secure_Key_9x7z",
}

DATABASE_URL = f"postgresql+asyncpg://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"


class FourPlusOneMigration:
    """Execute 4+1 architecture database migration."""

    def __init__(self):
        self.engine = None
        self.migration_start_time = None

    async def initialize(self):
        """Initialize database connection."""
        try:
            self.engine = create_async_engine(
                DATABASE_URL,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                echo=False,  # Set to True for SQL debugging
            )
            logger.info("✅ Database connection initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize database connection: {e}")
            return False

    async def validate_prerequisites(self):
        """Validate prerequisites for migration."""
        try:
            async with self.engine.begin() as conn:
                # Check if tables already exist
                result = await conn.execute(
                    text(
                        """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('autonomous_agents', 'conversational_interfaces', 'autonomous_agent_decisions')
                """
                    )
                )
                existing_tables = [row[0] for row in result.fetchall()]

                if existing_tables:
                    logger.warning(
                        f"⚠️  Some 4+1 architecture tables already exist: {existing_tables}"
                    )
                    return False

                # Check if unified_agents table exists (should exist)
                result = await conn.execute(
                    text(
                        """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'unified_agents'
                """
                    )
                )
                unified_exists = result.fetchone()

                if not unified_exists:
                    logger.error(
                        "❌ unified_agents table does not exist - prerequisite not met"
                    )
                    return False

                logger.info("✅ Prerequisites validated - ready for migration")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to validate prerequisites: {e}")
            return False

    async def execute_migration(self):
        """Execute the 4+1 architecture migration."""
        try:
            self.migration_start_time = datetime.now()
            logger.info("🚀 Starting 4+1 architecture migration...")

            async with self.engine.begin() as conn:
                # Step 1: Create autonomous_agents table
                logger.info("📊 Creating autonomous_agents table...")
                await self._create_autonomous_agents_table(conn)

                # Step 2: Create conversational_interfaces table
                logger.info("💬 Creating conversational_interfaces table...")
                await self._create_conversational_interfaces_table(conn)

                # Step 3: Create autonomous_agent_decisions table
                logger.info("🧠 Creating autonomous_agent_decisions table...")
                await self._create_autonomous_agent_decisions_table(conn)

                # Step 4: Create indexes
                logger.info("⚡ Creating performance indexes...")
                await self._create_indexes(conn)

                # Step 5: Validate migration
                logger.info("✅ Validating migration...")
                await self._validate_migration(conn)

            migration_time = datetime.now() - self.migration_start_time
            logger.info(
                f"🎉 4+1 architecture migration completed successfully in {migration_time}"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            await self._rollback_migration()
            return False

    async def _create_autonomous_agents_table(self, conn):
        """Create autonomous_agents table."""
        await conn.execute(
            text(
                """
            CREATE TABLE autonomous_agents (
                id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
                agent_id VARCHAR(255) NOT NULL UNIQUE,
                agent_type VARCHAR(50) NOT NULL,
                agent_class VARCHAR(255) NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'initializing',
                health_status VARCHAR(50) DEFAULT 'unknown',
                
                -- 4+1 Architecture Compliance Fields
                llm_free BOOLEAN NOT NULL DEFAULT true,
                uses_standard_decision_pipeline BOOLEAN NOT NULL DEFAULT true,
                architecture_type VARCHAR(50) NOT NULL DEFAULT 'autonomous',
                
                -- Performance Metrics
                total_decisions INTEGER NOT NULL DEFAULT 0,
                successful_decisions INTEGER NOT NULL DEFAULT 0,
                average_decision_time_ms FLOAT,
                last_decision_time_ms FLOAT,
                
                -- Configuration
                capabilities TEXT,
                optimization_config TEXT,
                
                -- Timestamps
                initialized_at TIMESTAMPTZ,
                last_heartbeat TIMESTAMPTZ,
                last_activity TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                
                -- Constraints
                CONSTRAINT ck_autonomous_agents_type CHECK (agent_type IN ('market', 'content', 'executive', 'logistics')),
                CONSTRAINT ck_autonomous_agents_status CHECK (status IN ('initializing', 'active', 'idle', 'processing', 'error', 'shutdown')),
                CONSTRAINT ck_autonomous_agents_llm_free CHECK (llm_free = true),
                CONSTRAINT ck_autonomous_agents_pipeline CHECK (uses_standard_decision_pipeline = true)
            )
        """
            )
        )
        logger.info("✅ autonomous_agents table created")

    async def _create_conversational_interfaces_table(self, conn):
        """Create conversational_interfaces table."""
        await conn.execute(
            text(
                """
            CREATE TABLE conversational_interfaces (
                id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
                interface_id VARCHAR(255) NOT NULL UNIQUE,
                interface_type VARCHAR(50) NOT NULL DEFAULT 'strategic_chat',
                service_class VARCHAR(255) NOT NULL,
                
                -- LLM Configuration (Gemini-exclusive)
                llm_provider VARCHAR(100) NOT NULL DEFAULT 'gemini',
                gemini_model VARCHAR(100) NOT NULL,
                
                -- Status and Metrics
                status VARCHAR(50) NOT NULL DEFAULT 'active',
                total_conversations INTEGER NOT NULL DEFAULT 0,
                total_messages INTEGER NOT NULL DEFAULT 0,
                total_cost FLOAT NOT NULL DEFAULT 0.0,
                daily_budget FLOAT NOT NULL DEFAULT 10.0,
                health_status VARCHAR(50) DEFAULT 'unknown',
                
                -- Timestamps
                initialized_at TIMESTAMPTZ,
                last_activity TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                
                -- Constraints
                CONSTRAINT ck_conversational_interfaces_type CHECK (interface_type IN ('strategic_chat')),
                CONSTRAINT ck_conversational_interfaces_gemini_only CHECK (llm_provider = 'gemini'),
                CONSTRAINT ck_conversational_interfaces_status CHECK (status IN ('active', 'inactive', 'maintenance', 'error'))
            )
        """
            )
        )
        logger.info("✅ conversational_interfaces table created")

    async def _create_autonomous_agent_decisions_table(self, conn):
        """Create autonomous_agent_decisions table."""
        await conn.execute(
            text(
                """
            CREATE TABLE autonomous_agent_decisions (
                id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
                decision_id VARCHAR(255) NOT NULL,
                agent_id VARCHAR(255) NOT NULL,
                
                -- Decision Details
                decision_type VARCHAR(255) NOT NULL,
                context TEXT,
                result TEXT,
                
                -- Performance Tracking
                execution_time_ms FLOAT NOT NULL,
                confidence FLOAT NOT NULL,
                status VARCHAR(50) NOT NULL,
                
                -- 4+1 Architecture Compliance Tracking
                used_llm BOOLEAN NOT NULL DEFAULT false,
                used_standard_pipeline BOOLEAN NOT NULL DEFAULT true,
                algorithm_used VARCHAR(255),
                
                -- Timestamps
                started_at TIMESTAMPTZ NOT NULL,
                completed_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                
                -- Foreign Key Constraints
                CONSTRAINT fk_autonomous_agent_decisions_agent_id FOREIGN KEY (agent_id) REFERENCES autonomous_agents(id),
                
                -- Constraints
                CONSTRAINT ck_autonomous_agent_decisions_status CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
                CONSTRAINT ck_autonomous_agent_decisions_no_llm CHECK (used_llm = false),
                CONSTRAINT ck_autonomous_agent_decisions_standard_pipeline CHECK (used_standard_pipeline = true),
                CONSTRAINT ck_autonomous_agent_decisions_confidence CHECK (confidence >= 0.0 AND confidence <= 1.0),
                CONSTRAINT ck_autonomous_agent_decisions_execution_time CHECK (execution_time_ms >= 0.0)
            )
        """
            )
        )
        logger.info("✅ autonomous_agent_decisions table created")

    async def _create_indexes(self, conn):
        """Create performance indexes for 4+1 architecture tables."""
        indexes = [
            # Autonomous Agents Indexes
            "CREATE INDEX idx_autonomous_agents_type ON autonomous_agents(agent_type)",
            "CREATE INDEX idx_autonomous_agents_status ON autonomous_agents(status)",
            "CREATE INDEX idx_autonomous_agents_heartbeat ON autonomous_agents(last_heartbeat)",
            "CREATE INDEX idx_autonomous_agents_activity ON autonomous_agents(last_activity)",
            "CREATE INDEX idx_autonomous_agents_compliance ON autonomous_agents(llm_free, uses_standard_decision_pipeline)",
            # Conversational Interfaces Indexes
            "CREATE INDEX idx_conversational_interfaces_type ON conversational_interfaces(interface_type)",
            "CREATE INDEX idx_conversational_interfaces_status ON conversational_interfaces(status)",
            "CREATE INDEX idx_conversational_interfaces_activity ON conversational_interfaces(last_activity)",
            # Autonomous Agent Decisions Indexes
            "CREATE INDEX idx_autonomous_decisions_agent ON autonomous_agent_decisions(agent_id)",
            "CREATE INDEX idx_autonomous_decisions_type ON autonomous_agent_decisions(decision_type)",
            "CREATE INDEX idx_autonomous_decisions_status ON autonomous_agent_decisions(status)",
            "CREATE INDEX idx_autonomous_decisions_execution_time ON autonomous_agent_decisions(execution_time_ms)",
            "CREATE INDEX idx_autonomous_decisions_started_at ON autonomous_agent_decisions(started_at)",
            "CREATE INDEX idx_autonomous_decisions_compliance ON autonomous_agent_decisions(used_llm, used_standard_pipeline)",
            # Composite Indexes for Common Query Patterns
            "CREATE INDEX idx_agent_decisions_composite ON autonomous_agent_decisions(agent_id, status, started_at)",
            "CREATE INDEX idx_autonomous_agents_type_status ON autonomous_agents(agent_type, status)",
        ]

        for index_sql in indexes:
            await conn.execute(text(index_sql))

        logger.info(f"✅ Created {len(indexes)} performance indexes")

    async def _validate_migration(self, conn):
        """Validate that migration was successful."""
        # Check that all tables were created
        result = await conn.execute(
            text(
                """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('autonomous_agents', 'conversational_interfaces', 'autonomous_agent_decisions')
            ORDER BY table_name
        """
            )
        )
        created_tables = [row[0] for row in result.fetchall()]
        expected_tables = [
            "autonomous_agent_decisions",
            "autonomous_agents",
            "conversational_interfaces",
        ]

        if set(created_tables) != set(expected_tables):
            raise Exception(
                f"Migration validation failed - Expected tables: {expected_tables}, Created: {created_tables}"
            )

        # Check that indexes were created
        result = await conn.execute(
            text(
                """
            SELECT indexname
            FROM pg_indexes
            WHERE tablename IN ('autonomous_agents', 'conversational_interfaces', 'autonomous_agent_decisions')
            AND indexname LIKE 'idx_%'
        """
            )
        )
        created_indexes = [row[0] for row in result.fetchall()]

        if len(created_indexes) < 15:  # We expect at least 15 indexes
            raise Exception(
                f"Migration validation failed - Expected at least 15 indexes, found {len(created_indexes)}"
            )

        # Check constraints
        result = await conn.execute(
            text(
                """
            SELECT conname
            FROM pg_constraint
            WHERE conrelid IN (
                SELECT oid FROM pg_class WHERE relname IN ('autonomous_agents', 'conversational_interfaces', 'autonomous_agent_decisions')
            )
            AND conname LIKE 'ck_%'
        """
            )
        )
        constraints = [row[0] for row in result.fetchall()]

        if len(constraints) < 10:  # We expect multiple check constraints
            raise Exception(
                f"Migration validation failed - Expected multiple check constraints, found {len(constraints)}"
            )

        logger.info(
            "✅ Migration validation passed - all tables, indexes, and constraints created successfully"
        )

    async def _rollback_migration(self):
        """Rollback migration in case of failure."""
        try:
            logger.warning("🔄 Rolling back migration...")
            async with self.engine.begin() as conn:
                # Drop tables in reverse order
                await conn.execute(
                    text("DROP TABLE IF EXISTS autonomous_agent_decisions CASCADE")
                )
                await conn.execute(
                    text("DROP TABLE IF EXISTS conversational_interfaces CASCADE")
                )
                await conn.execute(
                    text("DROP TABLE IF EXISTS autonomous_agents CASCADE")
                )
            logger.info("✅ Migration rollback completed")
        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")

    async def create_initial_data(self):
        """Create initial data for 4+1 architecture."""
        try:
            logger.info("📝 Creating initial 4+1 architecture data...")

            async with self.engine.begin() as conn:
                # Create 4 autonomous agents
                agents = [
                    {
                        "agent_id": "market_autonomous_agent",
                        "agent_type": "market",
                        "agent_class": "MarketAutonomousAgent",
                        "capabilities": '["pricing_optimization", "competitor_analysis", "demand_forecasting", "inventory_optimization"]',
                    },
                    {
                        "agent_id": "content_autonomous_agent",
                        "agent_type": "content",
                        "agent_class": "ContentAutonomousAgent",
                        "capabilities": '["content_generation", "seo_optimization", "marketplace_adaptation", "template_creation"]',
                    },
                    {
                        "agent_id": "executive_autonomous_agent",
                        "agent_type": "executive",
                        "agent_class": "ExecutiveAutonomousAgent",
                        "capabilities": '["strategic_planning", "resource_allocation", "risk_assessment", "performance_analysis"]',
                    },
                    {
                        "agent_id": "logistics_autonomous_agent",
                        "agent_type": "logistics",
                        "agent_class": "LogisticsAutonomousAgent",
                        "capabilities": '["route_optimization", "shipping_calculation", "warehouse_allocation", "inventory_management"]',
                    },
                ]

                for agent in agents:
                    await conn.execute(
                        text(
                            """
                        INSERT INTO autonomous_agents (agent_id, agent_type, agent_class, capabilities, status, initialized_at)
                        VALUES (:agent_id, :agent_type, :agent_class, :capabilities, 'initializing', NOW())
                    """
                        ),
                        agent,
                    )

                # Create 1 conversational interface
                await conn.execute(
                    text(
                        """
                    INSERT INTO conversational_interfaces (
                        interface_id, interface_type, service_class, llm_provider, gemini_model, status, initialized_at
                    ) VALUES (
                        'strategic_chat_service', 'strategic_chat', 'StrategicChatService', 'gemini', 'gemini-pro', 'active', NOW()
                    )
                """
                    )
                )

            logger.info("✅ Initial 4+1 architecture data created successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to create initial data: {e}")
            return False

    async def generate_migration_report(self):
        """Generate comprehensive migration report."""
        try:
            async with self.engine.begin() as conn:
                # Count records in new tables
                autonomous_agents_count = await conn.execute(
                    text("SELECT COUNT(*) FROM autonomous_agents")
                )
                autonomous_agents_count = autonomous_agents_count.scalar()

                conversational_interfaces_count = await conn.execute(
                    text("SELECT COUNT(*) FROM conversational_interfaces")
                )
                conversational_interfaces_count = (
                    conversational_interfaces_count.scalar()
                )

                decisions_count = await conn.execute(
                    text("SELECT COUNT(*) FROM autonomous_agent_decisions")
                )
                decisions_count = decisions_count.scalar()

                # Get table sizes
                result = await conn.execute(
                    text(
                        """
                    SELECT
                        schemaname,
                        tablename,
                        attname,
                        n_distinct,
                        correlation
                    FROM pg_stats
                    WHERE tablename IN ('autonomous_agents', 'conversational_interfaces', 'autonomous_agent_decisions')
                    LIMIT 5
                """
                    )
                )

                migration_time = (
                    datetime.now() - self.migration_start_time
                    if self.migration_start_time
                    else "Unknown"
                )

                report = f"""
🎉 4+1 ARCHITECTURE MIGRATION REPORT
=====================================

Migration Status: ✅ SUCCESSFUL
Migration Time: {migration_time}
Database: {DATABASE_CONFIG['database']}
Host: {DATABASE_CONFIG['host']}

📊 TABLES CREATED:
- autonomous_agents: {autonomous_agents_count} records
- conversational_interfaces: {conversational_interfaces_count} records
- autonomous_agent_decisions: {decisions_count} records

🏗️ ARCHITECTURE COMPLIANCE:
✅ 4 Autonomous Agents (Market, Content, Executive, Logistics)
✅ 1 Conversational Interface (StrategicChatService)
✅ LLM-free constraints enforced on autonomous agents
✅ Gemini-exclusive constraints enforced on conversational interface
✅ Performance indexes created for optimal query performance
✅ Foreign key relationships established
✅ Check constraints enforcing 4+1 architecture compliance

🚀 NEXT STEPS:
1. Update agent implementations to use new tables
2. Update repositories and services
3. Update API endpoints
4. Run comprehensive testing
5. Validate performance targets (<1000ms decisions)

Migration completed at: {datetime.now()}
                """

                logger.info(report)
                return report

        except Exception as e:
            logger.error(f"❌ Failed to generate migration report: {e}")
            return None

    async def cleanup(self):
        """Cleanup database connection."""
        if self.engine:
            await self.engine.dispose()
            logger.info("✅ Database connection closed")


async def main():
    """Main migration execution function."""
    migration = FourPlusOneMigration()

    try:
        # Initialize database connection
        if not await migration.initialize():
            return False

        # Validate prerequisites
        if not await migration.validate_prerequisites():
            logger.error("❌ Prerequisites not met - aborting migration")
            return False

        # Execute migration
        if not await migration.execute_migration():
            logger.error("❌ Migration failed")
            return False

        # Create initial data
        if not await migration.create_initial_data():
            logger.warning("⚠️  Migration succeeded but initial data creation failed")

        # Generate report
        await migration.generate_migration_report()

        logger.info("🎉 4+1 Architecture migration completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Migration failed with exception: {e}")
        return False
    finally:
        await migration.cleanup()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
