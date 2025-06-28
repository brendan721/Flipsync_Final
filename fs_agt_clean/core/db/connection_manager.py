"""
Database Connection Manager

This module provides enhanced database connection management with retry mechanisms,
connection pooling, and robust error handling.
"""

import asyncio
import logging
import random
import time
from contextlib import asynccontextmanager
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from fs_agt_clean.core.config.config_manager import ConfigManager

logger = logging.getLogger(__name__)

# Type variable for generic return type
T = TypeVar("T")


class DatabaseConnectionManager:
    """
    Enhanced database connection manager with retry mechanisms and error handling.
    """

    def __init__(
        self,
        config_manager: ConfigManager,
        connection_string: Optional[str] = None,
        pool_size: int = 5,
        max_overflow: int = 10,
        echo: bool = False,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        max_retry_delay: float = 30.0,
        jitter: bool = True,
        health_check_interval: int = 60,
    ):
        """
        Initialize the database connection manager.

        Args:
            config_manager: Configuration manager
            connection_string: Database connection string
            pool_size: Connection pool size
            max_overflow: Maximum number of connections to allow in addition to pool_size
            echo: Whether to echo SQL statements
            max_retries: Maximum number of retry attempts for operations
            retry_delay: Initial delay between retries in seconds
            max_retry_delay: Maximum delay between retries in seconds
            jitter: Whether to add random jitter to retry delays
            health_check_interval: Interval in seconds for health checks
        """
        self.config = config_manager
        self._connection_string = connection_string
        self._pool_size = pool_size
        self._max_overflow = max_overflow
        self._echo = echo
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._max_retry_delay = max_retry_delay
        self._jitter = jitter
        self._health_check_interval = health_check_interval

        self._engine: Optional[AsyncEngine] = None
        self._session_factory = None
        self._initialized = False
        self._last_health_check = 0
        self._health_status = {"status": "unknown", "last_error": None}
        self._connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "errors": 0,
            "retries": 0,
            "successful_connections": 0,
        }

    async def initialize(self) -> bool:
        """
        Initialize the database connection with retry mechanism.

        Returns:
            True if initialization was successful, False otherwise
        """
        if self._initialized:
            return True

        # Load configuration if connection string not provided
        if not self._connection_string:
            db_config = self.config.get_section("database") or {}
            self._connection_string = db_config.get("connection_string")

            # If connection string is null in config, check environment variable
            if not self._connection_string:
                import os

                self._connection_string = os.getenv("DATABASE_URL")
                if self._connection_string:
                    # Convert from standard PostgreSQL URL to asyncpg format if needed
                    if self._connection_string.startswith("postgresql://"):
                        self._connection_string = self._connection_string.replace(
                            "postgresql://", "postgresql+asyncpg://", 1
                        )
                    logger.info(
                        "Using DATABASE_URL environment variable for database connection"
                    )

            self._pool_size = db_config.get("pool_size", self._pool_size)
            self._max_overflow = db_config.get("max_overflow", self._max_overflow)
            self._echo = db_config.get("echo", self._echo)
            self._max_retries = db_config.get("max_retries", self._max_retries)
            self._retry_delay = db_config.get("retry_delay", self._retry_delay)
            self._max_retry_delay = db_config.get(
                "max_retry_delay", self._max_retry_delay
            )

        if not self._connection_string:
            logger.error("Database connection string not provided")
            self._health_status = {
                "status": "error",
                "last_error": "Connection string not provided",
            }
            return False

        # Try to initialize with retries
        for retry in range(self._max_retries + 1):
            try:
                # Create engine with enhanced configuration
                self._engine = create_async_engine(
                    self._connection_string,
                    pool_size=self._pool_size,
                    max_overflow=self._max_overflow,
                    echo=self._echo,
                    pool_pre_ping=True,  # Check connection validity before using
                    pool_recycle=3600,  # Recycle connections after 1 hour
                    pool_timeout=30,  # Wait up to 30 seconds for a connection
                    connect_args={
                        "command_timeout": 10,  # Command timeout in seconds
                        "server_settings": {
                            "application_name": "FlipSync",  # Identify app in pg_stat_activity
                        },
                    },
                )

                # Create session factory
                self._session_factory = sessionmaker(
                    self._engine, class_=AsyncSession, expire_on_commit=False
                )

                # Test connection
                async with self._session_factory() as session:
                    result = await session.execute(text("SELECT 1"))
                    row = result.fetchone()
                    if not row or row[0] != 1:
                        raise Exception("Database connection test failed")

                # Update status and stats
                self._initialized = True
                self._health_status = {"status": "healthy", "last_error": None}
                self._connection_stats["successful_connections"] += 1
                self._last_health_check = time.time()

                logger.info("Database connection initialized successfully")
                return True

            except Exception as e:
                self._connection_stats["errors"] += 1
                error_message = f"Database initialization error (attempt {retry+1}/{self._max_retries+1}): {str(e)}"

                if retry < self._max_retries:
                    # Calculate delay with exponential backoff
                    delay = min(self._retry_delay * (2**retry), self._max_retry_delay)

                    # Add jitter if enabled (±25%)
                    if self._jitter:
                        delay = delay * (0.75 + random.random() * 0.5)

                    logger.warning(
                        f"{error_message}. Retrying in {delay:.2f} seconds..."
                    )
                    self._connection_stats["retries"] += 1
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"{error_message}. All retry attempts failed.")
                    self._health_status = {"status": "error", "last_error": str(e)}
                    return False

    async def check_health(self) -> Dict[str, Any]:
        """
        Check database health.

        Returns:
            Dictionary with health status information
        """
        # Skip health check if it was performed recently
        current_time = time.time()
        if (
            current_time - self._last_health_check < self._health_check_interval
            and self._health_status["status"] != "unknown"
        ):
            return self._health_status

        if not self._initialized:
            return {"status": "not_initialized", "last_error": None}

        try:
            # Test connection
            async with self._session_factory() as session:
                start_time = time.time()
                result = await session.execute(text("SELECT 1"))
                row = result.fetchone()
                query_time = time.time() - start_time

                if not row or row[0] != 1:
                    raise Exception("Database health check query failed")

                # Get connection pool statistics if available
                pool_stats = {}
                if hasattr(self._engine, "pool") and self._engine.pool is not None:
                    pool = self._engine.pool
                    pool_stats = {
                        "size": pool.size(),
                        "checkedin": pool.checkedin(),
                        "checkedout": pool.checkedout(),
                        "overflow": pool.overflow(),
                    }

                # Update health status
                self._health_status = {
                    "status": "healthy",
                    "last_error": None,
                    "query_time_ms": round(query_time * 1000, 2),
                    "pool": pool_stats,
                    "stats": self._connection_stats,
                }

            self._last_health_check = current_time
            return self._health_status

        except Exception as e:
            error_message = f"Database health check failed: {str(e)}"
            logger.error(error_message)
            self._health_status = {"status": "error", "last_error": str(e)}
            return self._health_status

    @asynccontextmanager
    async def get_session(self):
        """
        Get a database session with automatic retry on connection errors.

        Yields:
            AsyncSession: SQLAlchemy async session
        """
        if not self._initialized:
            success = await self.initialize()
            if not success:
                raise RuntimeError("Database not initialized")

        # Try to get a session with retries
        for retry in range(self._max_retries + 1):
            try:
                session = self._session_factory()
                self._connection_stats["total_connections"] += 1
                self._connection_stats["active_connections"] += 1

                try:
                    yield session
                finally:
                    self._connection_stats["active_connections"] -= 1
                    if hasattr(session, "close") and callable(session.close):
                        try:
                            await session.close()
                        except Exception as e:
                            logger.warning(f"Error closing session: {str(e)}")

                # If we get here without an exception, break the retry loop
                break

            except (OperationalError, DBAPIError) as e:
                self._connection_stats["errors"] += 1
                error_message = f"Database connection error (attempt {retry+1}/{self._max_retries+1}): {str(e)}"

                if retry < self._max_retries:
                    # Calculate delay with exponential backoff
                    delay = min(self._retry_delay * (2**retry), self._max_retry_delay)

                    # Add jitter if enabled (±25%)
                    if self._jitter:
                        delay = delay * (0.75 + random.random() * 0.5)

                    logger.warning(
                        f"{error_message}. Retrying in {delay:.2f} seconds..."
                    )
                    self._connection_stats["retries"] += 1
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"{error_message}. All retry attempts failed.")
                    raise

    async def execute_with_retry(
        self, operation: Callable[..., T], *args: Any, **kwargs: Any
    ) -> T:
        """
        Execute a database operation with retry mechanism.

        Args:
            operation: The operation to execute
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation

        Returns:
            The result of the operation

        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None

        for retry in range(self._max_retries + 1):
            try:
                async with self.get_session() as session:
                    # Pass session to the operation
                    if "session" in kwargs:
                        kwargs["session"] = session
                    elif len(args) > 0 and isinstance(args[0], AsyncSession):
                        # Replace first argument with session if it's a session
                        args = (session,) + args[1:]
                    else:
                        # Add session as first argument
                        args = (session,) + args

                    # Execute the operation
                    return await operation(*args, **kwargs)

            except (OperationalError, DBAPIError) as e:
                last_exception = e
                error_message = f"Database operation error (attempt {retry+1}/{self._max_retries+1}): {str(e)}"

                if retry < self._max_retries:
                    # Calculate delay with exponential backoff
                    delay = min(self._retry_delay * (2**retry), self._max_retry_delay)

                    # Add jitter if enabled (±25%)
                    if self._jitter:
                        delay = delay * (0.75 + random.random() * 0.5)

                    logger.warning(
                        f"{error_message}. Retrying in {delay:.2f} seconds..."
                    )
                    self._connection_stats["retries"] += 1
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"{error_message}. All retry attempts failed.")
                    raise
            except SQLAlchemyError as e:
                # Don't retry other SQLAlchemy errors (like integrity errors)
                logger.error(f"Database operation error (non-retryable): {str(e)}")
                raise
            except Exception as e:
                # Don't retry other exceptions
                logger.error(f"Unexpected error during database operation: {str(e)}")
                raise

        # If we get here, all retries failed
        if last_exception:
            raise last_exception

        # This should never happen, but just in case
        raise RuntimeError("Unexpected error in execute_with_retry")

    async def close(self) -> None:
        """Close the database connection."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self._initialized = False
            logger.info("Database connection closed")
