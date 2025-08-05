"""
Optimized Database Connection for FlipSync Production
===================================================

High-performance database connection optimized for the production environment
with minimal latency and maximum throughput.
"""

import asyncio
import logging
import os
import time
from typing import AsyncGenerator, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class OptimizedDatabase:
    """
    Optimized database connection with minimal overhead and maximum performance.

    Designed specifically for the FlipSync production environment to eliminate
    the 12+ second connection times observed with the standard configuration.
    """

    def __init__(self, connection_string: Optional[str] = None):
        """Initialize optimized database connection."""
        self.connection_string = connection_string or os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:your_password@localhost:5432/flipsync_db",
        )

        # Ensure asyncpg driver
        if self.connection_string.startswith("postgresql://"):
            self.connection_string = self.connection_string.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )

        self._engine: Optional[AsyncEngine] = None
        self._session_factory = None
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize database with optimized settings for minimal latency."""
        if self._initialized:
            return True

        try:
            start_time = time.perf_counter()

            # Create engine with aggressive optimization for speed
            self._engine = create_async_engine(
                self.connection_string,
                # Connection pool settings optimized for speed
                pool_size=5,  # Smaller pool for faster initialization
                max_overflow=10,  # Reasonable overflow
                pool_timeout=5,  # Fast timeout for quick failure detection
                pool_recycle=3600,  # 1 hour recycle
                pool_pre_ping=False,  # Disable pre-ping for speed
                echo=False,  # Disable SQL echo for performance
                # Connection arguments optimized for production
                connect_args={
                    "command_timeout": 5,  # Fast command timeout
                    "server_settings": {
                        "application_name": "FlipSync_Optimized",
                        "jit": "off",  # Disable JIT compilation for faster connection
                    },
                    # Disable SSL for internal network (production droplet)
                    "ssl": "disable",
                },
                # Additional performance optimizations
                future=True,  # Use SQLAlchemy 2.0 style
                query_cache_size=0,  # Disable query cache for minimal overhead
            )

            # Create session factory
            self._session_factory = sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,  # Disable autoflush for performance
                autocommit=False,
            )

            # Test connection with minimal query
            async with self._session_factory() as session:
                result = await session.execute(text("SELECT 1"))
                result.scalar()

            init_time = (time.perf_counter() - start_time) * 1000
            logger.info(f"Optimized database initialized in {init_time:.2f}ms")

            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"Failed to initialize optimized database: {e}")
            return False

    def get_session(self):
        """Get database session with minimal overhead."""
        if not self._session_factory:
            raise RuntimeError("Database not initialized")
        return self._session_factory()

    async def close(self) -> None:
        """Close database connection."""
        if self._engine:
            await self._engine.dispose()
            self._initialized = False
            logger.info("Optimized database connection closed")

    async def count_records(self, table_name: str) -> int:
        """Count records in a table."""
        if not self._initialized:
            await self.initialize()

        async with self.get_session() as session:
            result = await session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            return result.scalar() or 0

    async def health_check(self) -> dict:
        """Perform quick health check."""
        try:
            start_time = time.perf_counter()

            async with self.get_session() as session:
                result = await session.execute(
                    text("SELECT current_database(), current_timestamp")
                )
                db_name, timestamp = result.fetchone()

            check_time = (time.perf_counter() - start_time) * 1000

            return {
                "status": "healthy",
                "database": db_name,
                "timestamp": str(timestamp),
                "response_time_ms": check_time,
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": None,
            }


# Global optimized database instance
_optimized_db_instance: Optional[OptimizedDatabase] = None


def get_optimized_database() -> OptimizedDatabase:
    """Get the global optimized database instance."""
    global _optimized_db_instance
    if _optimized_db_instance is None:
        _optimized_db_instance = OptimizedDatabase()
    return _optimized_db_instance


async def get_initialized_database() -> OptimizedDatabase:
    """Get an initialized database instance ready for use."""
    db = get_optimized_database()
    if not db._initialized:
        await db.initialize()
    return db


async def test_optimized_performance():
    """Test the optimized database performance."""
    print("🚀 Testing Optimized Database Performance")
    print("=" * 50)

    db = get_optimized_database()

    # Test multiple connections
    times = []
    for i in range(5):
        start_time = time.perf_counter()

        success = await db.initialize()
        if success:
            async with db.get_session() as session:
                result = await session.execute(text("SELECT current_database()"))
                db_name = result.scalar()

        await db.close()

        duration = (time.perf_counter() - start_time) * 1000
        times.append(duration)
        print(f"  Connection {i+1}: {duration:.2f}ms")

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    print(f"\n📊 Performance Results:")
    print(f"  Average: {avg_time:.2f}ms")
    print(f"  Minimum: {min_time:.2f}ms")
    print(f"  Maximum: {max_time:.2f}ms")
    print(f"  Target: <1000ms (Docker-aware)")
    print(f"  Status: {'✅ PASSED' if avg_time < 1000 else '❌ FAILED'}")

    return avg_time < 1000


if __name__ == "__main__":
    asyncio.run(test_optimized_performance())
