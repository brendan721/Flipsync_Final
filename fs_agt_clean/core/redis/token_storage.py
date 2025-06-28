"""
Token storage using Redis.

This module provides functionality for storing and retrieving tokens from Redis.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Union

from .redis_manager import RedisManager

logger = logging.getLogger(__name__)


class TokenRecord:
    """Record for a token in storage."""

    def __init__(
        self,
        jti: str,
        user_id: str,
        expires_at: datetime,
        refresh_token: str,
        refresh_expires_at: datetime,
        scopes: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a token record.

        Args:
            jti: JWT ID
            user_id: UnifiedUser ID
            expires_at: Expiry time
            refresh_token: Refresh token
            refresh_expires_at: Refresh token expiry time
            scopes: Token scopes
            metadata: Additional metadata
        """
        self.jti = jti
        self.user_id = user_id
        self.expires_at = expires_at
        self.refresh_token = refresh_token
        self.refresh_expires_at = refresh_expires_at
        self.scopes = scopes or []
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation
        """
        return {
            "token_id": self.jti,
            "user_id": self.user_id,
            "expires_at": self.expires_at.isoformat(),
            "refresh_token": self.refresh_token,
            "refresh_expires_at": self.refresh_expires_at.isoformat(),
            "scopes": self.scopes,
            "metadata": self.metadata,
        }


class TokenStorage:
    """Storage for tokens using Redis."""

    def __init__(self, redis_manager: RedisManager):
        """Initialize the token storage.

        Args:
            redis_manager: Redis manager instance
        """
        self.redis_manager = redis_manager
        self.token_prefix = "token:"
        self.refresh_prefix = "refresh:"
        self.revoked_prefix = "revoked:"

    async def store_token(self, token: TokenRecord) -> bool:
        """Store a token.

        Args:
            token: Token record to store

        Returns:
            bool: True if successful
        """
        try:
            # Store token data
            token_key = f"{self.token_prefix}{token.jti}"
            token_data = token.to_dict()

            # Store token with expiry
            redis_client = await self.redis_manager.get_client()
            await redis_client.set(
                token_key,
                str(token_data),
                ex=int((token.expires_at - datetime.now(timezone.utc)).total_seconds()),
            )

            # Store refresh token mapping
            refresh_key = f"{self.refresh_prefix}{token.refresh_token}"
            await redis_client.set(
                refresh_key,
                token.jti,
                ex=int(
                    (
                        token.refresh_expires_at - datetime.now(timezone.utc)
                    ).total_seconds()
                ),
            )

            logger.debug(f"Stored token {token.jti} for user {token.user_id}")
            return True
        except Exception as e:
            logger.error(f"Error storing token: {str(e)}")
            return False

    async def get_token(self, token_id: str) -> Optional[Dict[str, Any]]:
        """Get a token by ID.

        Args:
            token_id: Token ID

        Returns:
            Optional[Dict[str, Any]]: Token data or None if not found
        """
        try:
            token_key = f"{self.token_prefix}{token_id}"
            redis_client = await self.redis_manager.get_client()
            token_data = await redis_client.get(token_key)

            if not token_data:
                return None

            # Convert string representation back to dictionary
            import ast

            # Redis with decode_responses=True returns strings directly
            if isinstance(token_data, bytes):
                token_data = token_data.decode("utf-8")
            return ast.literal_eval(token_data)
        except Exception as e:
            logger.error(f"Error getting token: {str(e)}")
            return None

    async def get_token_by_refresh(
        self, refresh_token: str
    ) -> Optional[Dict[str, Any]]:
        """Get a token by refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            Optional[Dict[str, Any]]: Token data or None if not found
        """
        try:
            refresh_key = f"{self.refresh_prefix}{refresh_token}"
            redis_client = await self.redis_manager.get_client()
            token_id = await redis_client.get(refresh_key)

            if not token_id:
                return None

            # Redis with decode_responses=True returns strings directly
            if isinstance(token_id, bytes):
                token_id = token_id.decode("utf-8")
            return await self.get_token(token_id)
        except Exception as e:
            logger.error(f"Error getting token by refresh: {str(e)}")
            return None

    async def revoke_token(self, token_id: str) -> bool:
        """Revoke a token.

        Args:
            token_id: Token ID

        Returns:
            bool: True if successful
        """
        try:
            # Get token data
            token_data = await self.get_token(token_id)

            if not token_data:
                logger.warning(f"Token {token_id} not found for revocation")
                return False

            # Delete token
            redis_client = await self.redis_manager.get_client()
            token_key = f"{self.token_prefix}{token_id}"
            await redis_client.delete(token_key)

            # Delete refresh token mapping
            refresh_token = token_data.get("refresh_token")
            if refresh_token:
                refresh_key = f"{self.refresh_prefix}{refresh_token}"
                await redis_client.delete(refresh_key)

            # Add to revoked set with expiry
            revoked_key = f"{self.revoked_prefix}{token_id}"
            expires_at = token_data.get("expires_at")

            if expires_at:
                # Parse ISO format
                import dateutil.parser

                expiry_dt = dateutil.parser.parse(expires_at)
                expiry_seconds = int(
                    (expiry_dt - datetime.now(timezone.utc)).total_seconds()
                )

                # Only store if not already expired
                if expiry_seconds > 0:
                    await redis_client.set(revoked_key, "1", ex=expiry_seconds)

            logger.debug(f"Revoked token {token_id}")
            return True
        except Exception as e:
            logger.error(f"Error revoking token: {str(e)}")
            return False

    async def is_token_revoked(self, token_id: str) -> bool:
        """Check if a token is revoked.

        Args:
            token_id: Token ID

        Returns:
            bool: True if revoked
        """
        try:
            revoked_key = f"{self.revoked_prefix}{token_id}"
            redis_client = await self.redis_manager.get_client()
            return bool(await redis_client.exists(revoked_key))
        except Exception as e:
            logger.error(f"Error checking if token is revoked: {str(e)}")
            return False

    async def cleanup_expired_tokens(self) -> int:
        """Clean up expired tokens.

        Returns:
            int: Number of tokens cleaned up
        """
        # Redis automatically removes expired keys, so this is a no-op
        return 0
