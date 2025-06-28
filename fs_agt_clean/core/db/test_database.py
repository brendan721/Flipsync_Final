"""Test script for the database module."""

import asyncio
import logging
import sys

from fs_agt_clean.core.db.database import Database

from fs_agt_clean.core.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


async def test_database():
    """Test the database module."""
    logger.info("Testing database module...")

    # Get config manager
    config_manager = get_config_manager()

    # Set test database configuration
    config_manager.set(
        "database",
        {
            "connection_string": "sqlite+aiosqlite:///test.db",
            "pool_size": 5,
            "max_overflow": 10,
            "echo": True,
        },
    )

    # Create database instance
    db = Database(config_manager)

    # Initialize database
    try:
        await db.initialize()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

    # Test execute_query
    try:
        result = await db.execute_query("SELECT 1 as test")
        logger.info(f"Execute query result: {result}")
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return False

    # Test fetch_one
    try:
        result = await db.fetch_one("SELECT 1 as test")
        logger.info(f"Fetch one result: {result}")
    except Exception as e:
        logger.error(f"Error fetching one: {e}")
        return False

    # Test fetch_all
    try:
        result = await db.fetch_all("SELECT 1 as test UNION SELECT 2 as test")
        logger.info(f"Fetch all result: {result}")
    except Exception as e:
        logger.error(f"Error fetching all: {e}")
        return False

    # Test execute
    try:
        result = await db.execute(
            "CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY, name TEXT)"
        )
        logger.info("Created test table")

        result = await db.execute(
            "INSERT INTO test (name) VALUES (:name)", {"name": "Test"}
        )
        logger.info("Inserted test record")

        result = await db.fetch_all("SELECT * FROM test")
        logger.info(f"Test records: {result}")
    except Exception as e:
        logger.error(f"Error executing: {e}")
        return False

    # Test session
    try:
        async with db.get_session() as session:
            result = await session.execute("SELECT * FROM test")
            rows = result.fetchall()
            logger.info(f"Session query result: {rows}")
    except Exception as e:
        logger.error(f"Error using session: {e}")
        return False

    # Close database
    try:
        await db.close()
        logger.info("Database closed successfully")
    except Exception as e:
        logger.error(f"Error closing database: {e}")
        return False

    logger.info("Database tests completed successfully")
    return True


def main():
    """Main function."""
    logger.info("Starting database tests...")
    result = asyncio.run(test_database())
    if result:
        logger.info("All tests passed")
        return 0
    else:
        logger.error("Tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
