#!/usr/bin/env python3

print("XXXXX DEBUG: THIS IS THE VERY FIRST LINE OF THE SCRIPT XXXXX")
"""
Complete FlipSync Database Initialization Script
===============================================

This script creates all database tables for the FlipSync application based on the
unified model architecture. It imports all model classes and uses SQLAlchemy's
create_all() method to generate the complete database schema.

Features:
- Creates all tables from unified models
- Handles database connection and error management
- Provides comprehensive logging
- Supports both development and production environments
- Includes table verification and status reporting

Usage:
    python init_complete_database.py [--drop-existing] [--verify-only]

Environment Variables:
    DATABASE_URL: PostgreSQL connection string
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD: Individual connection parameters
"""

print("DEBUG: Script execution started - very first line after docstring")

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

# Load environment variables first
try:
    from dotenv import load_dotenv

    load_dotenv("/opt/flipsync/.env")
    print("Loaded .env file successfully")
except ImportError:
    print("Warning: python-dotenv not available, using system environment variables")

import asyncpg
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import all model classes to ensure they're registered with SQLAlchemy
try:
    print("Importing unified base models...")
    # Import unified base models
    from fs_agt_clean.database.models.unified_base import Base

    print("Base imported successfully")

    print("Importing model modules...")
    # Import all model modules to register tables
    from fs_agt_clean.database.models import (
        ai_analysis,
        asin_data,
        chat,
        inventory,
        market,
        metrics,
        notification,
        revenue,
        unified_agent,
        unified_user,
    )

    print("Model modules imported successfully")

    # Import additional models that might be in other locations
    print("Importing additional models...")
    try:
        from fs_agt_clean.database.models.create_feature_flag_model import *
        from fs_agt_clean.database.models.create_marketplace_model import *

        print("Additional models imported successfully")
    except ImportError:
        print("Additional models not found (this is OK)")

    # Import models from core if they exist
    print("Importing core models...")
    try:
        from fs_agt_clean.core.models.database import *

        print("Core models imported successfully")
    except ImportError:
        print("Core models not found (this is OK)")

