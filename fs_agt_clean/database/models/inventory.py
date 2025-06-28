"""SQLAlchemy models for inventory management."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from fs_agt_clean.core.db.database import Base


class InventoryItem(Base):
    """SQLAlchemy model for inventory items."""

    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    quantity = Column(Integer, default=0, nullable=False)
    price = Column(Numeric(10, 2))
    cost = Column(Numeric(10, 2))
    weight = Column(Numeric(8, 3))
    dimensions = Column(String(100))  # Format: "LxWxH"
    location = Column(String(100))
    supplier = Column(String(255))
    barcode = Column(String(100))
    is_active = Column(Boolean, default=True, nullable=False)
    low_stock_threshold = Column(Integer, default=10)
    reorder_point = Column(Integer, default=5)
    reorder_quantity = Column(Integer, default=50)

    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    created_by = Column(String(100))
    updated_by = Column(String(100))

    # Relationships
    transactions = relationship(
        "InventoryTransaction", back_populates="item", cascade="all, delete-orphan"
    )
    adjustments = relationship(
        "InventoryAdjustment", back_populates="item", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<InventoryItem(id={self.id}, sku='{self.sku}', name='{self.name}', quantity={self.quantity})>"


class InventoryTransaction(Base):
    """SQLAlchemy model for inventory transactions."""

    __tablename__ = "inventory_transactions"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    transaction_type = Column(
        String(50), nullable=False
    )  # 'sale', 'purchase', 'adjustment', 'return', 'transfer'
    quantity = Column(
        Integer, nullable=False
    )  # Positive for inbound, negative for outbound
    unit_price = Column(Numeric(10, 2))
    total_amount = Column(Numeric(12, 2))
    reference_id = Column(String(100))  # Order ID, PO number, etc.
    reference_type = Column(String(50))  # 'order', 'purchase_order', 'manual', etc.
    notes = Column(Text)

    # Metadata
    transaction_date = Column(DateTime, default=func.now(), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    created_by = Column(String(100))

    # Relationships
    item = relationship("InventoryItem", back_populates="transactions")

    def __repr__(self):
        return f"<InventoryTransaction(id={self.id}, item_id={self.item_id}, type='{self.transaction_type}', quantity={self.quantity})>"


class InventoryAdjustment(Base):
    """SQLAlchemy model for inventory adjustments."""

    __tablename__ = "inventory_adjustments"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    adjustment_type = Column(
        String(50), nullable=False
    )  # 'increase', 'decrease', 'correction'
    quantity_before = Column(Integer, nullable=False)
    quantity_after = Column(Integer, nullable=False)
    quantity_change = Column(Integer, nullable=False)
    reason = Column(String(255))
    notes = Column(Text)

    # Metadata
    adjustment_date = Column(DateTime, default=func.now(), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    created_by = Column(String(100))
    approved_by = Column(String(100))
    approved_at = Column(DateTime)

    # Relationships
    item = relationship("InventoryItem", back_populates="adjustments")

    def __repr__(self):
        return f"<InventoryAdjustment(id={self.id}, item_id={self.item_id}, change={self.quantity_change})>"


class InventoryLocation(Base):
    """SQLAlchemy model for inventory locations/warehouses."""

    __tablename__ = "inventory_locations"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    address = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self):
        return (
            f"<InventoryLocation(id={self.id}, code='{self.code}', name='{self.name}')>"
        )


class InventoryMovement(Base):
    """SQLAlchemy model for inventory movements between locations."""

    __tablename__ = "inventory_movements"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    from_location_id = Column(Integer, ForeignKey("inventory_locations.id"))
    to_location_id = Column(Integer, ForeignKey("inventory_locations.id"))
    quantity = Column(Integer, nullable=False)
    movement_type = Column(
        String(50), nullable=False
    )  # 'transfer', 'receipt', 'shipment'
    reference_id = Column(String(100))
    notes = Column(Text)

    # Metadata
    movement_date = Column(DateTime, default=func.now(), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    created_by = Column(String(100))

    # Relationships
    item = relationship("InventoryItem")
    from_location = relationship("InventoryLocation", foreign_keys=[from_location_id])
    to_location = relationship("InventoryLocation", foreign_keys=[to_location_id])

    def __repr__(self):
        return f"<InventoryMovement(id={self.id}, item_id={self.item_id}, quantity={self.quantity})>"
