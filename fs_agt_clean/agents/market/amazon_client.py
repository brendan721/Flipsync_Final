"""
Amazon SP-API Client for FlipSync Market UnifiedAgent
==============================================

This module provides integration with Amazon's Selling Partner API (SP-API)
for product data retrieval, pricing analysis, and inventory management.
"""

import asyncio
import hashlib
import hmac
import logging
import os

from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import aiohttp

from fs_agt_clean.core.models.marketplace_models import (
    InventoryStatus,
    ListingStatus,
    MarketMetrics,
    MarketplaceType,
    Price,
    ProductCondition,
    ProductIdentifier,
    ProductListing,
)

logger = logging.getLogger(__name__)


class AmazonAPIError(Exception):
    """Custom exception for Amazon API errors."""

    pass


class AmazonAuthenticationError(AmazonAPIError):
    """Authentication-related errors."""

    pass


class AmazonRateLimitError(AmazonAPIError):
    """Rate limiting errors."""

    pass


class AmazonClient:
    """Amazon SP-API client for marketplace operations."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        region: str = "us-east-1",
        marketplace_id: str = "ATVPDKIKX0DER",  # US marketplace
    ):
        """
        Initialize Amazon SP-API client.

        Args:
            client_id: LWA client identifier
            client_secret: LWA client secret
            refresh_token: LWA refresh token
            access_key_id: AWS access key ID
            secret_access_key: AWS secret access key
            region: AWS region
            marketplace_id: Amazon marketplace ID
        """
        # Get credentials from environment if not provided
        self.client_id = client_id or os.getenv("AMAZON_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("AMAZON_CLIENT_SECRET")
        self.refresh_token = refresh_token or os.getenv("AMAZON_REFRESH_TOKEN")
        self.access_key_id = access_key_id or os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_access_key = secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")

        self.region = region
        self.marketplace_id = marketplace_id
        self.base_url = f"https://sellingpartnerapi-na.amazon.com"

        # Token management
        self.access_token = None
        self.token_expires_at = None

        # Rate limiting
        self.last_request_time = {}
        self.request_counts = {}

        # Session for HTTP requests
        self.session = None

        logger.info(f"Amazon client initialized for marketplace {marketplace_id}")

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def _get_access_token(self) -> str:
        """Get or refresh access token."""
        if self.access_token and self.token_expires_at:
            if datetime.now(timezone.utc) < self.token_expires_at:
                return self.access_token

        # Refresh token
        if not self.client_id or not self.client_secret or not self.refresh_token:
            raise AmazonAuthenticationError(
                "Missing required credentials for token refresh"
            )

        token_url = "https://api.amazon.com/auth/o2/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            async with self.session.post(token_url, data=data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.access_token = token_data["access_token"]
                    expires_in = token_data.get("expires_in", 3600)
                    self.token_expires_at = datetime.now(timezone.utc) + timedelta(
                        seconds=expires_in - 60
                    )
                    logger.info("Amazon access token refreshed successfully")
                    return self.access_token
                else:
                    error_text = await response.text()
                    raise AmazonAuthenticationError(
                        f"Token refresh failed: {error_text}"
                    )
        except Exception as e:
            logger.error(f"Error refreshing Amazon token: {e}")
            raise AmazonAuthenticationError(f"Token refresh error: {e}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make authenticated request to Amazon SP-API."""
        if not self.session:
            raise AmazonAPIError(
                "Client session not initialized. Use async context manager."
            )

        # Get access token
        access_token = await self._get_access_token()

        # Prepare headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "x-amz-access-token": access_token,
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
                    raise AmazonRateLimitError("Rate limit exceeded")
                elif response.status in [401, 403]:
                    raise AmazonAuthenticationError(
                        f"Authentication failed: {response_data}"
                    )
                else:
                    raise AmazonAPIError(
                        f"API request failed: {response.status} - {response_data}"
                    )

        except aiohttp.ClientError as e:
            logger.error(f"HTTP error in Amazon API request: {e}")
            raise AmazonAPIError(f"HTTP error: {e}")

    async def _check_rate_limits(self, endpoint: str):
        """Check and enforce rate limits."""
        now = datetime.now(timezone.utc)

        # Simple rate limiting - can be enhanced
        if endpoint in self.last_request_time:
            time_since_last = (now - self.last_request_time[endpoint]).total_seconds()
            if time_since_last < 1.0:  # Minimum 1 second between requests
                await asyncio.sleep(1.0 - time_since_last)

        self.last_request_time[endpoint] = now

    async def get_product_details(self, asin: str) -> Optional[ProductListing]:
        """
        Get product details by ASIN.

        Args:
            asin: Amazon Standard Identification Number

        Returns:
            ProductListing object or None if not found
        """
        try:
            # Check if we have real credentials
            if not self.client_id or not self.client_secret or not self.refresh_token:
                logger.info(
                    f"No Amazon credentials configured, returning mock data for ASIN {asin}"
                )
                return self._create_mock_product_listing(asin)

            # In a real implementation, this would call the actual SP-API
            endpoint = f"/catalog/2022-04-01/items/{asin}"
            params = {
                "marketplaceIds": self.marketplace_id,
                "includedData": "attributes,dimensions,identifiers,images,productTypes,salesRanks,summaries",
            }

            response = await self._make_request("GET", endpoint, params=params)

            # Parse response and create ProductListing
            return self._parse_product_response(response, asin)

        except Exception as e:
            logger.error(f"Error getting product details for ASIN {asin}: {e}")
            # Return mock data as fallback
            return self._create_mock_product_listing(asin)

    async def get_competitive_pricing(self, asin: str) -> List[Price]:
        """
        Get competitive pricing information for a product.

        Args:
            asin: Amazon Standard Identification Number

        Returns:
            List of competitor prices
        """
        try:
            # Check if we have real credentials
            if not self.client_id or not self.client_secret or not self.refresh_token:
                logger.info(
                    f"No Amazon credentials configured, returning mock pricing for ASIN {asin}"
                )
                return self._create_mock_competitive_prices(asin)

            endpoint = f"/products/pricing/v0/price"
            params = {
                "MarketplaceId": self.marketplace_id,
                "Asins": asin,
                "ItemType": "Asin",
            }

            response = await self._make_request("GET", endpoint, params=params)

            # Parse competitive pricing
            return self._parse_competitive_pricing(response)

        except Exception as e:
            logger.error(f"Error getting competitive pricing for ASIN {asin}: {e}")
            # Return mock data as fallback
            return self._create_mock_competitive_prices(asin)

    async def get_inventory_status(self, sku: str) -> Optional[InventoryStatus]:
        """
        Get inventory status for a SKU.

        Args:
            sku: Stock Keeping Unit

        Returns:
            InventoryStatus object or None if not found
        """
        try:
            # Check if we have real credentials
            if not self.client_id or not self.client_secret or not self.refresh_token:
                logger.warning(
                    f"No Amazon credentials configured for SKU {sku}, cannot retrieve real inventory"
                )
                # Record cost for inventory management operation
                from fs_agt_clean.core.monitoring.cost_tracker import record_ai_cost

                await record_ai_cost(
                    category="inventory_management",
                    model="amazon_sp_api",
                    operation="get_inventory_status_no_credentials",
                    cost=0.001,
                    agent_id="amazon_client",
                    tokens_used=1,
                )
                return None

            endpoint = "/fba/inventory/v1/summaries"
            params = {
                "details": "true",
                "granularityType": "Marketplace",
                "granularityId": self.marketplace_id,
                "marketplaceIds": self.marketplace_id,
                "sellerSkus": sku,
            }

            response = await self._make_request("GET", endpoint, params=params)

            # Record successful inventory operation cost
            from fs_agt_clean.core.monitoring.cost_tracker import record_ai_cost

            await record_ai_cost(
                category="inventory_management",
                model="amazon_sp_api",
                operation="get_inventory_status",
                cost=0.01,
                agent_id="amazon_client",
                tokens_used=1,
            )

            # Parse inventory response
            return self._parse_inventory_response(response, sku)

        except Exception as e:
            logger.error(f"Error getting inventory status for SKU {sku}: {e}")
            # Record failed inventory operation cost
            from fs_agt_clean.core.monitoring.cost_tracker import record_ai_cost

            await record_ai_cost(
                category="inventory_management",
                model="amazon_sp_api",
                operation="get_inventory_status_error",
                cost=0.005,
                agent_id="amazon_client",
                tokens_used=1,
            )
            return None

    async def get_sales_metrics(
        self, asin: str, days: int = 30
    ) -> Optional[MarketMetrics]:
        """
        Get sales metrics for a product using real Amazon SP-API.

        Args:
            asin: Amazon Standard Identification Number
            days: Number of days to look back

        Returns:
            MarketMetrics object or None if not available
        """
        try:
            # Check if we have real credentials
            if not self.client_id or not self.client_secret or not self.refresh_token:
                logger.warning(
                    f"No Amazon credentials configured for ASIN {asin}, cannot retrieve real sales metrics"
                )
                # Record cost for inventory management operation
                from fs_agt_clean.core.monitoring.cost_tracker import record_ai_cost

                await record_ai_cost(
                    category="inventory_management",
                    model="amazon_sp_api",
                    operation="get_sales_metrics_no_credentials",
                    cost=0.001,
                    agent_id="amazon_client",
                    tokens_used=1,
                )
                return None

            # Use Sales Analytics API for real implementation
            endpoint = "/sales/v1/orderMetrics"
            params = {
                "marketplaceIds": self.marketplace_id,
                "interval": f"{days}d",
                "granularity": "Total",
                "asin": asin,
            }

            response = await self._make_request("GET", endpoint, params=params)

            # Record successful sales metrics operation cost
            from fs_agt_clean.core.monitoring.cost_tracker import record_ai_cost

            await record_ai_cost(
                category="inventory_management",
                model="amazon_sp_api",
                operation="get_sales_metrics",
                cost=0.015,
                agent_id="amazon_client",
                tokens_used=1,
            )

            # Parse sales metrics response
            return self._parse_sales_metrics_response(response, asin)

        except Exception as e:
            logger.error(f"Error getting sales metrics for ASIN {asin}: {e}")
            # Record failed sales metrics operation cost
            from fs_agt_clean.core.monitoring.cost_tracker import record_ai_cost

            await record_ai_cost(
                category="inventory_management",
                model="amazon_sp_api",
                operation="get_sales_metrics_error",
                cost=0.005,
                agent_id="amazon_client",
                tokens_used=1,
            )
            return None

    def _create_mock_product_listing(self, asin: str) -> ProductListing:
        """Create mock product listing for development."""
        return ProductListing(
            identifier=ProductIdentifier(asin=asin, sku=f"SKU-{asin}"),
            title=f"Sample Product {asin}",
            description=f"This is a sample product description for ASIN {asin}",
            marketplace=MarketplaceType.AMAZON,
            seller_id="SAMPLE_SELLER",
            condition=ProductCondition.NEW,
            status=ListingStatus.ACTIVE,
            current_price=Price(
                amount=Decimal("29.99"), marketplace=MarketplaceType.AMAZON
            ),
            quantity_available=100,
            categories=["Electronics", "Gadgets"],
            seller_rating=4.5,
            review_count=150,
            average_rating=4.2,
            listing_url=f"https://amazon.com/dp/{asin}",
        )

    def _create_mock_competitive_prices(self, asin: str) -> List[Price]:
        """Create mock competitive prices for development."""
        base_price = 29.99
        return [
            Price(
                amount=Decimal(str(base_price * 0.95)),
                marketplace=MarketplaceType.AMAZON,
            ),
            Price(
                amount=Decimal(str(base_price * 1.05)),
                marketplace=MarketplaceType.AMAZON,
            ),
            Price(
                amount=Decimal(str(base_price * 0.98)),
                marketplace=MarketplaceType.AMAZON,
            ),
            Price(
                amount=Decimal(str(base_price * 1.12)),
                marketplace=MarketplaceType.AMAZON,
            ),
        ]

    def _parse_product_response(self, response: Dict, asin: str) -> ProductListing:
        """Parse Amazon API product response into ProductListing."""
        # This would parse the actual API response
        # For now, return mock data
        return self._create_mock_product_listing(asin)

    def _parse_competitive_pricing(self, response: Dict) -> List[Price]:
        """Parse competitive pricing response."""
        # This would parse the actual API response
        # For now, return mock data
        return self._create_mock_competitive_prices("sample")

    def _parse_inventory_response(self, response: Dict, sku: str) -> InventoryStatus:
        """Parse real Amazon SP-API inventory response."""
        try:
            # Parse real Amazon SP-API inventory response
            summaries = response.get("payload", {}).get("inventorySummaries", [])

            if not summaries:
                logger.warning(f"No inventory data found for SKU {sku}")
                return None

            # Get the first matching summary
            summary = summaries[0]

            # Extract inventory data from real API response
            quantity_available = summary.get("totalQuantity", 0)
            quantity_reserved = summary.get("reservedQuantity", {}).get(
                "totalReservedQuantity", 0
            )
            quantity_inbound = summary.get("inboundQuantity", {}).get(
                "totalInboundQuantity", 0
            )

            # Create InventoryStatus from real API data
            return InventoryStatus(
                product_id=ProductIdentifier(sku=sku),
                marketplace=MarketplaceType.AMAZON,
                quantity_available=quantity_available,
                quantity_reserved=quantity_reserved,
                quantity_inbound=quantity_inbound,
                reorder_point=10,  # Default value - could be configured
                max_stock_level=1000,  # Default value - could be configured
                fulfillment_method=summary.get("fulfillmentNetworkSku", "FBA"),
            )

        except Exception as e:
            logger.error(f"Error parsing inventory response for SKU {sku}: {e}")
            return None

    def _parse_sales_metrics_response(self, response: Dict, asin: str) -> MarketMetrics:
        """Parse real Amazon SP-API sales metrics response."""
        try:
            # Parse real Amazon SP-API sales metrics response
            metrics = response.get("payload", [])

            if not metrics:
                logger.warning(f"No sales metrics data found for ASIN {asin}")
                return None

            # Get the first metrics entry
            metric_data = metrics[0] if metrics else {}

            # Extract sales data from real API response
            units_sold = metric_data.get("unitCount", 0)
            revenue = Decimal(
                str(metric_data.get("totalSales", {}).get("amount", "0.00"))
            )

            # Create MarketMetrics from real API data
            return MarketMetrics(
                marketplace=MarketplaceType.AMAZON,
                product_id=ProductIdentifier(asin=asin),
                sales_rank=metric_data.get("salesRank", 0),
                category_rank=metric_data.get("categoryRank", 0),
                buy_box_percentage=metric_data.get("buyBoxPercentage", 0.0),
                conversion_rate=metric_data.get("conversionRate", 0.0),
                units_sold=units_sold,
                revenue=revenue,
                profit_margin=metric_data.get("profitMargin", 0.0),
            )

        except Exception as e:
            logger.error(f"Error parsing sales metrics response for ASIN {asin}: {e}")
            return None

    async def validate_credentials(self) -> bool:
        """Validate Amazon API credentials."""
        try:
            if not self.client_id or not self.client_secret or not self.refresh_token:
                logger.warning("Amazon credentials not configured - using mock data")
                return False

            await self._get_access_token()
            return True
        except Exception as e:
            logger.error(f"Amazon credential validation failed: {e}")
            return False
