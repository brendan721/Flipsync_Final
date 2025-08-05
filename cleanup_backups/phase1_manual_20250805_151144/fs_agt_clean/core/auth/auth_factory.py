"""
Unified Authentication Factory for FlipSync Production
=====================================================

This factory consolidates all FlipSync internal user authentication systems
into a single entry point using the UnifiedAuthSystem.

IMPORTANT: This handles FlipSync's internal user authentication (users logging
into the FlipSync application). This is COMPLETELY SEPARATE from eBay OAuth
integration which handles users connecting their eBay accounts within FlipSync.

eBay OAuth is handled in:
- fs_agt_clean/api/routes/marketplace.py
- fs_agt_clean/services/ebay/oauth_service.py
- fs_agt_clean/core/integrations/ebay/

This factory should NEVER be used for eBay OAuth flows.
"""

import os
import logging
from typing import Optional, Dict, Any
from .unified_auth_system import UnifiedAuthSystem

logger = logging.getLogger(__name__)


class AuthenticationFactory:
    """
    Factory for creating unified FlipSync user authentication instances.

    This factory creates and manages the single authentication system for
    FlipSync internal users (app login/registration). It does NOT handle
    eBay OAuth which is managed separately in marketplace integration.
    """

    _instance: Optional[UnifiedAuthSystem] = None
    _initialized: bool = False

    @classmethod
    async def get_auth_system(cls) -> UnifiedAuthSystem:
        """
        Get or create unified authentication system for FlipSync users.

        Returns:
            UnifiedAuthSystem: Configured authentication system for FlipSync users

        Note:
            This is for FlipSync user authentication only, NOT eBay OAuth
        """
        if cls._instance is None or not cls._initialized:
            cls._instance = await cls._create_auth_system()
            cls._initialized = True
        return cls._instance

    @classmethod
    async def _create_auth_system(cls) -> UnifiedAuthSystem:
        """
        Create unified authentication system with production configuration.

        Returns:
            UnifiedAuthSystem: Configured authentication system
        """
        try:
            # Get database service for FlipSync user storage
            from fs_agt_clean.core.db.database import get_database

            database = get_database()

            # Create unified auth system for FlipSync users
            auth_system = UnifiedAuthSystem(database_service=database)

            # Initialize with production configuration from environment
            await auth_system.initialize()

            logger.info("✅ Unified FlipSync user authentication system initialized")
            logger.info("📝 Note: This is separate from eBay OAuth integration")

            return auth_system

        except Exception as e:
            logger.error(f"❌ Failed to create unified auth system: {e}")
            raise

    @classmethod
    async def reset_instance(cls):
        """
        Reset the authentication system instance.

        This is primarily for testing and should not be used in production
        unless performing a controlled restart.
        """
        if cls._instance:
            try:
                await cls._instance.cleanup()
            except Exception as e:
                logger.warning(f"Error during auth system cleanup: {e}")

        cls._instance = None
        cls._initialized = False
        logger.info("🔄 Authentication system instance reset")

    @classmethod
    def get_configuration(cls) -> Dict[str, Any]:
        """
        Get current authentication configuration from environment.

        Returns:
            Dict containing authentication configuration
        """
        return {
            "service_type": os.getenv("AUTH_SERVICE_TYPE", "unified"),
            "development_mode": os.getenv("AUTH_DEVELOPMENT_MODE", "false").lower()
            == "true",
            "require_https": os.getenv("AUTH_REQUIRE_HTTPS", "true").lower() == "true",
            "database_enabled": os.getenv("AUTH_DATABASE_ENABLED", "true").lower()
            == "true",
            "token_blacklist_enabled": os.getenv(
                "AUTH_ENABLE_TOKEN_BLACKLIST", "true"
            ).lower()
            == "true",
            "refresh_token_rotation": os.getenv(
                "AUTH_ENABLE_REFRESH_TOKEN_ROTATION", "true"
            ).lower()
            == "true",
            "max_concurrent_sessions": int(
                os.getenv("AUTH_MAX_CONCURRENT_SESSIONS", "5")
            ),
            "jwt_algorithm": os.getenv("JWT_ALGORITHM", "HS256"),
            "jwt_issuer": os.getenv("JWT_ISSUER", "flipsync-api-prod"),
            "jwt_audience": os.getenv("JWT_AUDIENCE", "flipsync-app-prod"),
            "access_token_expire_minutes": int(
                os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
            ),
            "refresh_token_expire_days": int(
                os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")
            ),
        }

    @classmethod
    def validate_configuration(cls) -> bool:
        """
        Validate that required authentication configuration is present.

        Returns:
            bool: True if configuration is valid, False otherwise
        """
        required_vars = ["JWT_SECRET", "JWT_ALGORITHM", "AUTH_SERVICE_TYPE"]

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            logger.error(
                f"❌ Missing required authentication environment variables: {missing_vars}"
            )
            return False

        # Validate JWT secret strength
        jwt_secret = os.getenv("JWT_SECRET", "")
        if len(jwt_secret) < 32:
            logger.error("❌ JWT_SECRET must be at least 32 characters long")
            return False

        logger.info("✅ Authentication configuration validation passed")
        return True


# Convenience function for backward compatibility
async def get_unified_auth_system() -> UnifiedAuthSystem:
    """
    Convenience function to get the unified authentication system.

    This is a shortcut for AuthenticationFactory.get_auth_system()

    Returns:
        UnifiedAuthSystem: The unified authentication system for FlipSync users

    Note:
        This is for FlipSync user authentication only, NOT eBay OAuth
    """
    return await AuthenticationFactory.get_auth_system()


# Configuration validation on module import
def _validate_on_import():
    """Validate configuration when module is imported."""
    if not AuthenticationFactory.validate_configuration():
        logger.warning("⚠️ Authentication configuration validation failed on import")
        logger.warning(
            "🔧 Please check environment variables before using authentication"
        )


# Run validation on import (but don't fail import)
try:
    _validate_on_import()
except Exception as e:
    logger.warning(f"⚠️ Configuration validation error on import: {e}")
