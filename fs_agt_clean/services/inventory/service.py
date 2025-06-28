"""
Real implementation of inventory management service.

This service provides inventory management functionality using real database
repositories for inventory item management.
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from fs_agt_clean.core.db.database import Database
from fs_agt_clean.core.metrics.service import MetricsService
from fs_agt_clean.database.repositories.inventory_repository import InventoryRepository
from fs_agt_clean.services.notifications.service import NotificationService

logger = logging.getLogger(__name__)


class StockLevel(Enum):
    """Stock level enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class StorageLocation:
    """Storage location data class."""

    id: str
    name: str
    type: str  # 'warehouse', 'retail', etc.
    capacity: int
    current_utilization: int = 0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class InventoryItem:
    """Inventory item data class."""

    id: str
    name: str
    description: str
    quantity: int
    initial_quantity: int
    price: float
    category: str
    location: str
    stock_level: StockLevel = StockLevel.MEDIUM
    sales_velocity: float = 0.0
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.updated_at is None:
            self.updated_at = datetime.now(timezone.utc)


@dataclass
class InventoryTransaction:
    """Inventory transaction data class."""

    id: str
    item_id: str
    quantity: int
    transaction_type: str  # 'add', 'remove', 'sale', 'restock', etc.
    notes: Optional[str] = None
    timestamp: datetime = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


