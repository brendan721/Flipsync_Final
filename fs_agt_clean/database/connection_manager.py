"""
Database connection manager with connection pooling and error handling.
"""

import logging
import os
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Optional database dependencies
try:
    import psycopg2
    from psycopg2 import pool
    from psycopg2.extensions import connection as pg_connection
    from psycopg2.extras import RealDictCursor

    PSYCOPG2_AVAILABLE = True
except ImportError:
    logger.warning("psycopg2 not available - database functionality will be limited")
    PSYCOPG2_AVAILABLE = False

    # Create mock classes for type hints
    class MockConnection:
        pass

    class MockCursor:
        pass

    pg_connection = MockConnection
    RealDictCursor = MockCursor


class DatabaseConnectionManager:
    """
    Manages database connections with connection pooling and error handling.

    This class provides a centralized way to manage database connections,
    with built-in connection pooling, retry logic, and error handling.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure only one connection pool exists."""
        if cls._instance is None:
            cls._instance = super(DatabaseConnectionManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        host: str = None,
        port: int = None,
        dbname: str = None,
        user: str = None,
        password: str = None,
        min_connections: int = 1,
        max_connections: int = 10,
        max_retries: int = 3,
        retry_delay: float = 0.5,
    ):
        """
        Initialize the database connection manager.

        Args:
            host: Database host (default: from environment variable DB_HOST or 'localhost')
            port: Database port (default: from environment variable DB_PORT or 5432)
            dbname: Database name (default: from environment variable DB_NAME or 'flipsync')
            user: Database user (default: from environment variable DB_USER or 'postgres')
            password: Database password (default: from environment variable DB_PASSWORD)
            min_connections: Minimum number of connections in the pool
            max_connections: Maximum number of connections in the pool
            max_retries: Maximum number of retries for database operations
            retry_delay: Delay between retries in seconds
        """
        if self._initialized:
            return

        self.host = host or os.environ.get(
            "DB_HOST", "localhost"
        )  # Changed default from "db" to "localhost"
        self.port = port or int(os.environ.get("DB_PORT", 5432))
        self.dbname = dbname or os.environ.get("DB_NAME", "flipsync")
        self.user = user or os.environ.get("DB_USER", "postgres")
        self.password = password or os.environ.get("DB_PASSWORD", "postgres")
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self._connection_pool = None
        self._initialized = True

        # Initialize the connection pool
        self._initialize_pool()

    def _initialize_pool(self) -> None:
        """Initialize the connection pool."""
        if not PSYCOPG2_AVAILABLE:
            logger.warning(
                "psycopg2 not available - skipping database connection pool initialization"
            )
            return

        try:
            self._connection_pool = pool.ThreadedConnectionPool(
                minconn=self.min_connections,
                maxconn=self.max_connections,
                host=self.host,
                port=self.port,
                dbname=self.dbname,
                user=self.user,
                password=self.password,
            )
            logger.info(
                f"Initialized database connection pool with {self.min_connections} to "
                f"{self.max_connections} connections to {self.dbname} at {self.host}:{self.port}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize database connection pool: {e}")
            raise

    @contextmanager
    def get_connection(self) -> pg_connection:
        """
        Get a connection from the pool with retry logic.

        Returns:
            A database connection from the pool.

        Raises:
            Exception: If unable to get a connection after max_retries.
        """
        connection = None
        for attempt in range(self.max_retries):
            try:
                connection = self._connection_pool.getconn()
                break
            except (pool.PoolError, psycopg2.OperationalError) as e:
                if attempt == self.max_retries - 1:
                    logger.error(
                        f"Failed to get database connection after {self.max_retries} attempts: {e}"
                    )
                    raise
                logger.warning(
                    f"Failed to get database connection (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                time.sleep(self.retry_delay)

        if connection is None:
            raise Exception("Failed to get database connection")

        try:
            yield connection
        finally:
            try:
                self._connection_pool.putconn(connection)
            except Exception as e:
                logger.error(f"Failed to return connection to pool: {e}")

    @contextmanager
    def get_cursor(self, cursor_factory=RealDictCursor):
        """
        Get a cursor from a connection in the pool.

        Args:
            cursor_factory: The cursor factory to use (default: RealDictCursor)

        Returns:
            A database cursor.
        """
        with self.get_connection() as connection:
            cursor = connection.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
                connection.commit()
            except Exception as e:
                connection.rollback()
                logger.error(f"Database operation failed: {e}")
                raise
            finally:
                cursor.close()

    def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        fetch_all: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Execute a query and return the results.

        Args:
            query: The SQL query to execute
            params: The parameters for the query
            fetch_all: Whether to fetch all results or just one

        Returns:
            The query results as a list of dictionaries.
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params or {})
            if fetch_all:
                return cursor.fetchall()
            else:
                result = cursor.fetchone()
                return [result] if result else []

    def execute_transaction(
        self,
        queries: List[Dict[str, Any]],
    ) -> None:
        """
        Execute multiple queries in a transaction.

        Args:
            queries: A list of dictionaries with 'query' and 'params' keys
        """
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                try:
                    for query_dict in queries:
                        cursor.execute(
                            query_dict["query"], query_dict.get("params", {})
                        )
                    connection.commit()
                except Exception as e:
                    connection.rollback()
                    logger.error(f"Transaction failed: {e}")
                    raise

    def close(self) -> None:
        """Close the connection pool."""
        if self._connection_pool:
            self._connection_pool.closeall()
            logger.info("Closed database connection pool")
            self._connection_pool = None

    def __del__(self):
        """Ensure the connection pool is closed when the object is deleted."""
        self.close()


# Create a singleton instance for global use
try:
    db_manager = DatabaseConnectionManager()
except Exception as e:
    logger.warning(f"Failed to initialize database connection manager: {e}")
    # Create a dummy instance for testing
    db_manager = DatabaseConnectionManager.__new__(DatabaseConnectionManager)
    db_manager._initialized = True
