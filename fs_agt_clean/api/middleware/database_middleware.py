"""
Database Security Middleware

This module provides middleware for FastAPI to handle database security, including:
1. Setting current user context for row-level security
2. Collecting client information for audit logging
3. Managing database connection security
"""

import logging
import time
from typing import Callable, Dict, Optional

from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from fs_agt_clean.core.security.access_control import (
    UnifiedUserSession,
    get_current_user_session,
)
from fs_agt_clean.core.utils.logging import get_logger
from fs_agt_clean.database.connection_manager import db_manager

logger = get_logger(__name__)


class DatabaseSecurityMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for database security.

    This middleware sets the current user context for row-level security,
    collects client information for audit logging, and manages database
    connection security.
    """

    def __init__(
        self,
        app: FastAPI,
        get_user_session: Callable = get_current_user_session,
    ):
        """
        Initialize the middleware.

        Args:
            app: FastAPI application
            get_user_session: Function to get the current user session
        """
        super().__init__(app)
        self.get_user_session = get_user_session
        logger.info("Database security middleware initialized")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and set up database security context.

        Args:
            request: The request
            call_next: The next middleware or route handler

        Returns:
            The response
        """
        # Get client information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        session_id = request.cookies.get("session_id", "unknown")

        # Get user session
        user_session = None
        try:
            user_session = await self.get_user_session(request)
        except Exception as e:
            logger.warning("Error getting user session: %s", e)

        # Set up database security context
        async with db_manager.session() as session:
            try:
                # Set current user ID
                if user_session and user_session.user_id:
                    await session.execute(
                        text("SET LOCAL app.current_user_id = :user_id"),
                        {"user_id": user_session.user_id},
                    )
                else:
                    await session.execute(
                        text("SET LOCAL app.current_user_id = 'anonymous'")
                    )

                # Set client information
                await session.execute(
                    text("SET LOCAL app.client_ip = :client_ip"),
                    {"client_ip": client_ip},
                )
                await session.execute(
                    text("SET LOCAL app.user_agent = :user_agent"),
                    {"user_agent": user_agent},
                )
                await session.execute(
                    text("SET LOCAL app.session_id = :session_id"),
                    {"session_id": session_id},
                )

                # Commit the transaction to apply settings
                await session.commit()
            except Exception as e:
                logger.error("Error setting database security context: %s", e)
                await session.rollback()

        # Process the request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Log request for sensitive operations
        path = request.url.path
        method = request.method
        if any(
            sensitive in path
            for sensitive in ["/users", "/orders", "/payments", "/auth"]
        ):
            logger.info(
                "Sensitive operation: %s %s (%.3f sec) - UnifiedUser: %s, IP: %s",
                method,
                path,
                process_time,
                user_session.user_id if user_session else "anonymous",
                client_ip,
            )

        return response


# Dependency for getting a secure database session with user context
async def get_secure_db_session(
    request: Request,
    user_session: UnifiedUserSession = Depends(get_current_user_session),
) -> AsyncSession:
    """
    Get a secure database session with user context.

    Args:
        request: The request
        user_session: The user session

    Returns:
        A database session with security context
    """
    async with db_manager.session() as session:
        try:
            # Set current user ID
            if user_session and user_session.user_id:
                await session.execute(
                    text("SET LOCAL app.current_user_id = :user_id"),
                    {"user_id": user_session.user_id},
                )
            else:
                await session.execute(
                    text("SET LOCAL app.current_user_id = 'anonymous'")
                )

            # Set client information
            client_ip = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "unknown")
            session_id = request.cookies.get("session_id", "unknown")

            await session.execute(
                text("SET LOCAL app.client_ip = :client_ip"),
                {"client_ip": client_ip},
            )
            await session.execute(
                text("SET LOCAL app.user_agent = :user_agent"),
                {"user_agent": user_agent},
            )
            await session.execute(
                text("SET LOCAL app.session_id = :session_id"),
                {"session_id": session_id},
            )

            yield session
        finally:
            await session.close()
