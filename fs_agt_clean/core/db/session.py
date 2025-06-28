"""Database session management.

This module provides utility functions for database session handling,
context managers for transactions, and dependency injection helpers for FastAPI.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.models.database.base import Base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logger = logging.getLogger(__name__)


class SessionManager:
    """Session manager for handling database connections and sessions."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """Initialize the session manager.

        Args:
            config_manager: Optional configuration manager
        """
        self.config = config_manager or ConfigManager()
        self._engine = None
        self._session_factory = None
        self._initialize()

    def _initialize(self) -> None:
        """Initialize database connection."""
        db_config = self.config.get_section("database") or {}
        connection_string = db_config.get(
            "connection_string", "sqlite+aiosqlite:///fs_agt.db"
        )
        echo = db_config.get("echo", False)

        # Create engine arguments based on connection string
        engine_args = {"echo": echo}

        # Only add pool_size and max_overflow for non-SQLite connections
        if not connection_string.startswith("sqlite"):
            engine_args["pool_size"] = db_config.get("pool_size", 5)
            engine_args["max_overflow"] = db_config.get("max_overflow", 10)

        logger.info(
            f"Initializing database with connection string: {connection_string}"
        )
        self._engine = create_async_engine(connection_string, **engine_args)

        self._session_factory = async_sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )
        logger.info("Database initialized successfully")

    async def create_tables(self) -> None:
        """Create all database tables."""
        if not self._engine:
            self._initialize()

        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")

    async def get_session(self) -> AsyncSession:
        """Get a database session.

        Returns:
            AsyncSession: SQLAlchemy async session
        """
        if not self._session_factory:
            self._initialize()
        return self._session_factory()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session with automatic cleanup.

        Yields:
            AsyncSession: SQLAlchemy async session
        """
        session = await self.get_session()
        try:
            yield session
        finally:
            await session.close()

    async def close(self) -> None:
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database connections closed")


# Global session manager instance
_session_manager = None


def get_session_manager() -> SessionManager:
    """Get the global session manager instance.

    Returns:
        SessionManager: Session manager instance
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session for dependency injection.

    Yields:
        AsyncSession: SQLAlchemy async session
    """
    async with get_session_manager().session() as session:
        yield session
