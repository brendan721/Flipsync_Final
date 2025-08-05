"""
Enhanced WebSocket Resilience System for FlipSync Agentic System
===============================================================

Provides robust WebSocket connection management with automatic reconnection,
error handling, and performance monitoring for the unified agent system.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from enum import Enum
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

logger = logging.getLogger(__name__)


class ConnectionState(str, Enum):
    """WebSocket connection states."""
    
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass
class ConnectionMetrics:
    """WebSocket connection performance metrics."""
    
    total_connections: int = 0
    successful_connections: int = 0
    failed_connections: int = 0
    total_messages_sent: int = 0
    total_messages_received: int = 0
    total_reconnections: int = 0
    average_latency_ms: float = 0.0
    last_connection_time: Optional[datetime] = None
    last_disconnection_time: Optional[datetime] = None
    uptime_percentage: float = 0.0


@dataclass
class ReconnectionConfig:
    """Configuration for WebSocket reconnection behavior."""
    
    max_attempts: int = 5
    initial_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    backoff_multiplier: float = 2.0
    jitter_enabled: bool = True
    health_check_interval_seconds: float = 30.0


class EnhancedWebSocketClient:
    """Enhanced WebSocket client with resilience features."""
    
    def __init__(
        self,
        uri: str,
        client_id: str,
        reconnection_config: Optional[ReconnectionConfig] = None,
        message_handler: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        self.uri = uri
        self.client_id = client_id
        self.reconnection_config = reconnection_config or ReconnectionConfig()
        self.message_handler = message_handler
        
        # Connection state
        self.state = ConnectionState.DISCONNECTED
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.connection_task: Optional[asyncio.Task] = None
        self.health_check_task: Optional[asyncio.Task] = None
        
        # Metrics and monitoring
        self.metrics = ConnectionMetrics()
        self.message_queue: List[Dict[str, Any]] = []
        self.pending_messages: Dict[str, Dict[str, Any]] = {}
        
        # Reconnection state
        self.reconnection_attempts = 0
        self.last_ping_time: Optional[float] = None
        self.last_pong_time: Optional[float] = None
        
        logger.info(f"Enhanced WebSocket client initialized for {client_id}")
    
    async def connect(self) -> bool:
        """Connect to WebSocket server with resilience."""
        if self.state in [ConnectionState.CONNECTED, ConnectionState.CONNECTING]:
            logger.warning(f"Client {self.client_id} already connected or connecting")
            return True
        
        self.state = ConnectionState.CONNECTING
        self.metrics.total_connections += 1
        
        try:
            logger.info(f"Connecting WebSocket client {self.client_id} to {self.uri}")
            
            # Connect with timeout
            self.websocket = await asyncio.wait_for(
                websockets.connect(
                    self.uri,
                    ping_interval=20,
                    ping_timeout=10,
                    close_timeout=10
                ),
                timeout=10.0
            )
            
            self.state = ConnectionState.CONNECTED
            self.metrics.successful_connections += 1
            self.metrics.last_connection_time = datetime.now(timezone.utc)
            self.reconnection_attempts = 0
            
            # Start message handling and health check tasks
            self.connection_task = asyncio.create_task(self._handle_messages())
            self.health_check_task = asyncio.create_task(self._health_check_loop())
            
            # Send queued messages
            await self._send_queued_messages()
            
            logger.info(f"✅ WebSocket client {self.client_id} connected successfully")
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"❌ WebSocket connection timeout for {self.client_id}")
            self.state = ConnectionState.FAILED
            self.metrics.failed_connections += 1
            return False
            
        except Exception as e:
            logger.error(f"❌ WebSocket connection failed for {self.client_id}: {e}")
            self.state = ConnectionState.FAILED
            self.metrics.failed_connections += 1
            return False
    
    async def disconnect(self) -> None:
        """Gracefully disconnect from WebSocket server."""
        logger.info(f"Disconnecting WebSocket client {self.client_id}")
        
        self.state = ConnectionState.DISCONNECTED
        self.metrics.last_disconnection_time = datetime.now(timezone.utc)
        
        # Cancel tasks
        if self.connection_task and not self.connection_task.done():
            self.connection_task.cancel()
        
        if self.health_check_task and not self.health_check_task.done():
            self.health_check_task.cancel()
        
        # Close WebSocket connection
        if self.websocket and not self.websocket.closed:
            await self.websocket.close()
        
        self.websocket = None
        logger.info(f"WebSocket client {self.client_id} disconnected")
    
    async def send_message(self, message: Dict[str, Any]) -> bool:
        """Send message with automatic queuing if disconnected."""
        message_id = message.get("message_id", f"msg_{int(time.time() * 1000)}")
        message["client_id"] = self.client_id
        message["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        if self.state != ConnectionState.CONNECTED or not self.websocket:
            # Queue message for later sending
            self.message_queue.append(message)
            logger.info(f"Message queued for {self.client_id}: {message_id}")
            return False
        
        try:
            await self.websocket.send(json.dumps(message))
            self.metrics.total_messages_sent += 1
            self.pending_messages[message_id] = message
            
            logger.debug(f"Message sent from {self.client_id}: {message_id}")
            return True
            
        except (ConnectionClosed, WebSocketException) as e:
            logger.warning(f"Failed to send message from {self.client_id}: {e}")
            # Queue message and trigger reconnection
            self.message_queue.append(message)
            asyncio.create_task(self._handle_connection_loss())
            return False
        
        except Exception as e:
            logger.error(f"Unexpected error sending message from {self.client_id}: {e}")
            return False
    
    async def _handle_messages(self) -> None:
        """Handle incoming WebSocket messages."""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    self.metrics.total_messages_received += 1
                    
                    # Handle pong responses for latency measurement
                    if data.get("type") == "pong":
                        self._handle_pong_response(data)
                        continue
                    
                    # Call message handler if provided
                    if self.message_handler:
                        await self._safe_call_handler(data)
                    
                    logger.debug(f"Message received by {self.client_id}: {data.get('type', 'unknown')}")
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received by {self.client_id}: {e}")
                
                except Exception as e:
                    logger.error(f"Error processing message for {self.client_id}: {e}")
        
        except ConnectionClosed:
            logger.warning(f"WebSocket connection closed for {self.client_id}")
            await self._handle_connection_loss()
        
        except Exception as e:
            logger.error(f"Message handling error for {self.client_id}: {e}")
            await self._handle_connection_loss()
    
    async def _health_check_loop(self) -> None:
        """Periodic health check with ping/pong."""
        while self.state == ConnectionState.CONNECTED:
            try:
                await asyncio.sleep(self.reconnection_config.health_check_interval_seconds)
                
                if self.state != ConnectionState.CONNECTED:
                    break
                
                # Send ping
                ping_message = {
                    "type": "ping",
                    "timestamp": time.time(),
                    "client_id": self.client_id
                }
                
                self.last_ping_time = time.time()
                await self.send_message(ping_message)
                
                # Check for stale connection (no pong received)
                if (self.last_pong_time and 
                    time.time() - self.last_pong_time > 60):  # 60 seconds timeout
                    logger.warning(f"Stale connection detected for {self.client_id}")
                    await self._handle_connection_loss()
                    break
                
            except Exception as e:
                logger.error(f"Health check error for {self.client_id}: {e}")
                await self._handle_connection_loss()
                break
    
    async def _handle_connection_loss(self) -> None:
        """Handle connection loss and attempt reconnection."""
        if self.state == ConnectionState.RECONNECTING:
            return  # Already reconnecting
        
        logger.warning(f"Connection lost for {self.client_id}, attempting reconnection")
        self.state = ConnectionState.RECONNECTING
        self.metrics.total_reconnections += 1
        
        # Close existing connection
        if self.websocket and not self.websocket.closed:
            await self.websocket.close()
        
        # Attempt reconnection with exponential backoff
        delay = self.reconnection_config.initial_delay_seconds
        
        while (self.reconnection_attempts < self.reconnection_config.max_attempts and
               self.state == ConnectionState.RECONNECTING):
            
            self.reconnection_attempts += 1
            logger.info(f"Reconnection attempt {self.reconnection_attempts}/{self.reconnection_config.max_attempts} for {self.client_id}")
            
            await asyncio.sleep(delay)
            
            if await self.connect():
                logger.info(f"✅ Reconnection successful for {self.client_id}")
                return
            
            # Exponential backoff with jitter
            delay = min(
                delay * self.reconnection_config.backoff_multiplier,
                self.reconnection_config.max_delay_seconds
            )
            
            if self.reconnection_config.jitter_enabled:
                import random
                delay += random.uniform(0, delay * 0.1)  # Add 10% jitter
        
        # Max attempts reached
        logger.error(f"❌ Max reconnection attempts reached for {self.client_id}")
        self.state = ConnectionState.FAILED
    
    async def _send_queued_messages(self) -> None:
        """Send all queued messages after reconnection."""
        if not self.message_queue:
            return
        
        logger.info(f"Sending {len(self.message_queue)} queued messages for {self.client_id}")
        
        messages_to_send = self.message_queue.copy()
        self.message_queue.clear()
        
        for message in messages_to_send:
            success = await self.send_message(message)
            if not success:
                break  # Stop if sending fails
    
    def _handle_pong_response(self, data: Dict[str, Any]) -> None:
        """Handle pong response for latency measurement."""
        if self.last_ping_time:
            latency_ms = (time.time() - self.last_ping_time) * 1000
            
            # Update average latency with exponential moving average
            if self.metrics.average_latency_ms == 0:
                self.metrics.average_latency_ms = latency_ms
            else:
                self.metrics.average_latency_ms = (
                    0.8 * self.metrics.average_latency_ms + 0.2 * latency_ms
                )
        
        self.last_pong_time = time.time()
    
    async def _safe_call_handler(self, data: Dict[str, Any]) -> None:
        """Safely call message handler with error handling."""
        try:
            if asyncio.iscoroutinefunction(self.message_handler):
                await self.message_handler(data)
            else:
                self.message_handler(data)
        except Exception as e:
            logger.error(f"Message handler error for {self.client_id}: {e}")
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status and metrics."""
        uptime_percentage = 0.0
        if (self.metrics.last_connection_time and 
            self.metrics.last_disconnection_time):
            total_time = (datetime.now(timezone.utc) - self.metrics.last_connection_time).total_seconds()
            if total_time > 0:
                uptime_percentage = (total_time / (total_time + 1)) * 100  # Simplified calculation
        
        return {
            "client_id": self.client_id,
            "state": self.state.value,
            "uri": self.uri,
            "reconnection_attempts": self.reconnection_attempts,
            "queued_messages": len(self.message_queue),
            "pending_messages": len(self.pending_messages),
            "metrics": {
                "total_connections": self.metrics.total_connections,
                "successful_connections": self.metrics.successful_connections,
                "failed_connections": self.metrics.failed_connections,
                "total_messages_sent": self.metrics.total_messages_sent,
                "total_messages_received": self.metrics.total_messages_received,
                "total_reconnections": self.metrics.total_reconnections,
                "average_latency_ms": round(self.metrics.average_latency_ms, 2),
                "uptime_percentage": round(uptime_percentage, 2)
            }
        }


