"""Tests for dynamic configuration service."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from redis.asyncio import Redis

from fs_agt_clean.core.config.dynamic_config import DynamicConfig
from fs_agt_clean.core.redis.redis_manager import RedisManager
from fs_agt_clean.core.vault.vault_client import VaultClient


@pytest.fixture
def redis_client() -> Redis:
    """Create mock Redis client."""
    client = AsyncMock(spec=Redis)
    pubsub = AsyncMock()
    pubsub.subscribe = AsyncMock()
    pubsub.unsubscribe = AsyncMock()
    pubsub.get_message = AsyncMock(return_value=None)
    client.pubsub.return_value = pubsub
    return client


@pytest.fixture
def redis_manager(redis_client: Redis) -> RedisManager:
    """Create mock Redis manager."""
    manager = MagicMock(spec=RedisManager)
    manager.client = redis_client
    return manager


@pytest.fixture
def vault_client() -> VaultClient:
    """Create mock Vault client."""
    client = AsyncMock(spec=VaultClient)
    client.read_secret = AsyncMock(return_value={})
    client.write_secret = AsyncMock(return_value=True)
    return client


@pytest.fixture
def dynamic_config(
    redis_manager: RedisManager, vault_client: VaultClient
) -> DynamicConfig:
    """Create dynamic configuration service."""
    return DynamicConfig(
        redis=redis_manager, vault_client=vault_client, refresh_interval=1
    )


@pytest.mark.asyncio
async def test_initialization(dynamic_config: DynamicConfig):
    """Test dynamic config initialization."""
    await dynamic_config.initialize()
    assert dynamic_config.initialized
    assert dynamic_config._config_cache == {}
    assert dynamic_config._config_versions == {}


@pytest.mark.asyncio
async def test_get_set_config(dynamic_config: DynamicConfig, vault_client: VaultClient):
    """Test getting and setting configuration values."""
    await dynamic_config.initialize()

    # Set config value
    test_key = "test_key"
    test_value = "test_value"
    success = await dynamic_config.set_config(test_key, test_value)
    assert success

    # Verify value was stored
    assert await dynamic_config.get_config(test_key) == test_value
    assert dynamic_config.get_config_version(test_key) == 1

    # Verify vault storage
    vault_client.write_secret.assert_called_with("config/data", {test_key: test_value})


@pytest.mark.asyncio
async def test_delete_config(dynamic_config: DynamicConfig, vault_client: VaultClient):
    """Test deleting configuration values."""
    await dynamic_config.initialize()

    # Set and then delete config
    test_key = "test_key"
    test_value = "test_value"
    await dynamic_config.set_config(test_key, test_value)
    success = await dynamic_config.delete_config(test_key)

    assert success
    assert await dynamic_config.get_config(test_key) is None
    assert dynamic_config.get_config_version(test_key) == 0


@pytest.mark.asyncio
async def test_config_refresh(dynamic_config: DynamicConfig, vault_client: VaultClient):
    """Test configuration refresh."""
    await dynamic_config.initialize()

    # Setup mock vault data
    test_data = {"key1": "value1", "key2": "value2"}
    vault_client.read_secret.return_value = test_data

    # Trigger refresh
    await dynamic_config._refresh_config()

    # Verify cache update
    assert dynamic_config._config_cache == test_data
    assert all(v == 1 for v in dynamic_config._config_versions.values())


@pytest.mark.asyncio
async def test_config_notifications(dynamic_config: DynamicConfig, redis_client: Redis):
    """Test configuration change notifications."""
    await dynamic_config.initialize()

    # Subscribe to changes
    subscriber_id = "test_subscriber"
    await dynamic_config.subscribe(subscriber_id)

    # Set config to trigger notification
    await dynamic_config.set_config("test_key", "test_value")

    # Verify notification was published
    redis_client.publish.assert_called()

    # Unsubscribe
    await dynamic_config.unsubscribe(subscriber_id)
    assert subscriber_id not in dynamic_config._subscribers


@pytest.mark.asyncio
async def test_config_refresh_loop(dynamic_config: DynamicConfig):
    """Test configuration refresh loop."""
    await dynamic_config.initialize()

    # Mock refresh method
    refresh_mock = AsyncMock()
    dynamic_config._refresh_config = refresh_mock

    # Start refresh loop
    refresh_task = asyncio.create_task(dynamic_config._config_refresh_loop())

    # Wait for a refresh cycle
    await asyncio.sleep(1.1)

    # Cancel task and verify refresh was called
    refresh_task.cancel()
    try:
        await refresh_task
    except asyncio.CancelledError:
        pass

    refresh_mock.assert_called()


@pytest.mark.asyncio
async def test_error_handling(dynamic_config: DynamicConfig, vault_client: VaultClient):
    """Test error handling during configuration operations."""
    await dynamic_config.initialize()

    # Simulate vault error
    vault_client.write_secret.side_effect = Exception("Vault error")

    # Attempt to set config
    success = await dynamic_config.set_config("test_key", "test_value")
    assert not success
    assert "test_key" not in dynamic_config._config_cache


@pytest.mark.asyncio
async def test_cleanup(dynamic_config: DynamicConfig):
    """Test service cleanup."""
    await dynamic_config.initialize()
    await dynamic_config.cleanup()

    # Verify shutdown notification was sent
    dynamic_config.redis.client.publish.assert_called()
