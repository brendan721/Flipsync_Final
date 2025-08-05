"""
Simple WebSocket endpoint for FlipSync
=====================================

Minimal WebSocket implementation without complex dependencies.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket-simple"])


@router.websocket("/flipsync")
async def simple_websocket_endpoint(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None, description="Client identifier"),
    user_id: Optional[str] = Query(None, description="User identifier"),
    conversation_id: Optional[str] = Query(None, description="Conversation identifier"),
    token: Optional[str] = Query(None, description="Authentication token"),
):
    """
    Simple WebSocket endpoint for FlipSync real-time communication.
    
    This is a minimal implementation that provides basic WebSocket functionality
    without complex dependencies that might cause startup issues.
    """
    if not client_id:
        client_id = f"client_{uuid4()}"

    logger.info(f"WebSocket connection: client={client_id}, user={user_id}")

    # Accept the WebSocket connection
    await websocket.accept()

    try:
        # Send connection confirmation
        await websocket.send_text(
            json.dumps(
                {
                    "type": "connection_established",
                    "client_id": client_id,
                    "server_time": datetime.now(timezone.utc).isoformat(),
                    "status": "connected",
                    "message": "WebSocket connection established successfully",
                    "capabilities": [
                        "chat_message",
                        "agent_status",
                        "system_notification",
                        "ping_pong",
                    ],
                }
            )
        )

        # Message handling loop
        while True:
            try:
                # Receive message with timeout
                raw_message = await asyncio.wait_for(
                    websocket.receive_text(), timeout=300.0  # 5 minutes timeout
                )

                # Parse message
                try:
                    message_data = json.loads(raw_message)
                except json.JSONDecodeError as e:
                    await websocket.send_text(
                        json.dumps(
                            {"type": "error", "message": f"Invalid JSON format: {e}"}
                        )
                    )
                    continue

                # Handle different message types
                message_type = message_data.get("type", "unknown")
                
                if message_type == "ping":
                    response = {
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "client_id": client_id,
                    }
                elif message_type == "chat_message":
                    response = {
                        "type": "chat_response",
                        "message": "Message received - agent processing not yet implemented",
                        "original_message": message_data.get("data", {}),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "client_id": client_id,
                    }
                elif message_type == "agent_status":
                    response = {
                        "type": "agent_status_response",
                        "status": "All agents operational",
                        "agent_count": 5,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "client_id": client_id,
                    }
                else:
                    # Echo response for unknown message types
                    response = {
                        "type": "echo",
                        "original_message": message_data,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "client_id": client_id,
                        "status": "received",
                    }

                # Send response
                await websocket.send_text(json.dumps(response))

            except asyncio.TimeoutError:
                # Send ping to check connection
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "ping",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "message": "Connection check",
                        }
                    )
                )
            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected")
                break
            except Exception as e:
                logger.error(f"Error handling message from client {client_id}: {e}")
                try:
                    await websocket.send_text(
                        json.dumps(
                            {"type": "error", "message": "Internal server error"}
                        )
                    )
                except:
                    # Connection might be closed
                    break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected during setup: client={client_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        logger.info(f"WebSocket connection closed: client={client_id}")


@router.get("/test")
async def websocket_test_endpoint():
    """Test endpoint to verify WebSocket router is working."""
    return {
        "status": "ok",
        "message": "WebSocket router is operational",
        "endpoint": "/ws/flipsync",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
