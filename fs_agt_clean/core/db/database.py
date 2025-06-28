"""Database abstraction layer for FlipSync."""

import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.database.models.unified_base import Base

logger = logging.getLogger(__name__)

# Global database instance
_database_instance = None


class Database:
    """Database abstraction layer for FlipSync."""

    def __init__(
        self,
        config_manager: ConfigManager,
        connection_string: Optional[str] = None,
        pool_size: int = 10,  # Increased for better concurrency
        max_overflow: int = 20,  # Increased for peak loads
        echo: bool = False,
        pool_timeout: int = 30,  # Connection timeout
        pool_recycle: int = 3600,  # Recycle connections every hour
        pool_pre_ping: bool = True,  # Validate connections before use
    ):
        """Initialize database connection with optimized settings.

        Args:
            config_manager: Configuration manager instance
            connection_string: Database connection string (optional, can be loaded from config)
            pool_size: Connection pool size (increased for better concurrency)
            max_overflow: Maximum number of connections to allow in addition to pool_size
            echo: Whether to echo SQL statements
            pool_timeout: Timeout for getting connection from pool
            pool_recycle: Time in seconds to recycle connections
            pool_pre_ping: Whether to validate connections before use
        """
        self.config = config_manager
        self._engine: Optional[AsyncEngine] = None
        self._session_factory = None
        self._connection_string = connection_string
        self._pool_size = pool_size
        self._max_overflow = max_overflow
        self._echo = echo
        self._pool_timeout = pool_timeout
        self._pool_recycle = pool_recycle
        self._pool_pre_ping = pool_pre_ping
        self.logger = logging.getLogger(__name__)
        self._health_check_interval = 300  # 5 minutes
        self._last_health_check = None

    async def initialize(self) -> None:
        """Initialize database connection.

        This method creates the database engine and session factory.
        It also creates the database tables if they don't exist.

        Raises:
            ValueError: If database connection string is not provided
        """
        if not self._connection_string:
            # First, try to get from environment variable (production priority)
            import os

            self._connection_string = os.getenv("DATABASE_URL")

            # Convert postgresql:// to postgresql+asyncpg:// for async support
            if self._connection_string and self._connection_string.startswith(
                "postgresql://"
            ):
                self._connection_string = self._connection_string.replace(
                    "postgresql://", "postgresql+asyncpg://", 1
                )
                self.logger.info("Converted DATABASE_URL to use asyncpg driver")

            # If not in environment, try config file
            if not self._connection_string:
                # Use get() method instead of get_config() for compatibility
                db_config = self.config.get("database", {})
                if isinstance(db_config, dict):
                    self._connection_string = db_config.get("connection_string")
                    self._pool_size = db_config.get("pool_size", self._pool_size)
                    self._max_overflow = db_config.get(
                        "max_overflow", self._max_overflow
                    )
                    self._echo = db_config.get("echo", self._echo)
                else:
                    # If get() returns a non-dict, try get_section() method
                    if hasattr(self.config, "get_section"):
                        db_config = self.config.get_section("database") or {}
                        self._connection_string = db_config.get("connection_string")
                        self._pool_size = db_config.get("pool_size", self._pool_size)
                        self._max_overflow = db_config.get(
                            "max_overflow", self._max_overflow
                        )
                        self._echo = db_config.get("echo", self._echo)

        if not self._connection_string:
            raise ValueError("Database connection string not provided")

        # Create optimized async engine with enhanced connection pooling
        self._engine = create_async_engine(
            self._connection_string,
            pool_size=self._pool_size,
            max_overflow=self._max_overflow,
            pool_timeout=self._pool_timeout,
            pool_recycle=self._pool_recycle,
            pool_pre_ping=self._pool_pre_ping,
            echo=self._echo,
            # Additional optimizations
            connect_args=(
                {
                    "server_settings": {
                        "application_name": "flipsync_agents",
                        "jit": "off",  # Disable JIT for faster connection
                    }
                }
                if "postgresql" in self._connection_string
                else {}
            ),
        )

        self._session_factory = sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create tables if they don't exist
        # In production, you would use migrations instead
        await self.create_tables()

        self.logger.info("Database initialized successfully")

    async def create_tables(self) -> None:
        """Create database tables.

        This method creates all tables defined in the models.
        It imports the models directly to ensure they are registered with the Base metadata.
        """
        self.logger.info("Starting to create database tables...")
        # Import models directly to ensure they are registered with the Base metadata
        try:
            from fs_agt_clean.database.models.unified_agent import UnifiedAgent

            self.logger.info("Imported UnifiedAgent")
            from fs_agt_clean.database.models.unified_user import UnifiedUser

            self.logger.info("Imported auth user models")
            from fs_agt_clean.core.models.database.dashboards import DashboardModel

            self.logger.info("Imported DashboardModel")
        except Exception as e:
            self.logger.error(f"Error importing database models: {str(e)}")

        # Import new chat and agent models
        try:
            from fs_agt_clean.database.models.chat import (
                ChatSession,
                Conversation,
                Message,
                MessageReaction,
            )

            self.logger.info("Imported chat models")
            from fs_agt_clean.database.models.unified_agent import (
                UnifiedAgentCommunication,
                UnifiedAgentDecision,
                UnifiedAgentPerformanceMetric,
                UnifiedAgentTask,
            )

            self.logger.info("Imported agent models")
        except Exception as e:
            self.logger.error(f"Error importing chat and agent models: {str(e)}")

        # Import metrics models
        try:
            from fs_agt_clean.database.models.metrics import (
                UnifiedAgentMetrics,
                AlertRecord,
                MetricDataPoint,
                MetricThreshold,
                SystemMetrics,
            )

            self.logger.info("Imported metrics models")
        except Exception as e:
            self.logger.error(f"Error importing metrics models: {str(e)}")

        # Get the tables we want to create
        try:
            tables = []

            # Add core auth tables
            try:
                tables.append(UnifiedUser.__table__)
                self.logger.info("Added UnifiedUser table to creation list")
            except NameError as e:
                self.logger.warning(f"UnifiedUser model not available: {e}")

            # Add other core tables
            try:
                tables.append(UnifiedAgent.__table__)
                self.logger.info("Added UnifiedAgent table to creation list")
            except NameError as e:
                self.logger.warning(f"UnifiedAgent not available: {e}")

            try:
                tables.append(DashboardModel.__table__)
                self.logger.info("Added DashboardModel table to creation list")
            except NameError as e:
                self.logger.warning(f"DashboardModel not available: {e}")

            # Add metrics tables if they were imported successfully
            try:
                tables.extend(
                    [
                        MetricDataPoint.__table__,  # Create metrics tables
                        SystemMetrics.__table__,
                        UnifiedAgentMetrics.__table__,
                        AlertRecord.__table__,
                        MetricThreshold.__table__,
                    ]
                )
                self.logger.info("Added metrics tables to creation list")
            except NameError as e:
                self.logger.warning(f"Metrics models not available: {e}")

            # Add chat and agent tables if they were imported successfully
            try:
                tables.extend(
                    [
                        Conversation.__table__,
                        Message.__table__,
                        ChatSession.__table__,
                        MessageReaction.__table__,
                        UnifiedAgentDecision.__table__,
                        UnifiedAgentPerformanceMetric.__table__,
                        UnifiedAgentCommunication.__table__,
                        UnifiedAgentTask.__table__,
                    ]
                )
                self.logger.info("Added chat and agent tables to creation list")
            except NameError as e:
                self.logger.warning(f"Chat and agent models not available: {e}")

            if tables:
                async with self._engine.begin() as conn:
                    # Create tables one by one to handle conflicts
                    for table in tables:
                        try:
                            await conn.run_sync(
                                lambda engine: Base.metadata.create_all(
                                    engine, tables=[table]
                                )
                            )
                            self.logger.info(f"Created table {table.name}")
                        except Exception as e:
                            self.logger.warning(
                                f"Error creating table {table.name}: {str(e)}"
                            )
            else:
                self.logger.warning("No tables to create")
        except Exception as e:
            self.logger.error(f"Error creating tables: {str(e)}")

    @asynccontextmanager
    async def get_session(self):
        """Get a database session as an async context manager.

        This method returns a database session that can be used in an async with statement.
        The session is automatically closed when the context manager exits.

        Yields:
            AsyncSession: Database session

        Raises:
            RuntimeError: If database is not initialized
        """
        if not self._session_factory:
            raise RuntimeError("Database not initialized")

        session = self._session_factory()
        try:
            yield session
        finally:
            if hasattr(session, "close") and callable(session.close):
                try:
                    await session.close()
                except Exception as e:
                    self.logger.warning(f"Error closing session: {str(e)}")

    @asynccontextmanager
    async def get_session_context(self):
        """Get a database session as an async context manager.

        This method is an alias for get_session for backward compatibility.

        Yields:
            AsyncSession: Database session

        Raises:
            RuntimeError: If database is not initialized
        """
        if not self._session_factory:
            raise RuntimeError("Database not initialized")
        session = self._session_factory()
        try:
            yield session
        finally:
            if hasattr(session, "close") and callable(session.close):
                try:
                    await session.close()
                except Exception as e:
                    self.logger.warning(f"Error closing session: {str(e)}")

    async def execute_query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute a raw SQL query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of dictionaries representing the query results

        Raises:
            RuntimeError: If database is not initialized
        """
        if not self._engine:
            raise RuntimeError("Database not initialized")

        async with self.get_session_context() as session:
            result = await session.execute(sa.text(query), params or {})
            return [dict(row) for row in result.mappings()]

    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a SQL query.

        This method executes a SQL query and commits the transaction.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Query result

        Raises:
            RuntimeError: If database is not initialized
        """
        if not self._engine:
            raise RuntimeError("Database not initialized")

        async with self.get_session_context() as session:
            result = await session.execute(sa.text(query), params or {})
            await session.commit()
            return result

    async def fetch_one(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Fetch a single row from a SQL query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Dictionary representing the query result or None if no result

        Raises:
            RuntimeError: If database is not initialized
        """
        if not self._engine:
            raise RuntimeError("Database not initialized")

        async with self.get_session_context() as session:
            result = await session.execute(sa.text(query), params or {})
            row = result.fetchone()

            if not row:
                return None

            # Try to convert to dict safely
            try:
                # First try to use mappings() if available
                if hasattr(row, "_mapping"):
                    return dict(row._mapping)
                # Then try direct conversion
                return dict(row)
            except Exception as e:
                self.logger.warning(f"Error converting row to dict: {e}")
                # If direct conversion fails, try to create a dict from the row's keys
                try:
                    if hasattr(row, "keys") and callable(row.keys):
                        return {key: row[key] for key in row.keys()}
                    # If that fails, try to access by index if it's a sequence
                    elif hasattr(row, "__getitem__") and hasattr(row, "__len__"):
                        # Get column names from result
                        column_names = result.keys()
                        if len(column_names) == len(row):
                            return {col: row[i] for i, col in enumerate(column_names)}
                except Exception as e2:
                    self.logger.error(f"Failed to convert row to dict: {e2}")

                # Last resort: return the row as is
                return row

    async def fetch_all(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Fetch all rows from a SQL query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of dictionaries representing the query results

        Raises:
            RuntimeError: If database is not initialized
        """
        if not self._engine:
            raise RuntimeError("Database not initialized")

        async with self.get_session_context() as session:
            result = await session.execute(sa.text(query), params or {})
            return [dict(row) for row in result.mappings()]

    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check.

        Returns:
            Dict containing health status and metrics
        """
        if not self._engine:
            return {
                "status": "unhealthy",
                "error": "Database not initialized",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        try:
            start_time = time.time()

            # Test basic connectivity
            async with self._engine.begin() as conn:
                result = await conn.execute(sa.text("SELECT 1 as health_check"))
                health_result = result.fetchone()

            response_time = time.time() - start_time

            # Get pool status
            pool_status = self._get_pool_status()

            self._last_health_check = datetime.now(timezone.utc)

            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000, 2),
                "pool_status": pool_status,
                "last_check": self._last_health_check.isoformat(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def _get_pool_status(self) -> Dict[str, Any]:
        """Get connection pool status."""
        if not self._engine or not hasattr(self._engine, "pool"):
            return {"status": "unknown"}

        pool = self._engine.pool
        return {
            "size": getattr(pool, "size", lambda: 0)(),
            "checked_in": getattr(pool, "checkedin", lambda: 0)(),
            "checked_out": getattr(pool, "checkedout", lambda: 0)(),
            "overflow": getattr(pool, "overflow", lambda: 0)(),
            "invalid": getattr(pool, "invalid", lambda: 0)(),
        }

    async def get_connection_metrics(self) -> Dict[str, Any]:
        """Get detailed connection metrics."""
        try:
            pool_status = self._get_pool_status()

            # Calculate utilization
            total_connections = pool_status.get("checked_in", 0) + pool_status.get(
                "checked_out", 0
            )
            max_connections = self._pool_size + self._max_overflow
            utilization = (
                (total_connections / max_connections * 100)
                if max_connections > 0
                else 0
            )

            return {
                "pool_utilization_percent": round(utilization, 2),
                "active_connections": pool_status.get("checked_out", 0),
                "idle_connections": pool_status.get("checked_in", 0),
                "total_connections": total_connections,
                "max_connections": max_connections,
                "overflow_connections": pool_status.get("overflow", 0),
                "invalid_connections": pool_status.get("invalid", 0),
                "pool_size": self._pool_size,
                "max_overflow": self._max_overflow,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Error getting connection metrics: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    async def close(self) -> None:
        """Close database connection.

        This method disposes the database engine, closing all connections.
        """
        if self._engine:
            await self._engine.dispose()
            self.logger.info("Database connection closed")


def get_database() -> Database:
    """Get the global database instance.

    Returns:
        Database: Global database instance
    """
    global _database_instance
    if _database_instance is None:
        from fs_agt_clean.core.config import get_settings

        _database_instance = Database(get_settings())
        # Note: Database initialization must be called separately in async context
        # This function only creates the instance, initialization happens in lifespan
    return _database_instance


async def get_db():
    """Get a database session for dependency injection.

    This function provides compatibility with FastAPI dependency injection patterns.

    Yields:
        AsyncSession: Database session
    """
    database = get_database()

    # Ensure database is initialized
    if not database._session_factory:
        await database.initialize()

    async with database.get_session() as session:
        yield session


def get_database_health() -> dict:
    """Get database health status synchronously.

    Returns:
        dict: Database health status
    """
    try:
        database = get_database()
        if not database._engine:
            return {"status": "unhealthy", "error": "Database not initialized"}
        return {"status": "healthy", "initialized": True}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def initialize_global_database() -> None:
    """Initialize the global database instance.

    This function should be called during application startup in an async context.
    """
    global _database_instance
    database = get_database()
    if database and not database._session_factory:
        await database.initialize()
        logger.info("Global database instance initialized successfully")
