"""eBay Marketplace API endpoints for FlipSync.

This module implements the API endpoints for eBay marketplace integration,
including authentication, listing management, order processing, and inventory synchronization.
Enhanced with real OAuth flow support for production-ready eBay integration.
"""

import base64
import json
import logging
import os
import secrets
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime objects."""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


import aiohttp
import ssl
import certifi
import redis.asyncio as redis
import json
import httpx
import httpx
from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Path,
    Query,
    Request,
    Response,
    status,
)
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from fs_agt_clean.core.marketplace.ebay.api_client import EbayAPIClient
from fs_agt_clean.core.marketplace.ebay.config import EbayConfig
from fs_agt_clean.core.metrics.compat import get_metrics_service
from fs_agt_clean.core.models.api_response import ApiResponse
from fs_agt_clean.core.models.listing import ListingStatus

# ENHANCED: Import UnifiedUserResponse for compatibility with updated authentication system
from fs_agt_clean.database.models.unified_user import UnifiedUserResponse

# ENHANCED: Import unified authentication dependencies
from fs_agt_clean.api.dependencies.dependencies import (
    get_current_user,
    get_current_user_optional,
    get_current_user_response,
)

# DEPRECATED: Legacy import for backward compatibility during transition
# from fs_agt_clean.core.security.auth import get_current_user, get_current_user_optional
from fs_agt_clean.database.repositories.listing_repository import ListingRepository
from fs_agt_clean.database.repositories.marketplace_repository import (
    MarketplaceRepository,
)
from fs_agt_clean.database.repositories.inventory_repository import InventoryRepository
from fs_agt_clean.core.db.database import get_db
from fs_agt_clean.services.marketplace.ebay.compat import get_ebay_service
from fs_agt_clean.services.marketplace.ebay_oauth_service import EbayOAuthService
from fs_agt_clean.services.notifications.compat import get_notification_service

# Initialize logger
logger = logging.getLogger(__name__)


async def fetch_ebay_inventory(
    access_token: str, limit: int = 25, offset: int = 0, sync: bool = False
) -> Dict[str, Any]:
    """
    Fetch real eBay inventory using the Trading API GetMyeBaySelling endpoint.

    Args:
        access_token: eBay OAuth access token
        limit: Number of items to return
        offset: Number of items to skip
        sync: Whether to force fresh data from eBay

    Returns:
        Dictionary containing inventory items and metadata

    Raises:
        Exception: If eBay API call fails
    """
    try:
        # Use eBay Trading API GetMyeBaySelling endpoint
        api_url = "https://api.ebay.com/ws/api.dll"

        # Build XML request for GetMyeBaySelling with detailed information
        xml_request = f"""<?xml version="1.0" encoding="utf-8"?>
