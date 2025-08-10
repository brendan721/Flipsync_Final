#!/usr/bin/env python3
"""
Setup PostgreSQL for FlipSync Proxmox Deployment
===============================================

This script sets up PostgreSQL with the proper schema and configuration
for the 4+1 autonomous agent architecture.
"""

import asyncio
import os
import sys
from pathlib import Path
import asyncpg
from dotenv import load_dotenv


class PostgreSQLSetup:
    def __init__(self):
        self.host = "localhost"
        self.port = 5432
        self.user = "postgres"
        self.password = None  # Try without password first
        self.database = "flipsync_agentic_test"

    async def create_database(self):
        """Create the FlipSync database if it doesn't exist."""
        print(f"🔧 Creating database '{self.database}'...")

        try:
            # Connect to default postgres database first
            if self.password:
                conn = await asyncpg.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database="postgres",
                )
            else:
                conn = await asyncpg.connect(
                    host=self.host, port=self.port, user=self.user, database="postgres"
                )

            # Check if database exists
            result = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1", self.database
            )

            if not result:
                await conn.execute(f'CREATE DATABASE "{self.database}"')
                print(f"✅ Database '{self.database}' created successfully")
            else:
                print(f"✅ Database '{self.database}' already exists")

            await conn.close()
            return True

        except Exception as e:
            print(f"❌ Failed to create database: {e}")
            return False

    async def create_schema(self):
        """Create the proper schema for 4+1 agent architecture."""
        print("🔧 Creating database schema...")

        try:
            conn = await asyncpg.connect(
                host=self.host, port=self.port, user=self.user, database=self.database
            )

            # Create autonomous_agents table
            await conn.execute(
                """
            CREATE TABLE IF NOT EXISTS autonomous_agents (
                id SERIAL PRIMARY KEY,
                agent_id VARCHAR(255) UNIQUE NOT NULL,
                agent_type VARCHAR(100) NOT NULL,
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            )

            # Create autonomous_agent_decisions table
            await conn.execute(
                """
            CREATE TABLE IF NOT EXISTS autonomous_agent_decisions (
                id SERIAL PRIMARY KEY,
                agent_id VARCHAR(255) NOT NULL,
                decision_type VARCHAR(100) NOT NULL,
                context TEXT,
                result TEXT,
                confidence REAL,
                execution_time_ms INTEGER,
                success BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent_id) REFERENCES autonomous_agents (agent_id)
            )
            """
            )

            # Create learning_knowledge_base table
            await conn.execute(
                """
            CREATE TABLE IF NOT EXISTS learning_knowledge_base (
                id SERIAL PRIMARY KEY,
                agent_type VARCHAR(100) NOT NULL,
                learning_type VARCHAR(100) NOT NULL,
                learning_data TEXT,
                success_rate REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            )

            # Create indexes for performance
            await conn.execute(
                """
            CREATE INDEX IF NOT EXISTS idx_autonomous_agents_agent_id 
            ON autonomous_agents (agent_id)
            """
            )

            await conn.execute(
                """
            CREATE INDEX IF NOT EXISTS idx_decisions_agent_id 
            ON autonomous_agent_decisions (agent_id)
            """
            )

            await conn.execute(
                """
            CREATE INDEX IF NOT EXISTS idx_learning_agent_type 
            ON learning_knowledge_base (agent_type)
            """
            )

            await conn.close()
            print("✅ Database schema created successfully")
            return True

        except Exception as e:
            print(f"❌ Failed to create schema: {e}")
            return False

    async def populate_test_data(self):
        """Populate database with test data for 4+1 architecture."""
        print("🔧 Populating test data...")

        try:
            conn = await asyncpg.connect(
                host=self.host, port=self.port, user=self.user, database=self.database
            )

            # Insert test agents for 4+1 architecture
            test_agents = [
                ("market_agent_test", "market"),
                ("executive_agent_test", "executive"),
                ("content_agent_test", "content"),
                ("logistics_agent_test", "logistics"),
                ("conversational_agent_test", "conversational"),
            ]

            for agent_id, agent_type in test_agents:
                await conn.execute(
                    """
                INSERT INTO autonomous_agents (agent_id, agent_type) 
                VALUES ($1, $2) ON CONFLICT (agent_id) DO NOTHING
                """,
                    agent_id,
                    agent_type,
                )

            # Insert test learning data
            await conn.execute(
                """
            INSERT INTO learning_knowledge_base 
            (agent_type, learning_type, learning_data, success_rate) 
            VALUES ($1, $2, $3, $4) ON CONFLICT DO NOTHING
            """,
                "market",
                "pricing_optimization",
                '{"test": "data"}',
                0.85,
            )

            # Verify data
            agent_count = await conn.fetchval("SELECT COUNT(*) FROM autonomous_agents")
            learning_count = await conn.fetchval(
                "SELECT COUNT(*) FROM learning_knowledge_base"
            )

            await conn.close()

            print(f"✅ Test data populated:")
            print(f"   - Agents: {agent_count}")
            print(f"   - Learning records: {learning_count}")
            return True

        except Exception as e:
            print(f"❌ Failed to populate test data: {e}")
            return False

    async def test_connection(self):
        """Test the database connection and functionality."""
        print("🧪 Testing database connection...")

        try:
            conn = await asyncpg.connect(
                host=self.host, port=self.port, user=self.user, database=self.database
            )

            # Test basic query
            version = await conn.fetchval("SELECT version()")
            print(f"✅ Connected to: {version}")

            # Test agent insertion (simulating what the code will do)
            test_agent_id = "market_agent_20250810_test"
            await conn.execute(
                """
            INSERT INTO autonomous_agents (agent_id, agent_type) 
            VALUES ($1, $2) ON CONFLICT (agent_id) DO NOTHING
            """,
                test_agent_id,
                "market",
            )

            # Test decision insertion
            await conn.execute(
                """
            INSERT INTO autonomous_agent_decisions 
            (agent_id, decision_type, context, result, confidence, execution_time_ms, success) 
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
                test_agent_id,
                "pricing_optimization",
                '{"test": "context"}',
                '{"test": "result"}',
                0.95,
                150,
                True,
            )

            # Verify the test
            decision_count = await conn.fetchval(
                "SELECT COUNT(*) FROM autonomous_agent_decisions WHERE agent_id = $1",
                test_agent_id,
            )

            await conn.close()

            print(f"✅ Database functionality test passed")
            print(f"   - Test decisions created: {decision_count}")
            return True

        except Exception as e:
            print(f"❌ Database connection test failed: {e}")
            return False

    def update_env_file(self):
        """Update .env file with PostgreSQL configuration."""
        print("🔧 Updating .env file...")

        env_path = Path("/home/brend/Flipsync_Final/.env")

        # Read current .env file
        if env_path.exists():
            content = env_path.read_text()
        else:
            content = ""

        # Update DATABASE_URL
        if self.password:
            new_database_url = f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        else:
            new_database_url = f"postgresql+asyncpg://{self.user}@{self.host}:{self.port}/{self.database}"

        # Replace or add DATABASE_URL
        lines = content.split("\n")
        updated = False

        for i, line in enumerate(lines):
            if line.startswith("DATABASE_URL="):
                lines[i] = f"DATABASE_URL={new_database_url}"
                updated = True
                break

        if not updated:
            lines.append(f"DATABASE_URL={new_database_url}")

        # Write back to file
        env_path.write_text("\n".join(lines))

        print(f"✅ Updated .env file with PostgreSQL configuration")
        print(f"   DATABASE_URL={new_database_url}")

    async def run_setup(self):
        """Run the complete PostgreSQL setup."""
        print("🚀 FlipSync PostgreSQL Setup for Proxmox")
        print("=" * 60)

        # Step 1: Create database
        if not await self.create_database():
            return False

        # Step 2: Create schema
        if not await self.create_schema():
            return False

        # Step 3: Populate test data
        if not await self.populate_test_data():
            return False

        # Step 4: Test connection
        if not await self.test_connection():
            return False

        # Step 5: Update environment file
        self.update_env_file()

        print("=" * 60)
        print("🎉 PostgreSQL setup completed successfully!")
        print(f"Database: {self.database}")
        print(f"Host: {self.host}:{self.port}")
        print("Ready for 4+1 agent architecture testing")

        return True


async def main():
    """Main setup function."""
    setup = PostgreSQLSetup()
    success = await setup.run_setup()

    if not success:
        print("❌ PostgreSQL setup failed!")
        sys.exit(1)

    print("\n✅ Next steps:")
    print("1. Test 4+1 agent decision making")
    print("2. Verify WebSocket endpoints")
    print("3. Run full system integration tests")


if __name__ == "__main__":
    asyncio.run(main())
