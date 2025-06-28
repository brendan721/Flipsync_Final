"""
Tests for the DatabaseConnectionManager class.
"""

import asyncio
import unittest.mock as mock
from contextlib import asynccontextmanager

import pytest
from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.db.connection_manager import DatabaseConnectionManager
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def config_manager():
    """Create a mock config manager."""
    config = mock.MagicMock(spec=ConfigManager)
    config.get_section.return_value = {
        "connection_string": "sqlite+aiosqlite:///:memory:",
        "pool_size": 5,
        "max_overflow": 10,
        "echo": False,
        "max_retries": 3,
        "retry_delay": 0.1,  # Short delay for tests
        "max_retry_delay": 0.5,  # Short delay for tests
    }
    return config


@pytest.fixture
def connection_manager(config_manager):
    """Create a connection manager with a mock config."""
    return DatabaseConnectionManager(
        config_manager=config_manager,
        max_retries=3,
        retry_delay=0.1,  # Short delay for tests
        max_retry_delay=0.5,  # Short delay for tests
        jitter=False,  # Disable jitter for predictable tests
    )


@pytest.mark.asyncio
async def test_initialize_success(connection_manager, monkeypatch):
    """Test successful initialization."""
    # Mock the create_async_engine function
    mock_engine = mock.AsyncMock()
    mock_session = mock.AsyncMock()
    mock_result = mock.MagicMock()
    mock_result.fetchone.return_value = (1,)

    mock_session_factory = mock.MagicMock()
    mock_session_factory.return_value = mock_session

    mock_session.__aenter__.return_value = mock_session
    mock_session.execute.return_value = mock_result

    with (
        mock.patch(
            "fs_agt_clean.core.db.connection_manager.create_async_engine",
            return_value=mock_engine,
        ),
        mock.patch(
            "fs_agt_clean.core.db.connection_manager.sessionmaker",
            return_value=mock_session_factory,
        ),
    ):

        result = await connection_manager.initialize()

        assert result is True
        assert connection_manager._initialized is True
        assert connection_manager._health_status["status"] == "healthy"
        assert connection_manager._connection_stats["successful_connections"] == 1


@pytest.mark.asyncio
async def test_initialize_failure(connection_manager, monkeypatch):
    """Test initialization failure."""
    # Mock the create_async_engine function to raise an exception
    with mock.patch(
        "fs_agt_clean.core.db.connection_manager.create_async_engine",
        side_effect=OperationalError("connection failed", None, None),
    ):

        result = await connection_manager.initialize()

        assert result is False
        assert connection_manager._initialized is False
        assert connection_manager._health_status["status"] == "error"
        assert (
            connection_manager._connection_stats["errors"] == 4
        )  # Initial attempt + 3 retries


@pytest.mark.asyncio
async def test_check_health_not_initialized(connection_manager):
    """Test health check when not initialized."""
    result = await connection_manager.check_health()

    assert result["status"] == "not_initialized"


@pytest.mark.asyncio
async def test_check_health_success(connection_manager, monkeypatch):
    """Test successful health check."""
    # Setup mock for initialization
    mock_engine = mock.AsyncMock()
    mock_session = mock.AsyncMock()
    mock_result = mock.MagicMock()
    mock_result.fetchone.return_value = (1,)

    mock_session_factory = mock.MagicMock()
    mock_session_factory.return_value = mock_session

    mock_session.__aenter__.return_value = mock_session
    mock_session.execute.return_value = mock_result

    # Mock pool stats
    mock_pool = mock.MagicMock()
    mock_pool.size.return_value = 5
    mock_pool.checkedin.return_value = 4
    mock_pool.checkedout.return_value = 1
    mock_pool.overflow.return_value = 0
    mock_engine.pool = mock_pool

    with (
        mock.patch(
            "fs_agt_clean.core.db.connection_manager.create_async_engine",
            return_value=mock_engine,
        ),
        mock.patch(
            "fs_agt_clean.core.db.connection_manager.sessionmaker",
            return_value=mock_session_factory,
        ),
    ):

        # Initialize first
        await connection_manager.initialize()

        # Reset the last health check time to force a new check
        connection_manager._last_health_check = 0

        # Check health
        result = await connection_manager.check_health()

        assert result["status"] == "healthy"
        assert "query_time_ms" in result
        assert "pool" in result
        assert result["pool"]["size"] == 5


