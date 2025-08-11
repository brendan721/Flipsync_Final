#!/usr/bin/env python3
"""
Fix Database Configuration Issues
=================================

This script fixes database connectivity issues by:
1. Setting the correct DATABASE_URL environment variable
2. Ensuring proper fallback mechanisms
3. Testing database connectivity
4. Creating the database if it doesn't exist
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
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Database configuration options for FlipSync Proxmox deployment (try in order)
DB_CONFIG_OPTIONS = [
    {
        "name": "Proxmox Production",
        "host": "localhost",
        "port": 5432,
        "database": "flipsync_agentic_test",
        "user": "postgres",
        "password": "FlipSync_DB_Prod_2024_Secure_Key_9x7z",
    },
    {
        "name": "Local Development",
        "host": "localhost",
        "port": 5432,
        "database": "flipsync_agentic_test",
        "user": "postgres",
        "password": "FlipSync_DB_Prod_2024_Secure_Key_9x7z",
    },
    {
        "name": "Local Default",
        "host": "localhost",
        "port": 5432,
        "database": "flipsync_agentic_test",
        "user": "postgres",
        "password": "postgres",
    },
]


def get_database_url(config):
    """Get database URL from config."""
    return (
        f"postgresql+asyncpg://{config['user']}:{config['password']}"
        f"@{config['host']}:{config['port']}/{config['database']}"
    )


async def test_database_connection(connection_string: str) -> bool:
    """Test database connection with the given connection string."""
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text

        engine = create_async_engine(connection_string, echo=False)

        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT current_database(), version()"))
            row = result.fetchone()

            if row:
                db_name = row[0]
                db_version = row[1]
                logger.info(f"✅ Connected to database: {db_name}")
                logger.info(f"Database version: {db_version}")

                # Verify we're connected to the correct database
                if db_name == CORRECT_DB_CONFIG["database"]:
                    logger.info("✅ Connected to correct database")
                    return True
                else:
                    logger.warning(f"⚠️ Connected to wrong database: {db_name}")
                    return False
            else:
                logger.error("❌ No response from database")
                return False

        await engine.dispose()

    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


async def create_database_if_not_exists():
    """Create the database if it doesn't exist."""
    try:
        # Connect to postgres database to create our target database
        admin_connection_string = (
            f"postgresql+asyncpg://{CORRECT_DB_CONFIG['user']}:{CORRECT_DB_CONFIG['password']}"
            f"@{CORRECT_DB_CONFIG['host']}:{CORRECT_DB_CONFIG['port']}/postgres"
        )

        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text

        engine = create_async_engine(admin_connection_string, echo=False)

        async with engine.begin() as conn:
            # Check if database exists
            result = await conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": CORRECT_DB_CONFIG["database"]},
            )

            if result.fetchone():
                logger.info(
                    f"✅ Database {CORRECT_DB_CONFIG['database']} already exists"
                )
            else:
                logger.info(f"Creating database {CORRECT_DB_CONFIG['database']}...")

                # Create database
                await conn.execute(text("COMMIT"))  # End transaction
                await conn.execute(
                    text(f"CREATE DATABASE {CORRECT_DB_CONFIG['database']}")
                )
                logger.info(
                    f"✅ Database {CORRECT_DB_CONFIG['database']} created successfully"
                )

        await engine.dispose()
        return True

    except Exception as e:
        logger.error(f"❌ Failed to create database: {e}")
        return False


async def fix_database_configuration():
    """Fix database configuration issues."""
    logger.info("🔧 Fixing FlipSync database configuration...")

    # Step 1: Set correct environment variable
    logger.info("Step 1: Setting correct DATABASE_URL environment variable")
    os.environ["DATABASE_URL"] = CORRECT_DATABASE_URL
    os.environ["DB_NAME"] = CORRECT_DB_CONFIG["database"]
    os.environ["DB_HOST"] = CORRECT_DB_CONFIG["host"]
    os.environ["DB_PORT"] = str(CORRECT_DB_CONFIG["port"])
    os.environ["DB_USER"] = CORRECT_DB_CONFIG["user"]
    os.environ["DB_PASSWORD"] = CORRECT_DB_CONFIG["password"]

    logger.info(f"✅ DATABASE_URL set to: {CORRECT_DATABASE_URL}")

    # Step 2: Create database if it doesn't exist
    logger.info("Step 2: Ensuring database exists")
    if not await create_database_if_not_exists():
        logger.error("❌ Failed to create database")
        return False

    # Step 3: Test connection
    logger.info("Step 3: Testing database connection")
    if not await test_database_connection(CORRECT_DATABASE_URL):
        logger.error("❌ Database connection test failed")
        return False

    # Step 4: Test FlipSync database initialization
    logger.info("Step 4: Testing FlipSync database initialization")
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

        # Write the correct environment variables to a file for future reference
        env_file_path = project_root / ".env.database"
        with open(env_file_path, "w") as f:
            f.write("# FlipSync Database Configuration\n")
            f.write(f"DATABASE_URL={CORRECT_DATABASE_URL}\n")
            f.write(f"DB_NAME={CORRECT_DB_CONFIG['database']}\n")
            f.write(f"DB_HOST={CORRECT_DB_CONFIG['host']}\n")
            f.write(f"DB_PORT={CORRECT_DB_CONFIG['port']}\n")
            f.write(f"DB_USER={CORRECT_DB_CONFIG['user']}\n")
            f.write(f"DB_PASSWORD={CORRECT_DB_CONFIG['password']}\n")

        logger.info(f"✅ Database configuration saved to {env_file_path}")

        return 0
    else:
        logger.error("❌ Database configuration fix failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
