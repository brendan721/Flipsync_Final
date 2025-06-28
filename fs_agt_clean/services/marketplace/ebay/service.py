import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fs_agt_clean.core.marketplace.ebay.api_client import EbayAPIClient
from fs_agt_clean.core.marketplace.ebay.config import EbayConfig
from fs_agt_clean.core.monitoring.alert_types import AlertSeverity
from fs_agt_clean.services.metrics.service import MetricsService
from fs_agt_clean.services.notifications.service import NotificationService


class EbayService:
    """Service for interacting with eBay API."""

    def __init__(
        self,
        config: Any,
        api_client: EbayAPIClient,
        metrics_service: MetricsService,
        notification_service: NotificationService,
    ):
        self.config = config
        self.api_client = api_client
        self.metrics_service = metrics_service
        self.notification_service = notification_service
        self._auth_refreshes = 0
        self._request_semaphores = {
            "search": asyncio.Semaphore(5),
            "item": asyncio.Semaphore(2),
            "inventory": asyncio.Semaphore(1),
        }
        self._token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._auth_lock = asyncio.Lock()

    async def _ensure_authenticated(self) -> None:
        """Ensure we have a valid authentication token."""
        async with self._auth_lock:
            now = datetime.now()
            if not self._token or not self._token_expiry or now >= self._token_expiry:
                try:
                    auth_result = await self.api_client.authenticate(
                        client_id=self.config.client_id,
                        client_secret=self.config.client_secret,
                    )
                    self._token = auth_result.get("access_token")
                    token_expires_in = auth_result.get("expires_in", 0)
                    self._token_expiry = now + timedelta(seconds=token_expires_in - 300)
                    self._auth_refreshes += 1
                    await self.metrics_service.increment_counter(
                        name="ebay_auth_refreshes_total", value=1.0
                    )

                    # Send notification if token is about to expire
                    if token_expires_in < 3600:  # Less than 1 hour
                        await self.notification_service.send_notification(
                            user_id="system",
                            template_id="ebay_token_expiry",
                            data={
                                "severity": AlertSeverity.MEDIUM,
                                "component": "ebay",
                                "expires_in": token_expires_in,
                            },
                            category="monitoring",
                        )
                except Exception as e:
                    await self.notification_service.send_notification(
                        user_id="system",
                        template_id="ebay_auth_error",
                        data={
                            "severity": AlertSeverity.CRITICAL,
                            "component": "ebay",
                            "error": str(e),
                        },
                        category="monitoring",
                    )
                    raise

    async def _execute_api(
        self,
        endpoint: str,
        method: str,
        params: Optional[Dict] = None,
        max_retries: int = 3,
    ) -> Dict:
        """Execute eBay API request with rate limiting and retry logic."""
        semaphore = self._request_semaphores.get(
            endpoint.split("/")[0], self._request_semaphores["search"]
        )

        # Record request metrics
        await self.metrics_service.increment_counter(
            name="ebay_requests_total", labels={"endpoint": endpoint}
        )

        start_time = datetime.now()
        try:
            try:
                await self._ensure_authenticated()
            except Exception:
                # Authentication errors are already handled in _ensure_authenticated
                raise

            async with semaphore:
                headers = {"Authorization": f"Bearer {self._token}"}
                if method == "GET":
                    response = await self.api_client.get(
                        endpoint, params=params, headers=headers
                    )
                elif method == "POST":
                    response = await self.api_client.post(
                        endpoint, json=params, headers=headers
                    )
                elif method == "PUT":
                    response = await self.api_client.put(
                        endpoint, json=params, headers=headers
                    )
                elif method == "DELETE":
                    response = await self.api_client.delete(endpoint, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                duration = (datetime.now() - start_time).total_seconds()

                # Record success metrics
                await self.metrics_service.record_metric(
                    name="ebay_request_duration_seconds",
                    value=duration,
                    labels={"endpoint": endpoint},
                )
                await self.metrics_service.increment_counter(
                    name="ebay_request_success", labels={"endpoint": endpoint}
                )
                return response
        except Exception as e:
            if isinstance(e, Exception) and "Authentication failed" in str(e):
                # Skip handling here as it's already handled in _ensure_authenticated
                raise

            # Record error metrics
            await self.metrics_service.increment_counter(
                name="ebay_errors_total",
                labels={"endpoint": endpoint, "error_type": type(e).__name__},
            )

            # Send notifications based on error type
            if max_retries == 0:  # Only send notification on final retry
                if "Rate limit exceeded" in str(e):
                    await self.metrics_service.increment_counter(
                        name="ebay_rate_limits_total", labels={"endpoint": endpoint}
                    )
                    await self.notification_service.send_notification(
                        user_id="system",
                        template_id="ebay_rate_limit",
                        data={
                            "severity": AlertSeverity.HIGH,
                            "component": "ebay",
                            "endpoint": endpoint,
                        },
                        category="monitoring",
                    )
                else:
                    await self.notification_service.send_notification(
                        user_id="system",
                        template_id="ebay_api_error",
                        data={
                            "severity": AlertSeverity.HIGH,
                            "component": "ebay",
                            "endpoint": endpoint,
                            "error": str(e),
                        },
                        category="monitoring",
                    )

            if max_retries > 0:
                await asyncio.sleep(1)
                return await self._execute_api(
                    endpoint=endpoint,
                    method=method,
                    params=params,
                    max_retries=max_retries - 1,
                )
            raise

    async def search_items(
        self, keywords: str, limit: int = 50, offset: int = 0, sort: str = "price"
    ) -> List[Dict]:
        """Search for items on eBay."""
        response = await self._execute_api(
            endpoint="search/items",
            method="GET",
            params={"q": keywords, "limit": limit, "offset": offset, "sort": sort},
        )
        return response.get("items", [])

    async def get_item(self, item_id: str) -> Optional[Dict]:
        """Get detailed item information."""
        response = await self._execute_api(endpoint=f"item/{item_id}", method="GET")
        return response.get("item")

    async def create_listing(self, listing_data: Dict) -> Dict:
        """Create a new eBay listing."""
        response = await self._execute_api(
            endpoint="inventory/listing", method="POST", params=listing_data
        )
        return response

    async def update_listing(self, listing_id: str, listing_data: Dict) -> Dict:
        """Update an existing eBay listing."""
        response = await self._execute_api(
            endpoint=f"inventory/listing/{listing_id}",
            method="PUT",
            params=listing_data,
        )
        return response

    async def delete_listing(self, listing_id: str) -> Dict:
        """Delete an eBay listing."""
        response = await self._execute_api(
            endpoint=f"inventory/listing/{listing_id}", method="DELETE"
        )
        return response

    async def get_inventory_item(self, sku: str) -> Optional[Dict]:
        """Get inventory item by SKU."""
        try:
            response = await self._execute_api(
                endpoint=f"inventory/item/{sku}", method="GET"
            )
            if response.get("status_code") == 404:
                return None
            response_data = response.get("json_payload", {})
            return response_data.get("product")
        except Exception:
            return None

    async def create_inventory_item(
        self, sku: str, product_data: Dict
    ) -> Optional[Dict]:
        """Create a new inventory item."""
        try:
            response = await self._execute_api(
                endpoint=f"inventory/item/{sku}", method="PUT", params=product_data
            )
            if response.get("status_code") == 200:
                return response.get("json_payload", {})
            return None
        except Exception:
            return None

    async def update_inventory_quantity(self, sku: str, quantity: int) -> bool:
        """Update inventory quantity for an item."""
        try:
            response = await self._execute_api(
                endpoint=f"inventory/item/{sku}/quantity",
                method="PUT",
                params={"quantity": quantity},
            )
            return bool(response.get("status_code") == 200)
        except Exception:
            return False

    async def create_offer(
        self, sku: str, price: float, quantity: int, listing_data: Dict
    ) -> Dict:
        """Create an offer for an inventory item."""
        try:
            offer_data = {
                "sku": sku,
                "price": price,
                "quantity": quantity,
                **listing_data,
            }
            response = await self._execute_api(
                endpoint="inventory/offer", method="POST", params=offer_data
            )
            if response.get("status_code") == 200:
                response_data = response.get("json_payload", {})
                offer_id = response_data.get("offerId")
                return {"success": True, "offer_id": offer_id}
            error_text = response.get("error", response.get("text", "Unknown error"))
            return {"success": False, "error": error_text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_category_item_specifics(self, category_id: str) -> Dict[str, Any]:
        """Get item specifics for a specific eBay category.

        Args:
            category_id: eBay category ID

        Returns:
            Dictionary containing item specifics information
        """
        try:
            response = await self._execute_api(
                endpoint=f"commerce/taxonomy/v1/category_tree/0/get_item_aspects_for_category",
                method="GET",
                params={"category_id": category_id},
            )

            # Parse the response to extract item specifics
            aspects = response.get("aspects", [])
            specifics = {}

            for aspect in aspects:
                name = aspect.get("localizedAspectName", "")
                if name:
                    specifics[name] = {
                        "required": aspect.get("aspectConstraint", {}).get(
                            "aspectRequired", False
                        ),
                        "importance": (
                            0.9
                            if aspect.get("aspectConstraint", {}).get(
                                "aspectRequired", False
                            )
                            else 0.7
                        ),
                        "values": [
                            val.get("localizedValue", "")
                            for val in aspect.get("aspectValues", [])
                        ],
                        "max_length": aspect.get("aspectConstraint", {}).get(
                            "aspectMaxLength", 65
                        ),
                        "usage": aspect.get("aspectUsage", "OPTIONAL"),
                    }

            return {
                "category_id": category_id,
                "specifics": specifics,
                "total_count": len(specifics),
            }

        except Exception as e:
            # Fallback to basic specifics if API call fails
            return {
                "category_id": category_id,
                "specifics": {
                    "Brand": {
                        "required": True,
                        "importance": 0.9,
                        "values": [],
                        "max_length": 65,
                        "usage": "REQUIRED",
                    },
                    "MPN": {
                        "required": False,
                        "importance": 0.8,
                        "values": [],
                        "max_length": 65,
                        "usage": "OPTIONAL",
                    },
                    "Model": {
                        "required": False,
                        "importance": 0.8,
                        "values": [],
                        "max_length": 65,
                        "usage": "OPTIONAL",
                    },
                    "Color": {
                        "required": False,
                        "importance": 0.7,
                        "values": [],
                        "max_length": 65,
                        "usage": "OPTIONAL",
                    },
                },
                "total_count": 4,
                "error": str(e),
            }

    async def get_categories(self, parent_id: Optional[str] = None) -> List[Dict]:
        """Get eBay categories.

        Args:
            parent_id: Optional parent category ID

        Returns:
            List of category dictionaries
        """
        try:
            params = {}
            if parent_id:
                params["parent_id"] = parent_id

            response = await self._execute_api(
                endpoint="commerce/taxonomy/v1/category_tree/0/get_categories",
                method="GET",
                params=params,
            )

            categories = response.get("categories", [])
            return [
                {
                    "id": cat.get("categoryId", ""),
                    "name": cat.get("categoryName", ""),
                    "level": cat.get("categoryTreeNodeLevel", 0),
                    "parent_id": cat.get("parentCategoryId"),
                    "leaf": cat.get("leafCategoryTreeNode", False),
                }
                for cat in categories
            ]

        except Exception as e:
            # Return empty list on error
            return []

    async def process_webhook_event(self, event_data: Dict[str, Any]) -> None:
        """Process webhook event from eBay.

        Args:
            event_data: Event data from eBay webhook
        """
        try:
            event_type = event_data.get("eventType")
            notification_data = event_data.get("notification", {})

            # Record metrics
            await self.metrics_service.increment_counter(
                name="ebay_webhook_events_total", labels={"event_type": str(event_type)}
            )

            # Send notification about the webhook event
            await self.notification_service.send_notification(
                user_id="system",
                template_id="ebay_webhook_event",
                data={
                    "event_type": str(event_type),
                    "notification": notification_data,
                    "timestamp": datetime.now().isoformat(),
                },
                category="marketplace",
            )

            # Process different event types
            if event_type == "ORDER_CREATED" or event_type == "ORDER_UPDATED":
                # Process order event
                order_data = notification_data.get("data", {}).get("order", {})
                if order_data and "orderId" in order_data:
                    # Process the order data
                    await self._process_order_notification(order_data)

            elif event_type == "INVENTORY_ITEM_UPDATED":
                # Process inventory update
                sku = notification_data.get("sku")
                quantity = notification_data.get("availableQuantity")
                if sku and quantity is not None:
                    await self.update_inventory_quantity(sku, quantity)

            elif event_type == "OFFER_CREATED" or event_type == "OFFER_UPDATED":
                # Process offer event
                offer_id = notification_data.get("offerId")
                sku = notification_data.get("sku")
                if offer_id and sku:
                    # Process the offer data
                    pass  # Implement offer processing logic

        except Exception as e:
            # Record error metrics
            await self.metrics_service.increment_counter(
                name="ebay_webhook_errors_total",
                labels={"event_type": str(event_data.get("eventType", "unknown"))},
            )

            # Send error notification
            await self.notification_service.send_notification(
                user_id="system",
                template_id="ebay_webhook_error",
                data={
                    "severity": "error",
                    "component": "ebay",
                    "error": str(e),
                    "event_type": str(event_data.get("eventType", "unknown")),
                },
                category="monitoring",
            )

    async def _process_order_notification(self, order_data: Dict[str, Any]) -> None:
        """Process order notification from eBay webhook.

        Args:
            order_data: Order data from eBay
        """
        try:
            order_id = order_data.get("orderId")
            if not order_id:
                return

            # Send notification about the order
            await self.notification_service.send_notification(
                user_id="system",
                template_id="ebay_order_notification",
                data={
                    "order_id": order_id,
                    "order_status": order_data.get("orderStatus", "unknown"),
                    "timestamp": datetime.now().isoformat(),
                },
                category="marketplace",
            )

            # Process the order data
            # This would typically involve updating inventory, creating fulfillment tasks, etc.
            # For now, we'll just log the order ID

        except Exception as e:
            # Send error notification
            await self.notification_service.send_notification(
                user_id="system",
                template_id="ebay_order_processing_error",
                data={
                    "severity": "error",
                    "component": "ebay",
                    "error": str(e),
                    "order_id": order_data.get("orderId", "unknown"),
                },
                category="monitoring",
            )
