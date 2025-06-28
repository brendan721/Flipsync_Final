"""
WebSocket Routes for FlipSync Real-time Communication
====================================================

This module provides WebSocket endpoints for real-time communication
between clients and the FlipSync backend.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Path, Query, WebSocket, WebSocketDisconnect

from fs_agt_clean.core.websocket.events import EventType, create_system_alert_event
from fs_agt_clean.core.websocket.manager import websocket_manager

logger = logging.getLogger(__name__)


def get_websocket_handler():
    """Get the current WebSocket handler instance."""
    from fs_agt_clean.core.websocket.handlers import websocket_handler

    return websocket_handler


router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("")
async def websocket_basic_endpoint(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None, description="Client ID"),
    user_id: Optional[str] = Query(None, description="UnifiedUser ID"),
):
    """
    Basic WebSocket endpoint for testing and simple communication.

    This endpoint provides:
    - Simple WebSocket connection without authentication
    - Basic message echo functionality
    - Testing and development support
    """
    if not client_id:
        client_id = f"test_client_{uuid.uuid4()}"

    logger.info(f"Basic WebSocket connection: client={client_id}, user={user_id}")

    try:
        await websocket.accept()

        # Send welcome message
        await websocket.send_text(
            json.dumps(
                {
                    "type": "connection_established",
                    "client_id": client_id,
                    "message": "WebSocket connection established",
                    "timestamp": datetime.now().isoformat(),
                }
            )
        )

        # Message handling loop
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()
                message = json.loads(data)

                logger.info(f"Received message from {client_id}: {message}")

                # Echo message back with processing info
                response = {
                    "type": "message_response",
                    "original_message": message,
                    "client_id": client_id,
                    "processed_at": datetime.now().isoformat(),
                    "status": "received_and_processed",
                }

                await websocket.send_text(json.dumps(response))

            except WebSocketDisconnect:
                logger.info(f"Basic WebSocket disconnected: {client_id}")
                break
            except Exception as e:
                logger.error(f"Error processing message from {client_id}: {e}")
                error_response = {
                    "type": "error",
                    "error": str(e),
                    "client_id": client_id,
                    "timestamp": datetime.now().isoformat(),
                }
                await websocket.send_text(json.dumps(error_response))

    except Exception as e:
        logger.error(f"Basic WebSocket error for {client_id}: {e}")


@router.websocket("/chat/{conversation_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    conversation_id: str = Path(..., description="Conversation ID"),
    client_id: Optional[str] = Query(None, description="Client ID"),
    user_id: Optional[str] = Query(None, description="UnifiedUser ID"),
    token: Optional[str] = Query(None, description="Authentication token"),
):
    """
    WebSocket endpoint for real-time chat communication.

    This endpoint handles:
    - Real-time message exchange
    - Typing indicators
    - Message reactions
    - UnifiedAgent responses

    Message Protocol:
    {
        "type": "message|typing|message_reaction",
        "conversation_id": "uuid",
        "data": { ... }
    }
    """
    # Validate authentication token
    if not token:
        logger.warning("🔒 WebSocket connection rejected: No token provided")
        await websocket.close(code=1008)
        return

    logger.info(f"🔑 WebSocket token received: {token[:50]}...")

    # Validate JWT token
    try:
        import jwt
        import os

        # Use JWT secret from environment variable
        secret = os.getenv(
            "JWT_SECRET", "development-jwt-secret-not-for-production-use"
        )
        logger.info(f"🔐 Using JWT secret: {secret[:20]}...")

        payload = jwt.decode(
            token, secret, algorithms=["HS256"], options={"verify_exp": False}
        )
        authenticated_user_id = payload.get("sub", "unknown")
        logger.info(f"✅ Token validated for user: {authenticated_user_id}")
        logger.info(f"🔍 Token payload: {payload}")

        # Use authenticated user ID if user_id not provided
        if not user_id:
            user_id = authenticated_user_id

    except Exception as jwt_error:
        logger.error(f"❌ JWT validation failed: {jwt_error}")
        logger.error(f"🔍 Token that failed: {token}")
        await websocket.close(code=1008)
        return

    # Generate client ID if not provided
    if not client_id:
        client_id = f"client_{uuid.uuid4()}"

    logger.info(
        f"WebSocket connection attempt: client={client_id}, conversation={conversation_id}, user={user_id}"
    )

    try:
        # Handle connection and await the message handling task
        # This keeps the WebSocket connection alive by waiting for the message loop
        handler = get_websocket_handler()
        await handler.handle_client_connection(
            websocket=websocket,
            client_id=client_id,
            conversation_id=conversation_id,
            user_id=user_id,
        )

        logger.info(f"WebSocket connection closed normally: {client_id}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {client_id}")
        await websocket_manager.disconnect(client_id, "websocket_disconnect")

    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        try:
            await websocket_manager.disconnect(client_id, f"error: {e}")
        except:
            pass


@router.websocket("/agent/{agent_id}")
async def websocket_agent_endpoint(
    websocket: WebSocket,
    agent_id: str = Path(..., description="UnifiedAgent ID"),
    agent_type: Optional[str] = Query(None, description="UnifiedAgent type"),
):
    """
    WebSocket endpoint for agent communication.

    This endpoint handles:
    - UnifiedAgent status updates
    - UnifiedAgent decision notifications
    - Task progress updates
    - Inter-agent communication
    """
    client_id = f"agent_{agent_id}"

    logger.info(
        f"UnifiedAgent WebSocket connection: agent={agent_id}, type={agent_type}"
    )

    try:
        # Handle agent connection and await the message handling task
        handler = get_websocket_handler()
        await handler.handle_client_connection(
            websocket=websocket,
            client_id=client_id,
            user_id=agent_id,  # Use agent_id as user_id for agents
            conversation_id=None,
            metadata={"is_agent": True, "agent_id": agent_id, "agent_type": agent_type},
        )

        logger.info(f"UnifiedAgent WebSocket connection closed normally: {agent_id}")

    except WebSocketDisconnect:
        logger.info(f"UnifiedAgent WebSocket disconnected: {agent_id}")
        await websocket_manager.disconnect(client_id, "agent_disconnect")

    except Exception as e:
        logger.error(f"UnifiedAgent WebSocket error for {agent_id}: {e}")
        try:
            await websocket_manager.disconnect(client_id, f"agent_error: {e}")
        except:
            pass


@router.websocket("/system")
async def websocket_system_endpoint(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None, description="Client ID"),
    user_id: Optional[str] = Query(None, description="UnifiedUser ID"),
):
    """
    WebSocket endpoint for system-wide notifications.

    This endpoint handles:
    - System alerts
    - Global notifications
    - System status updates
    - Administrative messages
    """
    if not client_id:
        client_id = f"system_{uuid.uuid4()}"

    logger.info(f"System WebSocket connection: client={client_id}, user={user_id}")

    try:
        # Handle system connection and await the message handling task
        handler = get_websocket_handler()
        await handler.handle_client_connection(
            websocket=websocket,
            client_id=client_id,
            user_id=user_id,
            conversation_id=None,
            metadata={"is_system": True, "subscription_type": "system_notifications"},
        )

        logger.info(f"System WebSocket connection closed normally: {client_id}")

    except WebSocketDisconnect:
        logger.info(f"System WebSocket disconnected: {client_id}")
        await websocket_manager.disconnect(client_id, "system_disconnect")

    except Exception as e:
        logger.error(f"System WebSocket error for {client_id}: {e}")
        try:
            await websocket_manager.disconnect(client_id, f"system_error: {e}")
        except:
            pass


@router.get("/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    return websocket_manager.get_connection_stats()


@router.get("/connections")
async def get_active_connections():
    """Get list of active WebSocket connections."""
    return {
        "connections": websocket_manager.get_active_connections(),
        "stats": websocket_manager.get_connection_stats(),
    }


@router.get("/conversations/{conversation_id}/clients")
async def get_conversation_clients(conversation_id: str):
    """Get clients connected to a specific conversation."""
    clients = websocket_manager.get_conversation_clients(conversation_id)
    return {
        "conversation_id": conversation_id,
        "client_count": len(clients),
        "clients": clients,
    }


@router.post("/broadcast/system")
async def broadcast_system_message(
    message: str, severity: str = "info", title: str = "System Notification"
):
    """Broadcast a system message to all connected clients."""
    try:
        # Create system alert event
        alert_event = create_system_alert_event(
            severity=severity, title=title, message=message, source="admin_api"
        )

        # Broadcast to all connections
        sent_count = await websocket_manager.broadcast(alert_event.dict())

        return {
            "success": True,
            "message": "System message broadcasted",
            "recipients": sent_count,
        }

    except Exception as e:
        logger.error(f"Error broadcasting system message: {e}")
        return {"success": False, "error": str(e)}


@router.post("/conversations/{conversation_id}/broadcast")
async def broadcast_to_conversation(
    conversation_id: str, message: str, message_type: str = "system_notification"
):
    """Broadcast a message to all clients in a conversation."""
    try:
        broadcast_message = {
            "type": message_type,
            "conversation_id": conversation_id,
            "data": {"message": message, "source": "admin_api"},
        }

        sent_count = await websocket_manager.send_to_conversation(
            conversation_id, broadcast_message
        )

        return {
            "success": True,
            "message": "Message broadcasted to conversation",
            "conversation_id": conversation_id,
            "recipients": sent_count,
        }

    except Exception as e:
        logger.error(f"Error broadcasting to conversation {conversation_id}: {e}")
        return {"success": False, "error": str(e)}


@router.get("/test")
async def websocket_test_page():
    """Serve a simple WebSocket test page for development."""
    # Test page moved to archive - use external WebSocket testing tools
    return {
        "message": "WebSocket test page moved to archive",
        "endpoints": {
            "chat": "/api/v1/ws/chat/{conversation_id}",
            "agent": "/api/v1/ws/agent/{agent_id}",
            "system": "/api/v1/ws/system",
        },
        "note": "Use external WebSocket testing tools or the test scripts in the repository",
    }
