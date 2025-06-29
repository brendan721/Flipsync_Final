"""eBay Marketplace API endpoints for FlipSync.

This module implements the API endpoints for eBay marketplace integration,
including authentication, listing management, order processing, and inventory synchronization.
Enhanced with real OAuth flow support for production-ready eBay integration.
"""

import base64
import logging
import os
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode, urlparse, parse_qs

import aiohttp
import redis.asyncio as redis
import json
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from fs_agt_clean.core.marketplace.ebay.api_client import EbayAPIClient
from fs_agt_clean.core.marketplace.ebay.config import EbayConfig
from fs_agt_clean.core.metrics.compat import get_metrics_service
from fs_agt_clean.core.models.api_response import ApiResponse
from fs_agt_clean.core.models.listing import ListingStatus
from fs_agt_clean.core.models.user import UnifiedUser
from fs_agt_clean.core.security.auth import get_current_user, get_current_user_optional
from fs_agt_clean.database.repositories.listing_repository import ListingRepository
from fs_agt_clean.database.repositories.marketplace_repository import (
    MarketplaceRepository,
)
from fs_agt_clean.services.marketplace.ebay.compat import get_ebay_service
from fs_agt_clean.services.notifications.compat import get_notification_service

# Initialize logger
logger = logging.getLogger(__name__)

# Create router with prefix
router = APIRouter(
    prefix="",
    tags=["ebay-marketplace"],
    responses={404: {"description": "Not found"}},
)


# Request and response models
class EbayAuthRequest(BaseModel):
    """eBay authentication request model."""

    client_id: str = Field(..., description="eBay client ID")
    client_secret: str = Field(..., description="eBay client secret")
    refresh_token: Optional[str] = Field(None, description="eBay refresh token")
    scopes: Optional[List[str]] = Field(None, description="eBay API scopes")


class EbayOAuthRequest(BaseModel):
    """eBay OAuth authorization request model."""

    scopes: Optional[List[str]] = Field(
        default=[
            "https://api.ebay.com/oauth/api_scope",
            "https://api.ebay.com/oauth/api_scope/sell.marketing.readonly",
            "https://api.ebay.com/oauth/api_scope/sell.marketing",
            "https://api.ebay.com/oauth/api_scope/sell.inventory.readonly",
            "https://api.ebay.com/oauth/api_scope/sell.inventory",
            "https://api.ebay.com/oauth/api_scope/sell.account.readonly",
            "https://api.ebay.com/oauth/api_scope/sell.account",
            "https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly",
            "https://api.ebay.com/oauth/api_scope/sell.fulfillment",
            "https://api.ebay.com/oauth/api_scope/sell.analytics.readonly",
            "https://api.ebay.com/oauth/api_scope/sell.finances",
            "https://api.ebay.com/oauth/api_scope/sell.payment.dispute",
            "https://api.ebay.com/oauth/api_scope/commerce.identity.readonly",
        ],
        description="eBay API scopes to request",
    )


class EbayOAuthCallbackRequest(BaseModel):
    """eBay OAuth callback request model."""

    code: str = Field(..., description="Authorization code from eBay")
    state: Optional[str] = Field(None, description="State parameter for security")


# Redis client for OAuth state storage
_redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    """Get Redis client for OAuth state storage."""
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        _redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
    return _redis_client


async def store_oauth_state(state: str, data: Dict[str, Any], ttl: int = 3600) -> None:
    """Store OAuth state in Redis with TTL."""
    redis_client = await get_redis_client()
    await redis_client.setex(f"oauth_state:{state}", ttl, json.dumps(data))


async def get_oauth_state(state: str) -> Optional[Dict[str, Any]]:
    """Get OAuth state from Redis."""
    redis_client = await get_redis_client()
    data = await redis_client.get(f"oauth_state:{state}")
    if data:
        return json.loads(data)
    return None


async def delete_oauth_state(state: str) -> None:
    """Delete OAuth state from Redis."""
    redis_client = await get_redis_client()
    await redis_client.delete(f"oauth_state:{state}")


async def get_ebay_credentials(user_id: str = "test_user") -> Optional[Dict[str, Any]]:
    """Get eBay credentials for a user from Redis storage."""
    try:
        redis_client = await get_redis_client()
        key = f"marketplace:ebay:{user_id}"
        data = await redis_client.get(key)
        if data:
            credentials = json.loads(data)
            logger.info(f"Retrieved eBay credentials for user {user_id}")
            return credentials
        else:
            logger.warning(f"No eBay credentials found for user {user_id}")
            return None
    except Exception as e:
        logger.error(f"Error retrieving eBay credentials: {e}")
        return None


async def update_ebay_client_credentials() -> bool:
    """Update eBay client instances with stored OAuth credentials."""
    try:
        credentials = await get_ebay_credentials()
        if not credentials:
            logger.warning("No eBay credentials available to update clients")
            return False

        # Notify all eBay clients/agents about new credentials
        # This would typically be done through a message queue or event system
        # For now, we'll store a flag that clients can check
        redis_client = await get_redis_client()
        await redis_client.setex(
            "ebay:credentials_updated", 300, "true"
        )  # 5 minute flag

        logger.info("eBay client credentials update notification sent")
        return True
    except Exception as e:
        logger.error(f"Error updating eBay client credentials: {e}")
        return False


class EbayListingRequest(BaseModel):
    """eBay listing request model."""

    title: str = Field(..., description="Product title")
    description: str = Field(..., description="Product description")
    price: float = Field(..., description="Product price")
    quantity: int = Field(..., description="Product quantity")
    sku: str = Field(..., description="Product SKU")
    category_id: str = Field(..., description="eBay category ID")
    images: List[str] = Field([], description="Product image URLs")
    attributes: Dict[str, Any] = Field({}, description="Product attributes")


