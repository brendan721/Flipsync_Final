"""
Clean eBay OAuth Service for FlipSync - Version 2.0

This service provides a clean, reliable implementation of eBay OAuth 2.0 flow
following eBay's official specification exactly. Designed for plug-and-play
integration with Flutter frontend.

Key Features:
- User-specific credential mapping (testuser -> sandbox, realuser -> production)
- Redis-based token storage with user-scoped isolation
- Automatic token refresh handling
- Comprehensive error handling and logging
- Flutter-friendly JSON responses
- WebSocket integration for real-time status updates
"""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple, Any
from urllib.parse import urlencode

import httpx
import redis.asyncio as redis
from fs_agt_clean.core.config.redis_config_unified import get_global_redis_config
from cryptography.fernet import Fernet
import os

logger = logging.getLogger(__name__)


class EbayCredentials:
    """eBay credentials configuration for different environments."""

    def __init__(
        self,
        environment: str,
        client_id: str,
        client_secret: str,
        runame: str,
        redirect_uri: str,
    ):
        self.environment = environment
        self.client_id = client_id
        self.client_secret = client_secret
        self.runame = runame
        self.redirect_uri = redirect_uri

        # Set eBay URLs based on environment
        if environment == "sandbox":
            self.auth_url = "https://auth.sandbox.ebay.com/oauth2/authorize"
            self.token_url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
        else:
            self.auth_url = "https://auth.ebay.com/oauth2/authorize"
            self.token_url = "https://api.ebay.com/identity/v1/oauth2/token"


