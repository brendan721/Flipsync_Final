"""Database-backed authentication service."""

import asyncio
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from fastapi import Depends, HTTPException, status

# JWT library - use python-jose for compatibility
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from pydantic import BaseModel, ConfigDict

# Optional imports with graceful fallbacks
try:
    from fs_agt_clean.core.db.auth_repository import AuthRepository
except ImportError:

    class AuthRepository:
        def __init__(self, *args, **kwargs):
            pass

        async def authenticate_user(self, *args, **kwargs):
            return False, None

        async def get_user_permissions(self, *args, **kwargs):
            return []

        async def update_last_login(self, *args, **kwargs):
            pass


try:
    from fs_agt_clean.core.db.database import Database
except ImportError:

    class Database:
        def __init__(self, *args, **kwargs):
            pass

        async def get_session(self):
            return self

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass


try:
    from fs_agt_clean.database.models.unified_user import UnifiedUnifiedUser

    _USING_REAL_AUTH_USER = True
except ImportError:
    # Mock class that does NOT inherit from Base to avoid SQLAlchemy registry conflicts
    class MockUnifiedUnifiedUser:
        """Mock UnifiedUnifiedUser class for fallback when real models unavailable."""

        pass

    # Alias for compatibility
    UnifiedUnifiedUser = MockUnifiedUnifiedUser
    _USING_REAL_AUTH_USER = False

try:
    from fs_agt_clean.core.redis.redis_manager import RedisManager
except ImportError:

    class RedisManager:
        def __init__(self, *args, **kwargs):
            pass


try:
    from fs_agt_clean.core.redis.token_revocation import TokenRevocationService
except ImportError:

    class TokenRevocationService:
        def __init__(self, *args, **kwargs):
            pass

        async def is_token_revoked(self, *args, **kwargs):
            return False

        async def revoke_token(self, *args, **kwargs):
            return True

        async def revoke_all_user_tokens(self, *args, **kwargs):
            return True


try:
    from fs_agt_clean.core.redis.token_storage import TokenRecord, TokenStorage
except ImportError:

    class TokenRecord:
        def __init__(self, *args, **kwargs):
            pass

    class TokenStorage:
        def __init__(self, *args, **kwargs):
            pass

        async def store_token(self, *args, **kwargs):
            pass


try:
    from fs_agt_clean.core.vault.secret_manager import VaultSecretManager
except ImportError:

    class VaultSecretManager:
        def __init__(self, *args, **kwargs):
            pass

        async def get_secret(self, *args, **kwargs):
            return {"value": "mock-secret"}


logger = logging.getLogger(__name__)


class Token(BaseModel):
    """Token model containing access and refresh tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token payload model."""

    sub: str
    scope: str
    exp: datetime
    permissions: List[str] = []
    nonce: Optional[str] = None
    jti: str  # JWT ID for revocation tracking


class AuthConfig(BaseModel):
    """Authentication service configuration."""

    jwt_secret_name: str = "jwt_secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    development_mode: bool = False

    @classmethod
    def from_env(cls) -> "AuthConfig":
        """Create AuthConfig from environment variables."""
        return cls(
            jwt_secret_name=os.getenv("JWT_SECRET_NAME", "jwt_secret"),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            access_token_expire_minutes=int(
                os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
            ),
            refresh_token_expire_days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")),
            development_mode=os.getenv("ENVIRONMENT", "").lower() == "development",
        )


