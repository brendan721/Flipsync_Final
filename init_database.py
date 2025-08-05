#!/usr/bin/env python3
"""
Database Initialization for FlipSync Agents
"""
import asyncio
import os
import sys

sys.path.append('/home/brend/Flipsync_Final')

async def init_database():
    """Initialize database for agent learning."""
    # Set correct environment
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:FlipSync_DB_Prod_2024_Secure_Key_9x7z@174.138.77.110:5432/flipsync_agentic_test"
    os.environ["DB_NAME"] = "flipsync_agentic_test"
    
    from fs_agt_clean.core.db.database import Database
    from fs_agt_clean.core.config.config_manager import ConfigManager
    
    config_manager = ConfigManager()
    database = Database(config_manager)
    
    try:
        await database.initialize()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(init_database())
