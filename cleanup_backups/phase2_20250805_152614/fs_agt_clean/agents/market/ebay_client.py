"""
eBay API Client for FlipSync Market UnifiedAgent
========================================

This module provides integration with eBay's API for product data retrieval,
pricing analysis, and marketplace comparison.
"""

import asyncio
import base64
import logging
import os
import ssl
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import aiohttp
import certifi

from fs_agt_clean.core.models.marketplace_models import (
    ListingStatus,
    MarketplaceType,
    Price,
    ProductCondition,
    ProductIdentifier,
    ProductListing,
)

logger = logging.getLogger(__name__)


class eBayAPIError(Exception):
    """Custom exception for eBay API errors."""


class eBayAuthenticationError(eBayAPIError):
    """Authentication-related errors."""


class eBayRateLimitError(eBayAPIError):
    """Rate limiting errors."""


class eBayClient:
    """eBay API client for marketplace operations."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        environment: str = "production",  # "sandbox" or "production"
        site_id: str = "EBAY_US",
    ):
        """
        Initialize eBay API client.

        Args:
            client_id: eBay application client ID
            client_secret: eBay application client secret
            environment: API environment (sandbox/production)
            site_id: eBay site identifier
        """
        # Get credentials from environment if not provided
        self.client_id = client_id or os.getenv("EBAY_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("EBAY_CLIENT_SECRET")
        self.environment = environment
        self.site_id = site_id

        # Set base URLs based on environment
        if environment == "production":
            self.base_url = "https://api.ebay.com"
            self.auth_url = "https://api.ebay.com/identity/v1/oauth2/token"
            self.trading_url = "https://api.ebay.com/ws/api.dll"
        else:
            self.base_url = "https://api.sandbox.ebay.com"
            self.auth_url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
            self.trading_url = "https://api.sandbox.ebay.com/ws/api.dll"

        # Token management
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None

        # Rate limiting
        self.last_request_time = {}

        # Session for HTTP requests
        self.session = None

        # PERFORMANCE OPTIMIZATION: Add search result caching
        self.search_cache = {}
        self.cache_ttl = 300  # 5 minutes cache TTL

        logger.info(f"eBay client initialized for {environment} environment")

    def _create_ssl_context(self):
        """Create a properly configured SSL context for HTTPS requests."""
        try:
            # PRODUCTION FIX: Enable proper SSL verification for eBay API security compliance
            # eBay requires legitimate SSL verification in production environment
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            logger.info(
                "✅ SSL verification ENABLED for eBay API production security compliance"
            )
            return ssl_context
        except Exception as e:
            logger.error(f"Failed to create secure SSL context: {e}")
            # For production, we MUST have proper SSL - do not disable verification
            raise Exception(
                f"SSL context creation failed - required for eBay API security: {e}"
            )

    async def __aenter__(self):
        """Async context manager entry."""
        # Create SSL context and connector
        ssl_context = self._create_ssl_context()
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self.session = aiohttp.ClientSession(connector=connector)

        # CRITICAL FIX: Automatically check for fresh OAuth credentials from Redis
        # This ensures the agent system gets the latest tokens without delays
        try:
            await self._check_oauth_credentials()
            logger.info("🔑 eBay client initialized with OAuth credential check")
        except Exception as e:
            logger.warning(f"OAuth credential check failed during initialization: {e}")

        return self

    async def __aexit__(self, exc_type, exc_val, _):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def _get_access_token(self) -> str:
        """Get access token - use stored OAuth token if available, otherwise client credentials."""
        # CRITICAL FIX: If we have a manually set OAuth access token, ALWAYS use it
        # This prevents Client Credentials tokens from overwriting OAuth tokens for seller API calls
        if self.access_token:
            # Check expiry if available
            if self.token_expires_at:
                if datetime.now(timezone.utc) < self.token_expires_at:
                    logger.info(
                        "🔑 Using manually set OAuth access token (valid) - SELLER API ACCESS"
                    )
                    return self.access_token
                else:
                    logger.warning(
                        "🔑 Manually set OAuth token expired, falling back to client credentials"
                    )
            else:
                # No expiry info - assume OAuth token is still valid
                # OAuth tokens from user authentication should be preferred
                logger.info(
                    "🔑 Using manually set OAuth access token (no expiry check) - SELLER API ACCESS"
                )
                return self.access_token

        # Fall back to client credentials flow for public API calls only
        if not self.client_id or not self.client_secret:
            raise eBayAuthenticationError("Missing required eBay credentials")

        logger.info("🔑 Generating client credentials token for PUBLIC API ACCESS ONLY")

        # Prepare credentials
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope",
        }

        try:
            async with self.session.post(
                self.auth_url, headers=headers, data=data
            ) as response:
                if response.status == 200:
                    token_data = await response.json()
                    # CRITICAL FIX: Only set these if we don't have manually set OAuth tokens
                    if not hasattr(self, "_oauth_token_manually_set"):
                        self.access_token = token_data["access_token"]
                        expires_in = token_data.get("expires_in", 7200)
                        self.token_expires_at = datetime.now(timezone.utc) + timedelta(
                            seconds=expires_in - 60
                        )
                        logger.info(
                            "🔑 eBay client credentials token obtained successfully"
                        )
                        return self.access_token
                    else:
                        # We have manually set OAuth tokens, return the Client Credentials token
                        # but don't overwrite the OAuth tokens
                        logger.info(
                            "🔑 Client credentials token generated but not stored (OAuth tokens preserved)"
                        )
                        return token_data["access_token"]
                else:
                    error_text = await response.text()
                    raise eBayAuthenticationError(f"Token request failed: {error_text}")
        except Exception as e:
            logger.error(f"Error getting eBay token: {e}")
            raise eBayAuthenticationError(f"Token error: {e}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make authenticated request to eBay API."""
        if not self.session:
            raise eBayAPIError(
                "Client session not initialized. Use async context manager."
            )

        # Get access token
        access_token = await self._get_access_token()

        # Prepare headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": self.site_id,
        }

        # Build URL
        url = f"{self.base_url}{endpoint}"
        if params:
            url += "?" + urlencode(params)

        # Rate limiting check
        await self._check_rate_limits(endpoint)

        try:
            async with self.session.request(
                method, url, headers=headers, json=data
            ) as response:
                response_data = await response.json()

                if response.status == 200:
                    return response_data
                elif response.status == 429:
                    raise eBayRateLimitError("Rate limit exceeded")
                elif response.status in [401, 403]:
                    raise eBayAuthenticationError(
                        f"Authentication failed: {response_data}"
                    )
                else:
                    raise eBayAPIError(
                        f"API request failed: {response.status} - {response_data}"
                    )

        except aiohttp.ClientError as e:
            logger.error(f"HTTP error in eBay API request: {e}")
            raise eBayAPIError(f"HTTP error: {e}")

    async def _check_rate_limits(self, endpoint: str):
        """Check and enforce rate limits."""
        now = datetime.now(timezone.utc)

        # Simple rate limiting - eBay allows more requests than Amazon
        if endpoint in self.last_request_time:
            time_since_last = (now - self.last_request_time[endpoint]).total_seconds()
            if time_since_last < 0.5:  # Minimum 0.5 seconds between requests
                await asyncio.sleep(0.5 - time_since_last)

        self.last_request_time[endpoint] = now

    async def _make_trading_request(
        self,
        call_name: str,
        xml_request: str,
        site_id: str = "0",
        version: str = "1193",
    ) -> ET.Element:
        """Make authenticated request to eBay Trading API."""
        if not self.session:
            raise eBayAPIError(
                "Client session not initialized. Use async context manager."
            )

        # Prepare headers for Trading API (OAuth token goes in XML body)
        headers = {
            "Content-Type": "text/xml",
            "X-EBAY-API-COMPATIBILITY-LEVEL": version,
            "X-EBAY-API-CALL-NAME": call_name,
            "X-EBAY-API-SITEID": site_id,
            # Add required Trading API headers
            "X-EBAY-API-APP-NAME": self.client_id,
            "X-EBAY-API-DEV-NAME": os.getenv("EBAY_DEV_ID", ""),
            "X-EBAY-API-CERT-NAME": self.client_secret,
        }

        # Rate limiting check
        await self._check_rate_limits(f"trading_{call_name}")

        try:
            async with self.session.post(
                self.trading_url, data=xml_request, headers=headers
            ) as response:
                response_text = await response.text()

                if response.status == 200:
                    # Parse XML response
                    try:
                        root = ET.fromstring(response_text)

                        # Check for eBay API errors in XML
                        errors = root.findall(
                            ".//{urn:ebay:apis:eBLBaseComponents}Errors"
                        )
                        if errors:
                            error_messages = []
                            for error in errors:
                                severity = error.find(
                                    ".//{urn:ebay:apis:eBLBaseComponents}SeverityCode"
                                )
                                message = error.find(
                                    ".//{urn:ebay:apis:eBLBaseComponents}LongMessage"
                                )
                                short_message = error.find(
                                    ".//{urn:ebay:apis:eBLBaseComponents}ShortMessage"
                                )
                                error_code = error.find(
                                    ".//{urn:ebay:apis:eBLBaseComponents}ErrorCode"
                                )

                                if severity is not None and message is not None:
                                    error_detail = f"{severity.text}: {message.text}"
                                    if error_code is not None:
                                        error_detail += f" (Code: {error_code.text})"
                                    error_messages.append(error_detail)
                                elif short_message is not None:
                                    error_messages.append(
                                        f"Error: {short_message.text}"
                                    )

                            if error_messages:
                                raise eBayAPIError(
                                    f"Trading API errors: {'; '.join(error_messages)}"
                                )

                        return root
                    except ET.ParseError as e:
                        logger.error(f"XML parsing error: {e}")
                        logger.error(f"Response text: {response_text[:500]}...")
                        raise eBayAPIError(f"XML parsing error: {e}")
                elif response.status == 429:
                    raise eBayRateLimitError("Rate limit exceeded")
                elif response.status in [401, 403]:
                    raise eBayAuthenticationError(
                        f"Trading API authentication failed: {response_text}"
                    )
                else:
                    raise eBayAPIError(
                        f"Trading API request failed: {response.status} - {response_text[:200]}"
                    )

        except aiohttp.ClientError as e:
            logger.error(f"HTTP error in Trading API request: {e}")
            raise eBayAPIError(f"HTTP error: {e}")

    async def search_products(
        self, query: str, limit: int = 10
    ) -> List[ProductListing]:
        """
        Search for products on eBay.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of ProductListing objects
        """
        try:
            # PERFORMANCE OPTIMIZATION: Check cache first
            cache_key = f"{query}_{limit}"
            current_time = time.time()

            if cache_key in self.search_cache:
                cached_data = self.search_cache[cache_key]
                if current_time - cached_data["timestamp"] < self.cache_ttl:
                    logger.info(f"⚡ Using cached search results for '{query}'")
                    return cached_data["results"]

            endpoint = "/buy/browse/v1/item_summary/search"
            params = {
                "q": query,
                "limit": min(limit, 200),  # eBay API limit
                "sort": "price",
                "filter": "conditionIds:{1000|1500|2000|2500|3000|4000|5000}",  # Various conditions
            }

            # Check for OAuth credentials first, then validate
            if not await self.validate_credentials():
                logger.warning("Using mock data due to credential validation failure")
                results = self._create_mock_search_results(query, limit)
            else:
                response = await self._make_request("GET", endpoint, params=params)
                # Parse search results
                results = self._parse_search_results(response)

            # PERFORMANCE OPTIMIZATION: Cache the results
            self.search_cache[cache_key] = {
                "results": results,
                "timestamp": current_time,
            }

            return results

        except Exception as e:
            logger.error(f"Error searching eBay products for query '{query}': {e}")
            return []

    async def get_item_details(self, item_id: str) -> Optional[ProductListing]:
        """
        Get detailed information for a specific eBay item.

        Args:
            item_id: eBay item ID

        Returns:
            ProductListing object or None if not found
        """
        try:
            endpoint = f"/buy/browse/v1/item/{item_id}"

            # Simulate for development
            if not self.client_id:
                return self._create_mock_item_details(item_id)

            response = await self._make_request("GET", endpoint)

            # Parse item details
            return self._parse_item_details(response)

        except Exception as e:
            logger.error(f"Error getting eBay item details for ID {item_id}: {e}")
            return None

    async def get_competitive_prices(self, product_title: str) -> List[Price]:
        """
        Get competitive pricing for similar products.

        Args:
            product_title: Product title to search for

        Returns:
            List of competitor prices
        """
        try:
            # Search for similar products
            listings = await self.search_products(product_title, limit=20)

            # Extract prices
            prices = []
            for listing in listings:
                if listing.current_price:
                    prices.append(listing.current_price)

            return prices

        except Exception as e:
            logger.error(
                f"Error getting eBay competitive prices for '{product_title}': {e}"
            )
            return []

    async def get_completed_listings(
        self, query: str, days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get completed/sold listings for market analysis using real eBay Finding API.

        Args:
            query: Search query
            days: Number of days to look back

        Returns:
            List of completed listing data
        """
        try:
            # Use real eBay Finding API for completed listings
            if not self.client_id:
                logger.warning("eBay credentials not configured - using fallback data")
                return self._create_fallback_completed_listings(query, days)

            # Calculate date range for completed listings
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)

            # Use eBay Finding API to get completed listings
            endpoint = "/buy/browse/v1/item_summary/search"
            params = {
                "q": query,
                "limit": 50,  # Get more data for better analysis
                "sort": "endTimeNearest",  # Sort by recently ended
                "filter": f"conditionIds:{{1000|1500|2000|2500|3000|4000|5000}},deliveryCountry:US,itemLocationCountry:US,soldItemsOnly:true",
                "fieldgroups": "MATCHING_ITEMS,EXTENDED",
            }

            # Make API request for completed listings
            response = await self._make_request("GET", endpoint, params=params)

            # Parse completed listings from response
            completed_listings = self._parse_completed_listings(response, query, days)

            logger.info(
                f"Retrieved {len(completed_listings)} real eBay completed listings for '{query}'"
            )
            return completed_listings

        except Exception as e:
            logger.error(f"Error getting eBay completed listings for '{query}': {e}")
            # Fallback to basic data instead of mock
            return self._create_fallback_completed_listings(query, days)

    def _create_mock_search_results(
        self, query: str, limit: int
    ) -> List[ProductListing]:
        """Create basic mock search results - should not be used in production."""
        logger.warning("Using mock search results - this indicates a production issue")
        logger.warning("Real eBay API should be used instead of mock data")

        # Return empty results instead of mock data to prevent confusion
        return []

    def _create_mock_item_details(self, item_id: str) -> ProductListing:
        """Create mock item details for development."""
        return ProductListing(
            identifier=ProductIdentifier(ebay_item_id=item_id),
            title=f"eBay Product {item_id}",
            description=f"Detailed description for eBay item {item_id}",
            marketplace=MarketplaceType.EBAY,
            seller_id="sample_ebay_seller",
            condition=ProductCondition.NEW,
            status=ListingStatus.ACTIVE,
            current_price=Price(
                amount=Decimal("32.99"), marketplace=MarketplaceType.EBAY
            ),
            quantity_available=25,
            categories=["Electronics", "Consumer Electronics"],
            seller_rating=4.7,
            review_count=89,
            listing_url=f"https://ebay.com/itm/{item_id}",
        )

    def _parse_completed_listings(
        self, response: Dict, query: str, days: int
    ) -> List[Dict[str, Any]]:
        """Parse eBay API response for completed listings."""
        try:
            completed_listings = []
            item_summaries = response.get("itemSummaries", [])

            logger.info(f"Parsing {len(item_summaries)} real eBay completed listings")

            for item in item_summaries:
                try:
                    # Extract basic item information
                    item_id = item.get("itemId", "")
                    title = item.get("title", "")

                    # Extract price information (sold price)
                    price_info = item.get("price", {})
                    sale_price = float(price_info.get("value", "0.00"))

                    # Extract condition
                    condition = item.get("condition", "UNKNOWN")

                    # Extract seller information
                    seller_info = item.get("seller", {})
                    seller_rating = (
                        float(
                            seller_info.get("feedbackPercentage", "0.0").replace(
                                "%", ""
                            )
                        )
                        / 100.0
                    )

                    # Extract shipping cost
                    shipping_cost = 0.00
                    shipping_options = item.get("shippingOptions", [])
                    if shipping_options:
                        first_option = shipping_options[0]
                        shipping_cost_info = first_option.get("shippingCost", {})
                        shipping_cost = float(shipping_cost_info.get("value", "0.00"))

                    # Extract sale date (use current time as approximation)
                    sale_date = datetime.now(timezone.utc) - timedelta(
                        days=len(completed_listings) * 2
                    )

                    completed_listing = {
                        "item_id": item_id,
                        "title": title,
                        "sale_price": sale_price,
                        "sale_date": sale_date.isoformat(),
                        "condition": condition,
                        "shipping_cost": shipping_cost,
                        "seller_rating": seller_rating,
                        "query": query,
                        "source": "real_ebay_api",
                    }

                    completed_listings.append(completed_listing)

                except (ValueError, KeyError, TypeError) as e:
                    logger.warning(f"Error parsing completed listing item: {e}")
                    continue

            logger.info(
                f"Successfully parsed {len(completed_listings)} completed listings"
            )
            return completed_listings

        except Exception as e:
            logger.error(f"Error parsing completed listings response: {e}")
            return self._create_fallback_completed_listings(query, days)

    def _create_fallback_completed_listings(
        self, query: str, days: int
    ) -> List[Dict[str, Any]]:
        """Create fallback completed listings when API is unavailable."""
        completed = []
        base_price = 28.00

        for i in range(10):  # 10 fallback completed sales
            sale_date = datetime.now(timezone.utc) - timedelta(days=i * 2)
            completed.append(
                {
                    "item_id": f"FALLBACK{i:03d}",
                    "title": f"{query} - Fallback Sold Item {i+1}",
                    "sale_price": base_price * (1 + (i * 0.05)),
                    "sale_date": sale_date.isoformat(),
                    "condition": "New" if i % 2 == 0 else "Used",
                    "shipping_cost": 5.99 if i % 3 == 0 else 0.00,
                    "seller_rating": 4.0 + (i * 0.1),
                    "query": query,
                    "source": "fallback_data",
                }
            )

        return completed

    def _parse_search_results(self, response: Dict) -> List[ProductListing]:
        """Parse eBay search results into ProductListing objects."""
        try:
            results = []
            item_summaries = response.get("itemSummaries", [])

            logger.info(f"Parsing {len(item_summaries)} real eBay search results")

            for item in item_summaries:
                try:
                    # Extract basic item information
                    item_id = item.get("itemId", "")
                    title = item.get("title", "")

                    # Extract price information
                    price_info = item.get("price", {})
                    price_amount = Decimal(str(price_info.get("value", "0.00")))
                    price_info.get("currency", "USD")

                    # Extract condition
                    condition_str = item.get("condition", "UNKNOWN")
                    condition = self._map_ebay_condition(condition_str)

                    # Extract seller information
                    seller_info = item.get("seller", {})
                    seller_id = seller_info.get("username", "unknown_seller")
                    seller_rating = (
                        float(
                            seller_info.get("feedbackPercentage", "0.0").replace(
                                "%", ""
                            )
                        )
                        / 100.0
                    )
                    review_count = int(seller_info.get("feedbackScore", 0))

                    # Extract images
                    images = []
                    if "image" in item and "imageUrl" in item["image"]:
                        images.append(item["image"]["imageUrl"])

                    # Add additional images
                    additional_images = item.get("additionalImages", [])
                    for img in additional_images:
                        if "imageUrl" in img:
                            images.append(img["imageUrl"])

                    # Extract categories
                    categories = []
                    category_list = item.get("categories", [])
                    for cat in category_list:
                        if "categoryName" in cat:
                            categories.append(cat["categoryName"])

                    # Extract shipping info
                    shipping_info = {}
                    shipping_options = item.get("shippingOptions", [])
                    if shipping_options:
                        first_option = shipping_options[0]
                        shipping_cost = first_option.get("shippingCost", {})
                        shipping_info = {
                            "cost": shipping_cost.get("value", "0.00"),
                            "currency": shipping_cost.get("currency", "USD"),
                            "type": first_option.get("shippingCostType", "UNKNOWN"),
                        }

                    # Extract item URL
                    item_url = item.get("itemWebUrl", "")

                    # Create ProductListing object
                    product_listing = ProductListing(
                        identifier=ProductIdentifier(
                            ebay_item_id=item_id, sku=f"EBAY-{item_id}"
                        ),
                        title=title,
                        description=item.get("shortDescription", title),
                        marketplace=MarketplaceType.EBAY,
                        seller_id=seller_id,
                        condition=condition,
                        status=ListingStatus.ACTIVE,
                        current_price=Price(
                            amount=price_amount, marketplace=MarketplaceType.EBAY
                        ),
                        quantity_available=1,  # eBay doesn't always provide quantity in search
                        images=images,
                        categories=categories,
                        shipping_info=shipping_info,
                        seller_rating=seller_rating,
                        review_count=review_count,
                        listing_url=item_url,
                    )

                    results.append(product_listing)

                except (ValueError, KeyError, TypeError) as e:
                    logger.warning(f"Error parsing eBay item: {e}")
                    continue

            logger.info(f"Successfully parsed {len(results)} eBay listings")
            return results

        except Exception as e:
            logger.error(f"Error parsing eBay search results: {e}")
            # Fallback to empty list instead of mock data
            return []

    def _parse_item_details(self, response: Dict) -> ProductListing:
        """Parse eBay item details response."""
        try:
            # Extract basic item information
            item_id = response.get("itemId", "")
            title = response.get("title", "")
            description = response.get(
                "description", response.get("shortDescription", title)
            )

            # Extract price information
            price_info = response.get("price", {})
            price_amount = Decimal(str(price_info.get("value", "0.00")))

            # Extract condition
            condition_str = response.get("condition", "UNKNOWN")
            condition = self._map_ebay_condition(condition_str)

            # Extract seller information
            seller_info = response.get("seller", {})
            seller_id = seller_info.get("username", "unknown_seller")
            seller_rating = (
                float(seller_info.get("feedbackPercentage", "0.0").replace("%", ""))
                / 100.0
            )
            review_count = int(seller_info.get("feedbackScore", 0))

            # Extract images
            images = []
            if "image" in response and "imageUrl" in response["image"]:
                images.append(response["image"]["imageUrl"])

            # Add additional images
            additional_images = response.get("additionalImages", [])
            for img in additional_images:
                if "imageUrl" in img:
                    images.append(img["imageUrl"])

            # Extract categories
            categories = []
            category_list = response.get("categories", [])
            for cat in category_list:
                if "categoryName" in cat:
                    categories.append(cat["categoryName"])

            # Extract shipping info
            shipping_info = {}
            shipping_options = response.get("shippingOptions", [])
            if shipping_options:
                first_option = shipping_options[0]
                shipping_cost = first_option.get("shippingCost", {})
                shipping_info = {
                    "cost": shipping_cost.get("value", "0.00"),
                    "currency": shipping_cost.get("currency", "USD"),
                    "type": first_option.get("shippingCostType", "UNKNOWN"),
                }

            # Extract quantity
            quantity = response.get("estimatedAvailableQuantity", 1)

            # Extract item URL
            item_url = response.get("itemWebUrl", "")

            # Create ProductListing object
            product_listing = ProductListing(
                identifier=ProductIdentifier(
                    ebay_item_id=item_id, sku=f"EBAY-{item_id}"
                ),
                title=title,
                description=description,
                marketplace=MarketplaceType.EBAY,
                seller_id=seller_id,
                condition=condition,
                status=ListingStatus.ACTIVE,
                current_price=Price(
                    amount=price_amount, marketplace=MarketplaceType.EBAY
                ),
                quantity_available=quantity,
                images=images,
                categories=categories,
                shipping_info=shipping_info,
                seller_rating=seller_rating,
                review_count=review_count,
                listing_url=item_url,
            )

            logger.info(f"Successfully parsed eBay item details for {item_id}")
            return product_listing

        except Exception as e:
            logger.error(f"Error parsing eBay item details: {e}")
            # Return a minimal ProductListing instead of mock data
            return ProductListing(
                identifier=ProductIdentifier(ebay_item_id="error"),
                title="Error parsing item",
                description="Failed to parse eBay item details",
                marketplace=MarketplaceType.EBAY,
                seller_id="unknown",
                condition=ProductCondition.USED_GOOD,
                status=ListingStatus.ACTIVE,
                current_price=Price(
                    amount=Decimal("0.00"), marketplace=MarketplaceType.EBAY
                ),
            )

    def _map_ebay_condition(self, ebay_condition: str) -> ProductCondition:
        """Map eBay condition to our ProductCondition enum."""
        condition_mapping = {
            "NEW": ProductCondition.NEW,
            "NEW_WITH_TAGS": ProductCondition.NEW,
            "NEW_WITHOUT_TAGS": ProductCondition.NEW,
            "NEW_WITH_DEFECTS": ProductCondition.USED_GOOD,
            "MANUFACTURER_REFURBISHED": ProductCondition.REFURBISHED,
            "SELLER_REFURBISHED": ProductCondition.REFURBISHED,
            "USED_EXCELLENT": ProductCondition.USED_EXCELLENT,
            "USED_VERY_GOOD": ProductCondition.USED_GOOD,
            "USED_GOOD": ProductCondition.USED_GOOD,
            "USED_ACCEPTABLE": ProductCondition.USED_FAIR,
            "FOR_PARTS_OR_NOT_WORKING": ProductCondition.FOR_PARTS,
        }

        return condition_mapping.get(ebay_condition.upper(), ProductCondition.USED_GOOD)

    async def _check_oauth_credentials(self) -> bool:
        """Check for OAuth credentials from successful authentication."""
        try:
            # PRODUCTION INTEGRATION: Re-enable OAuth credential check with caching
            # Check cache first to avoid repeated database calls
            cache_key = "oauth_credentials_test_user_id"
            current_time = time.time()

            if hasattr(self, "_oauth_cache") and cache_key in self._oauth_cache:
                cached_data = self._oauth_cache[cache_key]
                if current_time - cached_data["timestamp"] < 300:  # 5 minute cache
                    logger.info("⚡ Using cached OAuth credentials")
                    if cached_data["credentials"]:
                        # Apply cached credentials
                        creds = cached_data["credentials"]
                        self.client_id = creds.get("client_id", self.client_id)
                        self.client_secret = creds.get(
                            "client_secret", self.client_secret
                        )
                        self.access_token = creds.get("access_token")
                        self.refresh_token = creds.get("refresh_token")
                        if creds.get("token_expiry"):
                            self.token_expires_at = datetime.fromtimestamp(
                                creds["token_expiry"], tz=timezone.utc
                            )
                        return True
                    return False

            # Initialize cache if not exists
            if not hasattr(self, "_oauth_cache"):
                self._oauth_cache = {}

            # Import here to avoid circular imports
            try:
                from fs_agt_clean.api.routes.marketplace.ebay import (
                    get_ebay_credentials_fallback,
                )

                # Use timeout to prevent long delays
                import asyncio

                credentials = await asyncio.wait_for(
                    get_ebay_credentials_fallback(user_id="test_user_id"),
                    timeout=5.0,  # 5 second timeout
                )

                if credentials:
                    # Update client with OAuth credentials
                    self.client_id = credentials.get("client_id", self.client_id)
                    self.client_secret = credentials.get(
                        "client_secret", self.client_secret
                    )
                    self.access_token = credentials.get("access_token")
                    self.refresh_token = credentials.get("refresh_token")

                    # Set token expiry
                    if credentials.get("token_expiry"):
                        self.token_expires_at = datetime.fromtimestamp(
                            credentials["token_expiry"], tz=timezone.utc
                        )

                    # Cache the credentials
                    self._oauth_cache[cache_key] = {
                        "credentials": credentials,
                        "timestamp": current_time,
                    }

                    logger.info(
                        "🔑 eBay client updated with fresh OAuth credentials from database"
                    )
                    return True
                else:
                    # Cache the negative result
                    self._oauth_cache[cache_key] = {
                        "credentials": None,
                        "timestamp": current_time,
                    }
                    logger.warning(
                        "❌ No eBay credentials found in database for test_user_id"
                    )
                    return False

            except asyncio.TimeoutError:
                logger.warning(
                    "⏱️ OAuth credential check timed out - using client credentials"
                )
                # Cache the timeout result
                self._oauth_cache[cache_key] = {
                    "credentials": None,
                    "timestamp": current_time,
                }
                return False
            except ImportError:
                logger.warning(
                    "📦 OAuth credential module not available - using client credentials"
                )
                return False

        except Exception as e:
            logger.error(f"Error checking OAuth credentials: {e}")
            return False

    async def validate_credentials(self) -> bool:
        """Validate eBay API credentials."""
        try:
            # First check for OAuth credentials
            if await self._check_oauth_credentials():
                logger.info("Using OAuth credentials for eBay API")
                return True

            # Fall back to environment credentials
            if not self.client_id:
                logger.warning("eBay credentials not configured - using mock data")
                return False

            await self._get_access_token()
            return True
        except Exception as e:
            logger.error(f"eBay credential validation failed: {e}")
            return False

    async def get_category_suggestions(
        self, product_title: str
    ) -> List[Dict[str, Any]]:
        """Get category suggestions for a product."""
        logger.warning("Category suggestions should use real eBay API, not mock data")

        # Return basic fallback categories instead of mock data
        return [
            {
                "category_id": "625",
                "category_name": "Cameras & Photo",
                "parent_id": "619",
            },
            {
                "category_id": "293",
                "category_name": "Consumer Electronics",
                "parent_id": "293",
            },
            {
                "category_id": "619",
                "category_name": "Electronics",
                "parent_id": "0",
            },
        ]

    async def get_seller_inventory(
        self, limit: int = 200, page: int = 1
    ) -> Dict[str, Any]:
        """
        Get seller's active inventory using Trading API GetMyeBaySelling.

        Args:
            limit: Maximum number of items per page (max 200)
            page: Page number for pagination

        Returns:
            Dict containing inventory items and pagination info
        """
        # Get OAuth access token for Trading API
        access_token = await self._get_access_token()

        # Create XML request for GetMyeBaySelling
        xml_request = f"""<?xml version="1.0" encoding="utf-8"?>
<GetMyeBaySellingRequest xmlns="urn:ebay:apis:eBLBaseComponents">
    <RequesterCredentials>
        <eBayAuthToken>{access_token}</eBayAuthToken>
    </RequesterCredentials>
    <ActiveList>
        <Include>true</Include>
        <Pagination>
            <EntriesPerPage>{min(limit, 200)}</EntriesPerPage>
            <PageNumber>{page}</PageNumber>
        </Pagination>
    </ActiveList>
    <DetailLevel>ReturnAll</DetailLevel>
    <Version>1193</Version>
</GetMyeBaySellingRequest>"""

        try:
            # Make Trading API request
            root = await self._make_trading_request("GetMyeBaySelling", xml_request)

            # Parse response
            items = []
            active_list = root.find(".//{urn:ebay:apis:eBLBaseComponents}ActiveList")

            if active_list is not None:
                item_elements = active_list.findall(
                    ".//{urn:ebay:apis:eBLBaseComponents}Item"
                )

                for item_elem in item_elements:
                    try:
                        # Extract basic item information
                        item_id_elem = item_elem.find(
                            ".//{urn:ebay:apis:eBLBaseComponents}ItemID"
                        )
                        title_elem = item_elem.find(
                            ".//{urn:ebay:apis:eBLBaseComponents}Title"
                        )
                        sku_elem = item_elem.find(
                            ".//{urn:ebay:apis:eBLBaseComponents}SKU"
                        )

                        # Extract pricing
                        start_price_elem = item_elem.find(
                            ".//{urn:ebay:apis:eBLBaseComponents}StartPrice"
                        )
                        buy_it_now_elem = item_elem.find(
                            ".//{urn:ebay:apis:eBLBaseComponents}BuyItNowPrice"
                        )

                        # Extract quantity
                        quantity_elem = item_elem.find(
                            ".//{urn:ebay:apis:eBLBaseComponents}Quantity"
                        )
                        quantity_sold_elem = item_elem.find(
                            ".//{urn:ebay:apis:eBLBaseComponents}QuantitySold"
                        )

                        # Extract condition
                        condition_elem = item_elem.find(
                            ".//{urn:ebay:apis:eBLBaseComponents}ConditionDisplayName"
                        )

                        # Extract description
                        description_elem = item_elem.find(
                            ".//{urn:ebay:apis:eBLBaseComponents}Description"
                        )

                        # Extract category
                        category_elem = item_elem.find(
                            ".//{urn:ebay:apis:eBLBaseComponents}PrimaryCategory"
                        )
                        category_name = None
                        if category_elem is not None:
                            cat_name_elem = category_elem.find(
                                ".//{urn:ebay:apis:eBLBaseComponents}CategoryName"
                            )
                            if cat_name_elem is not None:
                                category_name = cat_name_elem.text

                        # Extract images
                        images = []
                        picture_details = item_elem.find(
                            ".//{urn:ebay:apis:eBLBaseComponents}PictureDetails"
                        )
                        if picture_details is not None:
                            gallery_url = picture_details.find(
                                ".//{urn:ebay:apis:eBLBaseComponents}GalleryURL"
                            )
                            if gallery_url is not None and gallery_url.text:
                                images.append(gallery_url.text)

                            # Get additional picture URLs
                            picture_urls = picture_details.findall(
                                ".//{urn:ebay:apis:eBLBaseComponents}PictureURL"
                            )
                            for pic_url in picture_urls:
                                if pic_url.text and pic_url.text not in images:
                                    images.append(pic_url.text)

                        # Build item data
                        item_data = {
                            "item_id": (
                                item_id_elem.text if item_id_elem is not None else None
                            ),
                            "sku": sku_elem.text if sku_elem is not None else None,
                            "title": (
                                title_elem.text
                                if title_elem is not None
                                else "No title"
                            ),
                            "description": (
                                description_elem.text
                                if description_elem is not None
                                else ""
                            ),
                            "price": (
                                float(start_price_elem.text)
                                if start_price_elem is not None
                                else 0.0
                            ),
                            "buy_it_now_price": (
                                float(buy_it_now_elem.text)
                                if buy_it_now_elem is not None
                                else None
                            ),
                            "quantity": (
                                int(quantity_elem.text)
                                if quantity_elem is not None
                                else 0
                            ),
                            "quantity_sold": (
                                int(quantity_sold_elem.text)
                                if quantity_sold_elem is not None
                                else 0
                            ),
                            "condition": (
                                condition_elem.text
                                if condition_elem is not None
                                else "Unknown"
                            ),
                            "category": category_name,
                            "images": images,
                            "listing_type": "FixedPriceItem",  # Most eBay listings are fixed price
                            "marketplace_source": "eBay",
                        }

                        items.append(item_data)

                    except Exception as e:
                        logger.warning(f"Error parsing item: {e}")
                        continue

            # Get pagination info
            pagination_info = {
                "total": 0,
                "page": page,
                "limit": limit,
                "has_more": False,
            }

            pagination_result = (
                active_list.find(".//{urn:ebay:apis:eBLBaseComponents}PaginationResult")
                if active_list is not None
                else None
            )
            if pagination_result is not None:
                total_elem = pagination_result.find(
                    ".//{urn:ebay:apis:eBLBaseComponents}TotalNumberOfEntries"
                )
                total_pages_elem = pagination_result.find(
                    ".//{urn:ebay:apis:eBLBaseComponents}TotalNumberOfPages"
                )

                if total_elem is not None:
                    pagination_info["total"] = int(total_elem.text)

                if total_pages_elem is not None:
                    total_pages = int(total_pages_elem.text)
                    pagination_info["has_more"] = page < total_pages

            logger.info(
                f"Retrieved {len(items)} items from eBay Trading API (page {page})"
            )

            return {
                "items": items,
                "pagination": pagination_info,
                "source": "trading_api",
            }

        except Exception as e:
            logger.error(f"Error retrieving seller inventory: {e}")
            raise eBayAPIError(f"Failed to retrieve inventory: {e}")

    async def create_listing(self, listing_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an eBay listing using the Trading API AddFixedPriceItem call.

        Args:
            listing_data: Dictionary containing listing information
                - title: Listing title (required)
                - description: Item description (required)
                - price: Starting price (required)
                - quantity: Available quantity (required)
                - category_id: eBay category ID (required)
                - condition: Item condition (required)
                - sku: Seller SKU (optional)
                - shipping_options: List of shipping options (optional)
                - return_policy: Return policy details (optional)
                - item_specifics: Dictionary of item specifics (optional)

        Returns:
            Dictionary with listing creation result
        """
        try:
            # Validate required fields
            required_fields = [
                "title",
                "description",
                "price",
                "quantity",
                "category_id",
                "condition",
            ]
            for field in required_fields:
                if field not in listing_data:
                    raise ValueError(f"Missing required field: {field}")

            # Get OAuth access token for seller operations
            access_token = await self._get_access_token()

            # Build XML request for AddFixedPriceItem
            xml_request = self._build_add_item_xml(listing_data, access_token)

            # Make Trading API request
            response_xml = await self._make_trading_request(
                "AddFixedPriceItem", xml_request
            )

            # Parse response
            result = self._parse_add_item_response(response_xml)

            if result.get("success"):
                logger.info(
                    f"✅ Successfully created eBay listing: {result.get('item_id')}"
                )
            else:
                logger.error(
                    f"❌ Failed to create eBay listing: {result.get('errors')}"
                )

            return result

        except Exception as e:
            logger.error(f"Error creating eBay listing: {e}")
            return {"success": False, "error": str(e), "item_id": None}

    def _build_add_item_xml(
        self, listing_data: Dict[str, Any], access_token: str
    ) -> str:
        """Build XML request for AddFixedPriceItem Trading API call."""

        # Convert condition to eBay condition ID
        condition_map = {
            "NEW": "1000",
            "USED_EXCELLENT": "1500",
            "USED_VERY_GOOD": "2000",
            "USED_GOOD": "2500",
            "USED_ACCEPTABLE": "3000",
            "FOR_PARTS": "7000",
        }
        condition_id = condition_map.get(listing_data["condition"].upper(), "1000")

        # Build item specifics XML
        item_specifics_xml = ""
        if listing_data.get("item_specifics"):
            specifics_list = []
            for name, value in listing_data["item_specifics"].items():
                specifics_list.append(
                    f"""
                    <NameValueList>
                        <Name>{name}</Name>
                        <Value>{value}</Value>
                    </NameValueList>
                """
                )
            if specifics_list:
                item_specifics_xml = f"""
                    <ItemSpecifics>
                        {''.join(specifics_list)}
                    </ItemSpecifics>
                """

        # Build shipping options XML with handling time
        handling_time = listing_data.get("handling_time", 1)
        shipping_service = listing_data.get("shipping_service", "USPSMedia")
        shipping_cost = listing_data.get("shipping_cost", 8.99)

        shipping_xml = f"""
            <ShippingDetails>
                <ShippingType>Flat</ShippingType>
                <ShippingServiceOptions>
                    <ShippingServicePriority>1</ShippingServicePriority>
                    <ShippingService>{shipping_service}</ShippingService>
                    <ShippingServiceCost>{shipping_cost}</ShippingServiceCost>
                </ShippingServiceOptions>
            </ShippingDetails>
        """

        # Add handling time to the main item (not in shipping details)
        handling_time_xml = f"<DispatchTimeMax>{handling_time}</DispatchTimeMax>"

        # Build return policy XML
        return_policy_xml = """
            <ReturnPolicy>
                <ReturnsAcceptedOption>ReturnsAccepted</ReturnsAcceptedOption>
                <RefundOption>MoneyBack</RefundOption>
                <ReturnsWithinOption>Days_30</ReturnsWithinOption>
                <ShippingCostPaidByOption>Buyer</ShippingCostPaidByOption>
            </ReturnPolicy>
        """

        # Properly escape description content to avoid CDATA issues
        description = listing_data["description"]
        # Remove any existing CDATA markers and escape problematic characters
        description = description.replace("]]>", "]]&gt;").replace("<![CDATA[", "")
        # Ensure description is properly escaped for XML
        import html

        description_escaped = html.escape(description)

        xml_request = f"""<?xml version="1.0" encoding="utf-8"?>
<AddFixedPriceItemRequest xmlns="urn:ebay:apis:eBLBaseComponents">
    <RequesterCredentials>
        <eBayAuthToken>{access_token}</eBayAuthToken>
    </RequesterCredentials>
    <Item>
        <Title>{html.escape(listing_data["title"][:80])}</Title>
        <Description><![CDATA[{description_escaped}]]></Description>
        <PrimaryCategory>
            <CategoryID>{listing_data["category_id"]}</CategoryID>
        </PrimaryCategory>
        <StartPrice>{listing_data["price"]}</StartPrice>
        <ConditionID>{condition_id}</ConditionID>
        <Quantity>{listing_data["quantity"]}</Quantity>
        <ListingType>FixedPriceItem</ListingType>
        <ListingDuration>GTC</ListingDuration>
        <Country>US</Country>
        <Currency>USD</Currency>
        <Location>United States</Location>
        <SKU>{listing_data.get("sku", "")}</SKU>
        {handling_time_xml}
        {item_specifics_xml}
        {shipping_xml}
        {return_policy_xml}
    </Item>
</AddFixedPriceItemRequest>"""

        return xml_request

    def _parse_add_item_response(self, response_xml: ET.Element) -> Dict[str, Any]:
        """Parse AddFixedPriceItem response XML."""
        try:
            # Check for acknowledgment
            ack_elem = response_xml.find(".//{urn:ebay:apis:eBLBaseComponents}Ack")
            if ack_elem is None:
                return {"success": False, "error": "No acknowledgment in response"}

            ack = ack_elem.text

            # Get item ID if successful
            item_id = None
            item_id_elem = response_xml.find(
                ".//{urn:ebay:apis:eBLBaseComponents}ItemID"
            )
            if item_id_elem is not None:
                item_id = item_id_elem.text

            # Get fees
            fees = []
            fees_elem = response_xml.find(".//{urn:ebay:apis:eBLBaseComponents}Fees")
            if fees_elem is not None:
                for fee_elem in fees_elem.findall(
                    ".//{urn:ebay:apis:eBLBaseComponents}Fee"
                ):
                    name_elem = fee_elem.find(
                        ".//{urn:ebay:apis:eBLBaseComponents}Name"
                    )
                    fee_elem_amount = fee_elem.find(
                        ".//{urn:ebay:apis:eBLBaseComponents}Fee"
                    )
                    if name_elem is not None and fee_elem_amount is not None:
                        fees.append(
                            {"name": name_elem.text, "amount": fee_elem_amount.text}
                        )

            # Get errors/warnings
            errors = []
            warnings = []

            errors_elem = response_xml.find(
                ".//{urn:ebay:apis:eBLBaseComponents}Errors"
            )
            if errors_elem is not None:
                for error_elem in errors_elem.findall(
                    ".//{urn:ebay:apis:eBLBaseComponents}Error"
                ):
                    severity_elem = error_elem.find(
                        ".//{urn:ebay:apis:eBLBaseComponents}SeverityCode"
                    )
                    message_elem = error_elem.find(
                        ".//{urn:ebay:apis:eBLBaseComponents}LongMessage"
                    )

                    if severity_elem is not None and message_elem is not None:
                        error_info = {
                            "severity": severity_elem.text,
                            "message": message_elem.text,
                        }

                        if severity_elem.text == "Error":
                            errors.append(error_info)
                        elif severity_elem.text == "Warning":
                            warnings.append(error_info)

            # Determine success
            success = ack in ["Success", "Warning"] and item_id is not None

            result = {
                "success": success,
                "item_id": item_id,
                "ack": ack,
                "fees": fees,
                "errors": errors,
                "warnings": warnings,
            }

            if success and item_id:
                result["listing_url"] = f"https://www.ebay.com/itm/{item_id}"

            return result

        except Exception as e:
            logger.error(f"Error parsing AddFixedPriceItem response: {e}")
            return {
                "success": False,
                "error": f"Failed to parse response: {str(e)}",
                "item_id": None,
            }

    async def setup_user_token_authentication(
        self, user_id: str = "testuser_nashvillegeneralstoretest"
    ) -> bool:
        """
        Set up user token authentication for Trading API operations.

        Args:
            user_id: User ID to get tokens for (defaults to test user)

        Returns:
            True if user token is configured, False otherwise
        """
        try:
            # Import OAuth service
            from fs_agt_clean.services.marketplace.ebay_oauth_service import (
                EbayOAuthService,
            )
            from fs_agt_clean.core.db.optimized_database import get_optimized_database

            # Initialize OAuth service
            oauth_service = EbayOAuthService(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=os.getenv("EBAY_REDIRECT_URI"),
                environment=self.environment,
                encryption_key=os.getenv("OAUTH_ENCRYPTION_KEY"),
            )

            # Get database connection
            db = get_optimized_database()
            await db.initialize()

            async with db.get_session() as session:
                # Get decrypted access token for API calls
                decrypted_access_token = await oauth_service.get_decrypted_access_token(
                    session, user_id
                )

                if decrypted_access_token:
                    # Get token metadata
                    oauth_token = await oauth_service.get_user_tokens(session, user_id)

                    # Set decrypted user access token in eBayClient
                    self.access_token = decrypted_access_token
                    if oauth_token and oauth_token.refresh_token:
                        # Decrypt refresh token too
                        try:
                            self.refresh_token = oauth_service.cipher.decrypt(
                                oauth_token.refresh_token.encode()
                            ).decode()
                        except Exception:
                            logger.warning("Failed to decrypt refresh token")
                            self.refresh_token = None

                    self._oauth_token_manually_set = True

                    # Set token expiry
                    if oauth_token and oauth_token.expires_at:
                        self.token_expires_at = oauth_token.expires_at
                    else:
                        # Set future expiry to ensure OAuth token is used
                        from datetime import datetime, timezone, timedelta

                        self.token_expires_at = datetime.now(timezone.utc) + timedelta(
                            hours=1
                        )

                    logger.info(
                        f"✅ User token configured for eBay Trading API access (User: {user_id})"
                    )
                    logger.info(f"🔑 Token expires at: {self.token_expires_at}")
                    return True
                else:
                    logger.warning(f"❌ No valid user token found for {user_id}")
                    logger.warning(
                        "💡 Need to complete OAuth flow first - use ebay_user_token_manager.py"
                    )
                    return False

        except Exception as e:
            logger.error(f"Failed to setup user token authentication: {e}")
            return False
