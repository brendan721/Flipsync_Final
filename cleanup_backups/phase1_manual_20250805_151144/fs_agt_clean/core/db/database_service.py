"""
Database Service Wrapper
========================

Simplified database service wrapper for FlipSync agents.
"""

import os
from typing import Optional
from contextlib import asynccontextmanager

from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.db.database import Database

class DatabaseService:
    """Simplified database service wrapper."""
    
    _instance: Optional['DatabaseService'] = None
    
    def __init__(self):
        """Initialize database service."""
        self.config_manager = ConfigManager()
        
        # Configure from environment
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            self.config_manager.set('database.connection_string', database_url)
            self.config_manager.set('database.pool_size', 10)
            self.config_manager.set('database.max_overflow', 20)
            self.config_manager.set('database.echo', False)
        
        self.database = Database(self.config_manager)
        self._initialized = False
    
    @classmethod
    def get_instance(cls) -> 'DatabaseService':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def initialize(self):
        """Initialize database connection."""
        if not self._initialized:
            await self.database.initialize()
            self._initialized = True
    
    @asynccontextmanager
    async def get_session(self):
        """Get database session."""
        if not self._initialized:
            await self.initialize()
        
        async with self.database.get_session() as session:
            yield session

# Global instance
_db_service = None

def get_database_service() -> DatabaseService:
    """Get global database service instance."""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service
