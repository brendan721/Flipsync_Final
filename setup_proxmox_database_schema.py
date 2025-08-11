#!/usr/bin/env python3
"""
Proxmox Database Schema Setup for FlipSync
==========================================

This script ensures the Proxmox PostgreSQL database has the complete
schema required for FlipSync's 4+1 autonomous agent architecture.
"""

import asyncio
import os
import sys
from pathlib import Path
import asyncpg
from dotenv import load_dotenv

# Load environment
load_dotenv()

class ProxmoxSchemaSetup:
    def __init__(self):
        """Initialize schema setup for Proxmox database."""
        self.host = "localhost"
        self.port = 5432
        self.database = "flipsync_agentic_test"
        self.user = "postgres"
        self.password = "FlipSync_DB_Prod_2024_Secure_Key_9x7z"

    async def create_autonomous_agents_table(self, conn):
        """Create the autonomous_agents table."""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS autonomous_agents (
                id SERIAL PRIMARY KEY,
                agent_id VARCHAR(255) UNIQUE NOT NULL,
                agent_type VARCHAR(100) NOT NULL,
                status VARCHAR(50) DEFAULT 'active',
                capabilities TEXT[],
                configuration JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Created autonomous_agents table")

    async def create_learning_table(self, conn):
        """Create the learning_knowledge_base table."""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS learning_knowledge_base (
                id SERIAL PRIMARY KEY,
                agent_type VARCHAR(100) NOT NULL,
                learning_type VARCHAR(100) NOT NULL,
                learning_data JSONB NOT NULL,
                success_rate DECIMAL(5,4),
                confidence_score DECIMAL(5,4),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB
            )
        """)
        print("✅ Created learning_knowledge_base table")

    async def create_decisions_table(self, conn):
        """Create the autonomous_agent_decisions table."""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS autonomous_agent_decisions (
                id SERIAL PRIMARY KEY,
                decision_id VARCHAR(255) UNIQUE NOT NULL,
                agent_id VARCHAR(255) NOT NULL,
                decision_type VARCHAR(100) NOT NULL,
                context JSONB,
                decision_data JSONB NOT NULL,
                confidence_score DECIMAL(5,4),
                execution_time_ms INTEGER,
                success BOOLEAN,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB
            )
        """)
        print("✅ Created autonomous_agent_decisions table")

    async def create_auth_tables(self, conn):
        """Create authentication tables."""
        # Users table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS auth_users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT true,
                is_admin BOOLEAN DEFAULT false,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP WITH TIME ZONE,
                metadata JSONB
            )
        """)
        
        # Roles table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Permissions table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS permissions (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                resource VARCHAR(100),
                action VARCHAR(100),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        print("✅ Created authentication tables")

    async def create_indexes(self, conn):
        """Create database indexes for performance."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_agents_type ON autonomous_agents(agent_type)",
            "CREATE INDEX IF NOT EXISTS idx_agents_status ON autonomous_agents(status)",
            "CREATE INDEX IF NOT EXISTS idx_learning_agent_type ON learning_knowledge_base(agent_type)",
            "CREATE INDEX IF NOT EXISTS idx_learning_type ON learning_knowledge_base(learning_type)",
            "CREATE INDEX IF NOT EXISTS idx_decisions_agent ON autonomous_agent_decisions(agent_id)",
            "CREATE INDEX IF NOT EXISTS idx_decisions_type ON autonomous_agent_decisions(decision_type)",
            "CREATE INDEX IF NOT EXISTS idx_decisions_created ON autonomous_agent_decisions(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON auth_users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_username ON auth_users(username)",
        ]
        
        for index_sql in indexes:
            await conn.execute(index_sql)
        
        print(f"✅ Created {len(indexes)} database indexes")

    async def insert_initial_data(self, conn):
        """Insert initial data for testing."""
        # Insert 4+1 agents
        agents = [
            ('market_agent_001', 'market', 'active'),
            ('executive_agent_001', 'executive', 'active'),
            ('content_agent_001', 'content', 'active'),
            ('logistics_agent_001', 'logistics', 'active'),
            ('strategic_chat_service', 'strategic_chat', 'active'),
        ]
        
        for agent_id, agent_type, status in agents:
            await conn.execute("""
                INSERT INTO autonomous_agents (agent_id, agent_type, status, capabilities)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (agent_id) DO NOTHING
            """, agent_id, agent_type, status, [f"{agent_type}_capabilities"])
        
        print("✅ Inserted 4+1 agent architecture data")
        
        # Insert sample learning data
        learning_data = [
            ('market', 'pricing_optimization', '{"strategy": "competitive_analysis"}', 0.85),
            ('executive', 'resource_allocation', '{"method": "constraint_satisfaction"}', 0.92),
            ('content', 'seo_optimization', '{"technique": "tf_idf"}', 0.78),
            ('logistics', 'route_optimization', '{"algorithm": "graph_optimization"}', 0.88),
        ]
        
        for agent_type, learning_type, data, success_rate in learning_data:
            await conn.execute("""
                INSERT INTO learning_knowledge_base (agent_type, learning_type, learning_data, success_rate)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT DO NOTHING
            """, agent_type, learning_type, data, success_rate)
        
        print("✅ Inserted sample learning data")

    async def verify_schema(self, conn):
        """Verify the database schema is complete."""
        print("🔍 Verifying database schema...")
        
        # Check tables
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        table_names = [row['table_name'] for row in tables]
        expected_tables = [
            'autonomous_agents',
            'learning_knowledge_base', 
            'autonomous_agent_decisions',
            'auth_users',
            'roles',
            'permissions'
        ]
        
        missing_tables = [t for t in expected_tables if t not in table_names]
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        
        print(f"✅ All {len(expected_tables)} required tables present")
        
        # Check data counts
        for table in expected_tables:
            count = await conn.fetchval(f'SELECT COUNT(*) FROM {table}')
            print(f"   - {table}: {count} records")
        
        return True

    async def run_setup(self):
        """Run the complete database schema setup."""
        print("🚀 Proxmox Database Schema Setup for FlipSync")
        print("=" * 60)
        
        try:
            # Connect to database
            conn = await asyncpg.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            
            print(f"✅ Connected to {self.host}:{self.port}/{self.database}")
            
            # Create tables
            await self.create_autonomous_agents_table(conn)
            await self.create_learning_table(conn)
            await self.create_decisions_table(conn)
            await self.create_auth_tables(conn)
            
            # Create indexes
            await self.create_indexes(conn)
            
            # Insert initial data
            await self.insert_initial_data(conn)
            
            # Verify schema
            if await self.verify_schema(conn):
                print("=" * 60)
                print("🎉 Database schema setup completed successfully!")
                print("✅ All tables created")
                print("✅ Indexes optimized")
                print("✅ Initial data populated")
                print("✅ Schema verified")
                print("\n🎯 Ready for FlipSync 4+1 architecture deployment!")
                return True
            else:
                print("❌ Schema verification failed")
                return False
                
        except Exception as e:
            print(f"❌ Database setup failed: {e}")
            return False
        finally:
            if 'conn' in locals():
                await conn.close()

async def main():
    """Main setup function."""
    setup = ProxmoxSchemaSetup()
    success = await setup.run_setup()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