except ImportError as e:
    print(f"Warning: Could not import some models: {e}")
    # Continue with available models

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/opt/flipsync/logs/database_init.log", mode="a"),
    ],
)
logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """Handles complete database initialization for FlipSync."""

    def __init__(self):
        logger.info("Initializing DatabaseInitializer...")
        logger.info("About to call _get_database_url()...")
        self.database_url = self._get_database_url()
        logger.info(f"Got database_url: {self.database_url}")
        logger.info("About to call _get_async_database_url()...")
        self.async_database_url = self._get_async_database_url()
        logger.info(f"Got async_database_url: {self.async_database_url}")
        self.engine = None
        self.async_engine = None
        logger.info("DatabaseInitializer initialization completed")

    def _get_database_url(self) -> str:
        """Get database URL from environment variables."""
        logger.info("Getting database URL from environment variables...")

        # Try DATABASE_URL first
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            logger.info(f"Using DATABASE_URL: {database_url}")
            return database_url

        # Build from individual components
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        name = os.getenv("DB_NAME", "flipsync_prod")
        user = os.getenv("DB_USER", "flipsync_app")
        password = os.getenv("DB_PASSWORD", "SecureTestPassword123!")

        logger.info(
            f"Building URL from components: host={host}, port={port}, name={name}, user={user}"
        )
        constructed_url = f"postgresql://{user}:{password}@{host}:{port}/{name}"
        logger.info(f"Constructed DATABASE_URL: {constructed_url}")
        return constructed_url

    def _get_async_database_url(self) -> str:
        """Get async database URL."""
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://")

    async def check_database_connection(self) -> bool:
        """Check if database connection is working."""
        try:
            # Parse connection details using urllib.parse
            parsed = urlparse(self.database_url)
            logger.info(
                f"Parsed URL - Host: {parsed.hostname}, Port: {parsed.port}, Database: {parsed.path[1:]}, User: {parsed.username}"
            )

            # Test connection
            conn = await asyncpg.connect(
                user=parsed.username,
                password=parsed.password,
                host=parsed.hostname,
                port=parsed.port or 5432,
                database=parsed.path[1:],  # Remove leading slash
            )
            await conn.close()
            logger.info("Database connection successful")
            return True

        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            logger.error(f"Database URL being used: {self.database_url}")
            return False

    def create_engines(self):
        """Create SQLAlchemy engines."""
        try:
            # Synchronous engine for table creation
            self.engine = create_engine(
                self.database_url,
                echo=False,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,
            )

            # Asynchronous engine for async operations
            self.async_engine = create_async_engine(
                self.async_database_url,
                echo=False,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,
            )

            logger.info("Database engines created successfully")

        except Exception as e:
            logger.error(f"Failed to create database engines: {e}")
            raise

    def get_existing_tables(self) -> List[str]:
        """Get list of existing tables in the database."""
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            logger.info(f"Found {len(tables)} existing tables: {tables}")
            return tables
        except Exception as e:
            logger.error(f"Failed to get existing tables: {e}")
            return []

    def drop_all_tables(self):
        """Drop all existing tables (use with caution)."""
        try:
            logger.warning("Dropping all existing tables...")
            Base.metadata.drop_all(bind=self.engine)
            logger.info("All tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            raise

    def create_all_tables(self):
        """Create all tables defined in the models."""
        try:
            logger.info("Creating all database tables...")

            # Get all tables that will be created
            table_names = list(Base.metadata.tables.keys())
            logger.info(f"Will create {len(table_names)} tables: {table_names}")

            # Create all tables
            Base.metadata.create_all(bind=self.engine)

            logger.info("All tables created successfully")

        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise

    def verify_tables(self) -> bool:
        """Verify that all expected tables were created."""
        try:
            inspector = inspect(self.engine)
            existing_tables = set(inspector.get_table_names())
            expected_tables = set(Base.metadata.tables.keys())

            missing_tables = expected_tables - existing_tables
            extra_tables = existing_tables - expected_tables

            if missing_tables:
                logger.error(f"Missing tables: {missing_tables}")
                return False

            if extra_tables:
                logger.info(f"Extra tables found: {extra_tables}")

            logger.info(
                f"Table verification successful. Found {len(existing_tables)} tables."
            )

            # Log table details
            for table_name in sorted(existing_tables):
                columns = inspector.get_columns(table_name)
                logger.info(f"Table '{table_name}': {len(columns)} columns")

            return True

        except Exception as e:
            logger.error(f"Table verification failed: {e}")
            return False

    async def create_initial_data(self):
        """Create initial data if needed."""
        try:
            logger.info("Creating initial data...")

            # Create async session
            async_session = sessionmaker(
                self.async_engine, class_=AsyncSession, expire_on_commit=False
            )

            async with async_session() as session:
                # Add any initial data creation logic here
                # For example, creating default admin user, default settings, etc.

                # Example: Check if admin user exists
                # admin_user = await session.execute(
                #     select(UnifiedUser).where(UnifiedUser.email == "admin@flipsync.com")
                # )
                # if not admin_user.scalar_one_or_none():
                #     # Create admin user
                #     pass

                await session.commit()
                logger.info("Initial data created successfully")

        except Exception as e:
            logger.error(f"Failed to create initial data: {e}")
            raise

    async def run_database_health_check(self):
        """Run comprehensive database health check."""
        try:
            logger.info("Running database health check...")

            # Check connection
            if not await self.check_database_connection():
                return False

            # Check table integrity
            inspector = inspect(self.engine)

            # Check for foreign key constraints
            for table_name in inspector.get_table_names():
                foreign_keys = inspector.get_foreign_keys(table_name)
                if foreign_keys:
                    logger.info(
                        f"Table '{table_name}' has {len(foreign_keys)} foreign key constraints"
                    )

            # Check for indexes
            for table_name in inspector.get_table_names():
                indexes = inspector.get_indexes(table_name)
                if indexes:
                    logger.info(f"Table '{table_name}' has {len(indexes)} indexes")

            logger.info("Database health check completed successfully")
            return True

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    def cleanup(self):
        """Clean up database connections."""
        try:
            if self.engine:
                self.engine.dispose()
            if self.async_engine:
                asyncio.create_task(self.async_engine.dispose())
            logger.info("Database connections cleaned up")
        except Exception as e:
            logger.error(f"Failed to cleanup database connections: {e}")


async def main():
    """Main function to initialize the database."""
    print("DEBUG: Main function started - very first line")

    try:
        print("DEBUG: About to import argparse")
        import argparse

        print("DEBUG: argparse imported successfully")

        print("DEBUG: About to log main function start")
        logger.info("DEBUG: Main function started")
        print("DEBUG: Logger message sent successfully")

    except Exception as e:
        print(f"DEBUG: Error in main function setup: {e}")
        import traceback

        traceback.print_exc()
        return 1

    parser = argparse.ArgumentParser(description="Initialize FlipSync Database")
    parser.add_argument(
        "--drop-existing",
        action="store_true",
        help="Drop all existing tables before creating new ones",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing tables, do not create new ones",
    )
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Run comprehensive database health check",
    )
    parser.add_argument(
        "--create-initial-data",
        action="store_true",
        help="Create initial data after table creation",
    )

    args = parser.parse_args()

    # Create logs directory if it doesn't exist
    os.makedirs("/opt/flipsync/logs", exist_ok=True)

    logger.info("Starting FlipSync database initialization...")
    logger.info(f"Arguments: {args}")

    logger.info("About to create DatabaseInitializer instance...")
    print("DEBUG: About to create DatabaseInitializer instance...")

    try:
        initializer = DatabaseInitializer()
        logger.info("DatabaseInitializer instance created successfully")
        print("DEBUG: DatabaseInitializer instance created successfully")
    except Exception as e:
        logger.error(f"Failed to create DatabaseInitializer: {e}")
        print(f"DEBUG: Failed to create DatabaseInitializer: {e}")
        import traceback

        traceback.print_exc()
        return 1

    try:
        # Check database connection
        if not await initializer.check_database_connection():
            logger.error("Cannot connect to database. Please check your configuration.")
            return 1

        # Create engines
        initializer.create_engines()

        if args.verify_only:
            # Only verify existing tables
            logger.info("Running verification only...")
            if initializer.verify_tables():
                logger.info("Database verification successful")
                return 0
            else:
                logger.error("Database verification failed")
                return 1

        if args.health_check:
            # Run health check
            if await initializer.run_database_health_check():
                logger.info("Database health check passed")
                return 0
            else:
                logger.error("Database health check failed")
                return 1

        # Get existing tables
        existing_tables = initializer.get_existing_tables()

        if args.drop_existing and existing_tables:
            # Drop existing tables if requested
            initializer.drop_all_tables()

        # Create all tables
        initializer.create_all_tables()

        # Verify tables were created
        if not initializer.verify_tables():
            logger.error("Table verification failed after creation")
            return 1

        # Create initial data if requested
        if args.create_initial_data:
            await initializer.create_initial_data()

        # Run final health check
        if await initializer.run_database_health_check():
            logger.info("Database initialization completed successfully!")
            return 0
        else:
            logger.error("Final health check failed")
            return 1

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return 1

    finally:
        initializer.cleanup()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
