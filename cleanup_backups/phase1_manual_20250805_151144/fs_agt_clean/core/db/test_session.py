"""
Tests for the SessionManager class.
"""

import unittest.mock as mock
from contextlib import asynccontextmanager

import pytest
from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.db.session import (
    SessionManager,
    get_db_session,
    get_session_manager,
)
from fs_agt_clean.core.models.database.base import Base
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession


@pytest.fixture
def config_manager():
    """Create a mock config manager."""
    config = mock.MagicMock(spec=ConfigManager)
    config.get_section.return_value = {
        "connection_string": "sqlite+aiosqlite:///:memory:",
        "pool_size": 5,
        "max_overflow": 10,
        "echo": False,
    }
    return config


@pytest.fixture
def session_manager(config_manager):
    """Create a session manager with a mock config."""
    return SessionManager(config_manager=config_manager)


@pytest.mark.asyncio
async def test_initialize(session_manager):
    """Test initialization."""
    # The session manager is initialized in the constructor
    assert session_manager._engine is not None
    assert session_manager._session_factory is not None


@pytest.mark.asyncio
async def test_create_tables(session_manager, monkeypatch):
    """Test creating tables."""
    # Mock the engine's begin method
    mock_conn = mock.AsyncMock()
    mock_engine = mock.AsyncMock(spec=AsyncEngine)

    @asynccontextmanager
    async def mock_begin():
        yield mock_conn

    mock_engine.begin = mock_begin
    session_manager._engine = mock_engine

    # Mock Base.metadata.create_all
    mock_create_all = mock.MagicMock()
    monkeypatch.setattr(Base.metadata, "create_all", mock_create_all)

    await session_manager.create_tables()

    # Verify that run_sync was called with create_all
    mock_conn.run_sync.assert_called_once()
    args, _ = mock_conn.run_sync.call_args
    assert args[0] == mock_create_all


@pytest.mark.asyncio
async def test_get_session(session_manager):
    """Test getting a session."""
    # Mock the session factory
    mock_session = mock.AsyncMock(spec=AsyncSession)
    mock_session_factory = mock.MagicMock()
    mock_session_factory.return_value = mock_session
    session_manager._session_factory = mock_session_factory

    session = await session_manager.get_session()

    assert session is mock_session
    mock_session_factory.assert_called_once()


@pytest.mark.asyncio
async def test_session_context_manager(session_manager):
    """Test the session context manager."""
    # Mock the session factory
    mock_session = mock.AsyncMock(spec=AsyncSession)
    mock_session_factory = mock.MagicMock()
    mock_session_factory.return_value = mock_session
    session_manager._session_factory = mock_session_factory

    # Use the session context manager
    async with session_manager.session() as session:
        assert session is mock_session

    # Verify that close was called
    mock_session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_close(session_manager):
    """Test closing the session manager."""
    # Mock the engine
    mock_engine = mock.AsyncMock(spec=AsyncEngine)
    session_manager._engine = mock_engine

    await session_manager.close()

    # Verify that dispose was called
    mock_engine.dispose.assert_awaited_once()
    assert session_manager._engine is None
    assert session_manager._session_factory is None


@pytest.mark.asyncio
async def test_get_session_manager():
    """Test the get_session_manager function."""
    # Reset the global instance
    import sys

    module = sys.modules[SessionManager.__module__]
    original_session_manager = module._session_manager
    module._session_manager = None

    try:
        # First call should create a new instance
        result1 = get_session_manager()
        assert isinstance(result1, SessionManager)

        # Second call should return the same instance
        result2 = get_session_manager()
        assert result2 is result1
    finally:
        # Restore the original session manager
        module._session_manager = original_session_manager


@pytest.mark.asyncio
async def test_get_db_session(monkeypatch):
    """Test the get_db_session function."""
    # Mock the session manager
    mock_session_manager = mock.AsyncMock(spec=SessionManager)
    mock_session = mock.AsyncMock(spec=AsyncSession)

    # Mock the session context manager
    @asynccontextmanager
    async def mock_session_cm():
        yield mock_session

    mock_session_manager.session = mock_session_cm

    # Patch get_session_manager
    monkeypatch.setattr(
        "fs_agt_clean.core.db.session.get_session_manager",
        lambda: mock_session_manager,
    )

    # Use get_db_session
    session_yielded = False
    async for session in get_db_session():
        assert session is mock_session
        session_yielded = True

    assert session_yielded, "Session was not yielded"
