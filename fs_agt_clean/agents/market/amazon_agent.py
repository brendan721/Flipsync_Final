"""
amazon_agent.py - Migrated Version

This is a migrated version of the original file.
The migration process was unable to generate valid code, so this is a fallback
that preserves the original functionality with improved documentation.
"""

"""Amazon market agent module for handling Amazon marketplace operations."""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, cast

from fs_agt_clean.agents.market.base_market_agent import (
    AlertManager,
    BaseMarketUnifiedAgent,
    BatteryOptimizer,
    ConfigManager,
)
from fs_agt_clean.core.exceptions import AuthenticationError
from fs_agt_clean.core.marketplace_client import MarketplaceAPIClient

logger = logging.getLogger(__name__)


class AmazonMarketUnifiedAgent(BaseMarketUnifiedAgent, MarketplaceAPIClient):
    """
    Specialized agent for Amazon marketplace operations.
    Handles product data retrieval and analysis through Selling Partner API.
    """

    def __init__(
        self,
        agent_id: str,
        config: Dict[str, Any],
        alert_manager: Optional[AlertManager] = None,
        battery_optimizer: Optional[BatteryOptimizer] = None,
    ):
        BaseMarketUnifiedAgent.__init__(
            self,
            agent_id,
            "amazon",
            cast(ConfigManager, config),
            cast(AlertManager, alert_manager),
            cast(BatteryOptimizer, battery_optimizer),
        )
        # Set the base URL for the appropriate region
        base_url = self._get_endpoint_for_region(config.get("region", "NA"))
        MarketplaceAPIClient.__init__(self, base_url=base_url, marketplace="amazon")

        self.metrics.update(
            {
                "products_fetched": 0,
                "data_points_analyzed": 0,
                "api_calls": 0,
                "token_refreshes": 0,
            }
        )

        # SP-API specific configuration
        self.client_id = config.get("client_id")
        self.client_secret = config.get("client_secret")
        self.refresh_token = config.get("refresh_token")
        self.marketplace_id = config.get("marketplace_id")
        self.region = config.get("region", "NA")

        # Access token cache
        self.access_token = None
        self.token_expiry = None

        # Create a directory for token caching if it doesn't exist
        self.token_cache_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "tokens",
        )
        os.makedirs(self.token_cache_dir, exist_ok=True)

    def _get_required_config_fields(self) -> List[str]:
        """Get required configuration fields"""
        return [
            "client_id",
            "client_secret",
            "refresh_token",
            "marketplace_id",
            "region",
        ]

    def _get_endpoint_for_region(self, region: str) -> str:
        """Get the SP-API endpoint for the specified region."""
        region_endpoints = {
            "NA": "https://sellingpartnerapi-na.amazon.com",
            "EU": "https://sellingpartnerapi-eu.amazon.com",
            "FE": "https://sellingpartnerapi-fe.amazon.com",
            "SANDBOX": "https://sandbox.sellingpartnerapi-na.amazon.com",
        }
        return region_endpoints.get(region, region_endpoints["NA"])

    async def _setup_marketplace_client(self) -> None:
        """Set up Amazon SP-API client. Now primarily handled by MarketplaceAPIClient.
        This method might still be needed for specific header setup or checks.
        """
        # The base MarketplaceAPIClient handles token injection via _get_access_token.
        # We might only need to set specific headers here if required beyond Authorization: Bearer.
        # SP-API uses a custom x-amz-access-token header, so we override default_headers.
        access_token = (
            await self._get_access_token()
        )  # Still need token for custom header
        self.default_headers = {
            "x-amz-access-token": access_token,
            "Content-Type": "application/json",
            "UnifiedUser-UnifiedAgent": f"FlipSync-AmazonUnifiedAgent/{self.agent_id}",
        }
        # No need to call super()._setup_marketplace_client() as it doesn't exist
        logger.info(f"Amazon SP-API client setup verified for region {self.region}")

    async def _cleanup_marketplace_client(self) -> None:
        """Clean up Amazon API client resources."""
        # Use the close method inherited from APIClient (via MarketplaceAPIClient)
        await self.close()

    async def _get_access_token(self, scope: Optional[str] = None) -> str:
        """
        Get the SP-API access token, refreshing if necessary.

        Returns:
            Access token string

        Raises:
            AuthenticationError: If unable to retrieve a token.
        """
        # Check if we have a valid token in memory
        if (
            self.access_token
            and self.token_expiry
            and datetime.now() < self.token_expiry
        ):
            return self.access_token

        # Check for a cached token on disk
        token_cache_path = os.path.join(
            self.token_cache_dir, f"{self.agent_id}_token.json"
        )
        if os.path.exists(token_cache_path):
            try:
                with open(token_cache_path, "r") as f:
                    token_data = json.load(f)
                    expiry = datetime.fromisoformat(token_data["expiry"])
                    if datetime.now() < expiry:
                        logger.info("Using cached SP-API access token")
                        self.access_token = token_data["access_token"]
                        self.token_expiry = expiry
                        return self.access_token
            except Exception as e:
                logger.warning(f"Error reading cached token: {e}")

        # No valid token found, request a new one
        logger.info("Requesting new SP-API access token")
        try:
            # *** Start of logic to be moved to utility ***
            import aiohttp

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
                        # Raise specific error
                        raise AuthenticationError(
                            f"SP-API auth failed with status {response.status}: {error_text}",
                            marketplace="amazon",
                            status_code=response.status,
                        )

                    data = await response.json()
                    # *** End of logic to be moved to utility ***

                    self.access_token = data["access_token"]
                    # Token usually expires in 1 hour, but we'll set it to 50 minutes to be safe
                    self.token_expiry = datetime.now() + timedelta(minutes=50)

                    # Cache the token
                    with open(token_cache_path, "w") as f:
                        json.dump(
                            {
                                "access_token": self.access_token,
                                "expiry": self.token_expiry.isoformat(),
                            },
                            f,
                        )

                    self.metrics["token_refreshes"] += 1
                    logger.info("SP-API access token refreshed and cached")
                    return self.access_token
        except AuthenticationError:  # Re-raise specific error
            raise
        except Exception as e:
            logger.error(f"Error obtaining SP-API access token: {e}")
            await self.alert_manager.send_alert(
                severity="error",
                message=f"Failed to obtain SP-API access token: {str(e)}",
                metadata={"agent_id": self.agent_id},
            )
            # Wrap generic exception
            raise AuthenticationError(
                f"Failed to obtain SP-API access token: {str(e)}",
                marketplace="amazon",
                original_error=e,
            ) from e

    async def _handle_listing_event(self, event: Dict[str, Any]) -> None:
        """Handle Amazon listing events"""
        event_subtype = event.get("subtype")
        if event_subtype == "product_update":
            await self._handle_product_update(event)
        elif event_subtype == "price_change":
            await self._handle_price_change(event)
        elif event_subtype == "inventory_update":
            await self._handle_inventory_update(event)
        else:
            logger.warning("Unknown Amazon event subtype: %s", event_subtype)
            self.metrics["unknown_events"] = self.metrics.get("unknown_events", 0) + 1
            await self.alert_manager.send_alert(
                severity="unknown_event",
                message=f"Received unknown Amazon event subtype: {event_subtype}",
                metadata={"event": event},
            )

    async def get_orders(
        self,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        last_updated_after: Optional[str] = None,
        last_updated_before: Optional[str] = None,
        order_statuses: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get orders from Amazon SP-API.
        Args:
            created_after: ISO 8601 timestamp string
            created_before: ISO 8601 timestamp string
            last_updated_after: ISO 8601 timestamp string
            last_updated_before: ISO 8601 timestamp string
            order_statuses: List of order statuses to filter by
        """
        params: Dict[str, Union[str, List[str]]] = {
            "MarketplaceIds": self.marketplace_id
        }
        if created_after:
            # Parameter is already a string
            params["CreatedAfter"] = created_after
        if created_before:
            params["CreatedBefore"] = created_before
        if last_updated_after:
            params["LastUpdatedAfter"] = last_updated_after
        if last_updated_before:
            params["LastUpdatedBefore"] = last_updated_before
        if order_statuses:
            params["OrderStatuses"] = ",".join(order_statuses)

        response = await self.get_with_retry("/orders/v0/orders", params=params)

        if response.get("payload") and response["payload"].get("Orders"):
            order_count = len(response["payload"]["Orders"])
            logger.info(f"Retrieved {order_count} orders from Amazon SP-API")

        return response

    async def get_inventory(self, sku: str) -> Dict[str, Any]:
        """Get inventory details for a SKU."""
        # Example - Assuming an inventory endpoint exists
        endpoint = "/fba/inventory/v1/summaries"
        params = {
            "marketplaceId": self.marketplace_id,
            "granularityType": "Marketplace",
            "details": "true",
            "sellerSkus": sku,
        }
        # Use inherited method
        return await self.get_with_retry(endpoint, params=params)

    async def _create_listing(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Amazon listing using the SP-API Listings API"""
        try:
            listing_data = task["data"]
            sku = listing_data.get("sku")

            if not sku:
                return {
                    "success": False,
                    "error": "SKU is required for creating a listing",
                }

            if not await self._validate_listing_data(listing_data):
                self.metrics["error_count"] = self.metrics.get("error_count", 0) + 1
                await self.alert_manager.send_alert(
                    severity="error",
                    message=f"Invalid listing data for SKU {sku}",
                    metadata={"data": listing_data},
                )
                return {"success": False, "error": "Invalid listing data"}

            # Prepare the request for the Listings API
            request_body = {
                "productType": listing_data.get("productType", "PRODUCT"),
                "requirements": listing_data.get("requirements", "LISTING"),
                "attributes": listing_data.get("attributes", {}),
            }

            # Make the API call to the Listings API
            response = await self.put_with_retry(
                f"/listings/2021-08-01/items/{sku}",
                json=request_body,
                params={"marketplaceIds": self.marketplace_id},
            )

            if response.get("status", 500) in [200, 201, 202]:
                self.metrics["listings_created"] = (
                    self.metrics.get("listings_created", 0) + 1
                )
                await self.alert_manager.send_alert(
                    severity="info",
                    message=f"Successfully created listing for SKU {sku}",
                    metadata={"sku": sku},
                )
                return {"success": True, "sku": sku, "details": response}
            else:
                self.metrics["error_count"] = self.metrics.get("error_count", 0) + 1
                await self.alert_manager.send_alert(
                    severity="error",
                    message=f"API error creating listing for SKU {sku}: {response.get('errors', [])}",
                    metadata={"response": response},
                )
                return {
                    "success": False,
                    "error": str(response.get("errors", ["Unknown API error"])),
                    "details": response,
                }
        except Exception as e:
            self.metrics["error_count"] = self.metrics.get("error_count", 0) + 1
            await self.alert_manager.send_alert(
                severity="error",
                message=f"Exception creating listing for SKU {sku}: {str(e)}",
                metadata={"error": str(e)},
            )
            return {"success": False, "error": str(e)}

    async def _update_listing(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing Amazon listing."""
        try:
            listing_data = task["data"]
            sku = listing_data.get("sku")

            if not sku:
                return {
                    "success": False,
                    "error": "SKU is required for updating a listing",
                }

            # Prepare update data
            update_data = {
                "productType": listing_data.get("productType", "PRODUCT"),
                "requirements": "LISTING",
                "attributes": listing_data.get("attributes", {}),
            }

            response = await self.patch_with_retry(
                f"/listings/2021-08-01/items/{sku}",
                json_data=update_data,
                params={"marketplaceIds": self.marketplace_id},
            )

            if response.get("status", 500) in [200, 202]:
                self.metrics["listings_updated"] = (
                    self.metrics.get("listings_updated", 0) + 1
                )
                await self.alert_manager.send_alert(
                    severity="info",
                    message=f"Successfully updated listing for SKU {sku}",
                    metadata={"sku": sku},
                )
                return {"success": True, "sku": sku, "details": response}
            else:
                self.metrics["error_count"] = self.metrics.get("error_count", 0) + 1
                return {
                    "success": False,
                    "error": str(response.get("errors", ["Unknown API error"])),
                    "details": response,
                }
        except Exception as e:
            self.metrics["error_count"] = self.metrics.get("error_count", 0) + 1
            return {"success": False, "error": str(e)}

    async def _delete_listing(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Delete/end an Amazon listing."""
        try:
            sku = task.get("sku")

            if not sku:
                return {
                    "success": False,
                    "error": "SKU is required for deleting a listing",
                }

            response = await self.delete_with_retry(
                f"/listings/2021-08-01/items/{sku}",
                params={"marketplaceIds": self.marketplace_id},
            )

            if response.get("status", 500) in [200, 202, 204]:
                self.metrics["listings_deleted"] = (
                    self.metrics.get("listings_deleted", 0) + 1
                )
                await self.alert_manager.send_alert(
                    severity="info",
                    message=f"Successfully deleted listing for SKU {sku}",
                    metadata={"sku": sku},
                )
                return {"success": True, "sku": sku, "details": response}
            else:
                self.metrics["error_count"] = self.metrics.get("error_count", 0) + 1
                return {
                    "success": False,
                    "error": str(response.get("errors", ["Unknown API error"])),
                    "details": response,
                }
        except Exception as e:
            self.metrics["error_count"] = self.metrics.get("error_count", 0) + 1
            return {"success": False, "error": str(e)}

    async def _manage_fba_inventory(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Manage FBA inventory operations."""
        try:
            operation = task.get("operation")
            sku = task.get("sku")

            if operation == "update_quantity":
                quantity = task.get("quantity", 0)
                response = await self.post_with_retry(
                    "/fba/inventory/v1/adjustments",
                    json_data={
                        "InventoryAdjustments": [
                            {
                                "SellerSKU": sku,
                                "Quantity": quantity,
                                "AdjustmentType": "SET",
                            }
                        ]
                    },
                )

                if response.get("status", 500) in [200, 202]:
                    self.metrics["inventory_updates"] = (
                        self.metrics.get("inventory_updates", 0) + 1
                    )
                    return {"success": True, "sku": sku, "quantity": quantity}
                else:
                    return {
                        "success": False,
                        "error": str(response.get("errors", ["Unknown error"])),
                    }

            elif operation == "create_shipment":
                shipment_data = task.get("shipment_data", {})
                response = await self.post_with_retry(
                    "/fba/inbound/v0/shipments",
                    json_data={
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
                    },
                )

                if response.get("status", 500) in [200, 201]:
                    self.metrics["shipments_created"] = (
                        self.metrics.get("shipments_created", 0) + 1
                    )
                    return {
                        "success": True,
                        "shipment_id": response.get("payload", {}).get("ShipmentId"),
                    }
                else:
                    return {
                        "success": False,
                        "error": str(response.get("errors", ["Unknown error"])),
                    }

            else:
                return {
                    "success": False,
                    "error": f"Unknown FBA operation: {operation}",
                }

        except Exception as e:
            self.metrics["error_count"] = self.metrics.get("error_count", 0) + 1
            return {"success": False, "error": str(e)}

    async def _sync_inventory(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronize inventory levels across multiple SKUs."""
        try:
            inventory_updates = task.get("inventory_updates", [])
            results = []

            for update in inventory_updates:
                sku = update.get("sku")
                quantity = update.get("quantity")

                try:
                    result = await self._manage_fba_inventory(
                        {
                            "operation": "update_quantity",
                            "sku": sku,
                            "quantity": quantity,
                        }
                    )
                    results.append(
                        {
                            "sku": sku,
                            "success": result.get("success", False),
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

            successful_updates = len([r for r in results if r["success"]])
            self.metrics["bulk_inventory_syncs"] = (
                self.metrics.get("bulk_inventory_syncs", 0) + 1
            )

            return {
                "success": True,
                "total_updates": len(inventory_updates),
                "successful_updates": successful_updates,
                "failed_updates": len(inventory_updates) - successful_updates,
                "results": results,
            }

        except Exception as e:
            self.metrics["error_count"] = self.metrics.get("error_count", 0) + 1
            return {"success": False, "error": str(e)}

    async def _update_inventory(self, task: Dict[str, Any]) -> bool:
        # ... (logic to build request_body)
        try:
            # Ensure request_body is defined before use
            request_body = {
                "requests": [
                    {
                        "type": "REPLACE",
                        "payload": {
                            "sku": task["sku"],
                            "quantity": task["quantity"],
                            # Add other necessary fields
                        },
                    }
                ]
            }
            # Pass request_body as json parameter
            response = await self.put_with_retry(
                "/inventory/v1/inventoryItems",  # Assuming this is the correct endpoint
                json=request_body,
            )
            logger.info(f"Inventory updated for {task.get('sku')}: {response}")
            self.metrics["inventory_updates"] += 1
            return True
        except Exception as e:
            logger.error(f"Failed to update inventory for {task.get('sku')}: {e}")
            self.metrics["error_count"] = self.metrics.get("error_count", 0) + 1
            await self.alert_manager.send_alert(
                severity="error",
                message=f"Inventory update failed: {str(e)}",
                metadata=task,
            )
            return False

    async def _validate_listing_data(self, data: Dict[str, Any]) -> bool:
        """Validate listing data for Amazon"""
        required_fields = ["sku", "attributes"]
        return all(field in data for field in required_fields)

    async def _handle_product_update(self, event: Dict[str, Any]) -> None:
        """Handle Amazon product update events"""
        product_data = event.get("data", {})
        product_id = product_data.get("asin") or product_data.get("sku")

        if not product_id:
            logger.error("Missing ASIN or SKU in product update event")
            self.metrics["error_count"] = self.metrics.get("error_count", 0) + 1
            await self.alert_manager.send_alert(
                severity="missing_product_id",
                message="Product update event missing ASIN or SKU",
                metadata={"event": event},
            )
            return

        try:
            logger.info(
                "Processing Amazon product update for product ID: %s", product_id
            )
            self.metrics["products_processed"] = (
                self.metrics.get("products_processed", 0) + 1
            )

            # Verify product data
            if not self._validate_product_data(product_data):
                logger.warning("Invalid product data for product ID: %s", product_id)
                self.metrics["validation_failures"] = (
                    self.metrics.get("validation_failures", 0) + 1
                )
                await self.alert_manager.send_alert(
                    severity="invalid_product_data",
                    message=f"Invalid product data for product ID: {product_id}",
                    metadata={"product_data": product_data},
                )
                return

            # Process product update
            result = await self._update_product_data(product_id, product_data)
            self.metrics["data_points_analyzed"] = self.metrics.get(
                "data_points_analyzed", 0
            ) + len(product_data)

            if result:
                logger.info(
                    "Successfully updated product data for product ID: %s", product_id
                )
            else:
                logger.warning(
                    "Failed to update product data for product ID: %s", product_id
                )
        except Exception as e:
            logger.error("Error processing product update: %s", str(e))
            self.metrics["error_count"] = self.metrics.get("error_count", 0) + 1
            await self.alert_manager.send_alert(
                severity="product_update_error",
                message=f"Error processing product update for product ID: {product_id}",
                metadata={"error": str(e), "event": event},
            )

    async def _handle_price_change(self, event: Dict[str, Any]) -> None:
        """Handle price changes for Amazon products"""
        try:
            price_data = event["data"]
            product_id = price_data.get("asin") or price_data.get("sku")
            if not product_id:
                raise ValueError("Missing ASIN or SKU in price change event")

            updated = await self._update_price_data(product_id, price_data)
            if updated:
                self.metrics["products_fetched"] += 1
                await self.alert_manager.send_alert(
                    severity="info",
                    message=f"Successfully updated price data for product ID {product_id}",
                    metadata={
                        "metric": "products_fetched",
                        "value": self.metrics["products_fetched"],
                    },
                )
            else:
                self.metrics["error_count"] = self.metrics.get("error_count", 0) + 1
                await self.alert_manager.send_alert(
                    severity="error",
                    message=f"Failed to update price data for product ID {product_id}",
                    metadata={
                        "metric": "error_count",
                        "value": self.metrics["error_count"],
                    },
                )
        except Exception as e:
            self.metrics["error_count"] = self.metrics.get("error_count", 0) + 1
            await self.alert_manager.send_alert(
                severity="error",
                message=f"Error handling price change: {str(e)}",
                metadata={
                    "metric": "error_count",
                    "value": self.metrics["error_count"],
                },
            )
            logger.error("Error handling price change: %s", e)

    async def _handle_inventory_update(self, event: Dict[str, Any]) -> None:
        """Handle inventory updates for Amazon products"""
        try:
            inventory_data = event["data"]
            product_id = inventory_data.get("asin") or inventory_data.get("sku")
            if not product_id:
                raise ValueError("Missing ASIN or SKU in inventory update event")

            updated = await self._update_inventory_data(product_id, inventory_data)
            if updated:
                self.metrics["products_fetched"] += 1
                await self.alert_manager.send_alert(
                    severity="info",
                    message=f"Successfully updated inventory data for product ID {product_id}",
                    metadata={
                        "metric": "products_fetched",
                        "value": self.metrics["products_fetched"],
                    },
                )
            else:
                self.metrics["error_count"] = self.metrics.get("error_count", 0) + 1
                await self.alert_manager.send_alert(
                    severity="error",
                    message=f"Failed to update inventory data for product ID {product_id}",
                    metadata={
                        "metric": "error_count",
                        "value": self.metrics["error_count"],
                    },
                )
        except Exception as e:
            self.metrics["error_count"] = self.metrics.get("error_count", 0) + 1
            await self.alert_manager.send_alert(
                severity="error",
                message=f"Error handling inventory update: {str(e)}",
                metadata={
                    "metric": "error_count",
                    "value": self.metrics["error_count"],
                },
            )
            logger.error("Error handling inventory update: %s", e)

    async def _update_product_data(self, product_id: str, data: Dict[str, Any]) -> bool:
        """Update product data in internal state

        Args:
            product_id: Product identifier (ASIN or SKU)
            data: Product data to update

        Returns:
            True if successful, False otherwise
        """
        try:
            # Here we would update our internal product database
            # For now, just log the update
            logger.info(
                f"Would update product data for {product_id}: {len(data)} fields"
            )
            return True
        except Exception as e:
            logger.error(f"Error updating product data: {e}")
            return False

    async def _update_price_data(self, product_id: str, data: Dict[str, Any]) -> bool:
        """Update price data for a product

        Args:
            product_id: Product identifier (ASIN or SKU)
            data: Price data to update

        Returns:
            True if successful, False otherwise
        """
        try:
            # Here we would update our internal price database
            # For now, just log the update
            logger.info(
                f"Would update price data for {product_id}: {data.get('price')}"
            )
            return True
        except Exception as e:
            logger.error(f"Error updating price data: {e}")
            return False

    async def _update_inventory_data(
        self, product_id: str, data: Dict[str, Any]
    ) -> bool:
        """Update inventory data for a product

        Args:
            product_id: Product identifier (ASIN or SKU)
            data: Inventory data to update

        Returns:
            True if successful, False otherwise
        """
        try:
            # Here we would update our internal inventory database
            # For now, just log the update
            logger.info(
                f"Would update inventory data for {product_id}: {data.get('quantity')} units"
            )
            return True
        except Exception as e:
            logger.error(f"Error updating inventory data: {e}")
            return False

    def _validate_product_data(self, data: Dict[str, Any]) -> bool:
        """Validate product data

        Args:
            data: Product data to validate

        Returns:
            True if valid, False otherwise
        """
        # Basic validation - at least one identifier is required
        if not (data.get("asin") or data.get("sku")):
            return False
        return True

    async def get_product_details(self, asin: str) -> Dict[str, Any]:
        """Get product details using Catalog Items API."""
        endpoint = f"/catalog/2020-12-01/items/{asin}"
        params = {
            "marketplaceIds": self.marketplace_id,
            "includedData": "attributes,images,summaries",
        }
        # Use inherited method
        response = await self.get_with_retry(endpoint, params=params)
        self.metrics["products_fetched"] += 1
        # Add more granular metrics if needed
        return response


# Alias for backward compatibility
AmazonUnifiedAgent = AmazonMarketUnifiedAgent