class WebSocketResilienceManager:
    """Manager for multiple resilient WebSocket connections."""
    
    def __init__(self):
        self.clients: Dict[str, EnhancedWebSocketClient] = {}
        logger.info("WebSocket resilience manager initialized")
    
    async def create_client(
        self,
        client_id: str,
        uri: str,
        reconnection_config: Optional[ReconnectionConfig] = None,
        message_handler: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> EnhancedWebSocketClient:
        """Create and register a new resilient WebSocket client."""
        if client_id in self.clients:
            logger.warning(f"Client {client_id} already exists, returning existing client")
            return self.clients[client_id]
        
        client = EnhancedWebSocketClient(
            uri=uri,
            client_id=client_id,
            reconnection_config=reconnection_config,
            message_handler=message_handler
        )
        
        self.clients[client_id] = client
        logger.info(f"Created resilient WebSocket client: {client_id}")
        return client
    
    async def connect_client(self, client_id: str) -> bool:
        """Connect a specific client."""
        if client_id not in self.clients:
            logger.error(f"Client {client_id} not found")
            return False
        
        return await self.clients[client_id].connect()
    
    async def disconnect_client(self, client_id: str) -> None:
        """Disconnect a specific client."""
        if client_id in self.clients:
            await self.clients[client_id].disconnect()
    
    async def disconnect_all(self) -> None:
        """Disconnect all clients."""
        disconnect_tasks = [
            client.disconnect() for client in self.clients.values()
        ]
        
        if disconnect_tasks:
            await asyncio.gather(*disconnect_tasks, return_exceptions=True)
        
        logger.info("All WebSocket clients disconnected")
    
    def get_client(self, client_id: str) -> Optional[EnhancedWebSocketClient]:
        """Get a specific client."""
        return self.clients.get(client_id)
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all clients."""
        return {
            client_id: client.get_connection_status()
            for client_id, client in self.clients.items()
        }


# Global resilience manager instance
_resilience_manager: Optional[WebSocketResilienceManager] = None


def get_websocket_resilience_manager() -> WebSocketResilienceManager:
    """Get the global WebSocket resilience manager instance."""
    global _resilience_manager
    if _resilience_manager is None:
        _resilience_manager = WebSocketResilienceManager()
    return _resilience_manager
