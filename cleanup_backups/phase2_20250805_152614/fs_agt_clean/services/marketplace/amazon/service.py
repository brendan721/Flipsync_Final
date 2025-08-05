import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp
from prometheus_client import Counter, Histogram

from fs_agt_clean.core.api_client import APIClient
from fs_agt_clean.core.exceptions import AuthenticationError, MarketplaceError
from fs_agt_clean.services.metrics.service import MetricsService
from fs_agt_clean.services.notifications.service import NotificationService

logger = logging.getLogger(__name__)

SP_API_REQUEST_COUNT = Counter(
    "sp_api_requests_total", "Total SP-API requests", ["endpoint"]
)
SP_API_REQUEST_DURATION = Histogram(
    "sp_api_request_duration_seconds", "SP-API request duration"
)
SP_API_ERROR_COUNT = Counter(
    "sp_api_errors_total", "Total SP-API errors", ["error_type"]
)


class AmazonService(APIClient):
    """Service for interacting with Amazon SP-API with real credentials."""

    def __init__(
        self,
        metrics_service: Optional[MetricsService] = None,
        notification_service: Optional[NotificationService] = None,
        sp_api_config: Optional[Dict] = None,
    ):
        # Load credentials from environment or config
        self.client_id = os.getenv("LWA_APP_ID")
        self.client_secret = os.getenv("LWA_CLIENT_SECRET")
        self.refresh_token = os.getenv("SP_API_REFRESH_TOKEN")
        self.marketplace_id = os.getenv("MARKETPLACE_ID", "ATVPDKIKX0DER")
        self.region = "NA"  # Default to North America

        # Validate credentials
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            missing = []
            if not self.client_id:
                missing.append("LWA_APP_ID")
            if not self.client_secret:
                missing.append("LWA_CLIENT_SECRET")
            if not self.refresh_token:
                missing.append("SP_API_REFRESH_TOKEN")
            raise ValueError(f"Missing Amazon SP-API credentials: {', '.join(missing)}")

        # Set base URL based on region
        base_url = self._get_endpoint_for_region(self.region)
        super().__init__(base_url)

        self.metrics_service = metrics_service
        self.notification_service = notification_service
        self.config = sp_api_config or {}

        # Token management
        self.access_token = None
        self.token_expiry = None

        # Rate limiting semaphores
        self._request_semaphores = {
            "catalog": asyncio.Semaphore(5),
            "inventory": asyncio.Semaphore(2),
            "pricing": asyncio.Semaphore(1),
            "orders": asyncio.Semaphore(3),
            "listings": asyncio.Semaphore(2),
        }

        # Service metrics
        self.service_metrics = {
            "api_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "token_refreshes": 0,
            "last_call_time": None,
            "last_error": None,
        }

        logger.info(
            f"Amazon SP-API service initialized for marketplace {self.marketplace_id}"
        )

    def _get_endpoint_for_region(self, region: str) -> str:
        """Get the SP-API endpoint for the specified region."""
        region_endpoints = {
            "NA": "https://sellingpartnerapi-na.amazon.com",
            "EU": "https://sellingpartnerapi-eu.amazon.com",
            "FE": "https://sellingpartnerapi-fe.amazon.com",
            "SANDBOX": "https://sandbox.sellingpartnerapi-na.amazon.com",
        }
        return region_endpoints.get(region, region_endpoints["NA"])

    async def _get_access_token(self) -> str:
        """Get or refresh the SP-API access token."""
        # Check if current token is still valid
        if (
            self.access_token
            and self.token_expiry
            and datetime.now() < self.token_expiry
        ):
            return self.access_token

        # Request new token
        logger.info("Requesting new SP-API access token")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.amazon.com/auth/o2/token",
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": self.refresh_token,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    },
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Failed to get SP-API access token: {error_text}")
                        self.service_metrics["failed_calls"] += 1
                        self.service_metrics["last_error"] = (
                            f"Token refresh failed: {error_text}"
                        )
                        raise AuthenticationError(
                            f"SP-API auth failed with status {response.status}: {error_text}",
                            marketplace="amazon",
                            status_code=response.status,
                        )

                    data = await response.json()
                    self.access_token = data["access_token"]
                    # Token expires in 1 hour, set to 50 minutes to be safe
                    self.token_expiry = datetime.now() + timedelta(minutes=50)

                    self.service_metrics["token_refreshes"] += 1
                    logger.info("SP-API access token refreshed successfully")
                    return self.access_token
        except Exception as e:
            self.service_metrics["failed_calls"] += 1
            self.service_metrics["last_error"] = str(e)
            raise

    async def _execute_sp_api(
        self,
        endpoint: str,
        method: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        max_retries: int = 3,
    ) -> Dict:
        """Execute SP-API request with authentication, rate limiting and retry logic."""
        # Update metrics
        self.service_metrics["api_calls"] += 1
        self.service_metrics["last_call_time"] = datetime.now()

        # Get semaphore for rate limiting
        endpoint_category = endpoint.split("/")[1] if "/" in endpoint else "default"
        semaphore = self._request_semaphores.get(
            endpoint_category, self._request_semaphores["catalog"]
        )

        SP_API_REQUEST_COUNT.labels(endpoint=endpoint).inc()

        try:
            # Get access token
            access_token = await self._get_access_token()

            # Set up headers for SP-API
            headers = {
                "x-amz-access-token": access_token,
                "Content-Type": "application/json",
                "UnifiedUser-UnifiedAgent": "FlipSync-AmazonService/1.0",
            }

            async with semaphore:
                url = f"{self.base_url}{endpoint}"

                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method=method,
                        url=url,
                        headers=headers,
                        params=params,
                        json=json_data,
                    ) as response:
                        response_text = await response.text()

                        if response.status >= 400:
                            logger.error(
                                f"SP-API request failed: {response.status} - {response_text}"
                            )
                            self.service_metrics["failed_calls"] += 1
                            self.service_metrics["last_error"] = (
                                f"API call failed: {response_text}"
                            )

                            SP_API_ERROR_COUNT.labels(
                                error_type=f"http_{response.status}"
                            ).inc()

                            # Retry on certain errors
                            if (
                                response.status in [429, 500, 502, 503, 504]
                                and max_retries > 0
                            ):
                                await asyncio.sleep(
                                    2 ** (3 - max_retries)
                                )  # Exponential backoff
                                return await self._execute_sp_api(
                                    endpoint=endpoint,
                                    method=method,
                                    params=params,
                                    json_data=json_data,
                                    max_retries=max_retries - 1,
                                )

                            raise MarketplaceError(
                                f"SP-API request failed: {response_text}",
                                marketplace="amazon",
                                status_code=response.status,
                            )

                        self.service_metrics["successful_calls"] += 1
                        try:
                            return json.loads(response_text)
                        except json.JSONDecodeError:
                            return {"raw_response": response_text}

        except Exception as e:
            SP_API_ERROR_COUNT.labels(error_type=type(e).__name__).inc()
            self.service_metrics["failed_calls"] += 1
            self.service_metrics["last_error"] = str(e)

            if max_retries > 0 and not isinstance(e, AuthenticationError):
                await asyncio.sleep(1)
                return await self._execute_sp_api(
                    endpoint=endpoint,
                    method=method,
                    params=params,
                    json_data=json_data,
                    max_retries=max_retries - 1,
                )
            raise

    async def get_orders(
        self,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        order_statuses: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get orders from Amazon SP-API."""
        params = {"MarketplaceIds": self.marketplace_id}

        if created_after:
            params["CreatedAfter"] = created_after
        if created_before:
            params["CreatedBefore"] = created_before
        if order_statuses:
            params["OrderStatuses"] = ",".join(order_statuses)

        return await self._execute_sp_api("/orders/v0/orders", "GET", params=params)

    async def get_inventory_summary(self, sku: Optional[str] = None) -> Dict[str, Any]:
        """Get inventory summary from FBA Inventory API."""
        params = {
            "granularityType": "Marketplace",
            "granularityId": self.marketplace_id,  # Fixed: use granularityId for FBA inventory
            "details": "true",
        }

        if sku:
            params["sellerSkus"] = sku

        return await self._execute_sp_api(
            "/fba/inventory/v1/summaries", "GET", params=params
        )

    async def get_product_catalog(
        self, asin: Optional[str] = None, keywords: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get product catalog information."""
        params = {
            "marketplaceIds": self.marketplace_id
        }  # Fixed: use marketplaceIds (plural)

        if asin:
            params["asin"] = asin
        if keywords:
            params["keywords"] = keywords

        return await self._execute_sp_api(
            "/catalog/2022-04-01/items", "GET", params=params
        )

    async def create_listing(
        self, sku: str, listing_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new product listing."""
        request_body = {
            "productType": listing_data.get("productType", "PRODUCT"),
            "requirements": listing_data.get("requirements", "LISTING"),
            "attributes": listing_data.get("attributes", {}),
        }

        return await self._execute_sp_api(
            f"/listings/2021-08-01/items/{sku}",
            "PUT",
            params={"marketplaceIds": self.marketplace_id},
            json_data=request_body,
        )

    async def get_listing(self, sku: str) -> Dict[str, Any]:
        """Get listing information for a SKU."""
        return await self._execute_sp_api(
            f"/listings/2021-08-01/items/{sku}",
            "GET",
            params={"marketplaceIds": self.marketplace_id},
        )

    async def update_listing(
        self, sku: str, listing_updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing product listing."""
        request_body = {
            "productType": listing_updates.get("productType", "PRODUCT"),
            "requirements": listing_updates.get("requirements", "LISTING"),
            "attributes": listing_updates.get("attributes", {}),
        }

        return await self._execute_sp_api(
            f"/listings/2021-08-01/items/{sku}",
            "PATCH",
            params={"marketplaceIds": self.marketplace_id},
            json_data=request_body,
        )

    async def delete_listing(self, sku: str) -> Dict[str, Any]:
        """Delete/end a product listing."""
        return await self._execute_sp_api(
            f"/listings/2021-08-01/items/{sku}",
            "DELETE",
            params={"marketplaceIds": self.marketplace_id},
        )

    async def get_listing_status(self, sku: str) -> Dict[str, Any]:
        """Get the status of a listing."""
        response = await self.get_listing(sku)

        # Extract status information from the listing response
        if response.get("summaries"):
            summary = response["summaries"][0]
            return {
                "sku": sku,
                "status": summary.get("status", "UNKNOWN"),
                "condition": summary.get("condition", "NEW"),
                "fulfillment_availability": summary.get("fulfillmentAvailability", {}),
                "last_updated": datetime.now().isoformat(),
            }

        return {
            "sku": sku,
            "status": "NOT_FOUND",
            "last_updated": datetime.now().isoformat(),
        }

    # FBA Integration Workflows
    async def create_fba_shipment(
        self, shipment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new FBA inbound shipment."""
        request_body = {
            "InboundShipmentHeader": {
                "ShipmentName": shipment_data.get("shipment_name"),
                "ShipFromAddress": shipment_data.get("ship_from_address"),
                "DestinationFulfillmentCenterId": shipment_data.get(
                    "destination_fc_id"
                ),
                "LabelPrepPreference": shipment_data.get(
                    "label_prep_preference", "SELLER_LABEL"
                ),
                "ShipmentStatus": "WORKING",
            }
        }

        return await self._execute_sp_api(
            "/fba/inbound/v0/shipments",
            "POST",
            json_data=request_body,
        )

    async def update_fba_inventory(
        self, sku: str, quantity: int, fulfillment_center_id: str = None
    ) -> Dict[str, Any]:
        """Update FBA inventory quantity."""
        request_body = {
            "InventoryAdjustments": [
                {
                    "SellerSKU": sku,
                    "Quantity": quantity,
                    "AdjustmentType": "SET",
                }
            ]
        }

        if fulfillment_center_id:
            request_body["InventoryAdjustments"][0][
                "FulfillmentCenterId"
            ] = fulfillment_center_id

        return await self._execute_sp_api(
            "/fba/inventory/v1/adjustments",
            "POST",
            json_data=request_body,
        )

    async def get_fba_fees(self, asin: str, price: float) -> Dict[str, Any]:
        """Get FBA fees for a product."""
        request_body = {
            "FeesEstimateRequest": {
                "MarketplaceId": self.marketplace_id,
                "IdType": "ASIN",
                "IdValue": asin,
                "IsAmazonFulfilled": True,
                "PriceToEstimateFees": {
                    "ListingPrice": {"CurrencyCode": "USD", "Amount": price},
                },
            }
        }

        return await self._execute_sp_api(
            "/products/fees/v0/feesEstimate",
            "POST",
            json_data=request_body,
        )

    async def get_fba_shipment_status(self, shipment_id: str) -> Dict[str, Any]:
        """Get the status of an FBA shipment."""
        return await self._execute_sp_api(
            f"/fba/inbound/v0/shipments/{shipment_id}",
            "GET",
        )

    # Enhanced Order Management System
    async def get_order_details(self, order_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific order."""
        return await self._execute_sp_api(
            f"/orders/v0/orders/{order_id}",
            "GET",
        )

    async def get_order_items(self, order_id: str) -> Dict[str, Any]:
        """Get items for a specific order."""
        return await self._execute_sp_api(
            f"/orders/v0/orders/{order_id}/orderItems",
            "GET",
        )

    async def confirm_shipment(
        self, order_id: str, shipment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Confirm shipment for an order."""
        request_body = {
            "packageDetail": {
                "packageReferenceId": shipment_data.get("package_reference_id"),
                "carrierCode": shipment_data.get("carrier_code"),
                "trackingNumber": shipment_data.get("tracking_number"),
                "shipDate": shipment_data.get("ship_date"),
            }
        }

        return await self._execute_sp_api(
            f"/orders/v0/orders/{order_id}/shipment",
            "POST",
            json_data=request_body,
        )

    async def update_order_status(
        self, order_id: str, status: str, notes: str = None
    ) -> Dict[str, Any]:
        """Update order status and add notes."""
        request_body = {
            "orderStatus": status,
        }

        if notes:
            request_body["statusChangeNote"] = notes

        return await self._execute_sp_api(
            f"/orders/v0/orders/{order_id}/status",
            "PATCH",
            json_data=request_body,
        )

    # Real-time Inventory Synchronization
    async def sync_inventory_levels(
        self, inventory_updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Synchronize inventory levels across multiple SKUs."""
        results = []

        for update in inventory_updates:
            sku = update.get("sku")
            quantity = update.get("quantity")

            try:
                result = await self.update_fba_inventory(sku, quantity)
                results.append(
                    {
                        "sku": sku,
                        "success": True,
                        "result": result,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "sku": sku,
                        "success": False,
                        "error": str(e),
                    }
                )

        return {
            "total_updates": len(inventory_updates),
            "successful_updates": len([r for r in results if r["success"]]),
            "failed_updates": len([r for r in results if not r["success"]]),
            "results": results,
        }

    async def get_inventory_alerts(self, threshold: int = 10) -> Dict[str, Any]:
        """Get inventory items below threshold for reorder alerts."""
        inventory_data = await self.get_inventory_summary()

        low_stock_items = []
        if inventory_data.get("payload", {}).get("inventorySummaries"):
            for item in inventory_data["payload"]["inventorySummaries"]:
                total_quantity = item.get("totalQuantity", 0)
                if total_quantity <= threshold:
                    low_stock_items.append(
                        {
                            "sku": item.get("sellerSku"),
                            "asin": item.get("asin"),
                            "current_quantity": total_quantity,
                            "threshold": threshold,
                            "fulfillment_type": item.get("fulfillmentType"),
                        }
                    )

        return {
            "low_stock_count": len(low_stock_items),
            "threshold": threshold,
            "items": low_stock_items,
            "last_checked": datetime.now().isoformat(),
        }

    async def get_product_data(self, asin: str) -> Dict:
        """Get comprehensive product data from SP-API."""
        try:
            # Get product catalog data
            product_data = await self.get_product_catalog(asin=asin)

            # Try to get inventory data (may not be available for all products)
            inventory_data = {}
            try:
                inventory_data = await self.get_inventory_summary()
            except Exception as e:
                logger.warning(f"Could not get inventory data for {asin}: {e}")

            return self._combine_product_data(
                asin=asin,
                product_data=product_data,
                inventory_data=inventory_data,
            )
        except Exception as e:
            logger.error(f"Error getting product data for {asin}: {e}")
            raise

    async def test_connection(self) -> Dict[str, Any]:
        """Test the connection to Amazon SP-API."""
        try:
            # Simple test - just verify we can get an access token
            access_token = await self._get_access_token()

            if access_token:
                return {
                    "success": True,
                    "message": "Successfully authenticated with Amazon SP-API",
                    "data": {
                        "token_obtained": True,
                        "marketplace_id": self.marketplace_id,
                        "region": self.region,
                    },
                    "metrics": self.service_metrics,
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to obtain access token",
                    "metrics": self.service_metrics,
                }
        except Exception as e:
            logger.error(f"Amazon SP-API connection test failed: {e}")
            return {
                "success": False,
                "message": f"Connection test failed: {str(e)}",
                "error": str(e),
                "metrics": self.service_metrics,
            }

    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics."""
        return self.service_metrics.copy()

    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the Amazon service."""
        try:
            # Quick health check - just verify token can be obtained
            await self._get_access_token()

            success_rate = 0.0
            if self.service_metrics["api_calls"] > 0:
                success_rate = (
                    self.service_metrics["successful_calls"]
                    / self.service_metrics["api_calls"]
                )

            status = "healthy"
            if success_rate < 0.8:
                status = "degraded"
            elif success_rate < 0.5:
                status = "unhealthy"

            return {
                "status": status,
                "success_rate": success_rate,
                "metrics": self.service_metrics,
                "last_check": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "metrics": self.service_metrics,
                "last_check": datetime.now().isoformat(),
            }

    def _combine_product_data(
        self,
        asin: str,
        product_data: Dict,
        inventory_data: Dict,
    ) -> Dict:
        """Combine various product data into a unified structure."""
        # Extract data from SP-API response structure
        items = product_data.get("payload", {}).get("items", [])
        item_data = items[0] if items else {}

        # Extract inventory data
        inventory_summaries = inventory_data.get("payload", {}).get(
            "inventorySummaries", []
        )
        inventory_summary = inventory_summaries[0] if inventory_summaries else {}

        return {
            "asin": asin,
            "title": item_data.get("summaries", [{}])[0].get("itemName", ""),
            "brand": item_data.get("attributes", {})
            .get("brand", [{}])[0]
            .get("value", ""),
            "category": item_data.get("summaries", [{}])[0]
            .get("browseClassification", {})
            .get("displayName", "Unknown"),
            "description": item_data.get("attributes", {})
            .get("item_description", [{}])[0]
            .get("value", ""),
            "features": item_data.get("attributes", {}).get("bullet_point", []),
            "images": [img.get("link") for img in item_data.get("images", [])],
            "pricing": {
                "currency": "USD",
                "last_updated": datetime.now(),
            },
            "inventory": {
                "quantity": inventory_summary.get("totalQuantity", 0),
                "condition": inventory_summary.get("condition", "New"),
                "fulfillment_type": inventory_summary.get("fulfillmentType", "FBA"),
                "last_updated": datetime.now(),
            },
            "metrics": {
                "sales_rank": item_data.get("salesRanks", [{}])[0].get("rank"),
                "category": item_data.get("summaries", [{}])[0]
                .get("browseClassification", {})
                .get("displayName"),
                "last_updated": datetime.now(),
            },
        }

    async def record_pipeline_error(self, stage: str, error: Exception):
        """Record pipeline error metrics."""
        if self.metrics_service:
            await self.metrics_service.record_metric(
                name="pipeline_error",
                value=1.0,
                labels={"stage": stage, "error_type": type(error).__name__},
            )

    async def record_pipeline_stage_complete(self, stage: str):
        """Record pipeline stage completion metrics."""
        if self.metrics_service:
            await self.metrics_service.record_metric(
                name="pipeline_stage_complete",
                value=1.0,
                labels={"stage": stage},
            )

    async def record_pipeline_complete(self):
        """Record pipeline completion metrics."""
        if self.metrics_service:
            await self.metrics_service.record_metric(
                name="pipeline_complete",
                value=1.0,
                labels={"status": "success"},
            )
