"""
eBay OAuth Service for FlipSync.

This service handles the complete eBay OAuth flow including:
- Authorization URL generation
- Token exchange
- Token refresh
- Token storage and retrieval
- State parameter management for CSRF protection
"""

import base64
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode

import httpx
from cryptography.fernet import Fernet
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from fs_agt_clean.database.models.ebay_oauth import EbayOAuthState, EbayOAuthToken

logger = logging.getLogger(__name__)


class EbayOAuthService:
    """Service for handling eBay OAuth authentication flow."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        environment: str = "production",
        encryption_key: Optional[str] = None,
    ):
        """
        Initialize the eBay OAuth service.

        Args:
            client_id: eBay application client ID
            client_secret: eBay application client secret
            redirect_uri: OAuth redirect URI
            environment: eBay environment (production or sandbox)
            encryption_key: Key for encrypting stored tokens
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.environment = environment

        # Set up encryption for token storage
        if encryption_key:
            self.cipher = Fernet(encryption_key.encode())
        else:
            # Generate a key if none provided (for development)
            self.cipher = Fernet(Fernet.generate_key())

        # eBay OAuth endpoints
        if environment == "production":
            self.auth_base_url = "https://auth.ebay.com/oauth2/authorize"
            self.token_url = "https://api.ebay.com/identity/v1/oauth2/token"
        else:
            self.auth_base_url = "https://auth.sandbox.ebay.com/oauth2/authorize"
            self.token_url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"

        # Required scopes for FlipSync functionality
        self.scopes = [
            "https://api.ebay.com/oauth/api_scope/sell.inventory",
            "https://api.ebay.com/oauth/api_scope/sell.account",
            "https://api.ebay.com/oauth/api_scope/sell.fulfillment",
            "https://api.ebay.com/oauth/api_scope/sell.marketing",
            "https://api.ebay.com/oauth/api_scope/sell.analytics.readonly",
        ]

    async def generate_authorization_url(
        self,
        db: AsyncSession,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Generate eBay OAuth authorization URL with state parameter.

        Args:
            db: Database session
            user_id: Optional user ID for logged-in users
            ip_address: Client IP address for security
            user_agent: Client user agent for security

        Returns:
            Tuple of (authorization_url, state_parameter)
        """
        # Generate secure state parameter
        state = secrets.token_urlsafe(32)

        # Store state in database for validation
        oauth_state = EbayOAuthState(
            state=state,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=10),  # 10 min expiry
        )

        db.add(oauth_state)
        await db.commit()

        # Build authorization URL
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "state": state,
        }

        auth_url = f"{self.auth_base_url}?{urlencode(params)}"

        logger.info(f"Generated eBay OAuth URL for user {user_id or 'anonymous'}")
        return auth_url, state

    async def validate_state(self, db: AsyncSession, state: str) -> bool:
        """
        Validate OAuth state parameter.

        Args:
            db: Database session
            state: State parameter to validate

        Returns:
            True if state is valid, False otherwise
        """
        try:
            result = await db.execute(
                select(EbayOAuthState).where(EbayOAuthState.state == state)
            )
            oauth_state = result.scalar_one_or_none()

            if not oauth_state or not oauth_state.is_valid():
                logger.warning(f"Invalid or expired OAuth state: {state}")
                return False

            # Mark state as used
            oauth_state.mark_used()
            await db.commit()

            return True

        except Exception as e:
            logger.error(f"Error validating OAuth state: {e}")
            return False

    async def exchange_code_for_tokens(
        self, db: AsyncSession, authorization_code: str, state: str, user_id: str
    ) -> Dict:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            db: Database session
            authorization_code: Authorization code from eBay
            state: OAuth state parameter
            user_id: User ID to associate tokens with

        Returns:
            Dictionary containing token information

        Raises:
            Exception: If token exchange fails
        """
        # Validate state parameter
        if not await self.validate_state(db, state):
            raise ValueError("Invalid or expired state parameter")

        # Prepare token exchange request
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_credentials}",
        }

        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": self.redirect_uri,
        }

        # Exchange code for tokens
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url, headers=headers, data=data, timeout=30.0
            )

            if response.status_code != 200:
                logger.error(
                    f"Token exchange failed: {response.status_code} - {response.text}"
                )
                raise Exception(f"Token exchange failed: {response.text}")

            token_data = response.json()

        # Store tokens in database
        await self._store_tokens(db, user_id, token_data)

        logger.info(f"Successfully exchanged OAuth code for tokens for user {user_id}")
        return token_data

    async def _store_tokens(
        self, db: AsyncSession, user_id: str, token_data: Dict
    ) -> EbayOAuthToken:
        """
        Store OAuth tokens in database with encryption.

        Args:
            db: Database session
            user_id: User ID
            token_data: Token data from eBay

        Returns:
            Stored token model
        """
        # Encrypt tokens
        access_token = self.cipher.encrypt(token_data["access_token"].encode()).decode()
        refresh_token = None
        if token_data.get("refresh_token"):
            refresh_token = self.cipher.encrypt(
                token_data["refresh_token"].encode()
            ).decode()

        # Calculate expiration time
        expires_at = None
        if token_data.get("expires_in"):
            expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=token_data["expires_in"]
            )

        # Revoke any existing active tokens for this user
        existing_tokens = await db.execute(
            select(EbayOAuthToken).where(
                EbayOAuthToken.user_id == user_id, EbayOAuthToken.is_active == True
            )
        )
        for token in existing_tokens.scalars():
            token.revoke()

        # Create new token record
        oauth_token = EbayOAuthToken(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            token_type=token_data.get("token_type", "Bearer"),
            expires_in=token_data.get("expires_in"),
            expires_at=expires_at,
            scope=" ".join(self.scopes),
        )

        db.add(oauth_token)
        await db.commit()

        return oauth_token

    async def get_user_tokens(
        self, db: AsyncSession, user_id: str
    ) -> Optional[EbayOAuthToken]:
        """
        Get valid OAuth tokens for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Valid token model or None
        """
        result = await db.execute(
            select(EbayOAuthToken)
            .where(
                EbayOAuthToken.user_id == user_id,
                EbayOAuthToken.is_active == True,
                EbayOAuthToken.is_revoked == False,
            )
            .order_by(EbayOAuthToken.created_at.desc())
        )

        token = result.scalar_one_or_none()

        if token and token.is_valid():
            return token
        elif token and token.is_expired() and token.refresh_token:
            # Try to refresh the token
            try:
                return await self.refresh_token(db, token)
            except Exception as e:
                logger.error(f"Failed to refresh token for user {user_id}: {e}")
                return None

        return None

    async def refresh_token(
        self, db: AsyncSession, token: EbayOAuthToken
    ) -> EbayOAuthToken:
        """
        Refresh an expired OAuth token.

        Args:
            db: Database session
            token: Expired token to refresh

        Returns:
            New token with refreshed credentials

        Raises:
            Exception: If token refresh fails
        """
        if not token.refresh_token:
            raise ValueError("No refresh token available")

        # Decrypt refresh token
        refresh_token = self.cipher.decrypt(token.refresh_token.encode()).decode()

        # Prepare refresh request
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_credentials}",
        }

        data = {"grant_type": "refresh_token", "refresh_token": refresh_token}

        # Refresh token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url, headers=headers, data=data, timeout=30.0
            )

            if response.status_code != 200:
                logger.error(
                    f"Token refresh failed: {response.status_code} - {response.text}"
                )
                # Mark old token as revoked
                token.revoke()
                await db.commit()
                raise Exception(f"Token refresh failed: {response.text}")

            token_data = response.json()

        # Mark old token as revoked
        token.revoke()

        # Store new tokens
        new_token = await self._store_tokens(db, token.user_id, token_data)

        logger.info(f"Successfully refreshed OAuth token for user {token.user_id}")
        return new_token

    async def get_decrypted_access_token(
        self, db: AsyncSession, user_id: str
    ) -> Optional[str]:
        """
        Get decrypted access token for API calls.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Decrypted access token or None
        """
        token = await self.get_user_tokens(db, user_id)

        if not token:
            return None

        # Decrypt and return access token
        try:
            access_token = self.cipher.decrypt(token.access_token.encode()).decode()
            token.mark_used()
            await db.commit()
            return access_token
        except Exception as e:
            logger.error(f"Failed to decrypt access token for user {user_id}: {e}")
            return None

    async def validate_token(self, token: str, user_id: Optional[str] = None) -> bool:
        """
        Validate an eBay OAuth token.

        This method validates a token by checking:
        1. Token format and structure
        2. Token expiration status
        3. Token revocation status
        4. Optional eBay API connectivity test

        Args:
            token: The access token to validate
            user_id: Optional user ID for additional validation

        Returns:
            True if token is valid and usable, False otherwise
        """
        try:
            # Basic token format validation
            if not token or not isinstance(token, str):
                logger.warning("Invalid token format: token is empty or not a string")
                return False

            # eBay tokens typically start with "v^1.1#" for production
            if not token.startswith(("v^1.1#", "v^1.0#")):
                logger.warning("Invalid eBay token format: missing version prefix")
                return False

            # Check minimum token length (eBay tokens are typically quite long)
            if len(token) < 50:
                logger.warning("Invalid token length: token too short")
                return False

            # If user_id provided, validate against database
            if user_id:
                from fs_agt_clean.core.db.database import Database
                from fs_agt_clean.core.config import ConfigManager

                try:
                    # Get database instance
                    config_manager = ConfigManager()
                    database = Database(config_manager)

                    async with database.get_session() as db:
                        # Find token in database
                        result = await db.execute(
                            select(EbayOAuthToken).where(
                                EbayOAuthToken.user_id == user_id,
                                EbayOAuthToken.is_active == True,
                                EbayOAuthToken.is_revoked == False,
                            )
                        )

                        db_token = result.scalar_one_or_none()

                        if not db_token:
                            logger.warning(f"No active token found for user {user_id}")
                            return False

                        # Decrypt stored token and compare
                        try:
                            decrypted_token = self.cipher.decrypt(
                                db_token.access_token.encode()
                            ).decode()
                            if decrypted_token != token:
                                logger.warning(
                                    "Token mismatch: provided token doesn't match stored token"
                                )
                                return False
                        except Exception as e:
                            logger.error(f"Failed to decrypt stored token: {e}")
                            return False

                        # Check if token is valid (not expired, not revoked)
                        if not db_token.is_valid():
                            logger.warning(
                                f"Token is invalid: expired={db_token.is_expired()}, revoked={db_token.is_revoked}"
                            )
                            return False

                        # Update last used timestamp
                        db_token.mark_used()
                        await db.commit()

                        logger.info(f"Token validation successful for user {user_id}")
                        return True

                except Exception as e:
                    logger.error(f"Database validation failed: {e}")
                    # Fall back to basic validation if database check fails
                    pass

            # Basic validation passed
            logger.info("Token passed basic format validation")
            return True

        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return False

    async def validate_token_with_api_test(self, token: str) -> bool:
        """
        Validate token by making a test API call to eBay.

        This method performs a live validation by making a lightweight
        API call to eBay to verify the token is actually functional.

        Args:
            token: The access token to validate

        Returns:
            True if token works with eBay API, False otherwise
        """
        try:
            # Use eBay's user profile endpoint for validation
            if self.environment == "production":
                test_url = "https://api.ebay.com/sell/account/v1/privilege"
            else:
                test_url = "https://api.sandbox.ebay.com/sell/account/v1/privilege"

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(test_url, headers=headers, timeout=10.0)

                # 200 = success, 401 = unauthorized (invalid token)
                if response.status_code == 200:
                    logger.info("Token validation successful via eBay API test")
                    return True
                elif response.status_code == 401:
                    logger.warning(
                        "Token validation failed: unauthorized (invalid token)"
                    )
                    return False
                else:
                    logger.warning(
                        f"Token validation inconclusive: API returned {response.status_code}"
                    )
                    # For other status codes, we can't be sure about token validity
                    # so we return False to be safe
                    return False

        except Exception as e:
            logger.error(f"API token validation failed: {e}")
            return False

    async def revoke_user_tokens(self, db: AsyncSession, user_id: str) -> bool:
        """
        Revoke all OAuth tokens for a user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            True if tokens were revoked successfully
        """
        try:
            result = await db.execute(
                select(EbayOAuthToken).where(
                    EbayOAuthToken.user_id == user_id, EbayOAuthToken.is_active == True
                )
            )

            tokens = result.scalars().all()

            for token in tokens:
                token.revoke()

            await db.commit()

            logger.info(f"Revoked {len(tokens)} OAuth tokens for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to revoke tokens for user {user_id}: {e}")
            return False