class EbayOAuthServiceV2:
    """
    Clean eBay OAuth Service following eBay's OAuth 2.0 specification exactly.

    This service handles:
    - User-specific credential mapping
    - Authorization URL generation
    - Token exchange and refresh
    - Secure token storage in Redis
    - Real-time status updates via WebSocket
    """

    def __init__(
        self,
        redis_host: Optional[str] = None,
        redis_port: Optional[int] = None,
        redis_db: int = 1,
        encryption_key: Optional[str] = None,
    ):
        """
        Initialize the eBay OAuth service.

        Args:
            redis_host: Redis server host
            redis_port: Redis server port
            redis_db: Redis database number (1 for eBay tokens)
            encryption_key: Key for token encryption (generated if not provided)
        """
        # Resolve Redis via unified config (production uses authenticated Redis)
        cfg = get_global_redis_config()
        self.redis_host = redis_host or cfg.host
        self.redis_port = redis_port or cfg.port
        self.redis_db = redis_db
        self._redis_password = cfg.password

        # Initialize encryption
        if encryption_key:
            self.cipher = Fernet(encryption_key.encode())
        else:
            self.cipher = Fernet(Fernet.generate_key())

        # Redis client (initialized lazily)
        self._redis_client: Optional[redis.Redis] = None

        # Credential configurations
        self._credentials = self._load_credentials()

        logger.info("EbayOAuthServiceV2 initialized successfully")

    def _load_credentials(self) -> Dict[str, EbayCredentials]:
        """Load eBay credentials from environment variables with safe fallbacks."""
        # Environment variable names
        SANDBOX_ID = os.getenv("EBAY_SANDBOX_CLIENT_ID")
        SANDBOX_SECRET = os.getenv("EBAY_SANDBOX_CLIENT_SECRET")
        PROD_ID = os.getenv("EBAY_PRODUCTION_CLIENT_ID")
        PROD_SECRET = os.getenv("EBAY_PRODUCTION_CLIENT_SECRET")

        # Existing hardcoded values preserved as fallbacks but not embedded
        # Fetch from a secure default provider or leave None to force env usage
        fallback_sandbox_id = None
        fallback_sandbox_secret = None
        fallback_production_id = None
        fallback_production_secret = None

        # Warn if env vars are missing and fall back
        if not SANDBOX_ID or not SANDBOX_SECRET:
            logger.warning(
                "eBay sandbox credentials not set via env; falling back to configured defaults."
            )
        if not PROD_ID or not PROD_SECRET:
            logger.warning(
                "eBay production credentials not set via env; falling back to configured defaults."
            )

        sandbox_client_id = SANDBOX_ID or fallback_sandbox_id or ""
        sandbox_client_secret = SANDBOX_SECRET or fallback_sandbox_secret or ""
        production_client_id = PROD_ID or fallback_production_id or ""
        production_client_secret = PROD_SECRET or fallback_production_secret or ""

        # RuName and redirect URI remain as configured constants (no secrets)
        sandbox_runame = "Brendan_Blomfie-BrendanB-Nashvi-pzkbhtbtg"
        production_runame = "Brendan_Blomfie-BrendanB-Nashvi-vuwrefym"
        redirect_uri = "https://www.flipsyncai.com/ebay-oauth"

        return {
            "sandbox": EbayCredentials(
                environment="sandbox",
                client_id=sandbox_client_id,
                client_secret=sandbox_client_secret,
                runame=sandbox_runame,
                redirect_uri=redirect_uri,
            ),
            "production": EbayCredentials(
                environment="production",
                client_id=production_client_id,
                client_secret=production_client_secret,
                runame=production_runame,
                redirect_uri=redirect_uri,
            ),
        }

    def _get_credentials_for_user(self, user_id: str) -> EbayCredentials:
        """
        Get eBay credentials based on user ID mapping.

        Args:
            user_id: User identifier

        Returns:
            EbayCredentials for the appropriate environment
        """
        # User-specific credential mapping
        if user_id == "testuser":
            return self._credentials["sandbox"]
        elif user_id == "realuser":
            return self._credentials["production"]
        else:
            # Default to sandbox for unknown users (safer for development)
            logger.warning(
                f"Unknown user_id '{user_id}', defaulting to sandbox credentials"
            )
            return self._credentials["sandbox"]

    async def _get_redis_client(self) -> redis.Redis:
        """Get Redis client with lazy initialization."""
        if self._redis_client is None:
            client_kwargs = {
                "host": self.redis_host,
                "port": self.redis_port,
                "db": self.redis_db,
                "decode_responses": True,
            }
            if self._redis_password:
                client_kwargs["password"] = self._redis_password
            self._redis_client = redis.Redis(**client_kwargs)
            # Test connection
            await self._redis_client.ping()
            logger.info(
                f"Redis client connected: {self.redis_host}:{self.redis_port}/db{self.redis_db}"
            )

        return self._redis_client

    def _encrypt_token(self, token: str) -> str:
        """Encrypt a token for secure storage."""
        return self.cipher.encrypt(token.encode()).decode()

    def _decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt a token from storage."""
        return self.cipher.decrypt(encrypted_token.encode()).decode()

    async def generate_authorization_url(
        self, user_id: str, scopes: Optional[list] = None
    ) -> Tuple[str, str]:
        """
        Generate eBay OAuth authorization URL.

        Args:
            user_id: User identifier for credential mapping
            scopes: List of eBay API scopes to request

        Returns:
            Tuple of (authorization_url, state_parameter)
        """
        credentials = self._get_credentials_for_user(user_id)

        # Default scopes if not provided
        if not scopes:
            scopes = [
                "https://api.ebay.com/oauth/api_scope",
                "https://api.ebay.com/oauth/api_scope/sell.inventory",
                "https://api.ebay.com/oauth/api_scope/sell.account",
                "https://api.ebay.com/oauth/api_scope/sell.fulfillment",
                "https://api.ebay.com/oauth/api_scope/sell.marketing",
            ]

        # Generate secure state parameter
        state = secrets.token_urlsafe(32)

        # Store state data in Redis for validation
        state_data = {
            "user_id": user_id,
            "environment": credentials.environment,
            "scopes": scopes,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "client_id": credentials.client_id,
        }

        redis_client = await self._get_redis_client()
        await redis_client.setex(
            f"oauth_state:{state}", 600, json.dumps(state_data)  # 10 minutes TTL
        )

        # Build authorization URL
        auth_params = {
            "client_id": credentials.client_id,
            "response_type": "code",
            "redirect_uri": credentials.runame,  # eBay requires RuName as redirect_uri
            "scope": " ".join(scopes),
            "state": state,
        }

        auth_url = f"{credentials.auth_url}?{urlencode(auth_params)}"

        logger.info(
            f"Generated OAuth URL for user {user_id} ({credentials.environment})"
        )
        return auth_url, state

    async def exchange_code_for_tokens(self, code: str, state: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access tokens.

        Args:
            code: Authorization code from eBay
            state: State parameter for validation

        Returns:
            Dictionary containing token data and user information

        Raises:
            ValueError: If state validation fails
            Exception: If token exchange fails
        """
        # Validate and retrieve state data
        redis_client = await self._get_redis_client()
        state_data_json = await redis_client.get(f"oauth_state:{state}")

        if not state_data_json:
            raise ValueError("Invalid or expired state parameter")

        state_data = json.loads(state_data_json)
        user_id = state_data["user_id"]
        environment = state_data["environment"]
        scopes = state_data["scopes"]

        # Clean up state data
        await redis_client.delete(f"oauth_state:{state}")

        # Get credentials for token exchange
        credentials = self._get_credentials_for_user(user_id)

        # Prepare token exchange request
        auth_header = base64.b64encode(
            f"{credentials.client_id}:{credentials.client_secret}".encode()
        ).decode()

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {auth_header}",
        }

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": credentials.runame,
        }

        # Exchange code for tokens
        async with httpx.AsyncClient() as client:
            response = await client.post(
                credentials.token_url, headers=headers, data=data, timeout=30.0
            )

            if response.status_code != 200:
                logger.error(
                    f"Token exchange failed: {response.status_code} - {response.text}"
                )
                raise Exception(f"Token exchange failed: {response.text}")

            token_data = response.json()

        # Store tokens securely in Redis
        await self._store_user_tokens(user_id, token_data, scopes)

        logger.info(f"Successfully exchanged code for tokens for user {user_id}")

        return {
            "user_id": user_id,
            "environment": environment,
            "token_type": token_data.get("token_type", "Bearer"),
            "expires_in": token_data.get("expires_in"),
            "scopes": scopes,
            "connected": True,
        }

    async def _store_user_tokens(
        self, user_id: str, token_data: Dict[str, Any], scopes: list
    ) -> None:
        """
        Store user tokens securely in Redis.

        Args:
            user_id: User identifier
            token_data: Token data from eBay
            scopes: Granted scopes
        """
        redis_client = await self._get_redis_client()

        # Encrypt tokens
        encrypted_access_token = self._encrypt_token(token_data["access_token"])
        encrypted_refresh_token = None
        if token_data.get("refresh_token"):
            encrypted_refresh_token = self._encrypt_token(token_data["refresh_token"])

        # Calculate expiry time
        expires_in = token_data.get("expires_in", 7200)  # Default 2 hours
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        # Store token data
        token_record = {
            "access_token": encrypted_access_token,
            "refresh_token": encrypted_refresh_token,
            "token_type": token_data.get("token_type", "Bearer"),
            "expires_at": expires_at.isoformat(),
            "scopes": scopes,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "environment": self._get_credentials_for_user(user_id).environment,
        }

        # Store with user-scoped key
        await redis_client.setex(
            f"ebay_tokens:{user_id}",
            expires_in + 3600,  # Add 1 hour buffer for refresh
            json.dumps(token_record),
        )

        logger.info(f"Stored encrypted tokens for user {user_id}")

    async def get_user_tokens(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get valid tokens for a user, refreshing if necessary.

        Args:
            user_id: User identifier

        Returns:
            Dictionary containing valid token data, or None if no tokens
        """
        redis_client = await self._get_redis_client()
        token_data_json = await redis_client.get(f"ebay_tokens:{user_id}")

        if not token_data_json:
            return None

        token_data = json.loads(token_data_json)

        # Check if token is expired
        expires_at = datetime.fromisoformat(token_data["expires_at"])
        now = datetime.now(timezone.utc)

        # If token expires in less than 5 minutes, refresh it
        if expires_at <= now + timedelta(minutes=5):
            if token_data.get("refresh_token"):
                try:
                    return await self._refresh_user_tokens(user_id, token_data)
                except Exception as e:
                    logger.error(f"Token refresh failed for user {user_id}: {e}")
                    return None
            else:
                logger.warning(f"Token expired and no refresh token for user {user_id}")
                return None

        # Decrypt and return valid tokens
        try:
            decrypted_access_token = self._decrypt_token(token_data["access_token"])
        except Exception as e:
            logger.warning(
                f"Token decryption failed for user {user_id} (likely key mismatch): {e}"
            )
            # Clear invalid tokens to force re-authentication
            await self._clear_invalid_tokens(user_id)
            return None

        return {
            "access_token": decrypted_access_token,
            "token_type": token_data["token_type"],
            "expires_at": expires_at,
            "scopes": token_data["scopes"],
            "environment": token_data["environment"],
        }

    async def _clear_invalid_tokens(self, user_id: str):
        """
        Clear invalid tokens for a user.

        This method removes tokens that cannot be decrypted due to key mismatches
        or other encryption issues, forcing the user to re-authenticate.

        Args:
            user_id: User identifier
        """
        try:
            redis_client = await self._get_redis_client()
            await redis_client.delete(f"ebay_tokens:{user_id}")
            logger.info(
                f"Cleared invalid tokens for user {user_id} - re-authentication required"
            )
        except Exception as e:
            logger.error(f"Failed to clear invalid tokens for user {user_id}: {e}")

    async def _refresh_user_tokens(
        self, user_id: str, token_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Refresh user tokens using refresh token.

        Args:
            user_id: User identifier
            token_data: Current token data

        Returns:
            Dictionary containing refreshed token data
        """
        credentials = self._get_credentials_for_user(user_id)

        # Decrypt refresh token
        try:
            refresh_token = self._decrypt_token(token_data["refresh_token"])
        except Exception as e:
            logger.warning(
                f"Refresh token decryption failed for user {user_id} (likely key mismatch): {e}"
            )
            # Clear invalid tokens to force re-authentication
            await self._clear_invalid_tokens(user_id)
            raise Exception(f"Token decryption failed - re-authentication required")

        # Prepare refresh request
        auth_header = base64.b64encode(
            f"{credentials.client_id}:{credentials.client_secret}".encode()
        ).decode()

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {auth_header}",
        }

        data = {"grant_type": "refresh_token", "refresh_token": refresh_token}

        # Refresh tokens
        async with httpx.AsyncClient() as client:
            response = await client.post(
                credentials.token_url, headers=headers, data=data, timeout=30.0
            )

            if response.status_code != 200:
                logger.error(
                    f"Token refresh failed: {response.status_code} - {response.text}"
                )
                raise Exception(f"Token refresh failed: {response.text}")

            new_token_data = response.json()

        # Store refreshed tokens
        await self._store_user_tokens(user_id, new_token_data, token_data["scopes"])

        logger.info(f"Successfully refreshed tokens for user {user_id}")

        # Return decrypted token data
        return {
            "access_token": new_token_data["access_token"],
            "token_type": new_token_data.get("token_type", "Bearer"),
            "expires_at": datetime.now(timezone.utc)
            + timedelta(seconds=new_token_data.get("expires_in", 7200)),
            "scopes": token_data["scopes"],
            "environment": token_data["environment"],
        }

    async def get_auth_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get authentication status for a user.

        Args:
            user_id: User identifier

        Returns:
            Dictionary containing authentication status
        """
        tokens = await self.get_user_tokens(user_id)

        if not tokens:
            return {
                "authenticated": False,
                "user_id": user_id,
                "environment": self._get_credentials_for_user(user_id).environment,
                "message": "No valid tokens found",
            }

        return {
            "authenticated": True,
            "user_id": user_id,
            "environment": tokens["environment"],
            "token_type": tokens["token_type"],
            "expires_at": tokens["expires_at"].isoformat(),
            "scopes": tokens["scopes"],
            "message": "Authentication valid",
        }

    async def revoke_user_tokens(self, user_id: str) -> bool:
        """
        Revoke and delete user tokens.

        Args:
            user_id: User identifier

        Returns:
            True if tokens were revoked successfully
        """
        try:
            redis_client = await self._get_redis_client()

            # Delete tokens from Redis
            deleted = await redis_client.delete(f"ebay_tokens:{user_id}")

            if deleted:
                logger.info(f"Revoked tokens for user {user_id}")
                return True
            else:
                logger.warning(f"No tokens found to revoke for user {user_id}")
                return False

        except Exception as e:
            logger.error(f"Failed to revoke tokens for user {user_id}: {e}")
            return False

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._redis_client:
            await self._redis_client.close()
            logger.info("Redis client closed")


# Global service instance for dependency injection
_ebay_oauth_service: Optional[EbayOAuthServiceV2] = None


def get_ebay_oauth_service() -> EbayOAuthServiceV2:
    """Get the global eBay OAuth service instance."""
    global _ebay_oauth_service

    if _ebay_oauth_service is None:
        # Use a consistent encryption key from environment or default
        import os

        encryption_key = os.getenv("EBAY_OAUTH_ENCRYPTION_KEY")
        if not encryption_key:
            # Generate a new key if none provided (development only)
            if os.getenv("ENVIRONMENT") == "production":
                raise ValueError("EBAY_OAUTH_ENCRYPTION_KEY must be set in production")
            encryption_key = Fernet.generate_key().decode()
        _ebay_oauth_service = EbayOAuthServiceV2(encryption_key=encryption_key)

    return _ebay_oauth_service
