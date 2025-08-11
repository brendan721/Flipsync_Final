#!/usr/bin/env python3
"""
Fix Database Configuration Issues - Version 2
==============================================

This script fixes database connectivity issues by:
1. Testing multiple database configurations
2. Setting the correct DATABASE_URL environment variable
3. Testing database connectivity with fallback
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Database configuration options for FlipSync (try in order)
DB_CONFIG_OPTIONS = [
    {
        "name": "Production Remote",
        "host": "174.138.77.110",
        "port": 5432,
        "database": "flipsync_agentic_test",
        "user": "postgres",
        "password": "FlipSync_DB_Prod_2024_Secure_Key_9x7z"
    },
    {
        "name": "Local Development",
        "host": "localhost",
        "port": 5432,
        "database": "flipsync_agentic_test",
        "user": "postgres",
        "password": "FlipSync_DB_Prod_2024_Secure_Key_9x7z"
    },
    {
        "name": "Local Default",
        "host": "localhost",
        "port": 5432,
        "database": "flipsync_agentic_test",
        "user": "postgres",
        "password": "postgres"
    }
]


def get_database_url(config):
    """Get database URL from config."""
    return (
        f"postgresql+asyncpg://{config['user']}:{config['password']}"
        f"@{config['host']}:{config['port']}/{config['database']}"
    )


async def test_database_connection(connection_string: str, timeout: int = 10) -> bool:
    """Test database connection with the given connection string."""
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        
        # Create engine with short timeout
        engine = create_async_engine(
            connection_string, 
            echo=False,
            pool_timeout=timeout,
            connect_args={"command_timeout": timeout}
        )
        
        # Test connection with timeout
        async with asyncio.timeout(timeout):
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT current_database(), version()"))
                row = result.fetchone()
                
                if row:
                    db_name = row[0]
                    logger.info(f"✅ Connected to database: {db_name}")
                    await engine.dispose()
                    return True
                else:
                    logger.error("❌ No response from database")
                    await engine.dispose()
                    return False
        
    except asyncio.TimeoutError:
        logger.warning(f"⚠️ Database connection timed out after {timeout}s")
        return False
    except Exception as e:
        logger.warning(f"⚠️ Database connection failed: {e}")
        return False


async def find_working_database_config():
    """Find a working database configuration from the options."""
    for config in DB_CONFIG_OPTIONS:
        logger.info(f"Trying {config['name']} configuration...")
        connection_string = get_database_url(config)
        
        if await test_database_connection(connection_string):
            logger.info(f"✅ Found working configuration: {config['name']}")
            return config, connection_string
        else:
            logger.warning(f"⚠️ {config['name']} configuration failed")
    
    logger.error("❌ No working database configuration found")
    return None, None


async def fix_database_configuration():
    """Fix database configuration issues."""
    logger.info("🔧 Fixing FlipSync database configuration...")
    
    # Step 1: Find working database configuration
    logger.info("Step 1: Finding working database configuration")
    working_config, working_url = await find_working_database_config()
    
    if not working_config:
        logger.error("❌ No working database configuration found")
        return False
    
    # Step 2: Set environment variables
    logger.info("Step 2: Setting environment variables")
    os.environ["DATABASE_URL"] = working_url
    os.environ["DB_NAME"] = working_config['database']
    os.environ["DB_HOST"] = working_config['host']
    os.environ["DB_PORT"] = str(working_config['port'])
    os.environ["DB_USER"] = working_config['user']
    os.environ["DB_PASSWORD"] = working_config['password']
    
    logger.info(f"✅ DATABASE_URL set to: {working_url}")
    
    # Step 3: Test FlipSync database initialization
    logger.info("Step 3: Testing FlipSync database initialization")
    try:
        from fs_agt_clean.core.db.database import Database
        from fs_agt_clean.core.config.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        database = Database(config_manager)
        
        await database.initialize()
        logger.info("✅ FlipSync database initialization successful")
        
        # Test a simple query
        async with database.get_session() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            if result.fetchone():
                logger.info("✅ Database session test successful")
            else:
                logger.error("❌ Database session test failed")
                return False
        
        await database.close()
        
    except Exception as e:
        logger.error(f"❌ FlipSync database initialization failed: {e}")
        return False
    
    logger.info("🎉 Database configuration fixed successfully!")
    return True


async def main():
    """Main function."""
    logger.info("🚀 Starting database configuration fix...")
    
    success = await fix_database_configuration()
    
    if success:
        logger.info("✅ Database configuration fix completed successfully")
        return 0
    else:
        logger.error("❌ Database configuration fix failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
