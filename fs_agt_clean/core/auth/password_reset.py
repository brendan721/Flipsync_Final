"""
password_reset.py - FALLBACK MIGRATION

This file was migrated as part of the Flipsync clean-up project.
WARNING: This is a fallback migration due to issues with the automated migration.
"""

"""
Password reset token generation and validation.

This module provides functionality for generating and validating
password reset tokens.
"""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple
from uuid import uuid4

import jwt

from fs_agt_clean.core.auth.auth_service import AuthService
from fs_agt_clean.core.redis.redis_manager import RedisManager
from fs_agt_clean.core.redis.token_storage import TokenRecord

logger = logging.getLogger(__name__)

# Constants
PASSWORD_RESET_TOKEN_EXPIRY_HOURS = 24
PASSWORD_RESET_TOKEN_PREFIX = "pwd_reset_"


class PasswordResetService:
    """Service for handling password reset tokens."""

    def __init__(self, auth_service: AuthService, redis_manager: RedisManager):
        """Initialize the password reset service.

        Args:
            auth_service: Authentication service for token operations
            redis_manager: Redis manager for token storage
        """
        self.auth_service = auth_service
        self.redis_manager = redis_manager
        self.token_storage = auth_service._token_storage

    async def generate_reset_token(self, user_id: str, email: str) -> str:
        """Generate a password reset token.

        Args:
            user_id: UnifiedUser ID
            email: UnifiedUser email

        Returns:
            str: Password reset token
        """
        # Generate a unique token ID
        jti = f"{PASSWORD_RESET_TOKEN_PREFIX}{str(uuid4())}"

        # Set expiration time
        expire = datetime.now(timezone.utc) + timedelta(
            hours=PASSWORD_RESET_TOKEN_EXPIRY_HOURS
        )

        # Create token data
        data = {
            "sub": user_id,
            "email": email,
            "scope": "password_reset",
            "exp": expire,
            "nonce": secrets.token_hex(8),
            "jti": jti,
        }

        # Get secret key
        if self.auth_service.config.development_mode:
            secret = "development-jwt-secret-not-for-production-use"
        else:
            secret = await self.auth_service._get_secret()

        # Encode token
        token = jwt.encode(
            data, secret, algorithm=self.auth_service.config.jwt_algorithm
        )

        # Store token in Redis
        await self.token_storage.store_token(
            TokenRecord(
                jti=jti,
                user_id=user_id,
                expires_at=expire,
                metadata={"scope": "password_reset", "email": email},
            )
        )

        logger.info(f"Generated password reset token for user {user_id}")
        return token

    async def validate_reset_token(self, token: str) -> Tuple[bool, Optional[Dict]]:
        """Validate a password reset token.

        Args:
            token: Password reset token

        Returns:
            Tuple[bool, Optional[Dict]]: (is_valid, token_data)
        """
        try:
            # Get secret key
            if self.auth_service.config.development_mode:
                secret = "development-jwt-secret-not-for-production-use"
            else:
                secret = await self.auth_service._get_secret()

            # Decode token
            payload = jwt.decode(
                token, secret, algorithms=[self.auth_service.config.jwt_algorithm]
            )

            # Validate token type
            if payload.get("scope") != "password_reset":
                logger.warning("Invalid token scope for password reset")
                return False, None

            # Check if token is revoked
            jti = payload.get("jti")
            if not jti:
                logger.warning("Missing JTI in password reset token")
                return False, None

            is_revoked = await self.auth_service._revocation_service.is_token_revoked(
                jti
            )
            if is_revoked:
                logger.warning(f"Password reset token {jti} has been revoked")
                return False, None

            # Return validation result
            return True, payload
        except jwt.ExpiredSignatureError:
            logger.warning("Password reset token has expired")
            return False, None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid password reset token: {str(e)}")
            return False, None
        except Exception as e:
            logger.error(f"Error validating password reset token: {str(e)}")
            return False, None

    async def revoke_reset_token(self, token: str) -> bool:
        """Revoke a password reset token.

        Args:
            token: Password reset token

        Returns:
            bool: True if token was revoked, False otherwise
        """
        try:
            # Get secret key
            if self.auth_service.config.development_mode:
                secret = "development-jwt-secret-not-for-production-use"
            else:
                secret = await self.auth_service._get_secret()

            # Decode token
            payload = jwt.decode(
                token, secret, algorithms=[self.auth_service.config.jwt_algorithm]
            )

            # Revoke token
            jti = payload.get("jti")
            if not jti:
                logger.warning("Missing JTI in password reset token")
                return False

            return await self.auth_service._revocation_service.revoke_token(jti)
        except Exception as e:
            logger.error(f"Error revoking password reset token: {str(e)}")
            return False
