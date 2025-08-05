"""
Tests for the DatabaseAdapter class.
"""

import unittest.mock as mock
from contextlib import asynccontextmanager

import pytest
from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.db.database import Database
from fs_agt_clean.core.db.database_adapter import (
    DatabaseAdapter,
    SessionAdapter,
)
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def config_manager():
    """Create a mock config manager."""
    config = mock.MagicMock(spec=ConfigManager)
    return config


@pytest.fixture
def database():
    """Create a mock database."""
    db = mock.AsyncMock(spec=Database)
    return db


@pytest.fixture
def database_adapter(config_manager, monkeypatch):
    """Create a database adapter with mocked dependencies."""
    # Mock the Database class
    mock_database = mock.AsyncMock(spec=Database)
    monkeypatch.setattr(
        "fs_agt_clean.core.db.database_adapter.Database",
        lambda **kwargs: mock_database,
    )

    adapter = DatabaseAdapter(config_manager=config_manager)
    adapter.database = mock_database
    return adapter


@pytest.mark.asyncio
async def test_initialize_success(database_adapter):
    """Test successful initialization."""
    database_adapter.database.initialize.return_value = None

    result = await database_adapter.initialize()

    assert result is True
    assert database_adapter.is_initialized is True
    database_adapter.database.initialize.assert_awaited_once()


@pytest.mark.asyncio
async def test_initialize_failure(database_adapter):
    """Test initialization failure."""
    database_adapter.database.initialize.side_effect = Exception("Connection failed")

    result = await database_adapter.initialize()

    assert result is False
    assert database_adapter.is_initialized is False
    database_adapter.database.initialize.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute(database_adapter):
    """Test execute method."""
    database_adapter.database.execute.return_value = "result"

    result = await database_adapter.execute(
        "SELECT * FROM table", param1="value1", param2="value2"
    )

    assert result == "result"
    database_adapter.database.execute.assert_awaited_once_with(
        "SELECT * FROM table", {"param1": "value1", "param2": "value2"}
    )


@pytest.mark.asyncio
async def test_execute_with_positional_args(database_adapter):
    """Test execute method with positional arguments."""
    database_adapter.database.execute.return_value = "result"

    result = await database_adapter.execute("SELECT * FROM table", "value1", "value2")

    assert result == "result"
    database_adapter.database.execute.assert_awaited_once_with(
        "SELECT * FROM table", {"param_0": "value1", "param_1": "value2"}
    )


@pytest.mark.asyncio
async def test_fetch_one(database_adapter):
    """Test fetch_one method."""
    database_adapter.database.fetch_one.return_value = {"id": 1, "name": "test"}

    result = await database_adapter.fetch_one(
        "SELECT * FROM table WHERE id = :id", id=1
    )

    assert result == {"id": 1, "name": "test"}
    database_adapter.database.fetch_one.assert_awaited_once_with(
        "SELECT * FROM table WHERE id = :id", {"id": 1}
    )


@pytest.mark.asyncio
async def test_fetch_all(database_adapter):
    """Test fetch_all method."""
    database_adapter.database.fetch_all.return_value = [
        {"id": 1, "name": "test1"},
        {"id": 2, "name": "test2"},
    ]

    result = await database_adapter.fetch_all("SELECT * FROM table")

    assert result == [{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}]
    database_adapter.database.fetch_all.assert_awaited_once_with(
        "SELECT * FROM table", {}
    )


def test_is_connected(database_adapter):
    """Test is_connected property."""
    database_adapter.is_initialized = True
    assert database_adapter.is_connected is True

    database_adapter.is_initialized = False
    assert database_adapter.is_connected is False


@pytest.mark.asyncio
async def test_disconnect_success(database_adapter):
    """Test successful disconnection."""
    database_adapter.is_initialized = True
    database_adapter.database.close.return_value = None

    result = await database_adapter.disconnect()

    assert result is True
    assert database_adapter.is_initialized is False
    database_adapter.database.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_disconnect_failure(database_adapter):
    """Test disconnection failure."""
    database_adapter.is_initialized = True
    database_adapter.database.close.side_effect = Exception("Disconnection failed")

    result = await database_adapter.disconnect()

    assert result is False
    assert database_adapter.is_initialized is True
    database_adapter.database.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_tables_success(database_adapter):
    """Test successful table creation."""
    database_adapter.database.create_tables.return_value = None

    result = await database_adapter.create_tables()

    assert result is True
    database_adapter.database.create_tables.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_tables_failure(database_adapter):
    """Test table creation failure."""
    database_adapter.database.create_tables.side_effect = Exception(
        "Table creation failed"
    )

    result = await database_adapter.create_tables()

    assert result is False
    database_adapter.database.create_tables.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_session_context(database_adapter):
    """Test get_session_context method."""
    mock_session = mock.AsyncMock(spec=AsyncSession)

    @asynccontextmanager
    async def mock_get_session_context():
        yield mock_session

    database_adapter.database.get_session_context = mock_get_session_context

    async with database_adapter.get_session_context() as session:
        assert isinstance(session, SessionAdapter)
        assert session.session is mock_session