class EbayOrderRequest(BaseModel):
    """eBay order processing request model."""

    order_ids: List[str] = Field(..., description="Order IDs to process")
    action: str = Field(
        ..., description="Action to perform (acknowledge, fulfill, ship)"
    )
    shipping_info: Optional[Dict[str, Any]] = Field(
        None, description="Shipping information"
    )


class EbayInventoryRequest(BaseModel):
    """eBay inventory update request model."""

    items: List[Dict[str, Any]] = Field(..., description="Inventory items to update")


# Dependencies
async def get_marketplace_repository() -> MarketplaceRepository:
    """Get the marketplace repository instance."""

    # Use Redis-based storage for eBay credentials
    class RedisMarketplaceRepository:
        def __init__(self):
            self.redis_prefix = "marketplace:ebay:"

        async def get_by_type(self, user_id: str, marketplace_type: str):
            """Get marketplace credentials from Redis."""
            if marketplace_type != "ebay":
                return None

            try:
                redis_client = await get_redis_client()
                key = f"{self.redis_prefix}{user_id}"
                data = await redis_client.get(key)
                if data:
                    credentials = json.loads(data)

                    # Create a marketplace object with has_valid_tokens method
                    class MarketplaceConnection:
                        def __init__(self, user_id, credentials):
                            self.id = f"ebay_{user_id}"
                            self.credentials = credentials
                            self.access_token = credentials.get("access_token")
                            self.token_expires_at = None
                            if credentials.get("expires_at"):
                                try:
                                    from datetime import datetime

                                    self.token_expires_at = datetime.fromisoformat(
                                        credentials["expires_at"]
                                    )
                                except:
                                    pass
                            self.is_connected = bool(self.access_token)
                            self.last_sync_at = None
                            self.ebay_user_id = credentials.get("ebay_user_id")
                            self.ebay_username = credentials.get("ebay_username")

                        def has_valid_tokens(self) -> bool:
                            """Check if the connection has valid OAuth tokens."""
                            if not self.access_token:
                                return False

                            if self.token_expires_at:
                                from datetime import datetime, timezone

                                if self.token_expires_at <= datetime.now(timezone.utc):
                                    return False

                            return True

                    return MarketplaceConnection(user_id, credentials)
                return None
            except Exception as e:
                logger.error(f"Error getting marketplace from Redis: {e}")
                return None

        async def create_marketplace(
            self, user_id: str, name: str, marketplace_type: str, credentials: dict
        ):
            """Store marketplace credentials in Redis."""
            if marketplace_type != "ebay":
                return None

            try:
                redis_client = await get_redis_client()
                key = f"{self.redis_prefix}{user_id}"

                # Store credentials with 30-day expiry
                await redis_client.setex(key, 30 * 24 * 3600, json.dumps(credentials))

                logger.info(f"eBay credentials stored for user {user_id}")
                return type(
                    "Marketplace",
                    (),
                    {"id": f"ebay_{user_id}", "credentials": credentials},
                )()
            except Exception as e:
                logger.error(f"Error storing marketplace in Redis: {e}")
                return None

        async def update_credentials(self, marketplace_id: str, credentials: dict):
            """Update marketplace credentials in Redis."""
            try:
                # Extract user_id from marketplace_id
                user_id = marketplace_id.replace("ebay_", "")
                redis_client = await get_redis_client()
                key = f"{self.redis_prefix}{user_id}"

                # Update credentials with 30-day expiry
                await redis_client.setex(key, 30 * 24 * 3600, json.dumps(credentials))

                logger.info(f"eBay credentials updated for user {user_id}")
                return type(
                    "Marketplace",
                    (),
                    {"id": marketplace_id, "credentials": credentials},
                )()
            except Exception as e:
                logger.error(f"Error updating marketplace in Redis: {e}")
                return None

    return RedisMarketplaceRepository()


async def get_listing_repository() -> ListingRepository:
    """Get the listing repository instance."""

    # For now, return a mock repository that doesn't require database session
    # In production, this would use proper dependency injection with database session
    class MockListingRepository:
        async def create_listing(self, **kwargs):
            return None

    return MockListingRepository()


