"""
Inventory Repository

This module provides database access for inventory management using SQLAlchemy.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fs_agt_clean.database.models.inventory import (
    InventoryAdjustment,
    InventoryItem,
    InventoryLocation,
    InventoryMovement,
    InventoryTransaction,
)

logger = logging.getLogger(__name__)


class InventoryRepository:
    """Repository for inventory data access using SQLAlchemy."""

    def __init__(self, db_session: AsyncSession):
        """Initialize inventory repository with database session."""
        self.db_session = db_session

    # Core CRUD operations for InventoryItem
    async def find_by_id(self, item_id: int) -> Optional[InventoryItem]:
        """Find inventory item by ID."""
        try:
            result = await self.db_session.execute(
                select(InventoryItem)
                .options(selectinload(InventoryItem.transactions))
                .options(selectinload(InventoryItem.adjustments))
                .where(InventoryItem.id == item_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error finding inventory item by ID {item_id}: {e}")
            return None

    async def get_by_sku(self, sku: str) -> Optional[InventoryItem]:
        """Find inventory item by SKU."""
        try:
            result = await self.db_session.execute(
                select(InventoryItem)
                .options(selectinload(InventoryItem.transactions))
                .options(selectinload(InventoryItem.adjustments))
                .where(InventoryItem.sku == sku)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error finding inventory item by SKU {sku}: {e}")
            return None

    async def create_item(self, item_data: Dict[str, Any]) -> InventoryItem:
        """Create a new inventory item."""
        try:
            item = InventoryItem(**item_data)
            self.db_session.add(item)
            await self.db_session.commit()
            await self.db_session.refresh(item)
            return item
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error creating inventory item: {e}")
            raise

    async def update_item(
        self, item_id: int, item_data: Dict[str, Any]
    ) -> Optional[InventoryItem]:
        """Update an inventory item."""
        try:
            item = await self.find_by_id(item_id)
            if not item:
                return None

            for key, value in item_data.items():
                if hasattr(item, key):
                    setattr(item, key, value)

            item.updated_at = datetime.utcnow()
            await self.db_session.commit()
            await self.db_session.refresh(item)
            return item
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error updating inventory item {item_id}: {e}")
            raise

    async def delete(self, item_id: int) -> bool:
        """Delete an inventory item."""
        try:
            item = await self.find_by_id(item_id)
            if not item:
                return False

            await self.db_session.delete(item)
            await self.db_session.commit()
            return True
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error deleting inventory item {item_id}: {e}")
            return False

    async def find_by_criteria(
        self, criteria: Dict[str, Any], limit: int = 100, offset: int = 0
    ) -> List[InventoryItem]:
        """Find inventory items by criteria."""
        try:
            # Optimized query without eager loading for better performance
            query = select(InventoryItem)

            # Apply filters based on criteria
            conditions = []
            for key, value in criteria.items():
                if hasattr(InventoryItem, key) and value is not None:
                    if isinstance(value, str):
                        conditions.append(
                            getattr(InventoryItem, key).ilike(f"%{value}%")
                        )
                    else:
                        conditions.append(getattr(InventoryItem, key) == value)

            if conditions:
                query = query.where(and_(*conditions))

            query = query.offset(offset).limit(limit)
            result = await self.db_session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error finding inventory items by criteria: {e}")
            return []

    async def find_by_criteria_with_relations(
        self, criteria: Dict[str, Any], limit: int = 100, offset: int = 0
    ) -> List[InventoryItem]:
        """Find inventory items by criteria with transactions and adjustments loaded."""
        try:
            # Use this method only when you need the related data
            query = select(InventoryItem).options(
                selectinload(InventoryItem.transactions),
                selectinload(InventoryItem.adjustments),
            )

            # Apply filters based on criteria
            conditions = []
            for key, value in criteria.items():
                if hasattr(InventoryItem, key) and value is not None:
                    if isinstance(value, str):
                        conditions.append(
                            getattr(InventoryItem, key).ilike(f"%{value}%")
                        )
                    else:
                        conditions.append(getattr(InventoryItem, key) == value)

            if conditions:
                query = query.where(and_(*conditions))

            query = query.offset(offset).limit(limit)
            result = await self.db_session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error finding inventory items with relations: {e}")
            return []

    async def search_items(self, query: str, limit: int = 100) -> List[InventoryItem]:
        """Search inventory items by name, SKU, or description."""
        try:
            search_query = (
                select(InventoryItem)
                .where(
                    or_(
                        InventoryItem.name.ilike(f"%{query}%"),
                        InventoryItem.sku.ilike(f"%{query}%"),
                        InventoryItem.description.ilike(f"%{query}%"),
                        InventoryItem.category.ilike(f"%{query}%"),
                    )
                )
                .limit(limit)
            )

            result = await self.db_session.execute(search_query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error searching inventory items: {e}")
            return []

    async def get_by_user_id(
        self, user_id: str, limit: int = 100, offset: int = 0
    ) -> List[InventoryItem]:
        """Get inventory items by user ID (created_by)."""
        try:
            query = (
                select(InventoryItem)
                .where(InventoryItem.created_by == user_id)
                .offset(offset)
                .limit(limit)
            )

            result = await self.db_session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting inventory items by user ID {user_id}: {e}")
            return []

    async def update_quantity(
        self,
        item_id: int,
        new_quantity: int,
        transaction_type: str = "adjustment",
        notes: str = None,
    ) -> bool:
        """Update item quantity and create transaction record."""
        try:
            item = await self.find_by_id(item_id)
            if not item:
                return False

            old_quantity = item.quantity
            quantity_change = new_quantity - old_quantity

            # Update item quantity
            item.quantity = new_quantity
            item.updated_at = datetime.utcnow()

            # Create transaction record
            transaction = InventoryTransaction(
                item_id=item_id,
                transaction_type=transaction_type,
                quantity=quantity_change,
                notes=notes
                or f"Quantity updated from {old_quantity} to {new_quantity}",
            )
            self.db_session.add(transaction)

            # Create adjustment record
            adjustment = InventoryAdjustment(
                item_id=item_id,
                adjustment_type="increase" if quantity_change > 0 else "decrease",
                quantity_before=old_quantity,
                quantity_after=new_quantity,
                quantity_change=quantity_change,
                reason=transaction_type,
                notes=notes,
            )
            self.db_session.add(adjustment)

            await self.db_session.commit()
            return True
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error updating quantity for item {item_id}: {e}")
            return False

    # Legacy methods for backward compatibility
    async def get_inventory_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get inventory item by ID (legacy method)."""
        try:
            item_id_int = int(item_id)
            item = await self.find_by_id(item_id_int)
            if item:
                return self._item_to_dict(item)
            return None
        except (ValueError, TypeError):
            logger.error(f"Invalid item ID format: {item_id}")
            return None

    async def create_inventory_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new inventory item (legacy method)."""
        item = await self.create_item(item_data)
        return self._item_to_dict(item)

    async def update_inventory_item(
        self, item_id: str, item_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update an inventory item (legacy method)."""
        try:
            item_id_int = int(item_id)
            item = await self.update_item(item_id_int, item_data)
            if item:
                return self._item_to_dict(item)
            return None
        except (ValueError, TypeError):
            logger.error(f"Invalid item ID format: {item_id}")
            return None

    async def delete_inventory_item(self, item_id: str) -> bool:
        """Delete an inventory item (legacy method)."""
        try:
            item_id_int = int(item_id)
            return await self.delete(item_id_int)
        except (ValueError, TypeError):
            logger.error(f"Invalid item ID format: {item_id}")
            return False

    async def list_inventory_items(
        self, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List inventory items (legacy method)."""
        items = await self.find_by_criteria({}, limit=limit, offset=offset)
        return [self._item_to_dict(item) for item in items]

    async def search_inventory_items(self, query: str) -> List[Dict[str, Any]]:
        """Search inventory items (legacy method)."""
        items = await self.search_items(query)
        return [self._item_to_dict(item) for item in items]

    def _item_to_dict(self, item: InventoryItem) -> Dict[str, Any]:
        """Convert InventoryItem to dictionary."""
        return {
            "id": str(item.id),
            "sku": item.sku,
            "name": item.name,
            "description": item.description,
            "category": item.category,
            "quantity": item.quantity,
            "price": float(item.price) if item.price else None,
            "cost": float(item.cost) if item.cost else None,
            "weight": float(item.weight) if item.weight else None,
            "dimensions": item.dimensions,
            "location": item.location,
            "supplier": item.supplier,
            "barcode": item.barcode,
            "status": "active" if item.is_active else "inactive",
            "low_stock_threshold": item.low_stock_threshold,
            "reorder_point": item.reorder_point,
            "reorder_quantity": item.reorder_quantity,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            "created_by": item.created_by,
            "updated_by": item.updated_by,
        }
