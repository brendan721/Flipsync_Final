"""Inventory management service."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fs_agt_clean.core.config.manager import ConfigManager
from fs_agt_clean.services.inventory.optimizer import InventoryOptimizer
from fs_agt_clean.services.inventory.service import (
    InventoryItem,
    InventoryTransaction,
    StockLevel,
    StorageLocation,
)
from fs_agt_clean.services.inventory.tracker import InventoryTracker

logger = logging.getLogger(__name__)


class InventoryManager:
    """Manages inventory operations."""

    def __init__(
        self,
        config_manager: ConfigManager,
        ai_marketing_agent: Optional[Any] = None,
    ):
        """Initialize manager.

        Args:
            config_manager: Configuration manager
            ai_marketing_agent: Optional AI marketing agent
        """
        inventory_config = config_manager.get("inventory", {})
        self.notification_interval = inventory_config.get("notification_interval", 3600)
        self.items: Dict[str, InventoryItem] = {}
        self.transactions: List[InventoryTransaction] = []
        self.storage_layout: Dict[str, List[str]] = {
            "warehouse": [],
            "retail": [],
        }
        self.optimizer = InventoryOptimizer(config_manager)
        self.tracker = InventoryTracker()
        self.ai_marketing_agent = ai_marketing_agent
        self._background_task = None

    async def start(self) -> None:
        """Start background tasks."""
        self._background_task = asyncio.create_task(self._run_background_tasks())

    async def stop(self) -> None:
        """Stop background tasks."""
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
            finally:
                self._background_task = None

    async def add_item(self, item_data: Dict[str, Any]) -> InventoryItem:
        """Add new inventory item.

        Args:
            item_data: Item data

        Returns:
            Created inventory item
        """
        if not self._validate_item_data(item_data):
            raise ValueError("Invalid item data")

        item_id = item_data.get("id") or f"item_{datetime.now().timestamp()}"
        if item_id in self.items:
            raise ValueError(f"Item {item_id} already exists")

        # Check for duplicate SKU
        if "metadata" in item_data and "sku" in item_data["metadata"]:
            sku = item_data["metadata"]["sku"]
            for existing_item in self.items.values():
                if existing_item.metadata and existing_item.metadata.get("sku") == sku:
                    raise ValueError(f"Item with SKU {sku} already exists")

        item = InventoryItem(
            id=item_id,
            name=item_data["name"],
            description=item_data.get("description", ""),
            quantity=item_data["quantity"],
            initial_quantity=item_data["quantity"],
            price=item_data["price"],
            category=item_data["category"],
            location=item_data.get("location", "warehouse"),
            metadata=item_data.get("metadata"),
        )

        self.items[item.id] = item
        self.storage_layout[item.location].append(item.id)
        await self._record_transaction(
            item.id, item.quantity, "add", "Initial inventory addition"
        )

        return item

    async def update_item(self, item_id: str, updates: Dict[str, Any]) -> InventoryItem:
        """Update inventory item.

        Args:
            item_id: Item ID
            updates: Update data

        Returns:
            Updated inventory item
        """
        if item_id not in self.items:
            raise ValueError(f"Item {item_id} not found")

        item = self.items[item_id]
        old_location = item.location

        for key, value in updates.items():
            if hasattr(item, key):
                setattr(item, key, value)

        if self._is_significant_update(updates):
            item.updated_at = datetime.now()

        # Handle location change
        if "location" in updates and updates["location"] != old_location:
            self.storage_layout[old_location].remove(item_id)
            self.storage_layout[item.location].append(item_id)

        await self._record_transaction(
            item.id, updates.get("quantity", 0), "update", "Item update"
        )

        return item

    async def delete_item(self, item_id: str) -> None:
        """Delete inventory item.

        Args:
            item_id: Item ID
        """
        if item_id not in self.items:
            raise ValueError(f"Item {item_id} not found")

        item = self.items[item_id]
        self.storage_layout[item.location].remove(item_id)
        del self.items[item_id]

        await self._record_transaction(item_id, 0, "delete", "Item deletion")

    def display_inventory(self) -> List[Dict[str, Any]]:
        """Get inventory display data.

        Returns:
            List of inventory items
        """
        return [
            {
                "id": item.id,
                "name": item.name,
                "quantity": item.quantity,
                "location": item.location,
                "stock_level": item.stock_level.name,
                "last_updated": item.updated_at.isoformat(),
            }
            for item in self.items.values()
        ]

    async def provide_marketing_options(self, item_id: str) -> Dict[str, Any]:
        """Get marketing options for item.

        Args:
            item_id: Item ID

        Returns:
            Marketing recommendations
        """
        if item_id not in self.items:
            raise ValueError(f"Item {item_id} not found")

        if not self.ai_marketing_agent:
            return {"error": "AI marketing agent not configured"}

        item = self.items[item_id]
        item_data = {
            "id": item.id,
            "name": item.name,
            "category": item.category,
            "price": item.price,
            "stock_level": item.stock_level.name,
            "sales_velocity": item.sales_velocity,
        }

        return await self.ai_marketing_agent.get_recommendations(item_data)

    async def optimize_storage(self) -> Dict[str, List[str]]:
        """Optimize storage layout.

        Returns:
            Optimized layout
        """
        items = list(self.items.values())
        optimized_layout = await self.optimizer.optimize_storage(
            items, self.storage_layout
        )

        # Apply optimized layout
        self.storage_layout = optimized_layout
        for item in items:
            for location, item_ids in optimized_layout.items():
                if item.id in item_ids:
                    item.location = location
                    break

        return optimized_layout

    async def _run_background_tasks(self) -> None:
        """Run background maintenance tasks."""
        try:
            while True:
                try:
                    await self._check_stock_levels()
                    await self._update_sales_metrics()
                    await asyncio.sleep(self.notification_interval)
                except asyncio.CancelledError:
                    raise  # Re-raise CancelledError to be caught by outer try
                except Exception as e:
                    logger.error("Error in background tasks: %s", e)
                    await asyncio.sleep(60)  # Wait before retrying
        except asyncio.CancelledError:
            # Clean up if needed
            raise  # Re-raise to mark task as cancelled

    async def _check_stock_levels(self) -> None:
        """Check and update stock levels."""
        for item in self.items.values():
            reorder_point = self.optimizer.calculate_reorder_point(item)
            if item.quantity <= reorder_point:
                item.stock_level = StockLevel.LOW
                logger.warning(
                    "Low stock alert: %s (%s units remaining)", item.name, item.quantity
                )

            elif item.quantity >= item.initial_quantity:
                item.stock_level = StockLevel.HIGH
            else:
                item.stock_level = StockLevel.MEDIUM

    async def _update_sales_metrics(self) -> None:
        """Update sales-related metrics."""
        for item in self.items.values():
            # Calculate sales velocity (units sold per day)
            sales_transactions = [
                t
                for t in self.transactions
                if t.item_id == item.id and t.transaction_type == "sale"
            ]
            if sales_transactions:
                total_sold = sum(t.quantity for t in sales_transactions)
                days_since_first_sale = (
                    datetime.now() - sales_transactions[0].timestamp
                ).days or 1
                item.sales_velocity = total_sold / days_since_first_sale

    async def _record_transaction(
        self,
        item_id: str,
        quantity: int,
        transaction_type: str,
        notes: Optional[str] = None,
    ) -> None:
        """Record inventory transaction.

        Args:
            item_id: Item ID
            quantity: Transaction quantity
            transaction_type: Type of transaction
            notes: Optional notes
        """
        transaction = InventoryTransaction(
            id=f"txn_{datetime.now().timestamp()}",
            item_id=item_id,
            quantity=quantity,
            transaction_type=transaction_type,
            notes=notes,
        )
        self.transactions.append(transaction)
        await self.tracker.track_transaction(transaction)

    def _validate_item_data(self, data: Dict[str, Any]) -> bool:
        """Validate item data.

        Args:
            data: Item data

        Returns:
            Whether data is valid
        """
        required_fields = {"name", "quantity", "price", "category"}
        return bool(all(field in data for field in required_fields))

    def _validate_storage_layout(self) -> bool:
        """Validate storage layout.

        Returns:
            Whether layout is valid
        """
        all_items = set()
        for items in self.storage_layout.values():
            if not all(item_id in self.items for item_id in items):
                return False
            all_items.update(items)
        return bool(all_items == set(self.items.keys()))

    def _is_significant_update(self, updates: Dict[str, Any]) -> bool:
        """Check if update is significant.

        Args:
            updates: Update data

        Returns:
            Whether update is significant
        """
        significant_fields = {"quantity", "price", "location", "stock_level"}
        return bool(significant_fields.intersection(updates.keys()))
