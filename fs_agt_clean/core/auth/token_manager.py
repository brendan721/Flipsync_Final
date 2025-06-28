"""
token_manager.py - FALLBACK MIGRATION

This file was migrated as part of the Flipsync clean-up project.
WARNING: This is a fallback migration due to issues with the automated migration.
"""

"""
Token management for the FlipSync application.

This module provides functionality for creating, validating, and revoking
authentication tokens.
"""

import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

# JWT library - use python-jose for compatibility
from jose import jwt

from fs_agt_clean.core.redis.token_storage import TokenRecord, TokenStorage

# Import real implementations
from fs_agt_clean.core.security.audit_logger import SecurityAuditLogger
from fs_agt_clean.core.vault.secret_manager import VaultSecretManager

logger = logging.getLogger(__name__)

# Constants
DEFAULT_TOKEN_EXPIRY_SECONDS = 1800  # 30 minutes
DEFAULT_REFRESH_TOKEN_EXPIRY_DAYS = 30
JWT_ALGORITHM = "HS256"


class TokenManager:
    """Manager for authentication tokens."""

    def __init__(
        self,
        secret_manager: VaultSecretManager,
        audit_logger: SecurityAuditLogger,
        cleanup_interval: timedelta = timedelta(hours=1),
    ):
        """Initialize the token manager.

        Args:
            secret_manager: Secret manager for JWT signing
            audit_logger: Security audit logger
            cleanup_interval: Interval for cleaning up expired tokens
        """
        self.secret_manager = secret_manager
        self.audit_logger = audit_logger
        self.cleanup_interval = cleanup_interval
        self._token_storage = TokenStorage()
        self._last_cleanup = datetime.now(timezone.utc)

    async def create_token(
        self,
        user_id: str,
        scopes: List[str] = None,
        expires_in: int = DEFAULT_TOKEN_EXPIRY_SECONDS,
        metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Create a new token.

        Args:
            user_id: UnifiedUser ID
            scopes: Token scopes
            expires_in: Token expiry in seconds
            metadata: Additional metadata

        Returns:
            Dict[str, Any]: Token data
        """
        # Generate token ID
        token_id = str(uuid.uuid4())

        # Set expiry time
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        # Create token data
        token_data = {
            "sub": user_id,
            "jti": token_id,
            "scope": " ".join(scopes) if scopes else "",
            "exp": int(expires_at.timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "nonce": secrets.token_hex(8),
        }

        # Add metadata if provided
        if metadata:
            token_data.update(metadata)

        # Get secret key
        secret = await self.secret_manager.get_secret("jwt_secret")

        # Create access token
        access_token = jwt.encode(token_data, secret, algorithm=JWT_ALGORITHM)

        # Create refresh token
        refresh_token = secrets.token_urlsafe(32)
        refresh_expires_at = datetime.now(timezone.utc) + timedelta(
            days=DEFAULT_REFRESH_TOKEN_EXPIRY_DAYS
        )

        # Store token in storage
        await self._token_storage.store_token(
            TokenRecord(
                jti=token_id,
                user_id=user_id,
                expires_at=expires_at,
                refresh_token=refresh_token,
                refresh_expires_at=refresh_expires_at,
                scopes=scopes,
                metadata=metadata,
            )
        )

        # Log token creation
        await self.audit_logger.log_security_event(
            event_type="token_created",
            user_id=user_id,
            details={
                "token_id": token_id,
                "scopes": scopes,
                "expires_at": expires_at.isoformat(),
            },
        )

        # Return token data
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": expires_in,
            "expires_at": expires_at,
            "refresh_token": refresh_token,
            "scope": " ".join(scopes) if scopes else "",
        }

    async def validate_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Validate a token.

        Args:
            token: Token to validate

        Returns:
            Tuple[bool, Optional[Dict[str, Any]]]: (is_valid, token_data)
        """
        try:
            # Get secret key
            secret = await self.secret_manager.get_secret("jwt_secret")

            # Decode token
            payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])

            # Check if token is revoked
            token_id = payload.get("jti")
            if not token_id:
                logger.warning("Token missing JTI claim")
                return False, None

            is_revoked = await self._token_storage.is_token_revoked(token_id)
            if is_revoked:
                logger.warning(f"Token {token_id} has been revoked")
                return False, None

            # Check for token cleanup
            await self._check_cleanup()

            # Return validation result
            return True, payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return False, None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return False, None
        except Exception as e:
            logger.error(f"Error validating token: {str(e)}")
            return False, None

    async def revoke_token(self, token_id: str) -> bool:
        """Revoke a token.

        Args:
            token_id: Token ID to revoke

        Returns:
            bool: True if token was revoked
        """
        try:
            # Revoke token
            result = await self._token_storage.revoke_token(token_id)

            # Log token revocation
            if result:
                await self.audit_logger.log_security_event(
                    event_type="token_revoked",
                    details={"token_id": token_id},
                )

            return result
        except Exception as e:
            logger.error(f"Error revoking token: {str(e)}")
            return False

    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh a token.

        Args:
            refresh_token: Refresh token

        Returns:
            Optional[Dict[str, Any]]: New token data
        """
        try:
            # Get token by refresh token
            token_data = await self._token_storage.get_token_by_refresh(refresh_token)
            if not token_data:
                logger.warning("Invalid refresh token")
                return None

            # Check if refresh token is expired
            refresh_expires_at = token_data.get("refresh_expires_at")
            if refresh_expires_at and datetime.now(timezone.utc) > refresh_expires_at:
                logger.warning("Refresh token has expired")
                return None

            # Revoke old token
            token_id = token_data.get("token_id")
            if token_id:
                await self.revoke_token(token_id)

            # Create new token
            user_id = token_data.get("user_id")
            scopes = token_data.get("scopes", [])
            metadata = token_data.get("metadata")

            # Create new token
            new_token = await self.create_token(
                user_id=user_id,
                scopes=scopes,
                metadata=metadata,
            )

            # Log token refresh
            await self.audit_logger.log_security_event(
                event_type="token_refreshed",
                user_id=user_id,
                details={
                    "old_token_id": token_id,
                    "new_token_id": new_token.get("jti"),
                },
            )

            return new_token
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return None

    async def _check_cleanup(self) -> None:
        """Check if token cleanup is needed and perform it if necessary."""
        now = datetime.now(timezone.utc)
        if now - self._last_cleanup > self.cleanup_interval:
            logger.info("Cleaning up expired tokens")
            try:
                count = await self._token_storage.cleanup_expired_tokens()
                logger.info(f"Cleaned up {count} expired tokens")
                self._last_cleanup = now
            except Exception as e:
                logger.error(f"Error cleaning up expired tokens: {str(e)}")
