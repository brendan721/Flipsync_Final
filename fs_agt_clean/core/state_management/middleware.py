"""
State Management Middleware for FastAPI.

This module provides middleware for state management in FastAPI applications.
"""

import logging
from typing import Callable, Dict, Optional

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from fs_agt_clean.core.state_management.state_manager import StateManager

logger = logging.getLogger(__name__)


class StateMiddleware(BaseHTTPMiddleware):
    """Middleware for state management in FastAPI applications."""

    def __init__(
        self,
        app: ASGIApp,
        state_manager: Optional[StateManager] = None,
        exclude_paths: Optional[list] = None,
    ):
        """
        Initialize the state middleware.

        Args:
            app: ASGI application
            state_manager: State manager instance
            exclude_paths: List of paths to exclude from state management
        """
        super().__init__(app)
        self.state_manager = state_manager or StateManager()
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/docs", "/redoc"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and response.

        Args:
            request: HTTP request
            call_next: Next middleware in the chain

        Returns:
            HTTP response
        """
        # Skip state management for excluded paths
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)

        # Add state manager to request state
        request.state.state_manager = self.state_manager

        # Process request
        response = await call_next(request)

        return response


def cleanup_state():
    """Clean up state management resources."""
    # This function is called when the application shuts down
    logger.info("Cleaning up state management resources")


def setup_state_middleware(
    app: FastAPI,
    state_manager: Optional[StateManager] = None,
    exclude_paths: Optional[list] = None,
) -> None:
    """
    Set up state management middleware.

    Args:
        app: FastAPI application
        state_manager: State manager instance
        exclude_paths: List of paths to exclude from state management
    """
    # Add middleware
    app.add_middleware(
        StateMiddleware,
        state_manager=state_manager,
        exclude_paths=exclude_paths,
    )

    # Add shutdown event handler
    app.add_event_handler("shutdown", cleanup_state)
