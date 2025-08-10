"""
WebSocket handler for eBay OAuth real-time status updates.

This module provides WebSocket endpoints for real-time OAuth status updates,
allowing the Flutter frontend to receive immediate notifications about
authentication status changes.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set, Optional

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter

from fs_agt_clean.api.models.ebay_oauth_models import WebSocketOAuthStatusMessage
from fs_agt_clean.services.marketplace.ebay_oauth_service_v2 import (
    get_ebay_oauth_service,
)
from fs_agt_clean.services.marketplace.ebay_token_lifecycle_manager import (
    get_token_lifecycle_manager,
    TokenEventType,
)

logger = logging.getLogger(__name__)

# WebSocket router
ws_router = APIRouter()

# Active WebSocket connections by user_id
active_connections: Dict[str, Set[WebSocket]] = {}


class EbayOAuthWebSocketManager:
    """Manager for eBay OAuth WebSocket connections."""

    def __init__(self):
        self.connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a WebSocket for a user."""
        await websocket.accept()

        if user_id not in self.connections:
            self.connections[user_id] = set()

        self.connections[user_id].add(websocket)
        logger.info(f"WebSocket connected for user {user_id}")

        # Send initial status
        await self.send_status_update(user_id)

    def disconnect(self, websocket: WebSocket, user_id: str):
        """Disconnect a WebSocket for a user."""
        if user_id in self.connections:
            self.connections[user_id].discard(websocket)

            # Clean up empty sets
            if not self.connections[user_id]:
                del self.connections[user_id]

        logger.info(f"WebSocket disconnected for user {user_id}")

    async def send_status_update(self, user_id: str):
        """Send OAuth status update to all connections for a user."""
        if user_id not in self.connections:
            return

        try:
            # Get current OAuth status
            oauth_service = get_ebay_oauth_service()
            status_data = await oauth_service.get_auth_status(user_id)

            # Create WebSocket message
            message = WebSocketOAuthStatusMessage(
                type="oauth_status",
                user_id=user_id,
                authenticated=status_data["authenticated"],
                environment=status_data.get("environment"),
                expires_at=(
                    datetime.fromisoformat(status_data["expires_at"])
                    if status_data.get("expires_at")
                    else None
                ),
                message=status_data["message"],
            )

            # Send to all connections for this user
            disconnected_websockets = []
            for websocket in self.connections[user_id].copy():
                try:
                    await websocket.send_text(message.json())
                except Exception as e:
                    logger.warning(f"Failed to send message to WebSocket: {e}")
                    disconnected_websockets.append(websocket)

            # Clean up disconnected WebSockets
            for websocket in disconnected_websockets:
                self.disconnect(websocket, user_id)

        except Exception as e:
            logger.error(f"Failed to send status update for user {user_id}: {e}")

    async def broadcast_status_update(
        self, user_id: str, message: str, authenticated: bool = None
    ):
        """Broadcast a custom status update to all connections for a user."""
        logger.info(f"📢 Broadcasting status update for user {user_id}: {message}")

        if user_id not in self.connections:
            logger.warning(
                f"⚠️ User {user_id} not found in connections during broadcast"
            )
            return

        if not self.connections[user_id]:
            logger.warning(
                f"⚠️ No active connections for user {user_id} during broadcast"
            )
            return

        try:
            # Create custom message
            custom_message = WebSocketOAuthStatusMessage(
                type="oauth_status",
                user_id=user_id,
                authenticated=authenticated if authenticated is not None else False,
                message=message,
            )

            logger.info(f"📝 Created WebSocket message: {custom_message.json()}")
            logger.info(
                f"🔗 Sending to {len(self.connections[user_id])} WebSocket connection(s)"
            )

            # Send to all connections for this user
            disconnected_websockets = []
            sent_count = 0

            for websocket in self.connections[user_id].copy():
                try:
                    await websocket.send_text(custom_message.json())
                    sent_count += 1
                    logger.debug(
                        f"✅ Message sent to WebSocket connection {sent_count}"
                    )
                except Exception as e:
                    logger.warning(
                        f"❌ Failed to send broadcast message to WebSocket: {e}"
                    )
                    disconnected_websockets.append(websocket)

            logger.info(
                f"📊 Broadcast complete: {sent_count} successful, {len(disconnected_websockets)} failed"
            )

            # Clean up disconnected WebSockets
            for websocket in disconnected_websockets:
                self.disconnect(websocket, user_id)

        except Exception as e:
            logger.error(
                f"❌ Failed to broadcast status update for user {user_id}: {e}"
            )
            logger.exception("Full broadcast exception details:")

    async def broadcast_token_event(
        self,
        user_id: str,
        event_type: TokenEventType,
        success: bool,
        message: str,
        metadata: Optional[Dict] = None,
    ):
        """Broadcast a token lifecycle event to all connections for a user."""
        if user_id not in self.connections:
            return

        try:
            # Create token event message
            event_message = {
                "type": "token_event",
                "user_id": user_id,
                "event_type": event_type.value,
                "success": success,
                "message": message,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Send to all connections for this user
            disconnected_websockets = []
            for websocket in self.connections[user_id].copy():
                try:
                    await websocket.send_text(json.dumps(event_message))
                except Exception as e:
                    logger.warning(f"Failed to send token event to WebSocket: {e}")
                    disconnected_websockets.append(websocket)

            # Clean up disconnected WebSockets
            for websocket in disconnected_websockets:
                self.disconnect(websocket, user_id)

            logger.info(
                f"📡 Token event broadcasted: {event_type.value} for user {user_id}"
            )

        except Exception as e:
            logger.error(f"Failed to broadcast token event for user {user_id}: {e}")


# Global WebSocket manager instance
ws_manager = EbayOAuthWebSocketManager()


@ws_router.websocket("/ws/ebay/oauth/{user_id}")
async def websocket_ebay_oauth_status(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for eBay OAuth status updates.

    This endpoint provides real-time updates about eBay OAuth authentication
    status for a specific user. The Flutter frontend can connect to this
    endpoint to receive immediate notifications about authentication changes.

    Message Format:
    {
        "type": "oauth_status",
        "user_id": "testuser",
        "authenticated": true,
        "environment": "sandbox",
        "expires_at": "2024-08-06T20:00:00Z",
        "message": "Authentication valid",
        "timestamp": "2024-08-06T18:00:00Z"
    }
    """
    await ws_manager.connect(websocket, user_id)

    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                # Handle different message types
                if message.get("type") == "ping":
                    # Respond to ping with pong
                    await websocket.send_text(
                        json.dumps(
                            {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
                        )
                    )

                elif message.get("type") == "status_request":
                    # Send current status
                    await ws_manager.send_status_update(user_id)

                else:
                    logger.warning(
                        f"Unknown WebSocket message type: {message.get('type')}"
                    )

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from WebSocket: {data}")

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        ws_manager.disconnect(websocket, user_id)


# Helper functions for triggering WebSocket updates from other parts of the application


async def notify_oauth_success(user_id: str, environment: str):
    """Notify WebSocket clients of successful OAuth authentication."""
    logger.info(
        f"🔔 Starting OAuth success notification for user {user_id} ({environment})"
    )

    try:
        # Check if user has active WebSocket connections
        if user_id not in ws_manager.connections or not ws_manager.connections[user_id]:
            logger.warning(f"⚠️ No active WebSocket connections for user {user_id}")
            return

        logger.info(
            f"📡 Found {len(ws_manager.connections[user_id])} active WebSocket connection(s) for user {user_id}"
        )

        await ws_manager.broadcast_status_update(
            user_id=user_id,
            message=f"eBay authentication successful ({environment})",
            authenticated=True,
        )

        logger.info(
            f"✅ OAuth success notification sent successfully for user {user_id}"
        )

        # Also notify the monitoring WebSocket for system-wide updates
        try:
            from fs_agt_clean.api.routes.websocket_monitoring import (
                notify_oauth_success_to_monitoring,
            )

            await notify_oauth_success_to_monitoring(user_id, environment)
            logger.info(
                f"📡 OAuth success also sent to monitoring WebSocket for user {user_id}"
            )
        except Exception as monitoring_error:
            logger.warning(
                f"Failed to notify monitoring WebSocket for user {user_id}: {monitoring_error}"
            )

    except Exception as e:
        logger.error(
            f"❌ Failed to send OAuth success notification for user {user_id}: {e}"
        )
        logger.exception("Full exception details:")
        raise


async def notify_oauth_failure(user_id: str, error_message: str):
    """Notify WebSocket clients of OAuth authentication failure."""
    await ws_manager.broadcast_status_update(
        user_id=user_id,
        message=f"eBay authentication failed: {error_message}",
        authenticated=False,
    )


async def notify_oauth_revoked(user_id: str):
    """Notify WebSocket clients that OAuth tokens were revoked."""
    await ws_manager.broadcast_status_update(
        user_id=user_id, message="eBay authentication revoked", authenticated=False
    )


async def notify_token_refresh(user_id: str):
    """Notify WebSocket clients that tokens were refreshed."""
    await ws_manager.send_status_update(user_id)
    await ws_manager.broadcast_token_event(
        user_id=user_id,
        event_type=TokenEventType.REFRESH_SUCCESS,
        success=True,
        message="Access token refreshed successfully",
    )


async def notify_proactive_refresh(user_id: str, environment: str):
    """Notify WebSocket clients of proactive token refresh."""
    await ws_manager.broadcast_token_event(
        user_id=user_id,
        event_type=TokenEventType.PROACTIVE_REFRESH,
        success=True,
        message=f"Token proactively refreshed ({environment})",
        metadata={"environment": environment},
    )


async def notify_refresh_failure(user_id: str, error_message: str):
    """Notify WebSocket clients of token refresh failure."""
    await ws_manager.broadcast_token_event(
        user_id=user_id,
        event_type=TokenEventType.REFRESH_FAILED,
        success=False,
        message=f"Token refresh failed: {error_message}",
        metadata={"error": error_message},
    )


async def notify_refresh_token_expiring(user_id: str, days_remaining: int):
    """Notify WebSocket clients that refresh token is expiring."""
    await ws_manager.broadcast_token_event(
        user_id=user_id,
        event_type=TokenEventType.REFRESH_TOKEN_RENEWED,
        success=False,  # Requires user action
        message=f"Refresh token expires in {days_remaining} days - re-authorization needed",
        metadata={"days_remaining": days_remaining},
    )


# Background task for periodic status updates
async def periodic_status_updates():
    """Background task to send periodic status updates to all connected clients."""
    while True:
        try:
            # Send status updates to all connected users
            for user_id in list(ws_manager.connections.keys()):
                await ws_manager.send_status_update(user_id)

            # Wait 5 minutes before next update
            await asyncio.sleep(300)

        except Exception as e:
            logger.error(f"Error in periodic status updates: {e}")
            await asyncio.sleep(60)  # Wait 1 minute on error


# Start background task when module is imported
# Note: This should be started by the main application
# asyncio.create_task(periodic_status_updates())
