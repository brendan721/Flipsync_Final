"""
Compatibility module for authentication services.

This module provides compatibility functions for creating auth services
when they're not available in the application state.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


async def get_auth_service() -> Any:
    """
    Create and return an auth service instance.

    This is a compatibility function that creates a minimal auth service
    when the main auth service is not available in the application state.

    Returns:
        AuthService: A minimal auth service instance
    """
    try:
        from fs_agt_clean.core.auth.auth_service import AuthService, AuthConfig
        from fs_agt_clean.core.redis.redis_manager import RedisManager
        import os

        # Create minimal configuration
        development_mode = os.environ.get("ENVIRONMENT", "").lower() in (
            "development",
            "dev",
        )
        auth_config = AuthConfig(development_mode=development_mode)

        # Create mock Redis manager
        class MockRedisManager:
            async def get(self, key):
                return None

            async def set(self, key, value=None):
                pass

            async def delete(self, key):
                pass

        redis_manager = MockRedisManager()

        # Create auth service without database (minimal mode)
        auth_service = AuthService(auth_config, redis_manager)

        logger.info("Created compatibility auth service")
        return auth_service

    except Exception as e:
        logger.error(f"Failed to create compatibility auth service: {e}")
        raise


async def get_db_auth_service() -> Any:
    """
    Create and return a database-backed auth service instance.

    This is a compatibility function that creates a minimal database auth service
    when the main db auth service is not available in the application state.

    Returns:
        DbAuthService: A minimal database auth service instance
    """
    try:
        from fs_agt_clean.core.auth.db_auth_service import DbAuthService
        from fs_agt_clean.core.auth.auth_service import AuthConfig
        from fs_agt_clean.core.redis.redis_manager import RedisManager
        from fs_agt_clean.core.db.database import Database
        import os

        # Create mock Redis manager
        class MockRedisManager:
            async def get(self, key):
                return None

            async def set(self, key, value=None):
                pass

            async def delete(self, key):
                pass

        # Create mock database
        class MockDatabase:
            async def get_session(self):
                return self

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        redis_manager = MockRedisManager()
        database = MockDatabase()

        # Create minimal configuration
        development_mode = os.environ.get("ENVIRONMENT", "").lower() in (
            "development",
            "dev",
        )
        auth_config = AuthConfig(development_mode=development_mode)

        # Create db auth service
        db_auth_service = DbAuthService(auth_config, redis_manager, database)

        logger.info("Created compatibility db auth service")
        return db_auth_service

    except Exception as e:
        logger.error(f"Failed to create compatibility db auth service: {e}")
        # Fall back to regular auth service
        logger.warning("Falling back to regular auth service")
        return await get_auth_service()


class SimpleAuthService:
    """
    Simple authentication service for direct database access.

    This bypasses the complex dependency injection and provides
    direct authentication functionality.
    """

    def __init__(self):
        self.development_mode = True

    async def authenticate_user(self, email: str, password: str) -> Optional[dict]:
        """
        Authenticate a user directly against the database.

        Args:
            email: User email
            password: User password

        Returns:
            User data if authentication successful, None otherwise
        """
        try:
            from fs_agt_clean.database.models.unified_user import UnifiedUser
            from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy import select

            # Database connection
            DATABASE_URL = "postgresql+asyncpg://postgres:postgres@flipsync-production-db:5432/flipsync"
            engine = create_async_engine(DATABASE_URL)
            async_session = sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )

            async with async_session() as session:
                # Get the user
                result = await session.execute(
                    select(UnifiedUser).where(UnifiedUser.email == email)
                )
                user = result.scalar_one_or_none()

                if not user:
                    logger.warning(f"User not found: {email}")
                    return None

                # Verify password
                if not user.verify_password(password):
                    logger.warning(f"Password verification failed for user: {email}")
                    return None

                # Check if user is active
                if not user.is_active:
                    logger.warning(f"User is not active: {email}")
                    return None

                # Return user data
                return {
                    "id": str(user.id),
                    "email": user.email,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_admin": user.is_admin,
                    "is_verified": user.is_verified,
                    "permissions": ["user"] + (["admin"] if user.is_admin else []),
                }

            await engine.dispose()

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None

    async def create_tokens(self, subject: str, permissions: list) -> Any:
        """
        Create JWT tokens for a user.

        Args:
            subject: User ID
            permissions: User permissions

        Returns:
            Token object with access and refresh tokens
        """
        try:
            import jwt
            import uuid
            from datetime import datetime, timezone, timedelta

            # JWT configuration
            secret = "development-jwt-secret-not-for-production-use"
            algorithm = "HS256"

            # Access token payload
            access_payload = {
                "sub": subject,
                "permissions": permissions,
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
                "iat": datetime.now(timezone.utc),
                "jti": str(uuid.uuid4()),
                "scope": "access_token",
            }

            # Refresh token payload
            refresh_payload = {
                "sub": subject,
                "exp": datetime.now(timezone.utc) + timedelta(days=30),
                "iat": datetime.now(timezone.utc),
                "jti": str(uuid.uuid4()),
                "scope": "refresh_token",
            }

            # Generate tokens
            access_token = jwt.encode(access_payload, secret, algorithm=algorithm)
            refresh_token = jwt.encode(refresh_payload, secret, algorithm=algorithm)

            # Create token object
            class Token:
                def __init__(self, access_token, refresh_token):
                    self.access_token = access_token
                    self.refresh_token = refresh_token

            return Token(access_token, refresh_token)

        except Exception as e:
            logger.error(f"Token creation error: {e}")
            raise


async def get_simple_auth_service() -> SimpleAuthService:
    """
    Get a simple auth service that works directly with the database.

    Returns:
        SimpleAuthService: A simple auth service instance
    """
    return SimpleAuthService()
