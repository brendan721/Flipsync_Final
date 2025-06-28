#!/usr/bin/env python3
"""
Database migration to add marketplace_connections table.
"""

import logging
import os
import sys
from datetime import datetime, timezone

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_database_url():
    """Get database URL from environment or use default."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/flipsync"
    )


async def create_marketplace_connections_table():
    """Create the marketplace_connections table."""
    
    # SQL to create the marketplace_connections table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS marketplace_connections (
        id VARCHAR(36) PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL,
        marketplace_type VARCHAR(50) NOT NULL,
        marketplace_id VARCHAR(36),
        
        -- OAuth token fields
        access_token TEXT,
        refresh_token TEXT,
        token_expires_at TIMESTAMP WITH TIME ZONE,
        
        -- Connection status
        is_connected BOOLEAN NOT NULL DEFAULT FALSE,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        last_sync_at TIMESTAMP WITH TIME ZONE,
        
        -- eBay specific fields
        ebay_user_id VARCHAR(255),
        ebay_username VARCHAR(255),
        
        -- Metadata
        connection_metadata JSONB NOT NULL DEFAULT '{}',
        error_message TEXT,
        
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        
        -- Foreign key constraint
        FOREIGN KEY (marketplace_id) REFERENCES marketplaces(id) ON DELETE SET NULL
    );
    """
    
    # SQL to create indexes
    create_indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_marketplace_connections_user_id ON marketplace_connections(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_marketplace_connections_type ON marketplace_connections(marketplace_type);",
        "CREATE INDEX IF NOT EXISTS idx_marketplace_connections_user_type ON marketplace_connections(user_id, marketplace_type);",
        "CREATE INDEX IF NOT EXISTS idx_marketplace_connections_active ON marketplace_connections(is_active);",
        "CREATE INDEX IF NOT EXISTS idx_marketplace_connections_connected ON marketplace_connections(is_connected);",
    ]
    
    try:
        # Use async engine for the migration
        database_url = get_database_url()
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        engine = create_async_engine(database_url)
        
        async with engine.begin() as conn:
            # Create the table
            logger.info("Creating marketplace_connections table...")
            await conn.execute(text(create_table_sql))
            
            # Create indexes
            logger.info("Creating indexes...")
            for index_sql in create_indexes_sql:
                await conn.execute(text(index_sql))
            
            logger.info("✅ marketplace_connections table created successfully!")
            
    except Exception as e:
        logger.error(f"❌ Failed to create marketplace_connections table: {e}")
        raise
    finally:
        await engine.dispose()


def create_marketplace_connections_table_sync():
    """Create the marketplace_connections table using sync engine."""
    
    # SQL to create the marketplace_connections table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS marketplace_connections (
        id VARCHAR(36) PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL,
        marketplace_type VARCHAR(50) NOT NULL,
        marketplace_id VARCHAR(36),
        
        -- OAuth token fields
        access_token TEXT,
        refresh_token TEXT,
        token_expires_at TIMESTAMP WITH TIME ZONE,
        
        -- Connection status
        is_connected BOOLEAN NOT NULL DEFAULT FALSE,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        last_sync_at TIMESTAMP WITH TIME ZONE,
        
        -- eBay specific fields
        ebay_user_id VARCHAR(255),
        ebay_username VARCHAR(255),
        
        -- Metadata
        connection_metadata JSONB NOT NULL DEFAULT '{}',
        error_message TEXT,
        
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        
        -- Foreign key constraint (only if marketplaces table exists)
        CONSTRAINT fk_marketplace_connections_marketplace_id 
        FOREIGN KEY (marketplace_id) REFERENCES marketplaces(id) ON DELETE SET NULL
    );
    """
    
    # SQL to create indexes
    create_indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_marketplace_connections_user_id ON marketplace_connections(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_marketplace_connections_type ON marketplace_connections(marketplace_type);",
        "CREATE INDEX IF NOT EXISTS idx_marketplace_connections_user_type ON marketplace_connections(user_id, marketplace_type);",
        "CREATE INDEX IF NOT EXISTS idx_marketplace_connections_active ON marketplace_connections(is_active);",
        "CREATE INDEX IF NOT EXISTS idx_marketplace_connections_connected ON marketplace_connections(is_connected);",
    ]
    
    try:
        # Use sync engine for the migration
        database_url = get_database_url()
        engine = create_engine(database_url)
        
        with engine.begin() as conn:
            # Check if marketplaces table exists first
            check_marketplaces_sql = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'marketplaces'
            );
            """
            
            result = conn.execute(text(check_marketplaces_sql))
            marketplaces_exists = result.scalar()
            
            if not marketplaces_exists:
                logger.warning("⚠️  marketplaces table does not exist. Creating without foreign key constraint.")
                # Remove foreign key constraint from SQL
                create_table_sql = create_table_sql.replace(
                    "-- Foreign key constraint (only if marketplaces table exists)\n        CONSTRAINT fk_marketplace_connections_marketplace_id \n        FOREIGN KEY (marketplace_id) REFERENCES marketplaces(id) ON DELETE SET NULL",
                    "-- Foreign key constraint skipped - marketplaces table does not exist"
                )
            
            # Create the table
            logger.info("Creating marketplace_connections table...")
            conn.execute(text(create_table_sql))
            
            # Create indexes
            logger.info("Creating indexes...")
            for index_sql in create_indexes_sql:
                conn.execute(text(index_sql))
            
            logger.info("✅ marketplace_connections table created successfully!")
            
    except Exception as e:
        logger.error(f"❌ Failed to create marketplace_connections table: {e}")
        raise


if __name__ == "__main__":
    import asyncio
    
    # Try async first, fall back to sync
    try:
        asyncio.run(create_marketplace_connections_table())
    except Exception as e:
        logger.warning(f"Async migration failed: {e}. Trying sync migration...")
        create_marketplace_connections_table_sync()