@router.post("/oauth/authorize", response_model=ApiResponse)
async def get_ebay_oauth_url(
    oauth_request: EbayOAuthRequest,
    current_user: Optional[UnifiedUser] = Depends(get_current_user_optional),
):
    """
    Generate eBay OAuth authorization URL.

    This endpoint generates the OAuth authorization URL for eBay marketplace integration
    using the configured RuName 'Brendan_Blomfie-BrendanB-Nashvi-lkajdgn'.
    """
    try:
        # Get eBay credentials from environment - Use PRODUCTION credentials
        client_id = os.getenv("EBAY_APP_ID")  # Production App ID
        if not client_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="eBay production client ID not configured in environment",
            )

        # Generate state parameter for security
        state = secrets.token_urlsafe(32)

        # Store state with user info in Redis
        state_data = {
            "user_id": (
                current_user.id if current_user else "anonymous"
            ),  # Handle optional user
            "scopes": oauth_request.scopes,
            "created_at": datetime.now().isoformat(),
            "authenticated": current_user is not None,
        }
        await store_oauth_state(state, state_data, ttl=3600)  # 1 hour TTL

        # eBay OAuth parameters - Use PRODUCTION RuName as redirect_uri
        ru_name = "Brendan_Blomfie-BrendanB-Nashvi-vuwrefym"  # Production RuName
        callback_url = os.getenv(
            "EBAY_CALLBACK_URL", "https://www.flipsyncai.com/ebay-oauth"
        )  # Production callback
        scope = " ".join(oauth_request.scopes)

        # Build authorization URL - CRITICAL: Use RuName as redirect_uri for eBay OAuth
        auth_params = {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": ru_name,  # eBay requires RuName, not callback URL
            "scope": scope,
            "state": state,
        }

        # Use production URL for live eBay integration
        base_url = "https://auth.ebay.com/oauth2/authorize"
        auth_url = f"{base_url}?{urlencode(auth_params)}"

        return ApiResponse(
            status=200,
            message="OAuth authorization URL generated successfully",
            success=True,
            data={
                "authorization_url": auth_url,
                "state": state,
                "ru_name": ru_name,
                "callback_url": callback_url,
                "scopes": oauth_request.scopes,
                "expires_in": 600,  # 10 minutes
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate OAuth URL: {str(e)}",
        )


@router.post("/oauth/callback", response_model=ApiResponse)
async def handle_ebay_oauth_callback(
    callback_request: EbayOAuthCallbackRequest,
    current_user: Optional[UnifiedUser] = Depends(get_current_user_optional),
    marketplace_repo: MarketplaceRepository = Depends(get_marketplace_repository),
):
    """
    Handle eBay OAuth callback and exchange authorization code for tokens.

    This endpoint processes the OAuth callback from eBay and exchanges the
    authorization code for access and refresh tokens.
    """
    try:
        # Validate state parameter
        if not callback_request.state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired state parameter",
            )

        state_data = await get_oauth_state(callback_request.state)
        if not state_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired state parameter",
            )

        # Handle both authenticated and unauthenticated OAuth flows
        user_id = state_data.get("user_id")
        scopes = state_data.get("scopes", [])

        # If no user_id in state, try to get from current_user
        if not user_id and current_user:
            user_id = current_user.id
            logger.info(f"Using current user ID for OAuth: {user_id}")
        elif not user_id:
            # For unauthenticated OAuth, create a temporary user or handle differently
            logger.warning(
                "No user_id available for OAuth callback - this may require user authentication"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User authentication required for eBay connection",
            )

        # Clean up state
        await delete_oauth_state(callback_request.state)

        # Get eBay credentials from environment - Use PRODUCTION credentials
        client_id = os.getenv("EBAY_APP_ID")  # Production App ID
        client_secret = os.getenv("EBAY_CERT_ID")  # Production Cert ID

        if not client_id or not client_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="eBay production credentials not configured in environment",
            )

        # Exchange authorization code for tokens
        # CRITICAL: redirect_uri must match exactly what was used in authorization URL (RuName)
        redirect_uri = "Brendan_Blomfie-BrendanB-Nashvi-vuwrefym"  # Production RuName
        token_data = await exchange_authorization_code(
            client_id=client_id,
            client_secret=client_secret,
            code=callback_request.code,
            redirect_uri=redirect_uri,
        )

        # Store credentials in database
        existing_marketplace = await marketplace_repo.get_by_type(
            user_id=user_id, marketplace_type="ebay"
        )

        credentials = {
            "client_id": client_id,
            "client_secret": client_secret,
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token"),
            "token_type": token_data.get("token_type", "Bearer"),
            "expires_in": token_data.get("expires_in"),
            "scopes": scopes,
            "token_expiry": (
                datetime.now().timestamp() + token_data.get("expires_in", 7200)
            ),
        }

        if existing_marketplace:
            marketplace = await marketplace_repo.update_credentials(
                marketplace_id=existing_marketplace.id, credentials=credentials
            )
        else:
            marketplace = await marketplace_repo.create_marketplace(
                user_id=user_id,
                name="eBay",
                marketplace_type="ebay",
                credentials=credentials,
            )

        # Update eBay client credentials after successful OAuth
        await update_ebay_client_credentials()

        return ApiResponse(
            status=200,
            message="Successfully authenticated with eBay via OAuth",
            success=True,
            data={
                "marketplace_id": marketplace.id if marketplace else None,
                "token_type": token_data.get("token_type", "Bearer"),
                "expires_in": token_data.get("expires_in"),
                "scopes": scopes,
                "connected": True,
            },
        )
    except Exception as e:
        # Return JSON error response for AJAX requests from Flutter web app
        # This fixes the CORS issue caused by RedirectResponse
        logger.error(f"eBay OAuth callback error: {str(e)}")
        return ApiResponse(
            status=400,
            message=f"eBay OAuth failed: {str(e)}",
            success=False,
            data={
                "marketplace": "ebay",
                "connected": False,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )


async def exchange_authorization_code(
    client_id: str, client_secret: str, code: str, redirect_uri: str
) -> Dict[str, Any]:
    """
    Exchange eBay authorization code for access and refresh tokens.

    Args:
        client_id: eBay application client ID
        client_secret: eBay application client secret
        code: Authorization code from eBay OAuth callback
        redirect_uri: Must match exactly the redirect_uri used in authorization URL
    """
    # Prepare credentials for Basic Auth
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }

    # Use production token endpoint
    token_url = "https://api.ebay.com/identity/v1/oauth2/token"

    async with aiohttp.ClientSession() as session:
        async with session.post(token_url, headers=headers, data=data) as response:
            response_text = await response.text()

            if response.status != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Token exchange failed: {response_text}",
                )

            try:
                return await response.json()
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Invalid token response: {str(e)}",
                )


# OPTIONS handlers for CORS preflight
@router.options("/status")
async def options_ebay_status():
    """Handle CORS preflight for eBay status endpoint."""
    return {"message": "OK"}