@pytest.mark.asyncio
async def test_check_health_failure(connection_manager, monkeypatch):
    """Test health check failure."""
    # Setup mock for initialization
    mock_engine = mock.AsyncMock()
    mock_session = mock.AsyncMock()
    mock_result = mock.MagicMock()
    mock_result.fetchone.return_value = (1,)

    mock_session_factory = mock.MagicMock()
    mock_session_factory.return_value = mock_session

    mock_session.__aenter__.return_value = mock_session

    # First make initialization succeed
    mock_session.execute.return_value = mock_result

    with (
        mock.patch(
            "fs_agt_clean.core.db.connection_manager.create_async_engine",
            return_value=mock_engine,
        ),
        mock.patch(
            "fs_agt_clean.core.db.connection_manager.sessionmaker",
            return_value=mock_session_factory,
        ),
    ):

        # Initialize first
        await connection_manager.initialize()

        # Now make health check fail
        mock_session.execute.side_effect = OperationalError(
            "connection lost", None, None
        )

        # Reset the last health check time to force a new check
        connection_manager._last_health_check = 0

        # Check health
        result = await connection_manager.check_health()

        assert result["status"] == "error"
        assert "connection lost" in result["last_error"]


@pytest.mark.asyncio
async def test_get_session_success(connection_manager, monkeypatch):
    """Test getting a session successfully."""
    # Setup mock for initialization
    mock_engine = mock.AsyncMock()
    mock_session = mock.AsyncMock()

    mock_session_factory = mock.MagicMock()
    mock_session_factory.return_value = mock_session

    with (
        mock.patch(
            "fs_agt_clean.core.db.connection_manager.create_async_engine",
            return_value=mock_engine,
        ),
        mock.patch(
            "fs_agt_clean.core.db.connection_manager.sessionmaker",
            return_value=mock_session_factory,
        ),
        mock.patch.object(connection_manager, "initialize", return_value=True),
    ):

        connection_manager._initialized = True
        connection_manager._session_factory = mock_session_factory

        async with connection_manager.get_session() as session:
            assert session is mock_session
            assert connection_manager._connection_stats["total_connections"] == 1
            assert connection_manager._connection_stats["active_connections"] == 1

        assert connection_manager._connection_stats["active_connections"] == 0
        mock_session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_session_retry(connection_manager, monkeypatch):
    """Test session retry on connection error."""
    # Setup mock for initialization
    mock_engine = mock.AsyncMock()
    mock_session = mock.AsyncMock()

    mock_session_factory = mock.MagicMock()
    # First call raises error, second succeeds
    mock_session_factory.side_effect = [
        OperationalError("connection error", None, None),
        mock_session,
    ]

    with (
        mock.patch(
            "fs_agt_clean.core.db.connection_manager.create_async_engine",
            return_value=mock_engine,
        ),
        mock.patch(
            "fs_agt_clean.core.db.connection_manager.sessionmaker",
            return_value=mock_session_factory,
        ),
        mock.patch.object(connection_manager, "initialize", return_value=True),
        mock.patch("asyncio.sleep"),
    ):  # Mock sleep to speed up test

        connection_manager._initialized = True
        connection_manager._session_factory = mock_session_factory

        async with connection_manager.get_session() as session:
            assert session is mock_session
            assert connection_manager._connection_stats["retries"] == 1
            assert connection_manager._connection_stats["errors"] == 1


@pytest.mark.asyncio
async def test_execute_with_retry_success(connection_manager, monkeypatch):
    """Test execute_with_retry with successful operation."""
    # Setup mock for session
    mock_session = mock.AsyncMock(spec=AsyncSession)

    # Mock operation that succeeds
    async def mock_operation(session):
        assert session is mock_session
        return "success"

    # Mock get_session to yield our mock session
    @asynccontextmanager
    async def mock_get_session():
        yield mock_session

    with mock.patch.object(connection_manager, "get_session", mock_get_session):
        result = await connection_manager.execute_with_retry(mock_operation)
        assert result == "success"


@pytest.mark.asyncio
async def test_execute_with_retry_failure(connection_manager, monkeypatch):
    """Test execute_with_retry with failing operation."""
    # Setup mock for session
    mock_session = mock.AsyncMock(spec=AsyncSession)

    # Mock operation that always fails with retryable error
    async def mock_operation(session):
        raise OperationalError("operation failed", None, None)

    # Mock get_session to yield our mock session
    @asynccontextmanager
    async def mock_get_session():
        yield mock_session

    with (
        mock.patch.object(connection_manager, "get_session", mock_get_session),
        mock.patch("asyncio.sleep"),
    ):  # Mock sleep to speed up test

        with pytest.raises(OperationalError):
            await connection_manager.execute_with_retry(mock_operation)


@pytest.mark.asyncio
async def test_close(connection_manager):
    """Test closing the connection manager."""
    # Setup mock engine
    mock_engine = mock.AsyncMock()
    connection_manager._engine = mock_engine
    connection_manager._initialized = True

    await connection_manager.close()

    mock_engine.dispose.assert_awaited_once()
    assert connection_manager._engine is None
    assert connection_manager._session_factory is None
    assert connection_manager._initialized is False
