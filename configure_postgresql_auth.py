#!/usr/bin/env python3
"""
Configure PostgreSQL Authentication for FlipSync Proxmox Deployment
==================================================================

This script configures PostgreSQL with proper authentication for the 4+1
autonomous agent architecture.
"""

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

class PostgreSQLConfigurator:
    def __init__(self):
        self.postgres_user = "postgres"
        self.postgres_password = "FlipSync_DB_Prod_2024_Secure_Key_9x7z"
        self.database_name = "flipsync_agentic_test"
        self.host = "localhost"
        self.port = 5432
        
    def run_sql_command(self, sql_command, database="postgres", use_password=False):
        """Run a SQL command using psql."""
        try:
            # Try different connection methods
            if use_password:
                env = os.environ.copy()
                env['PGPASSWORD'] = self.postgres_password
                cmd = ["psql", "-h", self.host, "-U", self.postgres_user, "-d", database, "-c", sql_command]
            else:
                # Try without password first (might work with trust auth)
                cmd = ["psql", "-h", self.host, "-U", self.postgres_user, "-d", database, "-c", sql_command]
                env = os.environ.copy()
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=30
            )
            
            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)
    
    def set_postgres_password(self):
        """Set the postgres user password."""
        print("🔧 Setting postgres user password...")
        
        # Try to set password using different methods
        methods = [
            # Method 1: Direct SQL command
            f"ALTER USER postgres PASSWORD '{self.postgres_password}';",
            # Method 2: Create user if not exists
            f"CREATE USER postgres WITH PASSWORD '{self.postgres_password}' SUPERUSER CREATEDB CREATEROLE;",
        ]
        
        for i, sql_command in enumerate(methods, 1):
            print(f"   Trying method {i}...")
            success, output = self.run_sql_command(sql_command)
            
            if success:
                print(f"✅ Password set successfully using method {i}")
                return True
            else:
                print(f"   Method {i} failed: {output}")
        
        # Try using system commands
        print("   Trying system command method...")
        try:
            # Use sudo to set password
            process = subprocess.Popen(
                ["sudo", "-u", "postgres", "psql", "-c", f"ALTER USER postgres PASSWORD '{self.postgres_password}';"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(timeout=30)
            
            if process.returncode == 0:
                print("✅ Password set successfully using sudo method")
                return True
            else:
                print(f"   Sudo method failed: {stderr}")
                
        except Exception as e:
            print(f"   Sudo method error: {e}")
        
        print("❌ Failed to set postgres password")
        return False
    
    def create_database(self):
        """Create the FlipSync database."""
        print(f"🔧 Creating database '{self.database_name}'...")
        
        # Try with password first, then without
        for use_password in [True, False]:
            success, output = self.run_sql_command(
                f"CREATE DATABASE {self.database_name};",
                use_password=use_password
            )
            
            if success:
                print(f"✅ Database '{self.database_name}' created successfully")
                return True
            elif "already exists" in output.lower():
                print(f"✅ Database '{self.database_name}' already exists")
                return True
            else:
                print(f"   Attempt failed: {output}")
        
        print(f"❌ Failed to create database '{self.database_name}'")
        return False
    
    def create_database_schema(self):
        """Create the required database schema."""
        print("🔧 Creating database schema...")
        
        schema_sql = """
        CREATE TABLE IF NOT EXISTS autonomous_agents (
            id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            agent_id VARCHAR(255) UNIQUE NOT NULL,
            agent_type VARCHAR(50) NOT NULL,
            agent_class VARCHAR(255) NOT NULL,
            status VARCHAR(50) DEFAULT 'initializing',
            health_status VARCHAR(50) DEFAULT 'unknown',
            llm_free BOOLEAN DEFAULT true,
            uses_standard_decision_pipeline BOOLEAN DEFAULT true,
            last_decision_time_ms FLOAT,
            capabilities TEXT,
            optimization_config TEXT,
            initialized_at TIMESTAMP WITH TIME ZONE,
            last_heartbeat TIMESTAMP WITH TIME ZONE,
            last_activity TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE TABLE IF NOT EXISTS autonomous_agent_decisions (
            id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            decision_id VARCHAR(255) NOT NULL,
            agent_id VARCHAR(255) NOT NULL,
            decision_type VARCHAR(255) NOT NULL,
            context TEXT,
            result TEXT,
            execution_time_ms FLOAT NOT NULL,
            confidence FLOAT NOT NULL,
            status VARCHAR(50) NOT NULL,
            success BOOLEAN,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE TABLE IF NOT EXISTS learning_knowledge_base (
            id SERIAL PRIMARY KEY,
            agent_type VARCHAR(100) NOT NULL,
            learning_type VARCHAR(100) NOT NULL,
            learning_data TEXT,
            success_rate REAL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_autonomous_agents_agent_id ON autonomous_agents (agent_id);
        CREATE INDEX IF NOT EXISTS idx_decisions_agent_id ON autonomous_agent_decisions (agent_id);
        CREATE INDEX IF NOT EXISTS idx_learning_agent_type ON learning_knowledge_base (agent_type);
        """
        
        # Try with password first, then without
        for use_password in [True, False]:
            success, output = self.run_sql_command(
                schema_sql,
                database=self.database_name,
                use_password=use_password
            )
            
            if success:
                print("✅ Database schema created successfully")
                return True
            else:
                print(f"   Schema creation attempt failed: {output}")
        
        print("❌ Failed to create database schema")
        return False
    
    def test_connection(self):
        """Test the database connection with the configured credentials."""
        print("🧪 Testing database connection...")
        
        try:
            import asyncpg
            
            async def test_async_connection():
                try:
                    conn = await asyncpg.connect(
                        host=self.host,
                        port=self.port,
                        user=self.postgres_user,
                        password=self.postgres_password,
                        database=self.database_name
                    )
                    
                    # Test basic query
                    version = await conn.fetchval('SELECT version()')
                    print(f"✅ Async connection successful: {version[:50]}...")
                    
                    # Test table access
                    count = await conn.fetchval('SELECT COUNT(*) FROM autonomous_agents')
                    print(f"✅ Table access successful: {count} agents in database")
                    
                    await conn.close()
                    return True
                    
                except Exception as e:
                    print(f"❌ Async connection failed: {e}")
                    return False
            
            return asyncio.run(test_async_connection())
            
        except ImportError:
            print("⚠️  asyncpg not available, testing with psql...")
            
            # Test with psql
            success, output = self.run_sql_command(
                "SELECT COUNT(*) FROM autonomous_agents;",
                database=self.database_name,
                use_password=True
            )
            
            if success:
                print(f"✅ Connection test successful: {output.strip()}")
                return True
            else:
                print(f"❌ Connection test failed: {output}")
                return False
    
    def configure_postgresql(self):
        """Run the complete PostgreSQL configuration."""
        print("🚀 Configuring PostgreSQL for FlipSync 4+1 Architecture")
        print("=" * 70)
        
        # Step 1: Set postgres password
        if not self.set_postgres_password():
            print("⚠️  Password setting failed, but continuing...")
        
        # Step 2: Create database
        if not self.create_database():
            print("❌ Database creation failed!")
            return False
        
        # Step 3: Create schema
        if not self.create_database_schema():
            print("❌ Schema creation failed!")
            return False
        
        # Step 4: Test connection
        if not self.test_connection():
            print("❌ Connection test failed!")
            return False
        
        print("=" * 70)
        print("🎉 PostgreSQL configuration completed successfully!")
        print(f"✅ Database: {self.database_name}")
        print(f"✅ User: {self.postgres_user}")
        print(f"✅ Host: {self.host}:{self.port}")
        print(f"✅ Connection string: postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.host}:{self.port}/{self.database_name}")
        
        return True

def main():
    """Main configuration function."""
    configurator = PostgreSQLConfigurator()
    success = configurator.configure_postgresql()
    
    if success:
        print("\n🚀 Ready to test 4+1 agents!")
        print("Next steps:")
        print("1. Test agent registration")
        print("2. Test decision making")
        print("3. Start FastAPI server")
    else:
        print("\n❌ Configuration failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
