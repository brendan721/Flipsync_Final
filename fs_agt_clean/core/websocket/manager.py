"""
Enhanced WebSocket Connection Manager for FlipSync
=================================================

This module provides a comprehensive WebSocket connection management system
for real-time communication between clients and the FlipSync backend.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ClientConnection:
    """Represents a WebSocket client connection with metadata."""

    def __init__(
        self,
        websocket: WebSocket,
        client_id: str,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ):
        self.websocket = websocket
        self.client_id = client_id
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.connected_at = datetime.now(timezone.utc)
        self.last_ping = time.time()
        self.subscriptions: Set[str] = set()
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert connection to dictionary for logging/monitoring."""
        return {
            "client_id": self.client_id,
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "connected_at": self.connected_at.isoformat(),
            "last_ping": self.last_ping,
            "subscriptions": list(self.subscriptions),
            "metadata": self.metadata,
        }


class EnhancedWebSocketManager:
    """Enhanced WebSocket connection manager with advanced features."""

    def __init__(self):
        # Core connection storage
        self.active_connections: Dict[str, ClientConnection] = {}

        # Conversation-based grouping
        self.conversation_connections: Dict[str, Set[str]] = {}

        # UnifiedUser-based grouping
        self.user_connections: Dict[str, Set[str]] = {}

        # Subscription-based grouping
        self.subscription_connections: Dict[str, Set[str]] = {}

        # Connection statistics
        self.connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "disconnections": 0,
        }

        # Heartbeat monitoring - increased for AI processing time
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_timeout_multiplier = 4  # Allow 120 seconds for AI processing
        self.heartbeat_task: Optional[asyncio.Task] = None

        logger.info("Enhanced WebSocket Manager initialized")

    async def connect(
        self,
        websocket: WebSocket,
        client_id: str,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> ClientConnection:
        """Connect a new WebSocket client with enhanced metadata."""
        try:
            await websocket.accept()

            # Create connection object
            connection = ClientConnection(
                websocket=websocket,
                client_id=client_id,
                user_id=user_id,
                conversation_id=conversation_id,
            )

            # Store connection
            self.active_connections[client_id] = connection

            # Group by conversation
            if conversation_id:
                if conversation_id not in self.conversation_connections:
                    self.conversation_connections[conversation_id] = set()
                self.conversation_connections[conversation_id].add(client_id)

            # Group by user
            if user_id:
                if user_id not in self.user_connections:
                    self.user_connections[user_id] = set()
                self.user_connections[user_id].add(client_id)

            # Update statistics
            self.connection_stats["total_connections"] += 1
            self.connection_stats["active_connections"] = len(self.active_connections)

            # Start heartbeat monitoring if this is the first connection
            if len(self.active_connections) == 1 and not self.heartbeat_task:
                self.heartbeat_task = asyncio.create_task(self._heartbeat_monitor())

            logger.info(
                f"Client {client_id} connected. "
                f"UnifiedUser: {user_id}, Conversation: {conversation_id}. "
                f"Active connections: {len(self.active_connections)}"
            )

            # Send welcome message
            await self.send_to_client(
                client_id,
                {
                    "type": "connection_established",
                    "data": {
                        "client_id": client_id,
                        "server_time": datetime.now(timezone.utc).isoformat(),
                        "heartbeat_interval": self.heartbeat_interval,
                        "heartbeat_timeout": self.heartbeat_interval
                        * self.heartbeat_timeout_multiplier,
                    },
                },
            )

            return connection

        except Exception as e:
            logger.error(f"Error connecting client {client_id}: {e}")
            raise

    async def disconnect(self, client_id: str, reason: str = "unknown") -> bool:
        """Disconnect a WebSocket client and clean up resources."""
        if client_id not in self.active_connections:
            return False

        connection = self.active_connections[client_id]

        try:
            # Remove from conversation groups
            if connection.conversation_id:
                if connection.conversation_id in self.conversation_connections:
                    self.conversation_connections[connection.conversation_id].discard(
                        client_id
                    )
                    if not self.conversation_connections[connection.conversation_id]:
                        del self.conversation_connections[connection.conversation_id]

            # Remove from user groups
            if connection.user_id:
                if connection.user_id in self.user_connections:
                    self.user_connections[connection.user_id].discard(client_id)
                    if not self.user_connections[connection.user_id]:
                        del self.user_connections[connection.user_id]

            # Remove from subscription groups
            for subscription in connection.subscriptions:
                if subscription in self.subscription_connections:
                    self.subscription_connections[subscription].discard(client_id)
                    if not self.subscription_connections[subscription]:
                        del self.subscription_connections[subscription]

            # Remove main connection
            del self.active_connections[client_id]

            # Update statistics
            self.connection_stats["disconnections"] += 1
            self.connection_stats["active_connections"] = len(self.active_connections)

            # Stop heartbeat monitoring if no connections remain
            if not self.active_connections and self.heartbeat_task:
                self.heartbeat_task.cancel()
                self.heartbeat_task = None

            logger.info(
                f"Client {client_id} disconnected. Reason: {reason}. "
                f"Active connections: {len(self.active_connections)}"
            )

            return True

        except Exception as e:
            logger.error(f"Error disconnecting client {client_id}: {e}")
            return False

    async def send_to_client(self, client_id: str, message: Dict[str, Any]) -> bool:
        """Send a message to a specific client."""
        if client_id not in self.active_connections:
            return False

        try:
            connection = self.active_connections[client_id]
            await connection.websocket.send_text(json.dumps(message))
            self.connection_stats["messages_sent"] += 1
            return True
        except Exception as e:
            logger.error(f"Error sending message to client {client_id}: {e}")
            await self.disconnect(client_id, f"send_error: {e}")
            return False

    async def send_to_conversation(
        self, conversation_id: str, message: Dict[str, Any]
    ) -> int:
        """Send a message to all clients in a conversation."""
        if conversation_id not in self.conversation_connections:
            return 0

        sent_count = 0
        client_ids = list(self.conversation_connections[conversation_id])

        for client_id in client_ids:
            if await self.send_to_client(client_id, message):
                sent_count += 1

        return sent_count

    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> int:
        """Send a message to all connections for a specific user."""
        if user_id not in self.user_connections:
            return 0

        sent_count = 0
        client_ids = list(self.user_connections[user_id])

        for client_id in client_ids:
            if await self.send_to_client(client_id, message):
                sent_count += 1

        return sent_count

    def update_client_conversation(
        self, client_id: str, new_conversation_id: str
    ) -> bool:
        """Update a client's conversation ID registration."""
        if client_id not in self.active_connections:
            return False

        connection = self.active_connections[client_id]
        old_conversation_id = connection.conversation_id

        # Remove from old conversation group
        if old_conversation_id and old_conversation_id in self.conversation_connections:
            self.conversation_connections[old_conversation_id].discard(client_id)
            if not self.conversation_connections[old_conversation_id]:
                del self.conversation_connections[old_conversation_id]

        # Add to new conversation group
        if new_conversation_id:
            if new_conversation_id not in self.conversation_connections:
                self.conversation_connections[new_conversation_id] = set()
            self.conversation_connections[new_conversation_id].add(client_id)

        # Update connection object
        connection.conversation_id = new_conversation_id

        logger.info(
            f"Updated client {client_id} conversation from {old_conversation_id} to {new_conversation_id}"
        )
        return True

    async def broadcast(
        self, message: Dict[str, Any], exclude_clients: Optional[Set[str]] = None
    ) -> int:
        """Broadcast a message to all connected clients."""
        sent_count = 0
        exclude_clients = exclude_clients or set()

        for client_id in list(self.active_connections.keys()):
            if client_id not in exclude_clients:
                if await self.send_to_client(client_id, message):
                    sent_count += 1

        return sent_count

    async def broadcast_workflow_update(
        self,
        workflow_id: str,
        workflow_type: str,
        status: str,
        progress: float,
        participating_agents: List[str],
        current_agent: Optional[str] = None,
        error_message: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> int:
        """Broadcast workflow status update to all connected clients."""
        workflow_event = {
            "type": "workflow_progress",
            "data": {
                "workflow_id": workflow_id,
                "workflow_type": workflow_type,
                "status": status,
                "progress": progress,
                "participating_agents": participating_agents,
                "current_agent": current_agent,
                "error_message": error_message,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_id": str(uuid4()),
        }

        if conversation_id:
            # Send to specific conversation
            return await self.send_to_conversation(conversation_id, workflow_event)
        else:
            # Broadcast to all clients
            return await self.broadcast(workflow_event)

    async def broadcast_agent_coordination(
        self,
        coordination_id: str,
        coordinating_agents: List[str],
        task: str,
        progress: float,
        current_phase: str,
        agent_statuses: Optional[Dict[str, str]] = None,
        conversation_id: Optional[str] = None,
    ) -> int:
        """Broadcast agent coordination status to connected clients."""
        coordination_event = {
            "type": "agent_coordination",
            "data": {
                "coordination_id": coordination_id,
                "coordinating_agents": coordinating_agents,
                "task": task,
                "progress": progress,
                "current_phase": current_phase,
                "agent_statuses": agent_statuses or {},
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_id": str(uuid4()),
        }

        if conversation_id:
            # Send to specific conversation
            return await self.send_to_conversation(conversation_id, coordination_event)
        else:
            # Broadcast to all clients
            return await self.broadcast(coordination_event)

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get current connection statistics."""
        return {
            **self.connection_stats,
            "conversations": len(self.conversation_connections),
            "users": len(self.user_connections),
            "subscriptions": len(self.subscription_connections),
        }

    def get_active_connections(self) -> List[Dict[str, Any]]:
        """Get list of all active connections."""
        return [conn.to_dict() for conn in self.active_connections.values()]

    def get_conversation_client_count(self, conversation_id: str) -> int:
        """Get the number of clients connected to a conversation."""
        return len(self.conversation_connections.get(conversation_id, set()))

    async def _heartbeat_monitor(self):
        """Monitor client connections with periodic heartbeat."""
        while self.active_connections:
            try:
                current_time = time.time()
                disconnected_clients = []

                for client_id, connection in self.active_connections.items():
                    # Check if client hasn't responded to ping in too long
                    # Use longer timeout to allow for AI processing time
                    timeout_seconds = (
                        self.heartbeat_interval * self.heartbeat_timeout_multiplier
                    )
                    if current_time - connection.last_ping > timeout_seconds:
                        logger.warning(
                            f"Client {client_id} heartbeat timeout after {timeout_seconds}s"
                        )
                        disconnected_clients.append(client_id)
                    else:
                        # Send ping
                        try:
                            await connection.websocket.send_text(
                                json.dumps({"type": "ping", "timestamp": current_time})
                            )
                        except Exception as e:
                            logger.warning(f"Failed to ping client {client_id}: {e}")
                            disconnected_clients.append(client_id)

                # Disconnect unresponsive clients
                for client_id in disconnected_clients:
                    await self.disconnect(client_id, "heartbeat_timeout")

                await asyncio.sleep(self.heartbeat_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat monitor: {e}")
                await asyncio.sleep(5)

    async def shutdown(self):
        """Gracefully shutdown the WebSocket manager."""
        logger.info("Shutting down WebSocket manager...")

        # Disconnect all clients
        client_ids = list(self.active_connections.keys())
        for client_id in client_ids:
            await self.disconnect(client_id, "server_shutdown")

        # Cancel heartbeat monitor if running
        if hasattr(self, "_heartbeat_task") and self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        logger.info("WebSocket manager shutdown complete")


# Global manager instance
websocket_manager = EnhancedWebSocketManager()