class InventoryManagementService:
    """
    Real implementation of inventory management service.

    This service provides inventory management functionality using real database
    repositories for inventory item management.
    """

    def __init__(
        self,
        database: Database,
        metrics_service: Optional[MetricsService] = None,
        notification_service: Optional[NotificationService] = None,
    ):
        """
        Initialize the inventory service.

        Args:
            database: Database instance
            metrics_service: Optional metrics service for tracking
            notification_service: Optional notification service for alerts
        """
        self.database = database
        self.metrics_service = metrics_service
        self.notification_service = notification_service
        # Repository will be initialized with session in each method

    async def get_inventory(
        self,
        seller_id: str,
        sku: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get inventory items.

        Args:
            seller_id: Seller ID
            sku: Optional SKU to filter by
            category: Optional category to filter by
            limit: Maximum number of items to return
            offset: Offset for pagination

        Returns:
            List of inventory items
        """
        try:
            async with self.database.get_session_context() as session:
                inventory_repository = InventoryRepository(session)

                # Build criteria
                criteria = {"created_by": seller_id}
                if sku:
                    criteria["sku"] = sku
                if category:
                    criteria["category"] = category

                # Get items from repository
                items = await inventory_repository.find_by_criteria(
                    criteria=criteria,
                    limit=limit,
                    offset=offset,
                )

                # Convert to dictionaries
                result = [inventory_repository._item_to_dict(item) for item in items]

            # Record metrics
            if self.metrics_service:
                await self.metrics_service.increment_counter(
                    name="inventory_queries",
                    value=1,
                    labels={
                        "seller_id": seller_id,
                        "has_sku": "true" if sku else "false",
                        "has_category": "true" if category else "false",
                    },
                )

            return result

        except Exception as e:
            logger.error(f"Error getting inventory: {str(e)}")

            # Record error metrics
            if self.metrics_service:
                await self.metrics_service.increment_counter(
                    name="inventory_errors",
                    value=1,
                    labels={
                        "operation": "get_inventory",
                        "error_type": type(e).__name__,
                    },
                )

            raise

    async def create_inventory_item(
        self, seller_id: str, sku: str, quantity: int, product_data: Dict[str, Any]
    ) -> str:
        """
        Create an inventory item.

        Args:
            seller_id: Seller ID
            sku: SKU
            quantity: Initial quantity
            product_data: Product data

        Returns:
            ID of the created inventory item

        Raises:
            ValueError: If an item with the same SKU already exists
        """
        try:
            async with self.database.get_session_context() as session:
                inventory_repository = InventoryRepository(session)

                # Check if item with SKU already exists
                existing_item = await inventory_repository.get_by_sku(sku)
                if existing_item:
                    raise ValueError(f"Inventory item with SKU {sku} already exists")

                # Create item
                item_data = {
                    "sku": sku,
                    "name": product_data.get("name", ""),
                    "description": product_data.get("description", ""),
                    "quantity": quantity,
                    "price": product_data.get("price", 0.0),
                    "cost": product_data.get("cost", 0.0),
                    "category": product_data.get("category", ""),
                    "created_by": seller_id,
                }

                item = await inventory_repository.create_item(item_data)

            # Record metrics
            if self.metrics_service:
                await self.metrics_service.increment_counter(
                    name="inventory_items_created",
                    value=1,
                    labels={"seller_id": seller_id},
                )

            # Send notification
            if self.notification_service:
                await self.notification_service.send_notification(
                    user_id=seller_id,
                    title="Inventory Item Created",
                    message=f"New inventory item created: {item.name} (SKU: {item.sku})",
                    data={
                        "item_id": str(item.id),
                        "sku": item.sku,
                        "name": item.name,
                        "quantity": item.quantity,
                    },
                    category="inventory",
                )

            return str(item.id)

        except Exception as e:
            logger.error(f"Error creating inventory item: {str(e)}")

            # Record error metrics
            if self.metrics_service:
                await self.metrics_service.increment_counter(
                    name="inventory_errors",
                    value=1,
                    labels={
                        "operation": "create_inventory_item",
                        "error_type": type(e).__name__,
                    },
                )

            raise

    async def update_inventory_item(
        self, inventory_id: str, seller_id: str, product_data: Dict[str, Any]
    ) -> None:
        """
        Update an inventory item.

        Args:
            inventory_id: Inventory item ID
            seller_id: Seller ID
            product_data: Product data to update

        Raises:
            ValueError: If the item is not found
        """
        try:
            # Get the item
            item = await self.inventory_repository.find_by_id(inventory_id)
            if not item:
                raise ValueError(f"Inventory item not found: {inventory_id}")

            # Check if the item belongs to the seller
            if item.user_id != seller_id:
                raise ValueError(
                    f"Inventory item {inventory_id} does not belong to seller {seller_id}"
                )

            # Update the item
            update_data = {}
            if "name" in product_data:
                update_data["name"] = product_data["name"]
            if "description" in product_data:
                update_data["description"] = product_data["description"]
            if "price" in product_data:
                update_data["price"] = product_data["price"]
            if "cost" in product_data:
                update_data["cost"] = product_data["cost"]
            if "category" in product_data:
                update_data["category"] = product_data["category"]
            if "tags" in product_data:
                update_data["tags"] = product_data["tags"]
            if "attributes" in product_data:
                update_data["attributes"] = product_data["attributes"]

            # Only update if there are changes
            if update_data:
                update_data["updated_at"] = datetime.utcnow()
                await self.inventory_repository.update_item(inventory_id, **update_data)

                # Record metrics
                if self.metrics_service:
                    await self.metrics_service.increment_counter(
                        name="inventory_items_updated",
                        value=1,
                        labels={"seller_id": seller_id},
                    )

                # Send notification
                if self.notification_service:
                    await self.notification_service.send_notification(
                        user_id=seller_id,
                        title="Inventory Item Updated",
                        message=f"Inventory item updated: {item.name} (SKU: {item.sku})",
                        data={
                            "item_id": item.id,
                            "sku": item.sku,
                            "name": item.name,
                            "updated_fields": list(update_data.keys()),
                        },
                        category="inventory",
                    )

        except Exception as e:
            logger.error(f"Error updating inventory item: {str(e)}")

            # Record error metrics
            if self.metrics_service:
                await self.metrics_service.increment_counter(
                    name="inventory_errors",
                    value=1,
                    labels={
                        "operation": "update_inventory_item",
                        "error_type": type(e).__name__,
                    },
                )

            raise

    async def delete_inventory_item(self, inventory_id: str, seller_id: str) -> None:
        """
        Delete an inventory item.

        Args:
            inventory_id: Inventory item ID
            seller_id: Seller ID

        Raises:
            ValueError: If the item is not found
        """
        try:
            # Get the item
            item = await self.inventory_repository.find_by_id(inventory_id)
            if not item:
                raise ValueError(f"Inventory item not found: {inventory_id}")

            # Check if the item belongs to the seller
            if item.user_id != seller_id:
                raise ValueError(
                    f"Inventory item {inventory_id} does not belong to seller {seller_id}"
                )

            # Delete the item
            await self.inventory_repository.delete(inventory_id)

            # Record metrics
            if self.metrics_service:
                await self.metrics_service.increment_counter(
                    name="inventory_items_deleted",
                    value=1,
                    labels={"seller_id": seller_id},
                )

            # Send notification
            if self.notification_service:
                await self.notification_service.send_notification(
                    user_id=seller_id,
                    title="Inventory Item Deleted",
                    message=f"Inventory item deleted: {item.name} (SKU: {item.sku})",
                    data={
                        "item_id": item.id,
                        "sku": item.sku,
                        "name": item.name,
                    },
                    category="inventory",
                )

        except Exception as e:
            logger.error(f"Error deleting inventory item: {str(e)}")

            # Record error metrics
            if self.metrics_service:
                await self.metrics_service.increment_counter(
                    name="inventory_errors",
                    value=1,
                    labels={
                        "operation": "delete_inventory_item",
                        "error_type": type(e).__name__,
                    },
                )

            raise

    async def update_inventory_quantity(
        self, inventory_id: str, seller_id: str, quantity: int
    ) -> None:
        """
        Update inventory quantity.

        Args:
            inventory_id: Inventory item ID
            seller_id: Seller ID
            quantity: New quantity

        Raises:
            ValueError: If the item is not found
        """
        try:
            # Get the item
            item = await self.inventory_repository.find_by_id(inventory_id)
            if not item:
                raise ValueError(f"Inventory item not found: {inventory_id}")

            # Check if the item belongs to the seller
            if item.user_id != seller_id:
                raise ValueError(
                    f"Inventory item {inventory_id} does not belong to seller {seller_id}"
                )

            # Update the quantity
            old_quantity = item.quantity
            await self.inventory_repository.update_quantity(inventory_id, quantity)

            # Record metrics
            if self.metrics_service:
                await self.metrics_service.increment_counter(
                    name="inventory_quantity_updates",
                    value=1,
                    labels={"seller_id": seller_id},
                )

                # Record quantity change
                await self.metrics_service.record_gauge(
                    name="inventory_quantity",
                    value=quantity,
                    labels={
                        "seller_id": seller_id,
                        "item_id": inventory_id,
                        "sku": item.sku,
                    },
                )

            # Send notification if quantity is low
            if self.notification_service and quantity < 5:
                await self.notification_service.send_notification(
                    user_id=seller_id,
                    title="Low Inventory Alert",
                    message=f"Inventory is low for {item.name} (SKU: {item.sku}): {quantity} units remaining",
                    data={
                        "item_id": item.id,
                        "sku": item.sku,
                        "name": item.name,
                        "quantity": quantity,
                        "old_quantity": old_quantity,
                    },
                    category="inventory",
                    priority="high",
                )

        except Exception as e:
            logger.error(f"Error updating inventory quantity: {str(e)}")

            # Record error metrics
            if self.metrics_service:
                await self.metrics_service.increment_counter(
                    name="inventory_errors",
                    value=1,
                    labels={
                        "operation": "update_inventory_quantity",
                        "error_type": type(e).__name__,
                    },
                )

            raise

    async def get_marketplace_ids(self, inventory_id: str) -> Dict[str, str]:
        """
        Get marketplace IDs for an inventory item.

        Args:
            inventory_id: Inventory item ID

        Returns:
            Dictionary mapping marketplace names to marketplace IDs

        Raises:
            ValueError: If the item is not found
        """
        try:
            # Get the item
            item = await self.inventory_repository.find_by_id(inventory_id)
            if not item:
                raise ValueError(f"Inventory item not found: {inventory_id}")

            # Get marketplace IDs from attributes
            marketplace_ids = {}
            attributes = item.attributes or {}

            # Extract marketplace IDs from attributes
            for key, value in attributes.items():
                if key.endswith("_marketplace_id"):
                    marketplace = key.replace("_marketplace_id", "")
                    marketplace_ids[marketplace] = value

            return marketplace_ids

        except Exception as e:
            logger.error(f"Error getting marketplace IDs: {str(e)}")

            # Record error metrics
            if self.metrics_service:
                await self.metrics_service.increment_counter(
                    name="inventory_errors",
                    value=1,
                    labels={
                        "operation": "get_marketplace_ids",
                        "error_type": type(e).__name__,
                    },
                )

            raise

    async def search_inventory(
        self,
        seller_id: str,
        search_term: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Search inventory items.

        Args:
            seller_id: Seller ID
            search_term: Search term
            limit: Maximum number of items to return
            offset: Offset for pagination

        Returns:
            List of matching inventory items
        """
        try:
            # Search items
            items = await self.inventory_repository.search_items(
                user_id=seller_id,
                search_term=search_term,
                limit=limit,
                offset=offset,
            )

            # Convert to dictionaries
            result = [item.to_dict() for item in items]

            # Record metrics
            if self.metrics_service:
                await self.metrics_service.increment_counter(
                    name="inventory_searches",
                    value=1,
                    labels={
                        "seller_id": seller_id,
                        "result_count": str(len(result)),
                    },
                )

            return result

        except Exception as e:
            logger.error(f"Error searching inventory: {str(e)}")

            # Record error metrics
            if self.metrics_service:
                await self.metrics_service.increment_counter(
                    name="inventory_errors",
                    value=1,
                    labels={
                        "operation": "search_inventory",
                        "error_type": type(e).__name__,
                    },
                )

            raise

    async def get_inventory_stats(self, seller_id: str) -> Dict[str, Any]:
        """
        Get inventory statistics.

        Args:
            seller_id: Seller ID

        Returns:
            Dictionary of inventory statistics
        """
        try:
            # Get all items for the seller
            items = await self.inventory_repository.get_by_user_id(seller_id)

            # Calculate statistics
            total_items = len(items)
            total_quantity = sum(item.quantity for item in items)
            total_value = sum(item.quantity * (item.price or 0) for item in items)

            # Count items by category
            categories = {}
            for item in items:
                category = item.category or "Uncategorized"
                if category not in categories:
                    categories[category] = 0
                categories[category] += 1

            # Count low stock items (less than 5 units)
            low_stock_items = sum(1 for item in items if item.quantity < 5)

            # Count out of stock items
            out_of_stock_items = sum(1 for item in items if item.quantity == 0)

            # Return statistics
            return {
                "total_items": total_items,
                "total_quantity": total_quantity,
                "total_value": total_value,
                "categories": categories,
                "low_stock_items": low_stock_items,
                "out_of_stock_items": out_of_stock_items,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting inventory statistics: {str(e)}")

            # Record error metrics
            if self.metrics_service:
                await self.metrics_service.increment_counter(
                    name="inventory_errors",
                    value=1,
                    labels={
                        "operation": "get_inventory_stats",
                        "error_type": type(e).__name__,
                    },
                )

            raise
