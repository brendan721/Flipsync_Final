"""
WebSocket API routes package for FlipSync.

This package contains WebSocket-related API routes and endpoints.
"""

# Import the basic websocket router with working authentication
from fs_agt_clean.api.routes.websocket_basic import router

__all__ = ["router"]
