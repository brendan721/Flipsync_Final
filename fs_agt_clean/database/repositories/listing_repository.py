"""
Listing repository for database operations.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    and_,
    delete,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from fs_agt_clean.core.db.database import get_database
from fs_agt_clean.database.models.unified_base import Base


class ListingModel(Base):
    """Database model for listings."""

    __tablename__ = "listings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(500), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    status = Column(String(50), nullable=False, default="draft")
    marketplace_id = Column(String(36), ForeignKey("marketplaces.id"), nullable=False)
    marketplace_listing_id = Column(String(255))  # External marketplace ID
    sku = Column(String(255))
    quantity = Column(Integer, nullable=False, default=1)
    category = Column(String(255))
    images = Column(JSONB, nullable=False, default=[])
    listing_metadata = Column(JSONB, nullable=False, default={})
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class ListingRepository:
    """Repository for listing operations."""

    def __init__(self, session: Optional[AsyncSession] = None):
        """Initialize repository with optional session."""
        self.session = session

    async def _get_session(self) -> AsyncSession:
        """Get database session."""
        if self.session:
            return self.session
        return await get_database().get_session()

    async def create_listing(
        self, listing_data: Dict[str, Any]
    ) -> Optional[ListingModel]:
        """Create a new listing."""
        try:
            session = await self._get_session()
            listing = ListingModel(
                id=str(uuid.uuid4()),
                title=listing_data.get("title"),
                description=listing_data.get("description"),
                price=listing_data.get("price"),
                currency=listing_data.get("currency", "USD"),
                status=listing_data.get("status", "draft"),
                marketplace_id=listing_data.get("marketplace_id"),
                marketplace_listing_id=listing_data.get("marketplace_listing_id"),
                sku=listing_data.get("sku"),
                quantity=listing_data.get("quantity", 1),
                category=listing_data.get("category"),
                images=listing_data.get("images", []),
                listing_metadata=listing_data.get("metadata", {}),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            session.add(listing)
            await session.commit()
            await session.refresh(listing)
            return listing
        except SQLAlchemyError as e:
            print(f"Error creating listing: {e}")
            if session:
                await session.rollback()
            return None

    async def find_by_criteria(self, criteria: Dict[str, Any]) -> List[ListingModel]:
        """Find listings by criteria."""
        try:
            session = await self._get_session()
            query = select(ListingModel)

            # Build where conditions based on criteria
            conditions = []

            if "marketplace_id" in criteria:
                conditions.append(
                    ListingModel.marketplace_id == criteria["marketplace_id"]
                )

            if "status" in criteria:
                conditions.append(ListingModel.status == criteria["status"])

            if "sku" in criteria:
                conditions.append(ListingModel.sku == criteria["sku"])

            if "marketplace_listing_id" in criteria:
                conditions.append(
                    ListingModel.marketplace_listing_id
                    == criteria["marketplace_listing_id"]
                )

            if conditions:
                query = query.where(and_(*conditions))

            result = await session.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"Error finding listings by criteria: {e}")
            return []

    async def update_quantity(self, listing_id: str, quantity: int) -> bool:
        """Update listing quantity."""
        try:
            session = await self._get_session()
            result = await session.execute(
                update(ListingModel)
                .where(ListingModel.id == listing_id)
                .values(quantity=quantity, updated_at=datetime.now(timezone.utc))
            )
            await session.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            print(f"Error updating listing quantity: {e}")
            if session:
                await session.rollback()
            return False


__all__ = ["ListingRepository", "ListingModel"]
