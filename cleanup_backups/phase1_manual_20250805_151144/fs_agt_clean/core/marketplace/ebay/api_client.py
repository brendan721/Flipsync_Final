from typing import Dict, Optional

from fs_agt_clean.core.api_client import APIClient


class EbayAPIClient(APIClient):
    """HTTP client for eBay API interactions."""

    def __init__(self, base_url: str):
        """Initialize the eBay API client.

        Args:
            base_url: Base URL for eBay API
        """
        super().__init__(base_url)

    async def authenticate(self, client_id: str, client_secret: str) -> Dict:
        """Authenticate with eBay API.

        Args:
            client_id: eBay client ID
            client_secret: eBay client secret

        Returns:
            Authentication response with access token
        """
        import base64

        credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "client_credentials",
            "scope": " ".join(
                [
                    "https://api.ebay.com/oauth/api_scope",
                    "https://api.ebay.com/oauth/api_scope/buy.item.feed",
                    "https://api.ebay.com/oauth/api_scope/buy.marketing",
                    "https://api.ebay.com/oauth/api_scope/buy.item.bulk",
                    "https://api.ebay.com/oauth/api_scope/buy.item.bulk.feed",
                    "https://api.ebay.com/oauth/api_scope/sell.inventory",
                    "https://api.ebay.com/oauth/api_scope/sell.marketing",
                    "https://api.ebay.com/oauth/api_scope/sell.analytics.readonly",
                ]
            ),
        }
        return await self.post("/identity/v1/oauth2/token", data=data, headers=headers)

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> Dict:
        """Send GET request to eBay API.

        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Request headers

        Returns:
            API response
        """
        return await super().get(endpoint, params=params, headers=headers)

    async def post(
        self,
        endpoint: str,
        json: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> Dict:
        """Send POST request to eBay API.

        Args:
            endpoint: API endpoint
            json: JSON payload
            data: Form data
            headers: Request headers

        Returns:
            API response
        """
        return await super().post(endpoint, json=json, data=data, headers=headers)

    async def get_inventory(self, access_token: Optional[str] = None) -> list:
        """Get inventory information from eBay.

        Args:
            access_token: Optional eBay API access token

        Returns:
            List of inventory items
        """
        headers = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        params = {
            "limit": 100,  # Maximum items per page
        }

        try:
            response = await self.get(
                endpoint="/sell/inventory/v1/inventory_item",
                params=params,
                headers=headers,
            )

            inventory_items = []
            for item in response.get("inventoryItems", []):
                inventory_items.append(
                    {
                        "sku": item.get("sku"),
                        "title": item.get("product", {}).get("title"),
                        "price": float(
                            item.get("offers", [{}])[0].get("price", {}).get("value", 0)
                        ),
                        "quantity": item.get("availability", {})
                        .get("shipToLocationAvailability", {})
                        .get("quantity", 0),
                        "condition": item.get("condition"),
                        "description": item.get("product", {}).get("description"),
                        "images": item.get("product", {}).get("imageUrls", []),
                    }
                )

            return inventory_items

        except Exception as e:
            raise ValueError(f"Failed to get inventory: {str(e)}") from e

    async def get_orders(
        self, access_token: Optional[str] = None, created_after: Optional[str] = None
    ) -> list:
        """Get orders from eBay.

        Args:
            access_token: Optional eBay API access token
            created_after: Optional ISO 8601 date string to filter orders created after this date

        Returns:
            List of orders
        """
        headers = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        params = {
            "limit": 50,  # Number of orders per page
            "orderStatuses": "ACTIVE,COMPLETED,FULFILLED",
        }

        if created_after:
            params["creationDateFrom"] = created_after

        try:
            response = await self.get(
                endpoint="/sell/fulfillment/v1/order",
                params=params,
                headers=headers,
            )

            orders = []
            for order in response.get("orders", []):
                items = []
                for line_item in order.get("lineItems", []):
                    items.append(
                        {
                            "item_id": line_item.get("itemId"),
                            "sku": line_item.get("sku"),
                            "title": line_item.get("title"),
                            "quantity": line_item.get("quantity"),
                            "price": float(
                                line_item.get("lineItemCost", {}).get("value", 0)
                            ),
                        }
                    )

                orders.append(
                    {
                        "order_id": order.get("orderId"),
                        "status": order.get("orderFulfillmentStatus"),
                        "created_date": order.get("creationDate"),
                        "buyer": order.get("buyer", {}).get("username"),
                        "total": float(
                            order.get("pricingSummary", {})
                            .get("total", {})
                            .get("value", 0)
                        ),
                        "items": items,
                    }
                )

            return orders

        except Exception as e:
            raise ValueError(f"Failed to get orders: {str(e)}") from e

    async def put(
        self,
        endpoint: str,
        json: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> Dict:
        """Send PUT request to eBay API.

        Args:
            endpoint: API endpoint
            json: JSON payload
            headers: Request headers

        Returns:
            API response
        """
        return await super().put(endpoint, json=json, headers=headers)

    async def delete(self, endpoint: str, headers: Optional[Dict] = None) -> Dict:
        """Send DELETE request to eBay API.

        Args:
            endpoint: API endpoint
            headers: Request headers

        Returns:
            API response
        """
        return await super().delete(endpoint, headers=headers)
