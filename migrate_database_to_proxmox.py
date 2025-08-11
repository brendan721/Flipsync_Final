#!/usr/bin/env python3
"""
FlipSync Database Migration to Proxmox Server
=============================================

This script migrates the FlipSync database configuration from DigitalOcean
to the Proxmox server, ensuring all connections use the correct database.
"""

import asyncio
import os
import sys
from pathlib import Path
import asyncpg
from dotenv import load_dotenv

# Load environment
load_dotenv()

class ProxmoxDatabaseMigrator:
    def __init__(self):
        """Initialize the database migrator for Proxmox."""
        self.proxmox_host = "localhost"
        self.proxmox_port = 5432
        self.database_name = "flipsync_agentic_test"
        self.username = "postgres"
        self.password = "FlipSync_DB_Prod_2024_Secure_Key_9x7z"
        
        # Proxmox database URL
        self.proxmox_db_url = f"postgresql://{self.username}:{self.password}@{self.proxmox_host}:{self.proxmox_port}/{self.database_name}"
        
        print(f"🎯 Target Proxmox Database: {self.proxmox_host}:{self.proxmox_port}/{self.database_name}")

    async def test_proxmox_connection(self):
        """Test connection to Proxmox PostgreSQL database."""
        print("🔍 Testing Proxmox PostgreSQL connection...")
        
        try:
            conn = await asyncpg.connect(
                host=self.proxmox_host,
                port=self.proxmox_port,
                user=self.username,
                password=self.password,
                database=self.database_name
            )
            
            # Test basic query
            version = await conn.fetchval('SELECT version()')
            print(f"✅ Proxmox PostgreSQL connection successful!")
            print(f"   Version: {version[:60]}...")
            
            await conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Proxmox PostgreSQL connection failed: {e}")
            return False

    async def create_database_if_not_exists(self):
        """Create the FlipSync database if it doesn't exist."""
        print(f"🔧 Ensuring database '{self.database_name}' exists...")
        
        try:
            # Connect to postgres database to create our database
            conn = await asyncpg.connect(
                host=self.proxmox_host,
                port=self.proxmox_port,
                user=self.username,
                password=self.password,
                database="postgres"
            )
            
            # Check if database exists
            exists = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1",
                self.database_name
            )
            
            if not exists:
                await conn.execute(f'CREATE DATABASE "{self.database_name}"')
                print(f"✅ Created database '{self.database_name}'")
            else:
                print(f"✅ Database '{self.database_name}' already exists")
            
            await conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Failed to create database: {e}")
            return False

    async def verify_database_schema(self):
        """Verify that the database has the required schema."""
        print("🔍 Verifying database schema...")
        
        try:
            conn = await asyncpg.connect(
                host=self.proxmox_host,
                port=self.proxmox_port,
                user=self.username,
                password=self.password,
                database=self.database_name
            )
            
            # Check for key tables
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name IN ('autonomous_agents', 'learning_knowledge_base', 'auth_users')
            """)
            
            table_names = [row['table_name'] for row in tables]
            print(f"✅ Found {len(table_names)} key tables: {table_names}")
            
            # Count records in key tables
            if 'autonomous_agents' in table_names:
                agent_count = await conn.fetchval('SELECT COUNT(*) FROM autonomous_agents')
                print(f"   - Autonomous agents: {agent_count}")
            
            if 'learning_knowledge_base' in table_names:
                learning_count = await conn.fetchval('SELECT COUNT(*) FROM learning_knowledge_base')
                print(f"   - Learning records: {learning_count}")
            
            await conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Schema verification failed: {e}")
            return False

    def update_environment_file(self):
        """Update the .env file with Proxmox database configuration."""
        print("🔧 Updating .env file for Proxmox deployment...")
        
        env_path = Path(".env")
        proxmox_env_path = Path(".env.proxmox")
        
        # Use the Proxmox environment file as the new .env
        if proxmox_env_path.exists():
            # Backup existing .env if it exists
            if env_path.exists():
                backup_path = Path(".env.backup")
                env_path.rename(backup_path)
                print(f"✅ Backed up existing .env to {backup_path}")
            
            # Copy Proxmox configuration to .env
            proxmox_content = proxmox_env_path.read_text()
            env_path.write_text(proxmox_content)
            print("✅ Updated .env with Proxmox configuration")
            
        else:
            print("❌ .env.proxmox file not found")
            return False
        
        return True

    async def test_flipsync_connection(self):
        """Test FlipSync application connection to Proxmox database."""
        print("🧪 Testing FlipSync application database connection...")
        
        try:
            # Set environment for testing
            os.environ["DATABASE_URL"] = f"postgresql+asyncpg://{self.username}:{self.password}@{self.proxmox_host}:{self.proxmox_port}/{self.database_name}"
            
            # Import FlipSync database components
            sys.path.append('.')
            from fs_agt_clean.core.db.database import Database
            from fs_agt_clean.core.config.config_manager import ConfigManager
            
            config_manager = ConfigManager()
            database = Database(config_manager)
            
            await database.initialize()
            print("✅ FlipSync database connection successful!")
            
            # Test a simple query
            async with database.get_session() as session:
                result = await session.execute("SELECT 1 as test")
                test_value = result.scalar()
                print(f"✅ Database query test successful: {test_value}")
            
            return True
            
        except Exception as e:
            print(f"❌ FlipSync database connection failed: {e}")
            return False

    async def run_migration(self):
        """Run the complete database migration to Proxmox."""
        print("🚀 FlipSync Database Migration to Proxmox Server")
        print("=" * 60)
        
        # Step 1: Test Proxmox connection
        if not await self.test_proxmox_connection():
            print("❌ Cannot connect to Proxmox PostgreSQL. Please ensure:")
            print("   1. PostgreSQL is installed and running on Proxmox VM")
            print("   2. Database credentials are correct")
            print("   3. Network connectivity is available")
            return False
        
        # Step 2: Create database if needed
        if not await self.create_database_if_not_exists():
            return False
        
        # Step 3: Verify schema
        if not await self.verify_database_schema():
            print("⚠️  Database schema verification failed - may need to run schema creation")
        
        # Step 4: Update environment configuration
        if not self.update_environment_file():
            return False
        
        # Step 5: Test FlipSync connection
        if not await self.test_flipsync_connection():
            return False
        
        print("=" * 60)
        print("🎉 Database migration to Proxmox completed successfully!")
        print(f"✅ Database: {self.database_name}")
        print(f"✅ Host: {self.proxmox_host}:{self.proxmox_port}")
        print("✅ Environment file updated")
        print("✅ FlipSync connection verified")
        print("\n🎯 Next steps:")
        print("   1. Deploy FlipSync to Proxmox VM 201")
        print("   2. Run database schema creation if needed")
        print("   3. Test all FlipSync services")
        
        return True

async def main():
    """Main migration function."""
    migrator = ProxmoxDatabaseMigrator()
    success = await migrator.run_migration()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