@router.options("/status/public")
async def options_ebay_status_public():
    """Handle CORS preflight for eBay public status endpoint."""
    return {"message": "OK"}


# Public status endpoint (no authentication required)
@router.get("/status/public", response_model=ApiResponse)
async def get_ebay_marketplace_status_public():
    """
    Get eBay marketplace connection status without authentication.

    This endpoint returns basic eBay marketplace status information
    without requiring user authentication.
    """
    return ApiResponse(
        status=200,
        message="eBay marketplace status retrieved",
        success=True,
        data={
            "ebay_connected": False,  # Default to false for unauthenticated requests
            "amazon_connected": False,  # For compatibility
            "connection_status": "not_connected",
            "last_sync": None,
            "credentials_valid": False,
            "authentication_required": True,
            "login_required": "Please log in to view your eBay connection status",
        },
    )


@router.get("/status", response_model=ApiResponse)
async def get_ebay_marketplace_status(
    current_user: UnifiedUser = Depends(get_current_user),
    marketplace_repo: MarketplaceRepository = Depends(get_marketplace_repository),
):
    """
    Get eBay marketplace connection status.

    This endpoint returns the current connection status for eBay marketplace integration.
    """
    try:
        # Get the marketplace
        marketplace = await marketplace_repo.get_by_type(
            user_id=current_user.id, marketplace_type="ebay"
        )

        if not marketplace:
            return ApiResponse(
                status=200,
                message="eBay marketplace status retrieved",
                success=True,
                data={
                    "ebay_connected": False,
                    "amazon_connected": False,  # For compatibility
                    "connection_status": "not_connected",
                    "last_sync": None,
                    "credentials_valid": False,
                },
            )

        # Check if credentials are valid and not expired
        credentials_valid = marketplace.has_valid_tokens()

        return ApiResponse(
            status=200,
            message="eBay marketplace status retrieved",
            success=True,
            data={
                "ebay_connected": True,
                "amazon_connected": False,  # For compatibility
                "connection_status": "connected" if credentials_valid else "expired",
                "last_sync": (
                    marketplace.last_sync_at.isoformat()
                    if marketplace.last_sync_at
                    else None
                ),
                "credentials_valid": credentials_valid,
                "marketplace_id": marketplace.id,
                "ebay_user_id": marketplace.ebay_user_id,
                "ebay_username": marketplace.ebay_username,
                "is_connected": marketplace.is_connected,
                "token_expires_at": (
                    marketplace.token_expires_at.isoformat()
                    if marketplace.token_expires_at
                    else None
                ),
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get marketplace status: {str(e)}",
        )


@router.get("/test-connection", response_model=ApiResponse)
async def test_ebay_connection():
    """
    Test eBay connection without authentication (for testing purposes).

    This endpoint tests the eBay integration and credential storage
    without requiring user authentication.
    """
    try:
        # Check if any eBay credentials are stored
        credentials = await get_ebay_credentials("test_user")

        if credentials:
            return ApiResponse(
                status=200,
                message="eBay credentials found",
                success=True,
                data={
                    "credentials_stored": True,
                    "client_id": credentials.get("client_id", "")[:20] + "...",
                    "has_access_token": bool(credentials.get("access_token")),
                    "has_refresh_token": bool(credentials.get("refresh_token")),
                    "scopes": credentials.get("scopes", []),
                    "storage_backend": "redis",
                },
            )
        else:
            return ApiResponse(
                status=200,
                message="No eBay credentials found",
                success=True,
                data={
                    "credentials_stored": False,
                    "storage_backend": "redis",
                    "message": "Complete eBay OAuth flow to store credentials",
                },
            )
    except Exception as e:
        logger.error(f"Error testing eBay connection: {e}")
        return ApiResponse(
            status=500,
            message=f"eBay connection test failed: {str(e)}",
            success=False,
            data={"error": str(e)},
        )


@router.get("/test-real-api", response_model=ApiResponse)
async def test_real_ebay_api():
    """
    Test real eBay API calls using stored OAuth credentials.

    This endpoint bypasses user authentication and uses stored OAuth credentials
    to make actual eBay API calls to verify the connection is working.
    """
    try:
        # Import eBay client
        from fs_agt_clean.agents.market.ebay_client import eBayClient

        # Create eBay client instance
        ebay_client = eBayClient()

        # Check if OAuth credentials are available
        if not await ebay_client.validate_credentials():
            return ApiResponse(
                status=401,
                message="No valid eBay credentials available",
                success=False,
                data={
                    "error": "OAuth credentials not found or expired",
                    "suggestion": "Complete eBay OAuth flow to authenticate",
                },
            )

        # Try to make a real eBay API call
        try:
            # Test with a simple inventory search
            listings = await ebay_client.search_products("iPhone", limit=5)

            return ApiResponse(
                status=200,
                message="eBay API connection successful",
                success=True,
                data={
                    "api_connection": "working",
                    "credentials_valid": True,
                    "test_results": {
                        "search_query": "iPhone",
                        "results_count": len(listings),
                        "sample_items": [
                            {
                                "title": (
                                    item.title[:50] + "..."
                                    if len(item.title) > 50
                                    else item.title
                                ),
                                "price": str(item.price),
                                "item_id": item.item_id,
                            }
                            for item in listings[:3]  # Show first 3 items
                        ],
                    },
                },
            )

        except Exception as api_error:
            return ApiResponse(
                status=500,
                message="eBay API call failed",
                success=False,
                data={
                    "api_connection": "failed",
                    "credentials_valid": True,
                    "error": str(api_error),
                    "error_type": type(api_error).__name__,
                },
            )

    except Exception as e:
        logger.error(f"Error testing real eBay API: {e}")
        return ApiResponse(
            status=500,
            message=f"eBay API test failed: {str(e)}",
            success=False,
            data={"error": str(e)},
        )


@router.post("/auth", response_model=ApiResponse)
async def authenticate_ebay(
    auth_request: EbayAuthRequest,
    current_user: UnifiedUser = Depends(get_current_user),
    marketplace_repo: MarketplaceRepository = Depends(get_marketplace_repository),
):
    """
    Authenticate with eBay Marketplace.

    This endpoint handles authentication with the eBay Marketplace API,
    storing credentials securely for future API calls.
    """
    try:
        # Create eBay config
        ebay_config = EbayConfig(
            client_id=auth_request.client_id,
            client_secret=auth_request.client_secret,
            scopes=auth_request.scopes,
        )

        # Create eBay API client
        api_client = EbayAPIClient(ebay_config.api_base_url)

        # Get the eBay service
        ebay_service = get_ebay_service(
            config=ebay_config,
            api_client=api_client,
            metrics_service=get_metrics_service(),
            notification_service=get_notification_service(),
        )

        # Test the connection
        auth_result = await ebay_service.authenticate()

        # Store the credentials in the database
        existing_marketplace = await marketplace_repo.get_by_type(
            user_id=current_user.id, marketplace_type="ebay"
        )

        credentials = {
            "client_id": auth_request.client_id,
            "client_secret": auth_request.client_secret,
            "refresh_token": auth_request.refresh_token,
            "scopes": auth_request.scopes,
            "token": auth_result.get("access_token"),
            "token_expiry": auth_result.get("expires_at"),
        }

        if existing_marketplace:
            # Update existing marketplace
            marketplace = await marketplace_repo.update_credentials(
                marketplace_id=existing_marketplace.id, credentials=credentials
            )
        else:
            # Create new marketplace
            marketplace = await marketplace_repo.create_marketplace(
                user_id=current_user.id,
                name="eBay",
                marketplace_type="ebay",
                credentials=credentials,
            )

        return ApiResponse(
            status=200,
            message="Successfully authenticated with eBay",
            success=True,
            data={
                "marketplace_id": marketplace.id if marketplace else None,
                "account_id": auth_result.get("account_id"),
                "username": auth_result.get("username"),
                "scopes": auth_result.get("scopes", []),
                "expires_at": auth_result.get("expires_at"),
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to authenticate with eBay: {str(e)}",
        )


@router.get("/listings", response_model=ApiResponse)
async def get_ebay_listings(
    status: Optional[ListingStatus] = Query(
        None, description="Filter by listing status"
    ),
    limit: int = Query(100, description="Maximum number of listings to return"),
    offset: int = Query(0, description="Offset for pagination"),
    current_user: UnifiedUser = Depends(get_current_user),  # noqa: B008
):
    """
    Get eBay listings.

    This endpoint retrieves listings from eBay Marketplace with optional filtering.
    """
    try:
        # Get eBay credentials for the current user
        credentials = await get_ebay_credentials(current_user.username)

        if not credentials:
            # Return empty response if no credentials
            return ApiResponse(
                status=200,
                message="No eBay credentials found - please connect your eBay account",
                success=True,
                data={
                    "listings": [],
                    "total": 0,
                    "limit": limit,
                    "offset": offset,
                },
            )

        # Use the eBay client directly for inventory API calls
        from fs_agt_clean.agents.market.ebay_client import eBayClient

        async with eBayClient() as ebay_client:
            # Update client with OAuth credentials
            await ebay_client._check_oauth_credentials()

            # Make direct API call to eBay Inventory API
            endpoint = "/sell/inventory/v1/inventory_item"
            params = {"limit": min(limit, 200), "offset": offset}

            inventory_response = await ebay_client._make_request(
                "GET", endpoint, params=params
            )

        # Extract inventory items
        inventory_items = inventory_response.get("inventoryItems", [])

        # Apply pagination
        start_index = offset
        end_index = offset + limit
        paginated_items = inventory_items[start_index:end_index]

        # Format listings for response
        formatted_listings = []
        for item in paginated_items:
            formatted_listings.append(
                {
                    "id": item.get("sku", f"ebay_item_{item.get('itemId', 'unknown')}"),
                    "title": item.get("product", {}).get("title", "Unknown Item"),
                    "price": float(
                        item.get("offers", [{}])[0].get("price", {}).get("value", 0.0)
                    ),
                    "quantity": int(
                        item.get("availability", {})
                        .get("shipToLocationAvailability", {})
                        .get("quantity", 0)
                    ),
                    "status": (
                        "ACTIVE"
                        if item.get("availability", {})
                        .get("shipToLocationAvailability", {})
                        .get("quantity", 0)
                        > 0
                        else "INACTIVE"
                    ),
                    "sku": item.get("sku", ""),
                    "url": f"https://www.ebay.com/itm/{item.get('itemId', '')}",
                    "created_at": item.get("createdDate", datetime.now().isoformat()),
                    "updated_at": item.get(
                        "lastModifiedDate", datetime.now().isoformat()
                    ),
                }
            )

        return ApiResponse(
            status=200,
            message="Successfully retrieved eBay listings",
            success=True,
            data={
                "listings": formatted_listings,
                "total": len(inventory_items),
                "limit": limit,
                "offset": offset,
            },
        )
    except Exception as e:
        logger.error(f"Error retrieving eBay listings: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve eBay listings: {str(e)}",
        )


@router.post("/listings", response_model=ApiResponse)
async def create_ebay_listing(
    listing_request: EbayListingRequest,
    current_user: UnifiedUser = Depends(get_current_user),
    marketplace_repo: MarketplaceRepository = Depends(get_marketplace_repository),
    listing_repo: ListingRepository = Depends(get_listing_repository),
):
    """
    Create a new eBay listing.

    This endpoint creates a new listing on eBay Marketplace.
    """
    try:
        # Get the marketplace
        marketplace = await marketplace_repo.get_by_type(
            user_id=current_user.id, marketplace_type="ebay"
        )

        if not marketplace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="eBay marketplace not found. Please authenticate first.",
            )

        # Create eBay config
        ebay_config = EbayConfig(
            client_id=marketplace.credentials.get("client_id"),
            client_secret=marketplace.credentials.get("client_secret"),
            scopes=marketplace.credentials.get("scopes"),
        )

        # Create eBay API client
        api_client = EbayAPIClient(ebay_config.api_base_url)

        # Get the eBay service
        ebay_service = get_ebay_service(
            config=ebay_config,
            api_client=api_client,
            metrics_service=get_metrics_service(),
            notification_service=get_notification_service(),
        )

        # Create the listing on eBay
        product_data = {
            "title": listing_request.title,
            "description": listing_request.description,
            "price": listing_request.price,
            "quantity": listing_request.quantity,
            "sku": listing_request.sku,
            "category_id": listing_request.category_id,
            "images": listing_request.images,
            "attributes": listing_request.attributes,
        }

        # Submit to eBay API
        listing_id = await ebay_service.create_product(
            seller_id=marketplace.credentials.get("account_id"),
            inventory_id=listing_request.sku,
            product_data=product_data,
        )

        # Create a dummy inventory item ID (in a real implementation, this would come from the inventory service)
        inventory_item_id = f"inv_{listing_request.sku}"

        # Store the listing in the database
        listing = await listing_repo.create_listing(
            marketplace_id=marketplace.id,
            inventory_item_id=inventory_item_id,
            external_id=listing_id,
            title=listing_request.title,
            description=listing_request.description,
            price=listing_request.price,
            quantity=listing_request.quantity,
            status="active",
            data=product_data,
        )

        return ApiResponse(
            status=201,
            message="Successfully created eBay listing",
            success=True,
            data={
                "listing_id": listing.id,
                "marketplace_id": marketplace.id,
                "ebay_item_id": listing_id,
                "sku": listing_request.sku,
                "url": f"https://www.ebay.com/itm/{listing_id}",
                "created_at": listing.created_at.isoformat(),
                "updated_at": listing.updated_at.isoformat(),
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create eBay listing: {str(e)}",
        )


@router.get("/listings/{listing_id}", response_model=ApiResponse)
async def get_ebay_listing(
    listing_id: str = Path(..., description="The eBay listing ID"),
    current_user: UnifiedUser = Depends(get_current_user),  # noqa: B008
):
    """
    Get a specific eBay listing.

    This endpoint retrieves details for a specific eBay listing.
    """
    # Implementation would include:
    # 1. Validate listing ID
    # 2. Query eBay API for listing details
    # 3. Format response data

    # Mock implementation for structure
    return ApiResponse(
        status=200,
        message="Successfully retrieved eBay listing",
        success=True,
        data={
            "id": listing_id,
            "title": "Wireless Bluetooth Headphones",
            "description": "High-quality wireless headphones with noise cancellation",
            "price": 49.99,
            "quantity": 10,
            "status": "ACTIVE",
            "sku": "WBH-001",
            "url": f"https://www.ebay.com/itm/{listing_id}",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "category_id": "123456",
            "category_name": "Cell Phones & Accessories",
            "condition": "New",
            "images": [
                {
                    "url": "https://i.ebayimg.com/images/g/abc/s-l1600.jpg",
                    "is_primary": True,
                },
                {
                    "url": "https://i.ebayimg.com/images/g/def/s-l1600.jpg",
                    "is_primary": False,
                },
            ],
            "shipping_options": [
                {
                    "service": "Standard",
                    "cost": 4.99,
                    "estimated_delivery_days": "3-5",
                },
                {
                    "service": "Expedited",
                    "cost": 9.99,
                    "estimated_delivery_days": "1-2",
                },
            ],
        },
    )


@router.put("/listings/{listing_id}", response_model=ApiResponse)
async def update_ebay_listing(
    listing_data: Dict,
    listing_id: str = Path(..., description="The eBay listing ID"),
    current_user: UnifiedUser = Depends(get_current_user),  # noqa: B008
):
    """
    Update an eBay listing.

    This endpoint updates an existing listing on eBay Marketplace.
    """
    # Implementation would include:
    # 1. Validate listing data
    # 2. Format for eBay API
    # 3. Submit listing update
    # 4. Handle response and errors

    # Mock implementation for structure
    return ApiResponse(
        status=200,
        message="Successfully updated eBay listing",
        success=True,
        data={
            "listing_id": listing_id,
            "updated_fields": list(listing_data.keys()),
            "url": f"https://www.ebay.com/itm/{listing_id}",
        },
    )


@router.delete("/listings/{listing_id}", response_model=ApiResponse)
async def delete_ebay_listing(
    listing_id: str = Path(..., description="The eBay listing ID"),
    current_user: UnifiedUser = Depends(get_current_user),  # noqa: B008
):
    """
    Delete an eBay listing.

    This endpoint deletes an existing listing from eBay Marketplace.
    """
    # Implementation would include:
    # 1. Validate listing ID
    # 2. Submit deletion request to eBay API
    # 3. Handle response and errors

    # Mock implementation for structure
    return ApiResponse(
        status=200,
        message="Successfully deleted eBay listing",
        success=True,
        data={
            "listing_id": listing_id,
            "deleted_at": datetime.now().isoformat(),
        },
    )


@router.post("/orders", response_model=ApiResponse)
async def process_ebay_orders(
    order_request: EbayOrderRequest,
    current_user: UnifiedUser = Depends(get_current_user),
    marketplace_repo: MarketplaceRepository = Depends(get_marketplace_repository),
):
    """
    Process eBay orders.

    This endpoint handles processing of eBay orders, including
    acknowledgment, fulfillment, and shipping confirmation.
    """
    try:
        # Get the marketplace
        marketplace = await marketplace_repo.get_by_type(
            user_id=current_user.id, marketplace_type="ebay"
        )

        if not marketplace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="eBay marketplace not found. Please authenticate first.",
            )

        # Create eBay config
        ebay_config = EbayConfig(
            client_id=marketplace.credentials.get("client_id"),
            client_secret=marketplace.credentials.get("client_secret"),
            scopes=marketplace.credentials.get("scopes"),
        )

        # Create eBay API client
        api_client = EbayAPIClient(ebay_config.api_base_url)

        # Get the eBay service
        ebay_service = get_ebay_service(
            config=ebay_config,
            api_client=api_client,
            metrics_service=get_metrics_service(),
            notification_service=get_notification_service(),
        )

        # Process the orders
        result = await ebay_service.process_orders(
            order_ids=order_request.order_ids,
            action=order_request.action,
            shipping_info=order_request.shipping_info,
        )

        return ApiResponse(
            status=200,
            message=f"Orders {order_request.action} processed successfully",
            success=True,
            data={
                "processed_orders": len(result.get("successful_orders", [])),
                "failed_orders": len(result.get("failed_orders", [])),
                "order_ids": result.get("successful_orders", []),
                "failed_order_ids": result.get("failed_orders", []),
                "errors": result.get("errors", {}),
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process eBay orders: {str(e)}",
        )


@router.get("/inventory", response_model=ApiResponse)
async def get_ebay_inventory(
    limit: int = Query(100, description="Maximum number of inventory items to return"),
    offset: int = Query(0, description="Number of inventory items to skip"),
    current_user: UnifiedUser = Depends(get_current_user),
    marketplace_repo: MarketplaceRepository = Depends(get_marketplace_repository),
):
    """
    Get eBay inventory items.

    This endpoint retrieves inventory items from eBay for the current user.
    """
    try:
        # Get the eBay marketplace connection
        marketplace = await marketplace_repo.get_by_type(
            user_id=current_user.id, marketplace_type="ebay"
        )

        if not marketplace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="eBay marketplace not found. Please authenticate first.",
            )

        # Create eBay agent to get inventory
        from fs_agt_clean.agents.market.ebay_agent import EbayUnifiedAgent

        ebay_agent = EbayUnifiedAgent()

        # Get inventory from eBay API
        inventory_response = await ebay_agent.get_inventory()

        # Extract inventory items
        inventory_items = inventory_response.get("inventoryItems", [])

        # Apply pagination
        start_index = offset
        end_index = offset + limit
        paginated_items = inventory_items[start_index:end_index]

        # Format items for mobile app
        formatted_items = []
        for item in paginated_items:
            formatted_item = {
                "sku": item.get("sku"),
                "title": item.get("product", {}).get("title"),
                "price": item.get("offers", [{}])[0].get("price", {}).get("value", 0),
                "quantity": item.get("availability", {})
                .get("shipToLocationAvailability", {})
                .get("quantity", 0),
                "condition": item.get("condition"),
                "description": item.get("product", {}).get("description"),
                "images": item.get("product", {}).get("imageUrls", []),
                "product": item.get("product", {}),
                "availability": item.get("availability", {}),
                "offers": item.get("offers", []),
            }
            formatted_items.append(formatted_item)

        return ApiResponse(
            status=200,
            message=f"Successfully retrieved {len(formatted_items)} eBay inventory items",
            success=True,
            data={
                "items": formatted_items,
                "total": len(inventory_items),
                "limit": limit,
                "offset": offset,
                "has_more": end_index < len(inventory_items),
            },
        )

    except Exception as e:
        logger.error(f"Error retrieving eBay inventory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve eBay inventory: {str(e)}",
        )


@router.post("/inventory", response_model=ApiResponse)
async def sync_ebay_inventory(
    inventory_request: EbayInventoryRequest,
    current_user: UnifiedUser = Depends(get_current_user),
    marketplace_repo: MarketplaceRepository = Depends(get_marketplace_repository),
    listing_repo: ListingRepository = Depends(get_listing_repository),
):
    """
    Synchronize inventory with eBay.

    This endpoint handles synchronization of inventory levels with
    eBay Marketplace to ensure accurate stock levels.
    """
    try:
        # Get the marketplace
        marketplace = await marketplace_repo.get_by_type(
            user_id=current_user.id, marketplace_type="ebay"
        )

        if not marketplace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="eBay marketplace not found. Please authenticate first.",
            )

        # Create eBay config
        ebay_config = EbayConfig(
            client_id=marketplace.credentials.get("client_id"),
            client_secret=marketplace.credentials.get("client_secret"),
            scopes=marketplace.credentials.get("scopes"),
        )

        # Create eBay API client
        api_client = EbayAPIClient(ebay_config.api_base_url)

        # Get the eBay service
        ebay_service = get_ebay_service(
            config=ebay_config,
            api_client=api_client,
            metrics_service=get_metrics_service(),
            notification_service=get_notification_service(),
        )

        # Update inventory on eBay
        result = await ebay_service.update_inventory(inventory_request.items)

        # Update listings in the database
        updated_listings = []
        failed_skus = []

        for item in inventory_request.items:
            try:
                # Find the listing by SKU
                listings = await listing_repo.find_by_criteria(
                    {"marketplace_id": marketplace.id, "sku": item["sku"]}
                )

                if listings:
                    # Update the listing
                    listing = await listing_repo.update_quantity(
                        listings[0].id, item["quantity"]
                    )
                    updated_listings.append(listing)
                else:
                    failed_skus.append(item["sku"])
            except Exception as e:
                failed_skus.append(item["sku"])

        return ApiResponse(
            status=200,
            message="Inventory synchronized successfully",
            success=True,
            data={
                "updated_skus": len(updated_listings),
                "failed_skus": len(failed_skus),
                "inventory_feed_id": result.get("feed_id"),
                "failed_sku_list": failed_skus,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to synchronize eBay inventory: {str(e)}",
        )


@router.get("/categories", response_model=ApiResponse)
async def get_ebay_categories(
    parent_id: Optional[str] = Query(None, description="Parent category ID"),
    level: Optional[int] = Query(None, description="Category level"),
    current_user: UnifiedUser = Depends(get_current_user),  # noqa: B008
):
    """
    Get eBay categories.

    This endpoint retrieves eBay category information, optionally filtered by parent category or level.
    """
    # Implementation would include:
    # 1. Validate request parameters
    # 2. Query eBay API for categories
    # 3. Format response data

    # Mock implementation for structure
    return ApiResponse(
        status=200,
        message="Successfully retrieved eBay categories",
        success=True,
        data={
            "categories": [
                {
                    "id": "9355",
                    "name": "Cell Phones & Accessories",
                    "level": 1,
                    "parent_id": None,
                    "leaf": False,
                },
                {
                    "id": "9394",
                    "name": "Cell Phone Accessories",
                    "level": 2,
                    "parent_id": "9355",
                    "leaf": False,
                },
                {
                    "id": "123456",
                    "name": "Headphones",
                    "level": 3,
                    "parent_id": "9394",
                    "leaf": True,
                },
            ],
            "total": 3,
        },
    )


@router.get("/item-specifics/{category_id}", response_model=ApiResponse)
async def get_ebay_item_specifics(
    category_id: str = Path(..., description="The eBay category ID"),
    current_user: UnifiedUser = Depends(get_current_user),  # noqa: B008
):
    """
    Get eBay item specifics for a category.

    This endpoint retrieves required and recommended item specifics for a given eBay category.
    """
    # Implementation would include:
    # 1. Validate category ID
    # 2. Query eBay API for item specifics
    # 3. Format response data

    # Mock implementation for structure
    return ApiResponse(
        status=200,
        message="Successfully retrieved eBay item specifics",
        success=True,
        data={
            "category_id": category_id,
            "category_name": "Headphones",
            "item_specifics": {
                "Brand": {
                    "required": True,
                    "values": ["Apple", "Samsung", "Sony", "Bose"],
                },
                "Model": {
                    "required": True,
                    "values": [],
                },
                "Color": {
                    "required": False,
                    "values": ["Black", "White", "Blue", "Red"],
                },
                "Connectivity": {
                    "required": False,
                    "values": ["Wireless", "Wired", "Bluetooth"],
                },
            },
        },
    )


@router.get("/market-data", response_model=ApiResponse)
async def get_ebay_market_data(
    keywords: str = Query(..., description="Search keywords"),
    category_id: Optional[str] = Query(
        None, description="Category ID to search within"
    ),
    limit: int = Query(10, description="Maximum number of results"),
    current_user: UnifiedUser = Depends(get_current_user),  # noqa: B008
):
    """
    Get eBay market data.

    This endpoint retrieves market data from eBay based on keywords and optional category.
    """
    # Implementation would include:
    # 1. Validate request parameters
    # 2. Query eBay API for market data
    # 3. Format response data

    # Mock implementation for structure
    return ApiResponse(
        status=200,
        message="Successfully retrieved eBay market data",
        success=True,
        data={
            "results": [
                {
                    "title": "Wireless Bluetooth Headphones Noise Cancelling",
                    "price": 45.99,
                    "shipping": 4.99,
                    "condition": "New",
                    "sold_count": 120,
                    "url": "https://www.ebay.com/itm/12345",
                },
                {
                    "title": "Premium Bluetooth Headphones with Case",
                    "price": 59.99,
                    "shipping": 0.00,
                    "condition": "New",
                    "sold_count": 85,
                    "url": "https://www.ebay.com/itm/67890",
                },
            ],
            "total": 2,
            "average_price": 52.99,
            "average_shipping": 2.50,
        },
    )


@router.post("/cross-list", response_model=ApiResponse)
async def cross_list_to_ebay(
    product_data: Dict = Body(..., description="Product data to list on eBay"),
    current_user: UnifiedUser = Depends(get_current_user),  # noqa: B008
):
    """
    Cross-list a product to eBay.

    This endpoint creates a new eBay listing based on product data from another source.
    """
    # Implementation would include:
    # 1. Validate product data
    # 2. Transform data for eBay listing format
    # 3. Create listing on eBay
    # 4. Return listing details

    # Mock implementation for structure
    return ApiResponse(
        status=201,
        message="Successfully cross-listed product to eBay",
        success=True,
        data={
            "listing_id": "ebay_item_12345",
            "title": product_data.get("title", ""),
            "price": product_data.get("price", 0.0),
            "url": "https://www.ebay.com/itm/12345",
            "source": product_data.get("source", ""),
            "source_id": product_data.get("source_id", ""),
        },
    )
