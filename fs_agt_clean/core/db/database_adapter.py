"""
Database adapter for FlipSync.

This module provides a compatibility layer to replace the in-memory database
with a real database implementation. It ensures that code that was using
the in-memory database can now use the real database without changes.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Union

from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.db.connection_manager import DatabaseConnectionManager
from fs_agt_clean.core.db.database import Database

logger = logging.getLogger(__name__)


class DatabaseAdapter:
    """
    Adapter for the real database implementation.

    This class provides the same interface as the InMemoryDatabase class
    but uses the real database implementation under the hood.
    """

    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        connection_string: Optional[str] = None,
        pool_size: int = 5,
        max_overflow: int = 10,
        echo: bool = False,
    ):
        """Initialize the database adapter.

        Args:
            config_manager: Optional configuration manager
            connection_string: Optional database connection string
            pool_size: Connection pool size
            max_overflow: Maximum number of connections to allow in addition to pool_size
            echo: Whether to echo SQL statements
        """
        self.config_manager = config_manager or ConfigManager()
        self.database = Database(
            config_manager=self.config_manager,
            connection_string=connection_string,
            pool_size=pool_size,
            max_overflow=max_overflow,
            echo=echo,
        )
        self.is_initialized = False
        logger.info("DatabaseAdapter initialized")

    async def initialize(self) -> bool:
        """Initialize the database.

        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            await self.database.initialize()
            self.is_initialized = True
            logger.info("Database initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            return False

    async def execute(self, query: str, *args, **kwargs) -> Any:
        """Execute a query.

        Args:
            query: SQL query to execute
            *args: Positional arguments for the query
            **kwargs: Keyword arguments for the query

        Returns:
            Query result
        """
        params = {}
        if args:
            for i, arg in enumerate(args):
                params[f"param_{i}"] = arg
        if kwargs:
            params.update(kwargs)

        return await self.database.execute(query, params)

    async def fetch_one(self, query: str, *args, **kwargs) -> Optional[Dict[str, Any]]:
        """Fetch a single row from a query.

        Args:
            query: SQL query to execute
            *args: Positional arguments for the query
            **kwargs: Keyword arguments for the query

        Returns:
            A single row or None if no rows are found
        """
        params = {}
        if args:
            for i, arg in enumerate(args):
                params[f"param_{i}"] = arg
        if kwargs:
            params.update(kwargs)

        return await self.database.fetch_one(query, params)

    async def fetch_all(self, query: str, *args, **kwargs) -> List[Dict[str, Any]]:
        """Fetch all rows from a query.

        Args:
            query: SQL query to execute
            *args: Positional arguments for the query
            **kwargs: Keyword arguments for the query

        Returns:
            A list of rows
        """
        params = {}
        if args:
            for i, arg in enumerate(args):
                params[f"param_{i}"] = arg
        if kwargs:
            params.update(kwargs)

        return await self.database.fetch_all(query, params)

    @property
    def is_connected(self) -> bool:
        """Check if the database is connected.

        Returns:
            True if the database is connected, False otherwise
        """
        return self.is_initialized

    async def disconnect(self) -> bool:
        """Disconnect from the database.

        Returns:
            True if disconnection was successful, False otherwise
        """
        try:
            await self.database.close()
            self.is_initialized = False
            logger.info("Database disconnected successfully")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting from database: {str(e)}")
            return False

    async def create_tables(self) -> bool:
        """Create database tables.

        Returns:
            True if table creation was successful, False otherwise
        """
        try:
            await self.database.create_tables()
            logger.info("Database tables created successfully")
            return True
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
            return False

    @asynccontextmanager
    async def get_session_context(self):
        """Get a session context.

        Yields:
            Session context
        """
        async with self.database.get_session_context() as session:
            yield SessionAdapter(session)


class SessionAdapter:
    """
    Adapter for the real database session.

    This class provides the same interface as the InMemorySessionContext class
    but uses the real database session under the hood.
    """

    def __init__(self, session):
        """Initialize the session adapter.

        Args:
            session: The database session
        """
        self.session = session
        logger.debug("SessionAdapter initialized")

    async def __aenter__(self):
        """Enter the session context."""
        logger.debug("Entering session context")
        return self

    async def __aexit__(self, exc_type, exc_val):
        """Exit the session context."""
        logger.debug("Exiting session context")
        return False

    async def execute(self, query: str, *args, **kwargs) -> None:
        """Execute a query.

        Args:
            query: SQL query to execute
            *args: Positional arguments for the query
            **kwargs: Keyword arguments for the query
        """
        from sqlalchemy import text

        params = {}
        if args:
            for i, arg in enumerate(args):
                params[f"param_{i}"] = arg
        if kwargs:
            params.update(kwargs)

        await self.session.execute(text(query), params)
        await self.session.commit()

    async def fetch_one(self, query: str, *args, **kwargs) -> Optional[Dict[str, Any]]:
        """Fetch a single row from a query.

        Args:
            query: SQL query to execute
            *args: Positional arguments for the query
            **kwargs: Keyword arguments for the query

        Returns:
            A single row or None if no rows are found
        """
        from sqlalchemy import text

        params = {}
        if args:
            for i, arg in enumerate(args):
                params[f"param_{i}"] = arg
        if kwargs:
            params.update(kwargs)

        result = await self.session.execute(text(query), params)
        row = result.fetchone()

        if not row:
            return None

        # Convert row to dict
        try:
            if hasattr(row, "_mapping"):
                return dict(row._mapping)
            return dict(row)
        except Exception:
            # If conversion fails, try to create a dict from the row's keys
            if hasattr(row, "keys") and callable(row.keys):
                return {key: row[key] for key in row.keys()}
            # Last resort: return None
            return None

    async def fetch_all(self, query: str, *args, **kwargs) -> List[Dict[str, Any]]:
        """Fetch all rows from a query.

        Args:
            query: SQL query to execute
            *args: Positional arguments for the query
            **kwargs: Keyword arguments for the query

        Returns:
            A list of rows
        """
        from sqlalchemy import text

        params = {}
        if args:
            for i, arg in enumerate(args):
                params[f"param_{i}"] = arg
        if kwargs:
            params.update(kwargs)

        result = await self.session.execute(text(query), params)
        return [dict(row._mapping) for row in result]

    def add(self, obj: Any) -> None:
        """Add an object to the session.

        Args:
            obj: Object to add
        """
        self.session.add(obj)

    def delete(self, obj: Any) -> None:
        """Delete an object from the session.

        Args:
            obj: Object to delete
        """
        self.session.delete(obj)

    async def commit(self) -> None:
        """Commit the session."""
        await self.session.commit()

    async def rollback(self) -> None:
        """Rollback the session."""
        await self.session.rollback()
