"""
WebSocket Authentication Fix for Mobile App Development
"""

from typing import Optional
from fastapi import WebSocket
import os


def is_development_origin(origin: Optional[str]) -> bool:
    """Check if the origin is from a development environment."""
    if not origin:
        return False

    development_origins = [
        "http://localhost:3000",
        "http://localhost:8081",
        "http://127.0.0.1:3000",
        "http://10.0.2.2:3000",
    ]

    return origin in development_origins


async def accept_websocket_with_mobile_support(
    websocket: WebSocket, token: Optional[str] = None
) -> bool:
    """Accept WebSocket connection with mobile app support."""
    try:
        # Get origin from headers
        origin = websocket.headers.get("origin")

        # In development, allow mobile app connections without strict JWT validation
        if os.getenv("ENVIRONMENT", "development") == "development":
            if is_development_origin(origin):
                await websocket.accept()
                return True

        # For production or non-mobile origins, validate JWT
        if token:
            # TODO: Add JWT validation logic here
            await websocket.accept()
            return True
        else:
            # Reject connection without token in production
            await websocket.close(code=1008, reason="Authentication required")
            return False

    except Exception as e:
        print(f"WebSocket authentication error: {e}")
        await websocket.close(code=1011, reason="Internal server error")
        return False
