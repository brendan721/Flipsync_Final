"""
Authentication middleware for protecting API endpoints.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Union

from fastapi import HTTPException, Request, Response, status
from starlette.authentication import AuthCredentials, AuthenticationBackend, SimpleUnifiedUser
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from fs_agt_clean.api.routes.agents import decode_token
from fs_agt_clean.core.auth.auth_service import AuthService
from fs_agt_clean.core.security.token_rotation import TokenRotationService


class AuthMixin:
    """Mixin providing authentication functionality for middleware."""

    def __init__(self):
        """Initialize the auth mixin."""
        self.logger = logging.getLogger(__name__)

    async def authenticate(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Authenticate the request by checking the Authorization header.

        Args:
            request: The incoming request

        Returns:
            The decoded token payload if authentication is successful, None otherwise
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            self.logger.debug("No Authorization header found")
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            self.logger.warning(f"Invalid Authorization header format: {auth_header}")
            return None

        token = parts[1]

        # Get the auth service from the application state
        if not hasattr(request.app.state, "auth"):
            self.logger.error("Auth service not available in application state")
            return None

        auth_service: AuthService = request.app.state.auth

        try:
            # Verify the token
            payload = await auth_service.verify_token(token)
            if not payload:
                self.logger.warning("Token verification failed")
                return None

            # Check if token is revoked
            if hasattr(request.app.state, "token_manager"):
                token_manager = request.app.state.token_manager
                token_id = payload.get("jti")
                if token_id and token_manager.is_revoked(token_id):
                    self.logger.warning(f"Token {token_id} is revoked")
                    return None

            return payload
        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            return None


class AuthMiddleware(AuthMixin, BaseHTTPMiddleware):
    """Middleware for authenticating API requests."""

    def __init__(
        self,
        app,
        excluded_paths: List[str] = None,
        excluded_methods: List[str] = None,
    ):
        """
        Initialize the authentication middleware.

        Args:
            app: The FastAPI application
            excluded_paths: List of paths to exclude from authentication
            excluded_methods: List of HTTP methods to exclude from authentication
        """
        BaseHTTPMiddleware.__init__(self, app)
        AuthMixin.__init__(self)
        self.excluded_paths = excluded_paths or []
        self.excluded_methods = excluded_methods or ["OPTIONS"]
        self.logger = logging.getLogger(__name__)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Process the request, authenticate if necessary, and add token rotation headers.

        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler

        Returns:
            The response from the next handler
        """
        # Skip authentication for excluded paths and methods
        if request.method in self.excluded_methods:
            self.logger.debug(f"Skipping auth for excluded method: {request.method}")
            return await call_next(request)

        for path in self.excluded_paths:
            if request.url.path.startswith(path):
                self.logger.debug(
                    f"Skipping auth for excluded path: {request.url.path}"
                )
                return await call_next(request)

        # Attempt to authenticate
        start_time = time.time()
        token_payload = await self.authenticate(request)
        auth_time = time.time() - start_time

        # Store token payload in request state for later use by endpoints
        request.state.token_payload = token_payload
        request.state.authenticated = token_payload is not None

        if token_payload:
            user_id = token_payload.get("sub")
            self.logger.debug(f"Authentication successful for user {user_id}")
        else:
            self.logger.debug("Authentication failed or not attempted")

        # Process the request
        response = await call_next(request)

        # Add token rotation header if needed
        if hasattr(request.app.state, "token_rotation_service") and token_payload:
            user_id = token_payload.get("sub")
            if user_id:
                token_rotation_service: TokenRotationService = (
                    request.app.state.token_rotation_service
                )

                # Check if the token needs rotation
                needs_rotation = token_rotation_service.needs_rotation(user_id)

                if needs_rotation:
                    response.headers["X-Token-Rotation-Required"] = "true"
                    self.logger.info(f"Token rotation required for user {user_id}")

        # Add authentication timing header for debugging
        response.headers["X-Auth-Time"] = str(auth_time)

        return response


class TokenAuthBackend(AuthenticationBackend):
    """Authentication backend for token-based authentication."""

    async def authenticate(self, request: Request) -> Optional[tuple]:
        """
        Authenticate the request using JWT tokens.

        Args:
            request: The incoming request

        Returns:
            A tuple of (auth_credentials, user) if authentication is successful,
            None otherwise
        """
        auth_header = request.headers.get("Authorization", "")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.replace("Bearer ", "")

        try:
            # Decode the token
            payload = decode_token(token)
            if not payload:
                return None

            # Check if token is revoked
            if hasattr(request.app.state, "token_manager"):
                token_manager = request.app.state.token_manager
                token_id = payload.get("jti")
                if token_id and token_manager.is_revoked(token_id):
                    return None

            # Extract user information
            user_id = payload.get("sub", "")
            roles = payload.get("roles", [])

            # Create credentials with scopes based on roles
            scopes = ["authenticated"] + [f"role:{role}" for role in roles]
            credentials = AuthCredentials(scopes)

            # Create a user object
            user = SimpleUnifiedUser(user_id)

            return credentials, user
        except Exception:
            return None
