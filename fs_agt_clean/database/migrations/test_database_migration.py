"""
Migration test for the database implementation.

This test validates that the database implementation can be
migrated to the new codebase structure without breaking functionality.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker

from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.db.database import Database


class TestDatabaseMigration:
    """Test the migration of the database implementation."""

    @pytest.fixture
    def mock_config_manager(self):
        """Create a mock config manager."""
        config = MagicMock(spec=ConfigManager)
        config.get_config.return_value = {
            "connection_string": "postgresql+asyncpg://user:password@localhost/postgres",
            "pool_size": 5,
            "max_overflow": 10,
            "echo": False,
        }
        return config

    @pytest.fixture
    def mock_engine(self):
        """Create a mock SQLAlchemy engine."""
        engine = AsyncMock(spec=AsyncEngine)
        return engine

    @pytest.fixture
    def mock_session(self):
        """Create a mock SQLAlchemy session."""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    def mock_session_factory(self, mock_session):
        """Create a mock session factory."""
        factory = MagicMock()
        factory.return_value = mock_session
        return factory

    @pytest.mark.asyncio
    @patch("fs_agt.core.db.database.create_async_engine")
    @patch("fs_agt.core.db.database.sessionmaker")
    async def test_basic_functionality(
        self, mock_sessionmaker, mock_create_engine,
        mock_config_manager, mock_engine, mock_session, mock_session_factory
    ):
        """Test that basic functionality works as expected."""
        # Arrange
        mock_create_engine.return_value = mock_engine
        mock_sessionmaker.return_value = mock_session_factory

        # Mock the execute result for fetch_one
        mock_row = MagicMock()
        mock_row._mapping = {"id": 1, "name": "test"}
        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result

        # Act - Initialize database
        db = Database(mock_config_manager)
        await db.initialize()

        # Execute a query
        result = await db.fetch_one("SELECT * FROM test WHERE id = :id", {"id": 1})

        # Close the database
        await db.close()

        # Assert
        assert result == {"id": 1, "name": "test"}

        # Verify the correct methods were called
        mock_create_engine.assert_called_once_with(
            "postgresql+asyncpg://user:password@localhost/postgres",
            pool_size=5,
            max_overflow=10,
            echo=False,
        )
        mock_sessionmaker.assert_called_once()
        mock_session.execute.assert_called_once()
        mock_result.fetchone.assert_called_once()
        mock_engine.dispose.assert_called_once()

    @pytest.mark.asyncio
    @patch("fs_agt.core.db.database.create_async_engine")
    @patch("fs_agt.core.db.database.sessionmaker")
    async def test_session_context_manager(
        self, mock_sessionmaker, mock_create_engine,
        mock_config_manager, mock_engine, mock_session, mock_session_factory
    ):
        """Test that the session context manager works as expected."""
        # Arrange
        mock_create_engine.return_value = mock_engine
        mock_sessionmaker.return_value = mock_session_factory

        # Act - Initialize database
        db = Database(mock_config_manager)
        await db.initialize()

        # Use the session context manager
        async with db.get_session() as session:
            # Assert
            assert session == mock_session

        # Assert session was closed
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("fs_agt.core.db.database.create_async_engine")
    @patch("fs_agt.core.db.database.sessionmaker")
    async def test_error_handling(
        self, mock_sessionmaker, mock_create_engine,
        mock_config_manager, mock_engine, mock_session, mock_session_factory
    ):
        """Test that error handling works as expected."""
        # Arrange
        mock_create_engine.return_value = mock_engine
        mock_sessionmaker.return_value = mock_session_factory

        # Mock an error during execute
        mock_session.execute.side_effect = Exception("Test error")

        # Act - Initialize database
        db = Database(mock_config_manager)
        await db.initialize()

        # Execute a query - should handle the error
        with pytest.raises(Exception):
            await db.fetch_one("SELECT * FROM test WHERE id = :id", {"id": 1})

        # Assert
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch("fs_agt.core.db.database.create_async_engine")
    @patch("fs_agt.core.db.database.sessionmaker")
    async def test_migration_compatibility(
        self, mock_sessionmaker, mock_create_engine,
        mock_config_manager, mock_engine, mock_session_factory
    ):
        """
        Test that the implementation is compatible with the migration plan.

        This test verifies that the implementation follows the interface
        defined in the migration plan and can be safely migrated.
        """
        # Arrange
        mock_create_engine.return_value = mock_engine
        mock_sessionmaker.return_value = mock_session_factory

        # Act - Initialize database
        db = Database(mock_config_manager)
        await db.initialize()

        # Assert
        assert db._engine == mock_engine
        assert db._session_factory == mock_session_factory

        # Verify the correct methods were called
        mock_create_engine.assert_called_once()
        mock_sessionmaker.assert_called_once()


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
