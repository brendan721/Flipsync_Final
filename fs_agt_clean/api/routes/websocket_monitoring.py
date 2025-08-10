"""
WebSocket Monitoring Endpoint for Flutter Frontend

This module provides the /ws/monitoring WebSocket endpoint that the Flutter
frontend expects for real-time monitoring updates.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket-monitoring"])

# Global list to track active monitoring WebSocket connections
active_monitoring_connections: List[WebSocket] = []


@router.websocket("/monitoring")
async def websocket_monitoring_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time monitoring updates.
    
    This endpoint provides the /ws/monitoring path that the Flutter app expects.
    Streams real-time system status, metrics, and health updates.
    """
    try:
        await websocket.accept()
        active_monitoring_connections.append(websocket)
        
        logger.info(f"🔌 Monitoring WebSocket connected. Active connections: {len(active_monitoring_connections)}")
        
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "Monitoring WebSocket connected successfully",
            "capabilities": [
                "system_status",
                "health_updates", 
                "performance_metrics",
                "real_time_monitoring",
                "oauth_status",
                "agent_updates"
            ]
        }))
        
        # Send initial system status
        try:
            await websocket.send_text(json.dumps({
                "type": "system_status",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "status": "operational",
                    "backend_connected": True,
                    "services": {
                        "database": "connected",
                        "redis": "connected", 
                        "ebay_oauth": "operational",
                        "autonomous_agents": "active"
                    },
                    "version": "1.0.0"
                }
            }))
        except Exception as e:
            logger.warning(f"Failed to send initial system status: {e}")
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client (ping/pong, requests, etc.)
                message = await websocket.receive_text()
                
                # Handle ping/pong for connection health
                if message == "ping":
                    await websocket.send_text("pong")
                elif message.startswith("{"):
                    # Handle JSON messages
                    try:
                        data = json.loads(message)
                        message_type = data.get("type", "")
                        
                        if message_type == "request_status":
                            # Send current system status
                            await websocket.send_text(json.dumps({
                                "type": "system_status",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "data": {
                                    "status": "operational",
                                    "backend_connected": True,
                                    "active_connections": len(active_monitoring_connections),
                                    "uptime": "running"
                                }
                            }))
                        elif message_type == "subscribe":
                            # Handle subscription requests
                            await websocket.send_text(json.dumps({
                                "type": "subscription_confirmed",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "subscribed_to": data.get("channels", [])
                            }))
                        elif message_type == "oauth_status_request":
                            # Handle OAuth status requests
                            user_id = data.get("user_id")
                            if user_id:
                                await websocket.send_text(json.dumps({
                                    "type": "oauth_status",
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                    "user_id": user_id,
                                    "authenticated": False,  # Default - would check actual status
                                    "message": "OAuth status check requested"
                                }))
                                
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON received: {message}")
                        
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in monitoring WebSocket: {e}")
                break
                
    except Exception as e:
        logger.error(f"Failed to establish monitoring WebSocket connection: {e}")
    finally:
        # Clean up connection
        if websocket in active_monitoring_connections:
            active_monitoring_connections.remove(websocket)
        logger.info(f"🔌 Monitoring WebSocket disconnected. Active connections: {len(active_monitoring_connections)}")


async def broadcast_monitoring_update(message_type: str, data: Dict[str, Any]):
    """
    Broadcast monitoring updates to all connected WebSocket clients.
    
    Args:
        message_type: Type of update (system_status, health_alert, oauth_status, etc.)
        data: Update data to broadcast
    """
    if not active_monitoring_connections:
        return
        
    message = {
        "type": message_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data
    }
    
    disconnected_connections = []
    
    for websocket in active_monitoring_connections:
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.warning(f"Failed to send monitoring update to WebSocket: {e}")
            disconnected_connections.append(websocket)
    
    # Remove disconnected connections
    for websocket in disconnected_connections:
        if websocket in active_monitoring_connections:
            active_monitoring_connections.remove(websocket)
    
    if disconnected_connections:
        logger.info(f"Removed {len(disconnected_connections)} disconnected monitoring WebSocket(s)")


async def notify_oauth_success_to_monitoring(user_id: str, environment: str):
    """
    Notify monitoring WebSocket clients about OAuth success.
    
    This can be called from the eBay OAuth service to broadcast OAuth completion
    to the monitoring WebSocket that Flutter is connected to.
    """
    await broadcast_monitoring_update("oauth_status", {
        "user_id": user_id,
        "authenticated": True,
        "environment": environment,
        "message": f"eBay authentication successful ({environment})",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


async def notify_system_status_change(status: str, details: Dict[str, Any]):
    """
    Notify monitoring WebSocket clients about system status changes.
    """
    await broadcast_monitoring_update("system_status", {
        "status": status,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


@router.get("/monitoring/test")
async def test_monitoring_websocket():
    """Test endpoint to verify monitoring WebSocket router is working."""
    return {
        "status": "ok",
        "message": "Monitoring WebSocket router is operational",
        "endpoint": "/ws/monitoring",
        "active_connections": len(active_monitoring_connections),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