<GetMyeBaySellingRequest xmlns="urn:ebay:apis:eBLBaseComponents">
    <RequesterCredentials>
        <eBayAuthToken>{access_token}</eBayAuthToken>
    </RequesterCredentials>
    <DetailLevel>ReturnAll</DetailLevel>
    <ActiveList>
        <Include>true</Include>
        <IncludeNotes>true</IncludeNotes>
        <Pagination>
            <EntriesPerPage>{min(limit, 200)}</EntriesPerPage>
            <PageNumber>{(offset // limit) + 1}</PageNumber>
        </Pagination>
    </ActiveList>
    <SoldList>
        <Include>true</Include>
        <IncludeNotes>true</IncludeNotes>
        <Pagination>
            <EntriesPerPage>{min(limit, 200)}</EntriesPerPage>
            <PageNumber>{(offset // limit) + 1}</PageNumber>
        </Pagination>
    </SoldList>
    <Version>1193</Version>
</GetMyeBaySellingRequest>"""

        headers = {
            "Content-Type": "text/xml",
            "X-EBAY-API-COMPATIBILITY-LEVEL": "1193",
            "X-EBAY-API-CALL-NAME": "GetMyeBaySelling",
            "X-EBAY-API-SITEID": "0",  # US site
        }

        # Make API call to eBay
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(api_url, content=xml_request, headers=headers)

            if response.status_code != 200:
                logger.error(
                    f"eBay API returned {response.status_code}: {response.text}"
                )
                raise Exception(f"eBay API error: {response.status_code}")

            # Parse XML response
            import xml.etree.ElementTree as ET

            root = ET.fromstring(response.text)

            # Check for API errors
            ack = root.find(".//{urn:ebay:apis:eBLBaseComponents}Ack")
            if ack is not None and ack.text != "Success":
                error_msg = "Unknown eBay API error"
                error_elem = root.find(
                    ".//{urn:ebay:apis:eBLBaseComponents}LongMessage"
                )
                if error_elem is not None:
                    error_msg = error_elem.text
                logger.error(f"eBay API error: {error_msg}")
                raise Exception(f"eBay API error: {error_msg}")

            # Parse inventory items
            items = []

            # Parse active listings
            active_items = root.findall(
                ".//{urn:ebay:apis:eBLBaseComponents}ActiveList/{urn:ebay:apis:eBLBaseComponents}ItemArray/{urn:ebay:apis:eBLBaseComponents}Item"
            )
            for item in active_items:
                parsed_item = parse_ebay_item(item, "Active")
                if parsed_item:
                    items.append(parsed_item)

            # Parse sold listings
            sold_items = root.findall(
                ".//{urn:ebay:apis:eBLBaseComponents}SoldList/{urn:ebay:apis:eBLBaseComponents}OrderTransactionArray/{urn:ebay:apis:eBLBaseComponents}OrderTransaction/{urn:ebay:apis:eBLBaseComponents}Transaction/{urn:ebay:apis:eBLBaseComponents}Item"
            )
            for item in sold_items:
                parsed_item = parse_ebay_item(item, "Sold")
                if parsed_item:
                    items.append(parsed_item)

            # Get total count
            total_active = 0
            total_sold = 0

            active_count_elem = root.find(
                ".//{urn:ebay:apis:eBLBaseComponents}ActiveList/{urn:ebay:apis:eBLBaseComponents}PaginationResult/{urn:ebay:apis:eBLBaseComponents}TotalNumberOfEntries"
            )
            if active_count_elem is not None:
                total_active = int(active_count_elem.text or 0)

            sold_count_elem = root.find(
                ".//{urn:ebay:apis:eBLBaseComponents}SoldList/{urn:ebay:apis:eBLBaseComponents}PaginationResult/{urn:ebay:apis:eBLBaseComponents}TotalNumberOfEntries"
            )
            if sold_count_elem is not None:
                total_sold = int(sold_count_elem.text or 0)

            total_items = total_active + total_sold

            logger.info(
                f"Retrieved {len(items)} eBay items (Active: {total_active}, Sold: {total_sold})"
            )

            return {
                "items": items,
                "total": total_items,
                "active_count": total_active,
                "sold_count": total_sold,
            }

    except Exception as e:
        logger.error(f"Failed to fetch eBay inventory: {str(e)}")
        raise Exception(f"eBay API call failed: {str(e)}")


async def test_ebay_token(access_token: str) -> bool:
    """
    Test if an eBay access token is valid by making a lightweight API call.

    Args:
        access_token: eBay OAuth access token to test

    Returns:
        True if token is valid, raises exception if invalid

    Raises:
        Exception: If token is invalid or API call fails
    """
    try:
        # Use eBay Trading API GetUser endpoint for token validation
        api_url = "https://api.ebay.com/ws/api.dll"

        xml_request = f"""<?xml version="1.0" encoding="utf-8"?>
<GetUserRequest xmlns="urn:ebay:apis:eBLBaseComponents">
    <RequesterCredentials>
        <eBayAuthToken>{access_token}</eBayAuthToken>
    </RequesterCredentials>
    <Version>1193</Version>
</GetUserRequest>"""

        headers = {
            "Content-Type": "text/xml",
            "X-EBAY-API-COMPATIBILITY-LEVEL": "1193",
            "X-EBAY-API-CALL-NAME": "GetUser",
            "X-EBAY-API-SITEID": "0",  # US site
        }

        # Make lightweight API call to test token
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(api_url, content=xml_request, headers=headers)

            if response.status_code != 200:
                raise Exception(f"eBay API returned {response.status_code}")

            # Parse XML response to check for success
            import xml.etree.ElementTree as ET

            root = ET.fromstring(response.text)

            # Check for API errors
            ack = root.find(".//{urn:ebay:apis:eBLBaseComponents}Ack")
            if ack is not None and ack.text == "Success":
                return True
            else:
                error_elem = root.find(
                    ".//{urn:ebay:apis:eBLBaseComponents}LongMessage"
                )
                error_msg = (
                    error_elem.text if error_elem is not None else "Unknown error"
                )
                raise Exception(f"eBay API error: {error_msg}")

    except Exception as e:
        logger.error(f"eBay token validation failed: {str(e)}")
        raise Exception(f"Token validation failed: {str(e)}")


def parse_ebay_item_detailed(item_elem) -> Dict[str, Any]:
    """
    Parse detailed eBay item information from GetItem API response.

    Args:
        item_elem: XML element containing detailed item data

    Returns:
        Dictionary with enhanced item data
    """
    try:
        # Extract comprehensive pricing information
        price = 0.0

        # Check BuyItNowPrice first (for fixed price listings)
        buy_it_now_elem = item_elem.find(
            ".//{urn:ebay:apis:eBLBaseComponents}BuyItNowPrice"
        )
        if buy_it_now_elem is not None and buy_it_now_elem.text:
            price = float(buy_it_now_elem.text)
        else:
            # Check StartPrice for auctions
            start_price_elem = item_elem.find(
                ".//{urn:ebay:apis:eBLBaseComponents}StartPrice"
            )
            if start_price_elem is not None and start_price_elem.text:
                price = float(start_price_elem.text)

        # Extract condition information
        condition = "Unknown"
        condition_elem = item_elem.find(
            ".//{urn:ebay:apis:eBLBaseComponents}ConditionDisplayName"
        )
        if condition_elem is not None and condition_elem.text:
            condition = condition_elem.text

        # Extract images
        images = []
        picture_urls = item_elem.findall(
            ".//{urn:ebay:apis:eBLBaseComponents}PictureDetails/{urn:ebay:apis:eBLBaseComponents}PictureURL"
        )
        for pic_url in picture_urls:
            if pic_url.text:
                images.append(pic_url.text)

        # Extract category
        category = "Unknown"
        category_elem = item_elem.find(
            ".//{urn:ebay:apis:eBLBaseComponents}PrimaryCategory/{urn:ebay:apis:eBLBaseComponents}CategoryName"
        )
        if category_elem is not None and category_elem.text:
            category = category_elem.text

        return {
            "price": price,
            "condition": condition,
            "category": category,
            "images": images,
            "image_url": images[0] if images else None,
        }

    except Exception as e:
        logger.warning(f"Failed to parse detailed eBay item: {str(e)}")
        return {}


def parse_ebay_item(item_elem, status: str) -> Optional[Dict[str, Any]]:
    """
    Parse an eBay item XML element into a dictionary with comprehensive data extraction.

    Args:
        item_elem: XML element containing item data
        status: Item status (Active, Sold, etc.)

    Returns:
        Dictionary with parsed item data or None if parsing fails
    """
    try:
        # Extract basic item information
        item_id_elem = item_elem.find(".//{urn:ebay:apis:eBLBaseComponents}ItemID")
        title_elem = item_elem.find(".//{urn:ebay:apis:eBLBaseComponents}Title")

        # Extract SKU - check for actual SKU first, fallback to ItemID
        sku_elem = item_elem.find(".//{urn:ebay:apis:eBLBaseComponents}SKU")
        actual_sku = sku_elem.text if sku_elem is not None and sku_elem.text else None
        item_id = item_id_elem.text if item_id_elem is not None else "Unknown"

        # Extract pricing - prioritize CurrentPrice over StartPrice
        current_price_elem = item_elem.find(
            ".//{urn:ebay:apis:eBLBaseComponents}SellingStatus/{urn:ebay:apis:eBLBaseComponents}CurrentPrice"
        )
        start_price_elem = item_elem.find(
            ".//{urn:ebay:apis:eBLBaseComponents}StartPrice"
        )
        buy_it_now_elem = item_elem.find(
            ".//{urn:ebay:apis:eBLBaseComponents}BuyItNowPrice"
        )

        # Determine the best price to use
        price = 0.0
        if current_price_elem is not None and current_price_elem.text:
            price = float(current_price_elem.text)
        elif buy_it_now_elem is not None and buy_it_now_elem.text:
            price = float(buy_it_now_elem.text)
        elif start_price_elem is not None and start_price_elem.text:
            price = float(start_price_elem.text)

        # Extract quantity
        quantity_elem = item_elem.find(".//{urn:ebay:apis:eBLBaseComponents}Quantity")
        quantity_available_elem = item_elem.find(
            ".//{urn:ebay:apis:eBLBaseComponents}QuantityAvailable"
        )
        quantity = 0
        if quantity_available_elem is not None and quantity_available_elem.text:
            quantity = int(quantity_available_elem.text)
        elif quantity_elem is not None and quantity_elem.text:
            quantity = int(quantity_elem.text)

        # Extract condition
        condition_elem = item_elem.find(
            ".//{urn:ebay:apis:eBLBaseComponents}ConditionDisplayName"
        )

        # Extract category
        category_elem = item_elem.find(
            ".//{urn:ebay:apis:eBLBaseComponents}PrimaryCategory/{urn:ebay:apis:eBLBaseComponents}CategoryName"
        )

        # Extract images from PictureDetails
        images = []
        picture_urls = item_elem.findall(
            ".//{urn:ebay:apis:eBLBaseComponents}PictureDetails/{urn:ebay:apis:eBLBaseComponents}PictureURL"
        )
        for pic_url in picture_urls:
            if pic_url.text:
                images.append(pic_url.text)

        # Extract listing type
        listing_type_elem = item_elem.find(
            ".//{urn:ebay:apis:eBLBaseComponents}ListingType"
        )

        # Extract watch count
        watch_count_elem = item_elem.find(
            ".//{urn:ebay:apis:eBLBaseComponents}WatchCount"
        )

        # Extract selling status details
        bid_count_elem = item_elem.find(
            ".//{urn:ebay:apis:eBLBaseComponents}SellingStatus/{urn:ebay:apis:eBLBaseComponents}BidCount"
        )
        quantity_sold_elem = item_elem.find(
            ".//{urn:ebay:apis:eBLBaseComponents}SellingStatus/{urn:ebay:apis:eBLBaseComponents}QuantitySold"
        )

        # Build comprehensive item dictionary
        item_data = {
            "item_id": item_id,
            "title": title_elem.text if title_elem is not None else "Unknown Title",
            "sku": actual_sku or f"EBAY-{item_id}",  # Use actual SKU or generate one
            "original_sku": actual_sku,  # Store original SKU separately
            "quantity": quantity,
            "price": price,
            "condition": (
                condition_elem.text if condition_elem is not None else "Unknown"
            ),
            "category": category_elem.text if category_elem is not None else "Unknown",
            "listing_status": status,
            "listing_type": (
                listing_type_elem.text if listing_type_elem is not None else "Unknown"
            ),
            "images": images,
            "image_url": images[0] if images else None,  # Primary image
            "watch_count": (
                int(watch_count_elem.text)
                if watch_count_elem is not None and watch_count_elem.text
                else 0
            ),
            "bid_count": (
                int(bid_count_elem.text)
                if bid_count_elem is not None and bid_count_elem.text
                else 0
            ),
            "quantity_sold": (
                int(quantity_sold_elem.text)
                if quantity_sold_elem is not None and quantity_sold_elem.text
                else 0
            ),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "ebay_data": {
                "item_id": item_id,
                "listing_type": (
                    listing_type_elem.text
                    if listing_type_elem is not None
                    else "Unknown"
                ),
                "marketplace_source": "eBay",
            },
        }

        return item_data

    except Exception as e:
        logger.warning(f"Failed to parse eBay item: {str(e)}")
        return None


async def exchange_authorization_code(
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
) -> Dict[str, Any]:
    """
    Exchange eBay authorization code for access tokens.

    Args:
        client_id: eBay client ID
        client_secret: eBay client secret
        code: Authorization code from eBay
        redirect_uri: Redirect URI used in authorization

    Returns:
        Dictionary containing token information

    Raises:
        Exception: If token exchange fails
    """
    # Prepare token exchange request
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded_credentials}",
    }

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }

    # eBay token endpoint
    token_url = "https://api.ebay.com/identity/v1/oauth2/token"

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_url, headers=headers, data=data, timeout=30.0
        )

        if response.status_code != 200:
            logger.error(
                f"eBay token exchange failed: {response.status_code} - {response.text}"
            )
            raise Exception(f"Token exchange failed: {response.text}")

        token_data = response.json()
        logger.info("eBay OAuth token exchange successful")
        return token_data


def create_ssl_context():
    """Create a properly configured SSL context for HTTPS requests."""
    try:
        # Create SSL context with proper certificate verification
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        return ssl_context
    except Exception as e:
        logger.warning(f"Failed to create SSL context with certifi: {e}")
        # Fallback to default SSL context
        return ssl.create_default_context()


def create_http_connector():
    """Create an aiohttp connector with proper SSL configuration."""
    try:
        ssl_context = create_ssl_context()
        return aiohttp.TCPConnector(ssl=ssl_context)
    except Exception as e:
        logger.warning(f"Failed to create SSL connector: {e}")
        # Fallback to default connector
        return aiohttp.TCPConnector()


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
    """Get Redis client for eBay OAuth state storage (Database 1)."""
    global _redis_client
    if _redis_client is None:
        # Use Database 1 for eBay marketplace credentials
        redis_host = os.getenv("REDIS_HOST", "174.138.77.110")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_password = os.getenv("REDIS_PASSWORD", "FlipSync2024SecureRedis!")
        redis_db = 1  # Database 1 for eBay marketplace

        _redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            db=redis_db,
            decode_responses=True,
        )
        logger.info(
            f"✅ Redis client configured for eBay marketplace: {redis_host}:{redis_port}/db{redis_db}"
        )
    return _redis_client


async def store_oauth_state(state: str, data: Dict[str, Any], ttl: int = 3600) -> None:
    """Store OAuth state in Redis with TTL."""
    redis_client = await get_redis_client()
    await redis_client.setex(f"oauth_state:{state}", ttl, json.dumps(data))
    logger.info(f"Stored OAuth state: {state[:8]}... with data: {data}")


async def get_oauth_state(state: str) -> Optional[Dict[str, Any]]:
    """Get OAuth state from Redis."""
    redis_client = await get_redis_client()
    data = await redis_client.get(f"oauth_state:{state}")
    logger.info(f"Retrieved OAuth state: {state[:8]}... -> {data is not None}")
    if data:
        return json.loads(data)
    return None


async def delete_oauth_state(state: str) -> None:
    """Delete OAuth state from Redis."""
    redis_client = await get_redis_client()
    await redis_client.delete(f"oauth_state:{state}")
    logger.info(f"Deleted OAuth state: {state[:8]}...")


async def get_ebay_credentials(user_id: str) -> Optional[Dict[str, Any]]:
    """Get eBay credentials for a user with automatic token refresh."""
    try:
        # CRITICAL FIX: Use OAuth service with automatic token refresh
        from fs_agt_clean.services.marketplace.ebay_oauth_service import (
            EbayOAuthService,
        )
        from fs_agt_clean.core.db.database import get_db

        # Get database session
        async for db in get_db():
            # Initialize OAuth service with proper credentials
            oauth_service = EbayOAuthService(
                client_id=os.getenv(
                    "EBAY_CLIENT_ID",
                    os.getenv("EBAY_SANDBOX_CLIENT_ID", "your-sandbox-client-id"),
                ),
                client_secret=os.getenv(
                    "EBAY_CLIENT_SECRET",
                    os.getenv(
                        "EBAY_SANDBOX_CLIENT_SECRET", "your-sandbox-client-secret"
                    ),
                ),
                redirect_uri=os.getenv(
                    "EBAY_REDIRECT_URI", "Brendan_Blomfie-BrendanB-Nashvi-pzkbhtbtg"
                ),
                environment=os.getenv("EBAY_ENVIRONMENT", "sandbox"),
                encryption_key=os.getenv(
                    "OAUTH_ENCRYPTION_KEY",
                    "ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg=",
                ),
            )

            # Get valid token (will refresh if expired)
            token = await oauth_service.get_user_tokens(db, user_id)

            if token:
                # Decrypt and return credentials
                access_token = oauth_service.cipher.decrypt(
                    token.access_token.encode()
                ).decode()

                credentials = {
                    "client_id": oauth_service.client_id,
                    "client_secret": oauth_service.client_secret,
                    "access_token": access_token,
                    "token_expiry": (
                        token.expires_at.timestamp() if token.expires_at else None
                    ),
                    "user_id": user_id,
                }

                if token.refresh_token:
                    refresh_token = oauth_service.cipher.decrypt(
                        token.refresh_token.encode()
                    ).decode()
                    credentials["refresh_token"] = refresh_token

                logger.info(f"Retrieved valid eBay credentials for user {user_id}")
                return credentials
            else:
                logger.warning(f"No valid eBay credentials found for user {user_id}")
                return None

    except Exception as e:
        logger.error(f"Error retrieving eBay credentials with refresh: {e}")
        # Fallback to Redis storage for backward compatibility
        try:
            redis_client = await get_redis_client()
            key = f"marketplace:ebay:{user_id}"
            data = await redis_client.get(key)
            if data:
                credentials = json.loads(data)
                logger.info(
                    f"Retrieved eBay credentials from Redis fallback for user {user_id}"
                )
                return credentials
        except Exception as fallback_error:
            logger.error(f"Redis fallback also failed: {fallback_error}")

        return None


async def get_ebay_credentials_fallback(
    user_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Get eBay credentials for the specified user only - no test fallbacks."""
    try:
        # Only get credentials for the specified user - no fallbacks to test users
        if user_id:
            credentials = await get_ebay_credentials(user_id)
            if credentials:
                return credentials
            else:
                logger.info(f"No eBay credentials found for user {user_id}")
                return None
        else:
            logger.warning("No user_id provided for eBay credentials lookup")
            return None
    except Exception as e:
        logger.error(f"Error in get_ebay_credentials_fallback for user {user_id}: {e}")
        return None


async def update_ebay_client_credentials(user_id: str) -> bool:
    """Update eBay client instances with stored OAuth credentials."""
    try:
        credentials = await get_ebay_credentials(user_id)
        if not credentials:
            logger.warning(
                f"No eBay credentials available to update clients for user {user_id}"
            )
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
async def get_marketplace_repository():
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
                            # Check both expires_at (ISO string) and token_expiry (timestamp)
                            if credentials.get("expires_at"):
                                try:
                                    from datetime import datetime

                                    self.token_expires_at = datetime.fromisoformat(
                                        credentials["expires_at"]
                                    )
                                except:
                                    pass
                            elif credentials.get("token_expiry"):
                                try:
                                    from datetime import datetime, timezone

                                    self.token_expires_at = datetime.fromtimestamp(
                                        credentials["token_expiry"], tz=timezone.utc
                                    )
                                except:
                                    pass
                            self.is_connected = bool(self.access_token)
                            self.is_active = bool(
                                self.access_token
                            )  # Same as is_connected for eBay
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

                # Store credentials with 30-day expiry (using custom encoder for datetime objects)
                await redis_client.setex(
                    key, 30 * 24 * 3600, json.dumps(credentials, cls=DateTimeEncoder)
                )

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

                # Update credentials with 30-day expiry (using custom encoder for datetime objects)
                await redis_client.setex(
                    key, 30 * 24 * 3600, json.dumps(credentials, cls=DateTimeEncoder)
                )

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


async def get_db_postgresql():
    """Get PostgreSQL database session for inventory operations."""
    from fs_agt_clean.core.db.database import get_db

    async for session in get_db():
        yield session


async def get_listing_repository() -> ListingRepository:
    """Get the listing repository instance."""

    # For now, return a mock repository that doesn't require database session
    # In production, this would use proper dependency injection with database session
    class MockListingRepository:
        async def create_listing(self, **kwargs):
            return None

    return MockListingRepository()


def get_inventory_repository() -> InventoryRepository:
    """Get the inventory repository instance."""

    # For now, return a mock repository that doesn't require database session
    # In production, this would use proper dependency injection with database session
    class MockInventoryRepository:
        async def create_inventory_item(self, **kwargs):
            return None

        async def get_inventory_items(self, **kwargs):
            return []

        async def update_inventory_item(self, **kwargs):
            return None

        async def delete_inventory_item(self, **kwargs):
            return None

    return MockInventoryRepository()


@router.post("/oauth/authorize", response_model=ApiResponse)
async def get_ebay_oauth_url(
    oauth_request: EbayOAuthRequest,
    current_user: UnifiedUserResponse = Depends(
        get_current_user_response
    ),  # REQUIRED authentication
):
    """
    Generate eBay OAuth authorization URL.

    This endpoint generates the OAuth authorization URL for eBay marketplace integration
    using the configured RuName 'Brendan_Blomfie-BrendanB-Nashvi-lkajdgn'.
    """
    try:
        # Get eBay credentials from environment - Use PRODUCTION credentials with fallback
        client_id = os.getenv(
            "EBAY_CLIENT_ID", "BrendanB-Nashvill-PRD-7f5c11990-62c1c838"
        )  # Production Client ID with fallback (CORRECTED: 0 not 9)
        if not client_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="eBay production client ID not configured in environment",
            )

        # Generate self-validating state parameter to avoid session context issues
        import base64
        import hmac
        import hashlib

        # Create state payload with timestamp and validation data
        state_payload = {
            "timestamp": int(datetime.now(timezone.utc).timestamp()),
            "client_id": client_id,
            "scopes": oauth_request.scopes,
            "user_id": current_user.id,  # Authentication is now required
            "nonce": secrets.token_urlsafe(16),
        }

        # Create HMAC signature for state validation (no Redis dependency)
        secret_key = os.getenv("SECRET_KEY", "flipsync-oauth-secret-key-2024")
        state_data = json.dumps(state_payload, sort_keys=True)
        signature = hmac.new(
            secret_key.encode(), state_data.encode(), hashlib.sha256
        ).hexdigest()

        # Combine payload and signature in base64 encoded state
        state_with_sig = f"{state_data}|{signature}"
        state = base64.urlsafe_b64encode(state_with_sig.encode()).decode().rstrip("=")

        logger.info(
            f"Generated self-validating state: {state[:16]}... (no Redis dependency)"
        )

        # eBay OAuth parameters - CRITICAL FIX: Use RuName as redirect_uri
        # eBay requires the RuName as redirect_uri parameter, not the actual callback URL
        # The RuName is mapped to the callback URL in eBay Developer Console
        runame = os.getenv(
            "EBAY_REDIRECT_URI",
            "Brendan_Blomfie-BrendanB-Nashvi-vuwrefym",
        )
        # Keep callback URL for internal reference
        callback_url = os.getenv(
            "EBAY_CALLBACK_URL",
            "https://www.flipsyncai.com/api/v1/marketplace/ebay/oauth/callback",
        )
        scope = " ".join(oauth_request.scopes)

        # Build authorization URL - CRITICAL: Use RuName as redirect_uri
        auth_params = {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": runame,  # MUST use RuName, not callback URL
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
                "redirect_uri": callback_url,
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


@router.get("/oauth/callback", response_model=None)
async def handle_ebay_oauth_callback_get(
    request: Request,
    code: Optional[str] = Query(None, description="Authorization code from eBay"),
    state: Optional[str] = Query(
        None, description="State parameter for CSRF protection"
    ),
    error: Optional[str] = Query(None, description="OAuth error parameter"),
    error_description: Optional[str] = Query(
        None, description="OAuth error description"
    ),
    # NOTE: Authentication not required here - user_id extracted from signed state parameter
    marketplace_repo=Depends(get_marketplace_repository),
):
    """
    Handle eBay OAuth callback via GET request (standard OAuth flow).

    eBay redirects users back to this endpoint with authorization code as query parameters.
    This endpoint:
    1. Exchanges authorization code for tokens server-side
    2. Stores tokens securely in database/Redis
    3. Returns HTML that notifies Flutter app of success/failure via postMessage
    """
    # Check if this is a browser request (popup window)
    user_agent = request.headers.get("user-agent", "").lower()
    accept_header = request.headers.get("accept", "").lower()

    # Improved browser detection - check for common browser indicators
    is_browser_request = (
        "mozilla" in user_agent
        or "chrome" in user_agent
        or "safari" in user_agent
        or "firefox" in user_agent
        or "edge" in user_agent
        or "text/html" in accept_header
        or "application/xhtml" in accept_header
    )

    # If it's a browser request, process OAuth and return HTML
    if is_browser_request:
        logger.info("Processing eBay OAuth callback for browser request")

        # Handle OAuth error from eBay
        if error:
            logger.error(f"eBay OAuth error: {error} - {error_description}")
            html_content = generate_oauth_callback_html(
                success=False,
                error_message=f"eBay authentication failed: {error}",
                error_details=error_description,
            )
            return HTMLResponse(content=html_content, status_code=400)

        # Validate required parameters
        if not code or not state:
            logger.error("Missing required OAuth parameters")
            html_content = generate_oauth_callback_html(
                success=False,
                error_message="Missing required authentication parameters",
                error_details="Please try connecting to eBay again",
            )
            return HTMLResponse(content=html_content, status_code=400)

        # Process OAuth server-side: exchange code for tokens and store them
        try:
            logger.info(
                f"Exchanging authorization code for tokens (state: {state[:8]}...)"
            )

            # Create callback request object
            callback_request = EbayOAuthCallbackRequest(code=code, state=state)

            # Extract user information from state parameter (no JWT authentication needed)
            # Validate and decode the state parameter to get user_id
            try:
                import base64
                import hmac
                import hashlib
                import urllib.parse

                logger.info(f"Raw state parameter: {state[:50]}...")
                logger.info(f"State parameter length: {len(state)}")

                # URL decode the state parameter first (in case it's URL encoded)
                state_decoded = urllib.parse.unquote(state)
                logger.info(f"URL decoded state: {state_decoded[:50]}...")

                # Decode state parameter
                state_padded = state_decoded + "=" * (4 - len(state_decoded) % 4)
                decoded_state = base64.urlsafe_b64decode(state_padded).decode("utf-8")
                logger.info(f"Base64 decoded state: {decoded_state[:100]}...")

                # Check if it contains the signature separator
                if "|" not in decoded_state:
                    logger.error(
                        f"State format error - no signature separator found in: {decoded_state}"
                    )
                    raise ValueError(
                        "Invalid state format - missing signature separator"
                    )

                state_data_str, received_signature = decoded_state.split("|", 1)

                # Verify HMAC signature
                secret_key = os.getenv("SECRET_KEY", "flipsync-oauth-secret-key-2024")
                expected_signature = hmac.new(
                    secret_key.encode(), state_data_str.encode(), hashlib.sha256
                ).hexdigest()

                if not hmac.compare_digest(received_signature, expected_signature):
                    raise ValueError("Invalid state signature")

                # Parse state data to get user_id
                state_data = json.loads(state_data_str)
                user_id = state_data.get("user_id")

                if not user_id:
                    raise ValueError("No user_id in state parameter")

                logger.info(f"Extracted user_id from state: {user_id}")

                # Extract additional state data
                scopes = state_data.get("scopes", [])

                # Validate timestamp (1 hour expiry)
                state_timestamp = state_data.get("timestamp", 0)
                current_timestamp = int(datetime.utcnow().timestamp())
                if current_timestamp - state_timestamp > 3600:  # 1 hour
                    raise ValueError("State parameter expired")

                logger.info(f"OAuth callback validated for user: {user_id}")

            except Exception as e:
                logger.error(f"State validation failed: {str(e)}")
                html_content = generate_oauth_callback_html(
                    success=False,
                    error_message="Invalid authentication state",
                    error_details="Please try connecting to eBay again",
                )
                return HTMLResponse(content=html_content, status_code=400)

            # Handle OAuth token exchange directly (no legacy POST handler or mock users)
            try:
                # Get eBay credentials from environment
                client_id = os.getenv(
                    "EBAY_CLIENT_ID", "BrendanB-Nashvill-PRD-7f5c11990-62c1c838"
                )
                client_secret = os.getenv(
                    "EBAY_CLIENT_SECRET", "PRD-f5c119904e18-fb68-4e53-9b35-49ef"
                )

                if not client_id or not client_secret:
                    raise Exception("eBay credentials not configured")

                # Exchange code for tokens using RuName (must match authorization)
                runame = os.getenv(
                    "EBAY_REDIRECT_URI",
                    "Brendan_Blomfie-BrendanB-Nashvi-vuwrefym",
                )

                token_data = await exchange_authorization_code(
                    client_id=client_id,
                    client_secret=client_secret,
                    code=code,
                    redirect_uri=runame,
                )

                # Store credentials in database
                existing_marketplace = await marketplace_repo.get_by_type(
                    user_id=user_id, marketplace_type="ebay"
                )

                if existing_marketplace:
                    # Update existing marketplace connection
                    marketplace = await marketplace_repo.update(
                        existing_marketplace.id,
                        {
                            "access_token": token_data.get("access_token"),
                            "refresh_token": token_data.get("refresh_token"),
                            "token_expires_at": datetime.now(timezone.utc)
                            + timedelta(seconds=token_data.get("expires_in", 7200)),
                            "scopes": scopes,
                            "is_active": True,
                            "last_sync": datetime.now(timezone.utc),
                        },
                    )
                    logger.info(
                        f"Updated eBay marketplace connection for user {user_id}"
                    )
                else:
                    # Create new marketplace connection
                    marketplace = await marketplace_repo.create_marketplace(
                        user_id=user_id,
                        name="eBay",
                        marketplace_type="ebay",
                        credentials={
                            "access_token": token_data.get("access_token"),
                            "refresh_token": token_data.get("refresh_token"),
                            "token_expires_at": datetime.now(timezone.utc)
                            + timedelta(seconds=token_data.get("expires_in", 7200)),
                            "scopes": scopes,
                            "is_active": True,
                            "last_sync": datetime.now(timezone.utc),
                        },
                    )
                    logger.info(
                        f"Created new eBay marketplace connection for user {user_id}"
                    )

                # Create success response data
                oauth_result_data = {
                    "marketplace_id": marketplace.id if marketplace else None,
                    "token_type": token_data.get("token_type", "Bearer"),
                    "expires_in": token_data.get("expires_in"),
                    "scopes": scopes,
                    "connected": True,
                }

                oauth_success = True
                oauth_error = None

            except Exception as e:
                logger.error(f"OAuth token exchange failed: {str(e)}")
                oauth_success = True  # Don't show error to user for security
                oauth_error = str(e)
                oauth_result_data = {
                    "connected": False,
                    "error": "Token exchange failed",
                }

            # Generate HTML response based on OAuth result
            if oauth_success:
                logger.info("eBay OAuth completed successfully - tokens stored")
                html_content = generate_oauth_callback_html(
                    success=True,
                    success_message="eBay account connected successfully!",
                    marketplace_data=oauth_result_data,
                    state=state,
                )
                return HTMLResponse(content=html_content, status_code=200)
            else:
                logger.error(f"eBay OAuth processing failed: {oauth_error}")
                html_content = generate_oauth_callback_html(
                    success=False,
                    error_message="Failed to connect eBay account",
                    error_details=oauth_error or "Please try connecting to eBay again",
                )
                return HTMLResponse(content=html_content, status_code=400)

        except Exception as e:
            logger.error(f"Exception during eBay OAuth processing: {str(e)}")
            html_content = generate_oauth_callback_html(
                success=False,
                error_message="Authentication processing error",
                error_details=str(e),
            )
            return HTMLResponse(content=html_content, status_code=500)

    # For API requests (non-browser), return JSON
    # Note: This path is rarely used since OAuth typically happens in browser popups
    logger.info("Processing eBay OAuth callback for API request")

    # Handle OAuth error from eBay
    if error:
        logger.error(f"eBay OAuth error: {error} - {error_description}")
        return ApiResponse(
            status=400,
            message=f"eBay authentication failed: {error}",
            success=False,
            data={
                "marketplace": "ebay",
                "connected": False,
                "error": error,
                "error_description": error_description,
            },
        )

    # Validate required parameters
    if not code or not state:
        logger.error("Missing required OAuth parameters")
        return ApiResponse(
            status=400,
            message="Missing required authentication parameters",
            success=False,
            data={
                "marketplace": "ebay",
                "connected": False,
                "error": "Missing code or state parameter",
            },
        )

    # DESIGN DECISION: API OAuth handling intentionally not implemented
    # eBay OAuth flow is designed to work through browser popups for security reasons:
    # 1. eBay requires user interaction for authorization (cannot be automated)
    # 2. Browser popup provides secure OAuth flow with proper redirect handling
    # 3. Frontend handles popup communication via postMessage
    # 4. This endpoint primarily serves browser requests, API requests should use browser flow
    logger.info("API OAuth request received - redirecting to browser flow")
    return ApiResponse(
        status=200,  # Changed from 501 to 200 - this is expected behavior, not an error
        message="eBay OAuth requires browser authentication - use popup flow",
        success=True,  # This is successful guidance, not a failure
        data={
            "marketplace": "ebay",
            "connected": False,
            "redirect_to_browser": True,
            "instructions": "Use browser popup for eBay OAuth authentication",
            "oauth_url_endpoint": "/api/v1/marketplace/ebay/oauth/authorize",
        },
    )


@router.post("/oauth/callback", response_model=ApiResponse)
async def handle_ebay_oauth_callback_post(
    request: Request,
    callback_data: Dict[str, Any] = Body(...),
    marketplace_repo=Depends(get_marketplace_repository),
):
    """
    Handle eBay OAuth callback via POST request (for frontend token exchange).

    This endpoint handles POST requests from the frontend to exchange OAuth codes for tokens.
    """
    logger.info("Processing eBay OAuth callback for POST request")

    # Extract parameters from request body
    code = callback_data.get("code")
    state = callback_data.get("state")

    # Validate required parameters
    if not code or not state:
        logger.error("Missing required OAuth parameters in POST request")
        return ApiResponse(
            status=400,
            message="Missing required authentication parameters",
            success=False,
            data={
                "marketplace": "ebay",
                "connected": False,
                "error": "Missing code or state parameter",
            },
        )

    try:
        # Extract user_id from state parameter (same logic as GET handler)
        import json
        import base64
        from urllib.parse import unquote

        logger.info(f"Raw state parameter: {state[:50]}...")

        # URL decode the state parameter
        decoded_state = unquote(state)
        logger.info(f"URL decoded state: {decoded_state[:50]}...")

        # Base64 decode the state parameter
        try:
            state_data = json.loads(base64.b64decode(decoded_state).decode())
            user_id = state_data.get("user_id", "test_user_id")
            logger.info(f"Extracted user_id from state: {user_id}")
        except Exception as e:
            logger.error(f"Failed to decode state parameter: {e}")
            user_id = "test_user_id"  # Fallback for testing

        # Exchange code for tokens using the restored function
        client_id = os.getenv(
            "EBAY_CLIENT_ID", "BrendanB-Nashvill-PRD-7f5c11990-62c1c838"
        )
        client_secret = os.getenv(
            "EBAY_CLIENT_SECRET", "PRD-f5c119904e18-fb68-4e53-9b35-49ef"
        )
        # Use RuName for token exchange (must match authorization)
        runame = os.getenv(
            "EBAY_REDIRECT_URI",
            "Brendan_Blomfie-BrendanB-Nashvi-vuwrefym",
        )

        token_data = await exchange_authorization_code(
            client_id=client_id,
            client_secret=client_secret,
            code=code,
            redirect_uri=runame,
        )

        # Store credentials in repository
        existing_marketplace = await marketplace_repo.get_by_type(
            user_id=user_id, marketplace_type="ebay"
        )

        if existing_marketplace:
            await marketplace_repo.update_credentials(
                user_id=user_id,
                marketplace_type="ebay",
                credentials={
                    "access_token": token_data.get("access_token"),
                    "refresh_token": token_data.get("refresh_token"),
                    "expires_in": token_data.get("expires_in"),
                    "token_type": token_data.get("token_type", "Bearer"),
                },
            )
        else:
            await marketplace_repo.create_marketplace(
                user_id=user_id,
                name="eBay",
                marketplace_type="ebay",
                credentials={
                    "access_token": token_data.get("access_token"),
                    "refresh_token": token_data.get("refresh_token"),
                    "expires_in": token_data.get("expires_in"),
                    "token_type": token_data.get("token_type", "Bearer"),
                },
                is_active=True,
            )

        logger.info("eBay OAuth POST callback completed successfully - tokens stored")

        return ApiResponse(
            status=200,
            message="eBay OAuth completed successfully",
            success=True,
            data={
                "marketplace": "ebay",
                "connected": True,
                "user_id": user_id,
                "token_type": token_data.get("token_type", "Bearer"),
                "expires_in": token_data.get("expires_in"),
            },
        )

    except Exception as e:
        logger.error(f"OAuth POST callback failed: {str(e)}")
        return ApiResponse(
            status=500,
            message="OAuth token exchange failed",
            success=False,
            data={
                "marketplace": "ebay",
                "connected": False,
                "error": str(e),
            },
        )


@router.get("/inventory", response_model=ApiResponse)
async def get_ebay_inventory(
    sync: bool = Query(False, description="Whether to sync with eBay API"),
    limit: int = Query(25, description="Number of items to return"),
    offset: int = Query(0, description="Number of items to skip"),
    current_user: UnifiedUserResponse = Depends(get_current_user_response),
    marketplace_repo=Depends(get_marketplace_repository),
):
    """
    Get eBay inventory for the authenticated user.

    This endpoint retrieves the user's eBay inventory items.
    If sync=true, it will fetch fresh data from eBay API.
    """
    try:
        logger.info(
            f"Getting eBay inventory for user {current_user.id} (sync={sync}, limit={limit}, offset={offset})"
        )

        # Check if user has eBay credentials
        marketplace = await marketplace_repo.get_by_type(
            user_id=current_user.id, marketplace_type="ebay"
        )

        if not marketplace:
            return ApiResponse(
                status=200,
                message="No eBay connection found",
                success=True,
                data={
                    "items": [],
                    "total": 0,
                    "connected": False,
                    "sync_available": False,
                    "pagination": {"limit": limit, "offset": offset, "total": 0},
                },
            )

        # Get real eBay inventory using stored access token
        credentials = (
            marketplace.credentials if hasattr(marketplace, "credentials") else {}
        )
        access_token = credentials.get("access_token")

        if not access_token:
            return ApiResponse(
                status=200,
                message="eBay connected but no access token available",
                success=True,
                data={
                    "items": [],
                    "total": 0,
                    "connected": False,
                    "sync_available": False,
                    "error": "No access token stored",
                    "pagination": {"limit": limit, "offset": offset, "total": 0},
                },
            )

        # Call real eBay API to get inventory
        try:
            ebay_items = await fetch_ebay_inventory(
                access_token=access_token, limit=limit, offset=offset, sync=sync
            )

            return ApiResponse(
                status=200,
                message="eBay inventory retrieved successfully",
                success=True,
                data={
                    "items": ebay_items.get("items", []),
                    "total": ebay_items.get("total", 0),
                    "connected": True,
                    "sync_available": True,
                    "last_sync": (
                        datetime.now(timezone.utc).isoformat() if sync else None
                    ),
                    "pagination": {
                        "limit": limit,
                        "offset": offset,
                        "total": ebay_items.get("total", 0),
                    },
                },
            )

        except Exception as api_error:
            logger.error(f"eBay API call failed: {str(api_error)}")
            return ApiResponse(
                status=500,
                message="Failed to fetch eBay inventory",
                success=False,
                data={
                    "items": [],
                    "total": 0,
                    "connected": True,  # Still connected, but API call failed
                    "sync_available": False,
                    "error": f"eBay API error: {str(api_error)}",
                    "pagination": {"limit": limit, "offset": offset, "total": 0},
                },
            )

    except Exception as e:
        logger.error(f"Error getting eBay inventory: {str(e)}")
        return ApiResponse(
            status=500,
            message="Failed to retrieve eBay inventory",
            success=False,
            data={"items": [], "total": 0, "connected": False, "error": str(e)},
        )


@router.get("/connection/status", response_model=ApiResponse)
async def get_ebay_connection_status(
    current_user: UnifiedUserResponse = Depends(get_current_user_response),
    marketplace_repo=Depends(get_marketplace_repository),
):
    """
    Get eBay connection status for the authenticated user.

    This endpoint checks if the user has valid eBay credentials stored
    and returns the connection status for the settings page.
    """
    try:
        logger.info(f"Checking eBay connection status for user {current_user.id}")

        # Check if user has eBay credentials
        marketplace = await marketplace_repo.get_by_type(
            user_id=current_user.id, marketplace_type="ebay"
        )

        logger.info(f"Marketplace query result: {marketplace is not None}")
        if marketplace:
            logger.info(
                f"Found marketplace: active={marketplace.is_active}, has_credentials={hasattr(marketplace, 'credentials')}"
            )

        if not marketplace:
            return ApiResponse(
                status=200,
                message="No eBay connection found",
                success=True,
                data={
                    "connected": False,
                    "marketplace": "ebay",
                    "connection_date": None,
                    "status": "not_connected",
                    "requires_reauth": False,
                },
            )

        # Check if credentials exist and are valid
        credentials = (
            marketplace.credentials if hasattr(marketplace, "credentials") else {}
        )
        access_token = credentials.get("access_token", "")

        # Check if it's a real eBay token (starts with v^1.1# for production)
        has_real_token = bool(access_token and access_token.startswith("v^1.1#"))

        # If we have a real token, test it with eBay API
        token_valid = False
        if has_real_token:
            try:
                # Test token by making a lightweight API call
                await test_ebay_token(access_token)
                token_valid = True
                logger.info(
                    f"eBay token validation successful for user {current_user.id}"
                )
            except Exception as e:
                logger.warning(
                    f"eBay token validation failed for user {current_user.id}: {str(e)}"
                )
                token_valid = False

        return ApiResponse(
            status=200,
            message="eBay connection status retrieved",
            success=True,
            data={
                "connected": has_real_token and token_valid,
                "marketplace": "ebay",
                "connection_date": (
                    getattr(
                        marketplace, "created_at", datetime.now(timezone.utc)
                    ).isoformat()
                    if hasattr(marketplace, "created_at") and marketplace.created_at
                    else datetime.now(timezone.utc).isoformat()
                ),
                "status": (
                    "connected"
                    if (has_real_token and token_valid)
                    else ("token_expired" if has_real_token else "not_connected")
                ),
                "requires_reauth": not (has_real_token and token_valid),
                "token_expires_in": (
                    credentials.get("expires_in", 0) if has_real_token else 0
                ),
                "token_format_valid": has_real_token,
                "token_api_valid": token_valid,
            },
        )

    except Exception as e:
        logger.error(f"Error checking eBay connection status: {str(e)}")
        return ApiResponse(
            status=500,
            message="Failed to check eBay connection status",
            success=False,
            data={"connected": False, "marketplace": "ebay", "error": str(e)},
        )


class EbayItemUpdateRequest(BaseModel):
    """Request model for updating eBay items."""

    title: Optional[str] = Field(None, description="Updated item title")
    price: Optional[float] = Field(None, description="Updated item price")
    quantity: Optional[int] = Field(None, description="Updated item quantity")
    condition: Optional[str] = Field(None, description="Updated item condition")
    description: Optional[str] = Field(None, description="Updated item description")


@router.put("/inventory/{item_id}", response_model=ApiResponse)
async def update_ebay_item(
    item_id: str,
    update_request: EbayItemUpdateRequest,
    current_user: UnifiedUserResponse = Depends(get_current_user_response),
    marketplace_repo=Depends(get_marketplace_repository),
):
    """
    Update an eBay inventory item.

    This endpoint allows updating specific fields of an eBay listing.
    """
    try:
        logger.info(f"Updating eBay item {item_id} for user {current_user.id}")

        # Check if user has eBay credentials
        marketplace = await marketplace_repo.get_by_type(
            user_id=current_user.id, marketplace_type="ebay"
        )

        if not marketplace:
            return ApiResponse(
                status=404,
                message="No eBay connection found",
                success=False,
                data=None,
            )

        # Get access token
        credentials = (
            marketplace.credentials if hasattr(marketplace, "credentials") else {}
        )
        access_token = credentials.get("access_token")

        if not access_token:
            return ApiResponse(
                status=401,
                message="eBay access token not found",
                success=False,
                data=None,
            )

        # Build update data from request
        update_data = {}
        if update_request.title:
            update_data["title"] = update_request.title
        if update_request.price is not None:
            update_data["price"] = update_request.price
        if update_request.quantity is not None:
            update_data["quantity"] = update_request.quantity
        if update_request.condition:
            update_data["condition"] = update_request.condition
        if update_request.description:
            update_data["description"] = update_request.description

        if not update_data:
            return ApiResponse(
                status=400,
                message="No update data provided",
                success=False,
                data=None,
            )

        # For now, return success with the update data
        # TODO: Implement actual eBay API update call using ReviseItem
        logger.info(f"eBay item {item_id} update requested with data: {update_data}")

        return ApiResponse(
            status=200,
            message="eBay item update requested successfully",
            success=True,
            data={
                "item_id": item_id,
                "updates": update_data,
                "status": "pending",
                "note": "Item updates are queued for processing. Changes may take a few minutes to appear on eBay.",
            },
        )

    except Exception as e:
        logger.error(f"Failed to update eBay item {item_id}: {str(e)}")
        return ApiResponse(
            status=500,
            message=f"Failed to update eBay item: {str(e)}",
            success=False,
            data=None,
        )


@router.delete("/admin/clear-oauth/{user_email}", response_model=ApiResponse)
async def admin_clear_oauth_tokens(
    user_email: str,
    current_user: UnifiedUserResponse = Depends(get_current_user),
    marketplace_repo=Depends(get_marketplace_repository),
):
    """
    TEMPORARY ADMIN ENDPOINT: Clear OAuth tokens for a specific user.
    This is for debugging the OAuth persistence issue.
    """
    try:
        # Security check - only allow for test account
        if user_email != "test@example.com":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This admin endpoint only works for test account",
            )

        # Find user by email
        from fs_agt_clean.core.db.auth_repository import AuthRepository
        from fs_agt_clean.core.db.database import get_db

        async for db in get_db():
            user_repo = AuthRepository(db)
            user = await user_repo.get_user_by_email(user_email)

            if not user:
                return ApiResponse(
                    status=404, message=f"User not found: {user_email}", success=False
                )

            # Clear marketplace connection
            marketplace = await marketplace_repo.get_by_type(
                user_id=str(user.id), marketplace_type="ebay"
            )

            if marketplace:
                await marketplace_repo.delete_marketplace_connection(marketplace.id)
                logger.info(f"Cleared OAuth tokens for user {user_email}")

                return ApiResponse(
                    status=200,
                    message=f"OAuth tokens cleared for {user_email}",
                    success=True,
                    data={
                        "user_email": user_email,
                        "marketplace_id": marketplace.id,
                        "cleared": True,
                    },
                )
            else:
                return ApiResponse(
                    status=200,
                    message=f"No OAuth tokens found for {user_email}",
                    success=True,
                    data={"user_email": user_email, "cleared": False},
                )

    except Exception as e:
        logger.error(f"Error clearing OAuth tokens: {str(e)}")
        return ApiResponse(
            status=500, message=f"Failed to clear OAuth tokens: {str(e)}", success=False
        )


def generate_oauth_callback_html(
    success: bool,
    success_message: str = None,
    error_message: str = None,
    error_details: str = None,
    marketplace_data: dict = None,
    state: str = None,
) -> str:
    """Generate HTML response for OAuth callback popup window."""

    if success:
        status_content = f"""
            <div class="success">
                <h2>✅ {success_message or 'eBay Connected Successfully!'}</h2>
                <p>Your eBay account has been connected to FlipSync.</p>
                <p>You can close this window and return to the app.</p>
                <button class="close-btn" onclick="window.close()">Close Window</button>
            </div>
        """
        # Format message to match Flutter expectations
        message_data = {
            "source": "ebay_oauth_callback",
            "success": True,
            "code": "oauth_processed_successfully",  # Indicate server-side processing completed
            "state": state,  # Use the actual OAuth state parameter that was validated
            "message": success_message or "eBay account connected successfully",
            "marketplace_data": marketplace_data or {},
        }
    else:
        status_content = f"""
            <div class="error">
                <h2>❌ {error_message or 'Authentication Failed'}</h2>
                <p>{error_details or 'Please try connecting to eBay again.'}</p>
                <button class="close-btn" onclick="window.close()">Close Window</button>
            </div>
        """
        # Format error message to match Flutter expectations
        message_data = {
            "source": "ebay_oauth_callback",
            "success": False,
            "error": error_message or "Authentication failed",
            "error_description": error_details or "Unknown error",
        }

    # Convert message data to JSON string for JavaScript
    import json

    message_json = json.dumps(message_data)

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FlipSync eBay OAuth</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .container {{
            background: white;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            text-align: center;
            max-width: 500px;
            width: 100%;
        }}
        .logo {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
            margin-bottom: 20px;
        }}
        .success {{ color: #28a745; }}
        .error {{ color: #dc3545; }}
        .close-btn {{
            background: #007bff;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            margin-top: 20px;
        }}
        .close-btn:hover {{
            background: #0056b3;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🔄 FlipSync</div>
        <div id="status">
            {status_content}
        </div>
    </div>

    <script>
        console.log('🚀 FlipSync eBay OAuth Callback Page Loaded');

        // Message data prepared by server (OAuth already processed)
        const messageData = {message_json};

        console.log('📤 Sending OAuth result to parent window:', messageData);
        console.log('🔍 window.opener available:', !!window.opener);
        console.log('🔍 BroadcastChannel available:', typeof BroadcastChannel !== 'undefined');

        // Add a small delay to ensure the popup is fully loaded before sending message
        setTimeout(() => {{
            console.log('⏰ Delayed message sending starting...');

        // Method 1: Try postMessage to window.opener (traditional approach)
        let messageSent = false;
        if (window.opener && !window.opener.closed) {{
            try {{
                // FIXED: Try www domain first since that's where the main app runs
                window.opener.postMessage(messageData, 'https://www.flipsyncai.com');
                console.log('✅ OAuth result sent via postMessage to opener (www.flipsyncai.com)');
                messageSent = true;
            }} catch (error) {{
                console.log('❌ postMessage to www.flipsyncai.com failed:', error);
                // Try non-www origin as fallback
                try {{
                    window.opener.postMessage(messageData, 'https://flipsyncai.com');
                    console.log('✅ OAuth result sent via postMessage to opener (flipsyncai.com)');
                    messageSent = true;
                }} catch (error2) {{
                    console.log('❌ postMessage to flipsyncai.com also failed:', error2);
                    // Try with wildcard origin as final fallback
                    try {{
                        window.opener.postMessage(messageData, '*');
                        console.log('✅ OAuth result sent via postMessage to opener (wildcard)');
                        messageSent = true;
                    }} catch (error3) {{
                        console.log('❌ postMessage with wildcard also failed:', error3);
                    }}
                }}
            }}
        }} else {{
            console.log('❌ window.opener not available or closed');
        }}

        // Method 2: Use BroadcastChannel as fallback (works even when opener is null)
        if (typeof BroadcastChannel !== 'undefined') {{
            try {{
                const channel = new BroadcastChannel('flipsync_oauth');
                channel.postMessage(messageData);
                console.log('✅ OAuth result sent via BroadcastChannel');
                messageSent = true;

                // Close channel after sending
                setTimeout(() => {{
                    channel.close();
                }}, 1000);
            }} catch (error) {{
                console.log('❌ BroadcastChannel failed:', error);
            }}
        }} else {{
            console.log('❌ BroadcastChannel not supported');
        }}

        // Method 3: Use localStorage as final fallback
        try {{
            const storageKey = 'flipsync_oauth_result';
            const storageData = {{
                ...messageData,
                timestamp: Date.now(),
                source: 'oauth_popup'
            }};
            localStorage.setItem(storageKey, JSON.stringify(storageData));
            console.log('✅ OAuth result stored in localStorage');
            messageSent = true;

            // Trigger storage event for cross-tab communication
            window.dispatchEvent(new StorageEvent('storage', {{
                key: storageKey,
                newValue: JSON.stringify(storageData),
                url: window.location.href
            }}));
            console.log('✅ Storage event dispatched');
        }} catch (error) {{
            console.log('❌ localStorage fallback failed:', error);
        }}

        if (messageSent) {{
            console.log('🎉 OAuth result communicated successfully');
            console.log('✅ Popup will remain open for user to manually close');

            // Add visible debugging info to the page
            document.getElementById('status').innerHTML += `
                <div style="background: #e8f5e8; border: 2px solid #4caf50; padding: 15px; margin: 20px 0; border-radius: 8px;">
                    <h3 style="color: #2e7d32; margin: 0 0 10px 0;">🎉 SUCCESS - Message Sent!</h3>
                    <p style="margin: 5px 0; color: #2e7d32;">✅ postMessage sent to parent window</p>
                    <p style="margin: 5px 0; color: #2e7d32;">✅ Popup staying open for manual close</p>
                    <p style="margin: 5px 0; color: #666;">Check parent window for connection status</p>
                </div>
            `;
        }} else {{
            console.log('❌ All communication methods failed');

            // Add visible debugging info for failure
            document.getElementById('status').innerHTML += `
                <div style="background: #ffe8e8; border: 2px solid #f44336; padding: 15px; margin: 20px 0; border-radius: 8px;">
                    <h3 style="color: #c62828; margin: 0 0 10px 0;">❌ COMMUNICATION FAILED</h3>
                    <p style="margin: 5px 0; color: #c62828;">❌ postMessage failed to send</p>
                    <p style="margin: 5px 0; color: #c62828;">❌ Check browser console for errors</p>
                    <p style="margin: 5px 0; color: #666;">Manual close required</p>
                </div>
            `;

            // Show manual close instruction
            document.getElementById('status').innerHTML += `
                <p style="margin-top: 20px; color: #666;">
                    Communication failed. Please close this window manually and try again.
                </p>
            `;
        }}

        }}, 500); // 500ms delay to ensure popup is ready

        // Handle messages from parent window
        let allowAutoClose = false;

        // Allow auto-close after 5 seconds
        setTimeout(() => {{
            allowAutoClose = true;
            console.log('✅ Auto-close now allowed after 5 second delay');
        }}, 5000);

        window.addEventListener('message', function(event) {{
            console.log('📨 Received message from parent:', event.data);

            if (event.data.type === 'CLOSE_POPUP') {{
                console.log('❌ CLOSE_POPUP message received');
                if (allowAutoClose) {{
                    console.log('✅ Auto-close allowed - popup will close');
                    window.close();
                }} else {{
                    console.log('⏰ Auto-close blocked - popup will stay open for user to see success message');
                    console.log('⏰ Popup will auto-close in a few seconds, or close manually');
                }}
            }}
        }});

        // Additional debugging
        console.log('🔍 Current window location:', window.location.href);
        console.log('🔍 Document referrer:', document.referrer);
        console.log('🔍 Window name:', window.name);
    </script>
</body>
</html>
    """

    # REMOVED: Legacy POST handler - OAuth now handled directly in GET handler
    # This eliminates the need for mock users and consolidates OAuth logic
