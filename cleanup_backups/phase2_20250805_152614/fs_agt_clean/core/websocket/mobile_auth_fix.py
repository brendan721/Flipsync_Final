"""
WebSocket Authentication Fix for Mobile App Development
FIXED: Proper JWT validation with secure fallback
"""

import logging
import os
from typing import Optional

import jwt
from fastapi import WebSocket

logger = logging.getLogger(__name__)


def _get_jwt_secret() -> str:
    """Get JWT secret using consistent logic with other auth components."""
    environment = os.getenv("ENVIRONMENT", "").lower()
    if environment in ("development", "dev", "test"):
        return "development-jwt-secret-not-for-production-use"

    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise ValueError("JWT_SECRET environment variable must be set for production")
    return secret


def _validate_jwt_token(token: str) -> bool:
    """Validate JWT token using consistent secret logic."""
    try:
        secret = _get_jwt_secret()
        jwt.decode(token, secret, algorithms=["HS256"])
        return True
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired")
        return False
    except jwt.InvalidTokenError as e:
        logger.warning("Invalid JWT token: %s", e)
        return False
    except Exception as e:
        logger.error("JWT validation error: %s", e)
        return False


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

        # FIXED: Always validate JWT token when provided, regardless of environment
        if token:
            if _validate_jwt_token(token):
                logger.info("WebSocket connection authenticated with valid JWT token")
                await websocket.accept()
                return True

            logger.warning("WebSocket connection rejected: Invalid JWT token")
            await websocket.close(code=1008, reason="Invalid authentication token")
            return False

        # SECURE: In development, allow connections from development origins without token
        # This provides a fallback for development but maintains security in production
        environment = os.getenv("ENVIRONMENT", "development").lower()
        if environment in ("development", "dev", "test") and is_development_origin(
            origin
        ):
            logger.info(
                "WebSocket connection accepted: Development environment with valid origin"
            )
            await websocket.accept()
            return True

        # Reject connection without token in production or invalid origin
        logger.warning(
            "WebSocket connection rejected: No token provided (env: %s, origin: %s)",
            environment,
            origin,
        )
        await websocket.close(code=1008, reason="Authentication required")
        return False

    except (jwt.PyJWTError, ValueError) as e:
        logger.error("WebSocket authentication error: %s", e)
        await websocket.close(code=1011, reason="Authentication error")
        return False
    except Exception as e:
        logger.error("WebSocket connection error: %s", e)
        await websocket.close(code=1011, reason="Internal server error")
        return False
