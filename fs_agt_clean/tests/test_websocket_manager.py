"""
WebSocket Manager Tests for FlipSync Phase 1
Tests the core WebSocket functionality and manager operations.
"""

import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest

from fs_agt_clean.core.websocket.events import (
    UnifiedAgentType,
    EventType,
    SenderType,
    create_agent_status_event,
    create_message_event,
    create_typing_event,
)
from fs_agt_clean.core.websocket.manager import (
    EnhancedWebSocketManager,
    websocket_manager,
)


class TestWebSocketManager:
    """Test cases for WebSocket Manager functionality."""

    @pytest.fixture
    def manager(self):
        """Create a fresh WebSocket manager for testing."""
        return EnhancedWebSocketManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket connection."""
        mock_ws = AsyncMock()
        mock_ws.send_text = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.close = AsyncMock()
        return mock_ws

    def test_manager_initialization(self, manager):
        """Test WebSocket manager initialization."""
        assert manager is not None
        assert manager.active_connections == {}
        assert manager.conversation_connections == {}
        assert manager.user_connections == {}

    def test_get_connection_stats(self, manager):
        """Test connection statistics retrieval."""
        stats = manager.get_connection_stats()

        assert isinstance(stats, dict)
        assert "total_connections" in stats
        assert "active_connections" in stats
        assert "messages_sent" in stats
        assert "messages_received" in stats
        assert "disconnections" in stats
        assert "conversations" in stats
        assert "users" in stats
        assert "subscriptions" in stats

    @pytest.mark.asyncio
    async def test_connect_client(self, manager, mock_websocket):
        """Test connecting a WebSocket client."""
        client_id = "test_client_1"
        user_id = "test_user_1"
        conversation_id = "test_conv_1"

        connection = await manager.connect(
            mock_websocket, client_id, user_id, conversation_id
        )

        assert client_id in manager.active_connections
        assert manager.active_connections[client_id] == connection
        assert connection.user_id == user_id
        assert conversation_id in manager.conversation_connections
        assert client_id in manager.conversation_connections[conversation_id]
        assert user_id in manager.user_connections
        assert client_id in manager.user_connections[user_id]

    @pytest.mark.asyncio
    async def test_disconnect_client(self, manager, mock_websocket):
        """Test disconnecting a WebSocket client."""
        client_id = "test_client_1"
        user_id = "test_user_1"

        # Connect client first
        await manager.connect(mock_websocket, client_id, user_id)
        assert client_id in manager.active_connections

        # Disconnect client
        result = await manager.disconnect(client_id)
        assert result is True
        assert client_id not in manager.active_connections

    @pytest.mark.asyncio
    async def test_send_to_conversation(self, manager, mock_websocket):
        """Test sending message to conversation subscribers."""
        client_id = "test_client_1"
        user_id = "test_user_1"
        conversation_id = "test_conv_1"

        # Setup connection
        await manager.connect(mock_websocket, client_id, user_id, conversation_id)

        # Create test message
        message_event = create_message_event(
            conversation_id=conversation_id,
            message_id="test_msg_1",
            content="Test message",
            sender=SenderType.USER,
        )

        # Send message to conversation
        sent_count = await manager.send_to_conversation(
            conversation_id, message_event.model_dump()
        )

        # Verify message was sent
        assert sent_count == 1
        mock_websocket.send_text.assert_called()

    @pytest.mark.asyncio
    async def test_send_to_user(self, manager, mock_websocket):
        """Test sending message to specific user."""
        client_id = "test_client_1"
        user_id = "test_user_1"

        # Setup connection
        await manager.connect(mock_websocket, client_id, user_id)

        # Create test message
        test_message = {
            "type": "system_alert",
            "data": {"message": "Test alert for user", "level": "info"},
        }

        # Send to user
        sent_count = await manager.send_to_user(user_id, test_message)

        # Verify message was sent
        assert sent_count == 1
        mock_websocket.send_text.assert_called()

    @pytest.mark.asyncio
    async def test_broadcast_functionality(self, manager, mock_websocket):
        """Test broadcasting to all connected clients."""
        client_id = "test_client_1"
        user_id = "test_user_1"

        # Setup connection
        await manager.connect(mock_websocket, client_id, user_id)

        # Create agent status event
        agent_status_event = create_agent_status_event(
            agent_id="test_agent_1",
            agent_type=UnifiedAgentType.EXECUTIVE,
            status="active",
            metrics={"health_score": 95.5, "effectiveness": 87.2},
        )

        # Broadcast agent status
        sent_count = await manager.broadcast(agent_status_event.model_dump())

        # Verify status update was sent
        assert sent_count == 1
        mock_websocket.send_text.assert_called()

    @pytest.mark.asyncio
    async def test_connection_error_handling(self, manager, mock_websocket):
        """Test connection cleanup when WebSocket errors occur."""
        client_id = "test_client_1"
        user_id = "test_user_1"

        # Setup connection
        await manager.connect(mock_websocket, client_id, user_id)
        assert client_id in manager.active_connections

        # Simulate WebSocket error
        mock_websocket.send_text.side_effect = Exception("Connection lost")

        # Try to send message (should handle error gracefully)
        test_message = {"type": "test", "data": {}}
        result = await manager.send_to_client(client_id, test_message)

        # Send should fail and connection should be cleaned up
        assert result is False
        assert client_id not in manager.active_connections

    def test_singleton_manager(self):
        """Test that websocket_manager is a singleton."""
        from fs_agt_clean.core.websocket.manager import websocket_manager

        # Get manager instance multiple times
        manager1 = websocket_manager
        manager2 = websocket_manager

        # Should be the same instance
        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_latency_requirement(self, manager, mock_websocket):
        """Test that message processing meets <100ms latency requirement."""
        client_id = "test_client_1"
        user_id = "test_user_1"
        conversation_id = "test_conv_1"

        # Setup connection
        await manager.connect(mock_websocket, client_id, user_id, conversation_id)

        # Measure message processing time
        start_time = asyncio.get_event_loop().time()

        message_event = create_message_event(
            conversation_id=conversation_id,
            message_id="latency_test_msg",
            content="Latency test message",
            sender=SenderType.USER,
        )

        await manager.send_to_conversation(conversation_id, message_event.model_dump())

        end_time = asyncio.get_event_loop().time()
        latency_ms = (end_time - start_time) * 1000

        # Verify latency is under 100ms
        assert latency_ms < 100, f"Latency {latency_ms:.2f}ms exceeds 100ms requirement"


# Integration tests
class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality."""

    @pytest.mark.asyncio
    async def test_full_message_flow(self):
        """Test complete message flow from creation to delivery."""
        manager = EnhancedWebSocketManager()
        mock_ws = AsyncMock()
        mock_ws.send_text = AsyncMock()
        mock_ws.accept = AsyncMock()

        # Setup
        client_id = "integration_test_client"
        user_id = "integration_test_user"
        conversation_id = "integration_test_conv"

        await manager.connect(mock_ws, client_id, user_id, conversation_id)

        # Create and send message
        message = create_message_event(
            conversation_id=conversation_id,
            message_id="integration_msg_1",
            content="Integration test message",
            sender=SenderType.USER,
        )

        sent_count = await manager.send_to_conversation(
            conversation_id, message.model_dump()
        )

        # Verify delivery
        assert sent_count == 1
        mock_ws.send_text.assert_called()

    @pytest.mark.asyncio
    async def test_multiple_connections_broadcast(self):
        """Test broadcasting to multiple connections."""
        manager = EnhancedWebSocketManager()

        # Setup multiple connections
        connections = []
        for i in range(3):
            mock_ws = AsyncMock()
            mock_ws.send_text = AsyncMock()
            mock_ws.accept = AsyncMock()
            client_id = f"multi_client_{i}"
            user_id = f"multi_user_{i}"

            await manager.connect(mock_ws, client_id, user_id, "multi_conv")
            connections.append(mock_ws)

        # Broadcast message
        message = create_message_event(
            conversation_id="multi_conv",
            message_id="multi_msg_1",
            content="Message to multiple users",
            sender=SenderType.AGENT,
            agent_type=UnifiedAgentType.EXECUTIVE,
        )

        sent_count = await manager.send_to_conversation(
            "multi_conv", message.model_dump()
        )

        # Verify all connections received the message
        assert sent_count == 3
        for mock_ws in connections:
            mock_ws.send_text.assert_called()
