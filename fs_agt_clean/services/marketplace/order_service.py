"""Mock implementation of OrderService for linting purposes."""

from typing import Any, Dict, List, Optional


class OrderService:
    """Mock implementation of OrderService for linting purposes."""

    def __init__(self, **kwargs):
        """Initialize the service."""
        pass

    async def get_orders(
        self,
        seller_id: str,
        marketplace: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get orders."""
        return []

    async def fulfill_order(
        self,
        order_id: str,
        seller_id: str,
        tracking_number: Optional[str] = None,
        carrier: Optional[str] = None,
        notes: str = "",
    ) -> None:
        """Fulfill an order."""
        # Mock implementation - in a real implementation, we would validate the inputs
        if tracking_number is None or carrier is None:
            raise ValueError("Tracking number and carrier are required")
        # Process the order fulfillment
        pass
