"""
Inventory Service Adapter

This adapter provides a simplified interface for the inventory API routes
that matches the expected method signatures.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fs_agt_clean.core.db.database import Database
from fs_agt_clean.database.repositories.inventory_repository import InventoryRepository

logger = logging.getLogger(__name__)


class InventoryServiceAdapter:
    """Adapter for inventory service that matches API route expectations."""

    def __init__(self, database: Database):
        """Initialize the inventory service adapter."""
        self.database = database

    async def get_items(
        self, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all inventory items."""
        try:
            async with self.database.get_session_context() as session:
                repository = InventoryRepository(session)
                items = await repository.find_by_criteria(
                    {}, limit=limit, offset=offset
                )
                return [repository._item_to_dict(item) for item in items]
        except Exception as e:
            logger.error(f"Error getting inventory items: {e}")
            return []

    async def get_item_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get inventory item by ID."""
        try:
            async with self.database.get_session_context() as session:
                repository = InventoryRepository(session)
                item = await repository.find_by_id(int(item_id))
                if item:
                    return repository._item_to_dict(item)
                return None
        except Exception as e:
            logger.error(f"Error getting inventory item {item_id}: {e}")
            return None

    async def get_item_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """Get inventory item by SKU."""
        try:
            async with self.database.get_session_context() as session:
                repository = InventoryRepository(session)
                item = await repository.get_by_sku(sku)
                if item:
                    return repository._item_to_dict(item)
                return None
        except Exception as e:
            logger.error(f"Error getting inventory item by SKU {sku}: {e}")
            return None

    async def create_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new inventory item."""
        try:
            async with self.database.get_session_context() as session:
                repository = InventoryRepository(session)

                # Check if SKU already exists
                if "sku" in item_data:
                    existing = await repository.get_by_sku(item_data["sku"])
                    if existing:
                        raise ValueError(
                            f"Item with SKU {item_data['sku']} already exists"
                        )

                # Set default values
                item_data.setdefault("quantity", 0)
                item_data.setdefault("is_active", True)
                item_data.setdefault("created_by", "system")

                item = await repository.create_item(item_data)
                return repository._item_to_dict(item)
        except Exception as e:
            logger.error(f"Error creating inventory item: {e}")
            raise

    async def update_item(
        self, item_id: str, item_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update an inventory item."""
        try:
            async with self.database.get_session_context() as session:
                repository = InventoryRepository(session)

                # Set updated_by if not provided
                item_data.setdefault("updated_by", "system")

                item = await repository.update_item(int(item_id), item_data)
                if item:
                    return repository._item_to_dict(item)
                return None
        except Exception as e:
            logger.error(f"Error updating inventory item {item_id}: {e}")
            raise

    async def delete_item(self, item_id: str) -> bool:
        """Delete an inventory item."""
        try:
            async with self.database.get_session_context() as session:
                repository = InventoryRepository(session)
                return await repository.delete(int(item_id))
        except Exception as e:
            logger.error(f"Error deleting inventory item {item_id}: {e}")
            return False

    async def adjust_quantity(
        self, item_id: str, adjustment_data: Dict[str, Any]
    ) -> bool:
        """Adjust inventory quantity."""
        try:
            async with self.database.get_session_context() as session:
                repository = InventoryRepository(session)

                quantity = adjustment_data.get("quantity", 0)
                transaction_type = adjustment_data.get("transaction_type", "adjustment")
                notes = adjustment_data.get("notes", "Manual adjustment")

                # Get current item to calculate new quantity
                item = await repository.find_by_id(int(item_id))
                if not item:
                    return False

                # Calculate new quantity based on adjustment type
                if adjustment_data.get("adjustment_type") == "set":
                    new_quantity = quantity
                else:
                    new_quantity = item.quantity + quantity

                # Ensure quantity doesn't go negative
                new_quantity = max(0, new_quantity)

                return await repository.update_quantity(
                    int(item_id), new_quantity, transaction_type, notes
                )
        except Exception as e:
            logger.error(f"Error adjusting inventory quantity for item {item_id}: {e}")
            return False

    async def get_transactions(self, item_id: str) -> List[Dict[str, Any]]:
        """Get transactions for an inventory item."""
        try:
            async with self.database.get_session_context() as session:
                repository = InventoryRepository(session)
                item = await repository.find_by_id(int(item_id))
                if not item:
                    return []

                # Convert transactions to dictionaries
                transactions = []
                for transaction in item.transactions:
                    transactions.append(
                        {
                            "id": transaction.id,
                            "item_id": transaction.item_id,
                            "transaction_type": transaction.transaction_type,
                            "quantity": transaction.quantity,
                            "unit_price": (
                                float(transaction.unit_price)
                                if transaction.unit_price
                                else None
                            ),
                            "total_amount": (
                                float(transaction.total_amount)
                                if transaction.total_amount
                                else None
                            ),
                            "reference_id": transaction.reference_id,
                            "reference_type": transaction.reference_type,
                            "notes": transaction.notes,
                            "transaction_date": (
                                transaction.transaction_date.isoformat()
                                if transaction.transaction_date
                                else None
                            ),
                            "created_at": (
                                transaction.created_at.isoformat()
                                if transaction.created_at
                                else None
                            ),
                            "created_by": transaction.created_by,
                        }
                    )

                return transactions
        except Exception as e:
            logger.error(f"Error getting transactions for item {item_id}: {e}")
            return []

    async def search_items(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Search inventory items."""
        try:
            async with self.database.get_session_context() as session:
                repository = InventoryRepository(session)
                items = await repository.search_items(query, limit)
                return [repository._item_to_dict(item) for item in items]
        except Exception as e:
            logger.error(f"Error searching inventory items: {e}")
            return []
