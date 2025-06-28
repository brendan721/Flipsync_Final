"""
Token Revocation Service

This module provides token revocation functionality using Redis.
"""

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class TokenRevocationService:
    """Service for managing token revocation."""

    def __init__(self, redis_manager):
        """Initialize token revocation service."""
        self.redis_manager = redis_manager

    async def revoke_token(self, jti: str) -> bool:
        """Revoke a token by JTI."""
        try:
            client = await self.redis_manager.get_client()
            await client.set(f"revoked_token:{jti}", "revoked")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke token {jti}: {e}")
            return False

    async def is_token_revoked(self, jti: str) -> bool:
        """Check if a token is revoked."""
        try:
            client = await self.redis_manager.get_client()
            result = await client.get(f"revoked_token:{jti}")
            return result is not None
        except Exception as e:
            logger.error(f"Failed to check token revocation {jti}: {e}")
            return False

    async def revoke_all_user_tokens(self, user_id: str) -> bool:
        """Revoke all tokens for a user."""
        try:
            client = await self.redis_manager.get_client()
            await client.set(f"revoked_user:{user_id}", "revoked")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke user tokens {user_id}: {e}")
            return False
