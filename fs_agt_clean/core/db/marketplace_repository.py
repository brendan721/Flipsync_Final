"""Repository for marketplace database operations."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from fs_agt_clean.core.models.database.marketplaces import MarketplaceModel

logger = logging.getLogger(__name__)


class MarketplaceRepository:
    """Repository for marketplace-related database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository with a database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create_marketplace(
        self, marketplace_data: Dict[str, Any]
    ) -> MarketplaceModel:
        """Create a new marketplace.

        Args:
            marketplace_data: Marketplace data

        Returns:
            MarketplaceModel: Created marketplace
        """
        # Create a new marketplace model
        marketplace_model = MarketplaceModel(
            **marketplace_data,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Add to session and commit
        self.session.add(marketplace_model)
        await self.session.commit()
        await self.session.refresh(marketplace_model)

        return marketplace_model

    async def get_marketplace_by_id(
        self, marketplace_id: str
    ) -> Optional[MarketplaceModel]:
        """Get a marketplace by ID.

        Args:
            marketplace_id: Marketplace ID

        Returns:
            MarketplaceModel: Marketplace if found, None otherwise
        """
        # Query the database
        result = await self.session.execute(
            select(MarketplaceModel).where(MarketplaceModel.id == marketplace_id)
        )
        return result.scalars().first()

    async def get_all_marketplaces(self) -> List[MarketplaceModel]:
        """Get all marketplaces.

        Returns:
            List[MarketplaceModel]: List of marketplaces
        """
        # Query the database
        result = await self.session.execute(select(MarketplaceModel))
        return result.scalars().all()

    async def update_marketplace(
        self, marketplace_id: str, marketplace_data: Dict[str, Any]
    ) -> Optional[MarketplaceModel]:
        """Update a marketplace.

        Args:
            marketplace_id: Marketplace ID
            marketplace_data: Marketplace data to update

        Returns:
            MarketplaceModel: Updated marketplace if found, None otherwise
        """
        # Query the database
        result = await self.session.execute(
            select(MarketplaceModel).where(MarketplaceModel.id == marketplace_id)
        )
        marketplace_model = result.scalars().first()

        if not marketplace_model:
            return None

        # Update fields
        for key, value in marketplace_data.items():
            if hasattr(marketplace_model, key):
                setattr(marketplace_model, key, value)

        marketplace_model.updated_at = datetime.now(timezone.utc)

        # Commit changes
        await self.session.commit()
        await self.session.refresh(marketplace_model)

        return marketplace_model

    async def delete_marketplace(self, marketplace_id: str) -> bool:
        """Delete a marketplace.

        Args:
            marketplace_id: Marketplace ID

        Returns:
            bool: True if marketplace was deleted, False otherwise
        """
        # Delete the marketplace
        result = await self.session.execute(
            delete(MarketplaceModel).where(MarketplaceModel.id == marketplace_id)
        )
        await self.session.commit()

        # Check if any rows were deleted
        return result.rowcount > 0 if hasattr(result, "rowcount") else True