class DbAuthService:
    """Database-backed authentication service."""

    def __init__(
        self,
        config: AuthConfig,
        redis_manager: RedisManager,
        database: Database,
        secret_manager: Optional[VaultSecretManager] = None,
    ):
        """Initialize the auth service with configuration."""
        self.config = config
        self._redis_manager = redis_manager
        self._database = database
        self._secret_manager = secret_manager
        self._token_storage = TokenStorage(redis_manager)
        self._revocation_service = TokenRevocationService(redis_manager)
        self._secret_cache: Optional[Dict] = None
        self._secret_cache_timestamp: Optional[datetime] = None
        self._secret_cache_ttl = timedelta(minutes=5)
        self._max_retries = 3
        self._retry_delay = 1  # seconds

    async def _get_secret(self) -> str:
        """Get JWT secret from Vault."""
        now = datetime.now(timezone.utc)

        # Check cache first
        if (
            self._secret_cache
            and self._secret_cache_timestamp
            and now - self._secret_cache_timestamp <= self._secret_cache_ttl
        ):
            return self._secret_cache["value"]

        # Use development secret in development mode
        if self.config.development_mode:
            logger.warning("Using development JWT secret - NOT FOR PRODUCTION USE")
            return "development-jwt-secret-not-for-production-use"

        # Get from Vault with retries
        if not self._secret_manager:
            raise RuntimeError(
                "Secret manager not initialized and not in development mode"
            )

        last_error = None
        for attempt in range(self._max_retries):
            try:
                secret = await self._secret_manager.get_secret(
                    self.config.jwt_secret_name
                )
                if not secret or "value" not in secret:
                    logger.error("JWT secret not found in Vault or has invalid format")
                    raise ValueError("JWT secret not found or invalid format")

                # Update cache
                self._secret_cache = {"value": secret["value"]}
                self._secret_cache_timestamp = now

                return secret["value"]

            except Exception as e:
                last_error = e
                logger.error(
                    "Attempt %s/%s failed: %s", attempt + 1, self._max_retries, str(e)
                )
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (attempt + 1))

        logger.critical("All attempts to retrieve JWT secret failed")
        raise RuntimeError(
            f"Failed to retrieve JWT secret after {self._max_retries} attempts"
        ) from last_error

    async def initialize(self) -> None:
        """Initialize the auth service and verify Vault connection."""
        try:
            # Test Vault connection and secret access
            await self._get_secret()
            logger.info("Successfully initialized DbAuthService with Vault connection")
        except Exception as e:
            logger.critical("Failed to initialize DbAuthService: %s", str(e))
            raise RuntimeError("DbAuthService initialization failed") from e

    async def create_access_token(self, subject: str, permissions: List[str]) -> str:
        """Create a new access token."""
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=self.config.access_token_expire_minutes
        )
        jti = str(uuid4())
        data = {
            "sub": subject,
            "scope": "access_token",
            "permissions": permissions,
            "exp": expire,
            "nonce": secrets.token_hex(8),
            "jti": jti,
        }

        # For development mode, use a simple secret
        if self.config.development_mode:
            secret = "development-jwt-secret-not-for-production-use"
        else:
            secret = await self._get_secret()

        token = jwt.encode(data, secret, algorithm=self.config.jwt_algorithm)

        # Store token in Redis
        await self._token_storage.store_token(
            TokenRecord(
                jti=jti,
                user_id=subject,
                expires_at=expire,
                metadata={"scope": "access_token"},
            )
        )

        return token

    async def create_refresh_token(self, subject: str) -> str:
        """Create a new refresh token."""
        expire = datetime.now(timezone.utc) + timedelta(
            days=self.config.refresh_token_expire_days
        )
        jti = str(uuid4())
        data = {
            "sub": subject,
            "scope": "refresh_token",
            "exp": expire,
            "nonce": secrets.token_hex(8),
            "jti": jti,
        }

        # For development mode, use a simple secret
        if self.config.development_mode:
            secret = "development-jwt-secret-not-for-production-use"
        else:
            secret = await self._get_secret()
        token = jwt.encode(data, secret, algorithm=self.config.jwt_algorithm)

        # Store token in Redis
        await self._token_storage.store_token(
            TokenRecord(
                jti=jti,
                user_id=subject,
                expires_at=expire,
                metadata={"scope": "refresh_token"},
            )
        )

        return token

    async def create_tokens(self, subject: str, permissions: List[str]) -> Token:
        """Create both access and refresh tokens."""
        return Token(
            access_token=await self.create_access_token(subject, permissions),
            refresh_token=await self.create_refresh_token(subject),
        )

    async def verify_token(self, token: str) -> TokenPayload:
        """Verify and decode a token."""
        try:
            # For development mode, use a simple secret
            if self.config.development_mode:
                secret = "development-jwt-secret-not-for-production-use"
            else:
                secret = await self._get_secret()
            payload = jwt.decode(token, secret, algorithms=[self.config.jwt_algorithm])
            token_payload = TokenPayload(**payload)

            # Check if token is revoked
            try:
                is_revoked = await self._revocation_service.is_token_revoked(
                    token_payload.jti
                )
                if is_revoked:
                    raise HTTPException(
                        status_code=401, detail="Token has been revoked"
                    )
            except Exception as e:
                logger.warning("Error checking token revocation status: %s", str(e))
                # Continue if revocation check fails - fail open for revocation checks
                pass

            return token_payload

        except ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

    async def refresh_tokens(self, refresh_token: str) -> Token:
        """Create new tokens using a refresh token."""
        payload = await self.verify_token(refresh_token)
        if payload.scope != "refresh_token":
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        # Revoke the used refresh token
        await self._revocation_service.revoke_token(payload.jti)

        # Create new tokens
        return await self.create_tokens(payload.sub, payload.permissions)

    def has_permission(self, payload: TokenPayload, permission: str) -> bool:
        """Check if a token payload has a specific permission."""
        return permission in payload.permissions

    async def revoke_user_tokens(
        self, user_id: str, reason: Optional[str] = None
    ) -> bool:
        """Revoke all tokens for a user."""
        return await self._revocation_service.revoke_all_user_tokens(user_id)

    async def revoke_token(self, token: str, reason: Optional[str] = None) -> bool:
        """Revoke a specific token."""
        try:
            # For development mode, use a simple secret
            if self.config.development_mode:
                secret = "development-jwt-secret-not-for-production-use"
            else:
                secret = await self._get_secret()
            payload = jwt.decode(token, secret, algorithms=[self.config.jwt_algorithm])
            token_payload = TokenPayload(**payload)
            return await self._revocation_service.revoke_token(token_payload.jti)
        except Exception as e:
            logger.error("Failed to revoke token: %s", str(e))
            return False

    async def authenticate_user(
        self, username_or_email: str, password: str
    ) -> Optional[Dict[str, Any]]:
        """Authenticate a user by username/email and password.

        Args:
            username_or_email: The username or email
            password: The password

        Returns:
            UnifiedUser data if authentication is successful, None otherwise
        """
        try:
            # Get a database session
            async with self._database.get_session() as session:
                # Create a repository
                repo = AuthRepository(session)

                # Authenticate the user
                success, user = await repo.authenticate_user(
                    username_or_email, password
                )

                if not success or not user:
                    return None

                # Get user permissions
                permissions = await repo.get_user_permissions(user)

                # Update last login
                await repo.update_last_login(user)

                # Return user data
                return {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_admin": user.is_admin,
                    "permissions": permissions,
                }
        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            return None