@pytest.mark.asyncio
async def test_session_adapter_execute():
    """Test SessionAdapter execute method."""
    mock_session = mock.AsyncMock(spec=AsyncSession)
    session_adapter = SessionAdapter(mock_session)

    # Mock sqlalchemy.text
    mock_text = mock.MagicMock()
    mock_text.return_value = "text_query"

    with mock.patch("sqlalchemy.text", mock_text):
        await session_adapter.execute(
            "SELECT * FROM table", param1="value1", param2="value2"
        )

        mock_text.assert_called_once_with("SELECT * FROM table")
        mock_session.execute.assert_awaited_once_with(
            "text_query", {"param1": "value1", "param2": "value2"}
        )
        mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_session_adapter_fetch_one():
    """Test SessionAdapter fetch_one method."""
    mock_session = mock.AsyncMock(spec=AsyncSession)
    mock_result = mock.MagicMock()
    mock_row = mock.MagicMock()
    mock_row._mapping = {"id": 1, "name": "test"}
    mock_result.fetchone.return_value = mock_row
    mock_session.execute.return_value = mock_result

    session_adapter = SessionAdapter(mock_session)

    # Mock sqlalchemy.text
    mock_text = mock.MagicMock()
    mock_text.return_value = "text_query"

    with mock.patch("sqlalchemy.text", mock_text):
        result = await session_adapter.fetch_one(
            "SELECT * FROM table WHERE id = :id", id=1
        )

        assert result == {"id": 1, "name": "test"}
        mock_text.assert_called_once_with("SELECT * FROM table WHERE id = :id")
        mock_session.execute.assert_awaited_once_with("text_query", {"id": 1})


@pytest.mark.asyncio
async def test_session_adapter_fetch_one_none():
    """Test SessionAdapter fetch_one method with no result."""
    mock_session = mock.AsyncMock(spec=AsyncSession)
    mock_result = mock.MagicMock()
    mock_result.fetchone.return_value = None
    mock_session.execute.return_value = mock_result

    session_adapter = SessionAdapter(mock_session)

    # Mock sqlalchemy.text
    mock_text = mock.MagicMock()
    mock_text.return_value = "text_query"

    with mock.patch("sqlalchemy.text", mock_text):
        result = await session_adapter.fetch_one(
            "SELECT * FROM table WHERE id = :id", id=999
        )

        assert result is None
        mock_text.assert_called_once_with("SELECT * FROM table WHERE id = :id")
        mock_session.execute.assert_awaited_once_with("text_query", {"id": 999})


@pytest.mark.asyncio
async def test_session_adapter_fetch_all():
    """Test SessionAdapter fetch_all method."""
    mock_session = mock.AsyncMock(spec=AsyncSession)
    mock_result = mock.MagicMock()
    mock_row1 = mock.MagicMock()
    mock_row1._mapping = {"id": 1, "name": "test1"}
    mock_row2 = mock.MagicMock()
    mock_row2._mapping = {"id": 2, "name": "test2"}
    mock_result.__iter__.return_value = [mock_row1, mock_row2]
    mock_session.execute.return_value = mock_result

    session_adapter = SessionAdapter(mock_session)

    # Mock sqlalchemy.text
    mock_text = mock.MagicMock()
    mock_text.return_value = "text_query"

    with mock.patch("sqlalchemy.text", mock_text):
        result = await session_adapter.fetch_all("SELECT * FROM table")

        expected = [{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}]
        assert result == expected
        mock_text.assert_called_once_with("SELECT * FROM table")
        mock_session.execute.assert_awaited_once_with("text_query", {})


@pytest.mark.asyncio
async def test_session_adapter_add():
    """Test SessionAdapter add method."""
    mock_session = mock.AsyncMock(spec=AsyncSession)
    session_adapter = SessionAdapter(mock_session)

    obj = object()
    session_adapter.add(obj)

    mock_session.add.assert_called_once_with(obj)


@pytest.mark.asyncio
async def test_session_adapter_delete():
    """Test SessionAdapter delete method."""
    mock_session = mock.AsyncMock(spec=AsyncSession)
    session_adapter = SessionAdapter(mock_session)

    obj = object()
    session_adapter.delete(obj)

    mock_session.delete.assert_called_once_with(obj)


@pytest.mark.asyncio
async def test_session_adapter_commit():
    """Test SessionAdapter commit method."""
    mock_session = mock.AsyncMock(spec=AsyncSession)
    session_adapter = SessionAdapter(mock_session)

    await session_adapter.commit()

    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_session_adapter_rollback():
    """Test SessionAdapter rollback method."""
    mock_session = mock.AsyncMock(spec=AsyncSession)
    session_adapter = SessionAdapter(mock_session)

    await session_adapter.rollback()

    mock_session.rollback.assert_awaited_once()
