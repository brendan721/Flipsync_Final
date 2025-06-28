"""
Social Authentication Providers

This module provides social authentication functionality for OAuth providers
like Google, Facebook, GitHub, etc.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


class SocialAuthError(Exception):
    """Exception raised for social authentication errors."""

    pass


@dataclass
class SocialAuthResponse:
    """Response from social authentication provider."""

    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    provider_specific: Optional[Dict[str, Any]] = None


class SocialAuthService:
    """Service for handling social authentication."""

    def __init__(self):
        """Initialize the social auth service."""
        pass

    async def exchange_code(self, provider: str, code: str) -> SocialAuthResponse:
        """
        Exchange authorization code for user information.

        Args:
            provider: Social provider name (google, facebook, etc.)
            code: Authorization code from provider

        Returns:
            SocialAuthResponse with user information

        Raises:
            SocialAuthError: If authentication fails
        """
        # This is a minimal implementation for compatibility
        # In production, this would integrate with actual OAuth providers

        if not code:
            raise SocialAuthError("Authorization code is required")

        # Mock response for testing
        return SocialAuthResponse(
            user_id=f"mock_user_{provider}",
            email=f"user@{provider}.com",
            name=f"Mock UnifiedUser from {provider}",
            picture=None,
            provider_specific={"provider": provider, "code": code},
        )
