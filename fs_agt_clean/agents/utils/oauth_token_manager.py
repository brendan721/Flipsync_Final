"""
OAuth token management utilities for FlipSync agents.

This module provides utilities for managing OAuth tokens across different
marketplace APIs, with support for token refresh, caching, and error handling.
"""

import base64
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fs_agt_clean.core.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


async def refresh_oauth_token(
    token_endpoint: str,
    refresh_token: str,
    client_id: str,
    client_secret: str,
    scope: Optional[str] = None,
    use_basic_auth: bool = False,
    marketplace: str = "unknown",
    additional_params: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Refresh an OAuth token using the provided credentials.

    Args:
        token_endpoint: OAuth token endpoint URL
        refresh_token: Refresh token to use
        client_id: OAuth client ID
        client_secret: OAuth client secret
        scope: Optional scope for the token
        use_basic_auth: Whether to use Basic authentication in header
        marketplace: Name of the marketplace for error reporting
        additional_params: Additional parameters to include in the request

    Returns:
        Dictionary containing token data with keys:
        - access_token: The new access token
        - expires_in: Token expiration time in seconds
        - token_type: Type of token (usually "Bearer")

    Raises:
        AuthenticationError: If token refresh fails
    """
    try:
        # Import aiohttp here to avoid import issues if not available
        import aiohttp

        # Prepare request data
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }

        if scope:
            data["scope"] = scope

        if additional_params:
            data.update(additional_params)

        # Prepare headers
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        if use_basic_auth:
            # Use Basic authentication in header
            credentials = f"{client_id}:{client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            headers["Authorization"] = f"Basic {encoded_credentials}"
        else:
            # Include credentials in request body
            data["client_id"] = client_id
            data["client_secret"] = client_secret

        logger.info(f"Refreshing OAuth token for {marketplace} marketplace")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                token_endpoint,
                data=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                response_text = await response.text()

                if response.status != 200:
                    logger.error(
                        f"Token refresh failed for {marketplace}: "
                        f"HTTP {response.status} - {response_text}"
                    )
                    raise AuthenticationError(
                        f"Token refresh failed with status {response.status}: {response_text}",
                        marketplace=marketplace,
                        status_code=response.status,
                    )

                try:
                    token_data = json.loads(response_text)
                except json.JSONDecodeError as e:
                    logger.error(
                        f"Invalid JSON response from {marketplace} token endpoint: {response_text}"
                    )
                    raise AuthenticationError(
                        f"Invalid JSON response from token endpoint: {str(e)}",
                        marketplace=marketplace,
                        original_error=e,
                    ) from e

                # Validate required fields
                if "access_token" not in token_data:
                    logger.error(
                        f"Missing access_token in {marketplace} response: {token_data}"
                    )
                    raise AuthenticationError(
                        "Missing access_token in token response",
                        marketplace=marketplace,
                    )

                # Set default values for optional fields
                if "expires_in" not in token_data:
                    token_data["expires_in"] = 3600  # Default to 1 hour

                if "token_type" not in token_data:
                    token_data["token_type"] = "Bearer"

                logger.info(
                    f"Successfully refreshed {marketplace} OAuth token, "
                    f"expires in {token_data['expires_in']} seconds"
                )

                return token_data

    except aiohttp.ClientError as e:
        logger.error(f"Network error during {marketplace} token refresh: {str(e)}")
        raise AuthenticationError(
            f"Network error during token refresh: {str(e)}",
            marketplace=marketplace,
            original_error=e,
        ) from e
    except Exception as e:
        if isinstance(e, AuthenticationError):
            raise  # Re-raise AuthenticationError as-is

        logger.error(f"Unexpected error during {marketplace} token refresh: {str(e)}")
        raise AuthenticationError(
            f"Unexpected error during token refresh: {str(e)}",
            marketplace=marketplace,
            original_error=e,
        ) from e


def calculate_token_expiry(expires_in: int, buffer_seconds: int = 60) -> datetime:
    """
    Calculate token expiry time with a buffer.

    Args:
        expires_in: Token lifetime in seconds
        buffer_seconds: Buffer time to subtract from expiry (default: 60 seconds)

    Returns:
        Datetime when the token should be considered expired
    """
    return datetime.now() + timedelta(seconds=expires_in - buffer_seconds)


def is_token_expired(expiry_time: datetime, buffer_seconds: int = 60) -> bool:
    """
    Check if a token is expired or will expire soon.

    Args:
        expiry_time: Token expiry datetime
        buffer_seconds: Buffer time to consider token expired early (default: 60 seconds)

    Returns:
        True if token is expired or will expire within buffer time
    """
    return datetime.now() >= (expiry_time - timedelta(seconds=buffer_seconds))


def format_token_for_header(token: str, token_type: str = "Bearer") -> str:
    """
    Format token for Authorization header.

    Args:
        token: Access token
        token_type: Token type (default: "Bearer")

    Returns:
        Formatted authorization header value
    """
    return f"{token_type} {token}"
