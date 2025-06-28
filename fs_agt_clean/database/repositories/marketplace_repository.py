"""Repository for marketplace database operations."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from fs_agt_clean.core.models.database.marketplaces import (
    MarketplaceModel,
    MarketplaceConnectionModel,
)

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

    # Marketplace Connection Methods
    async def create_marketplace_connection(
        self, connection_data: Dict[str, Any]
    ) -> MarketplaceConnectionModel:
        """Create a new marketplace connection.

        Args:
            connection_data: Connection data

        Returns:
            MarketplaceConnectionModel: Created connection
        """
        # Create a new connection model
        connection_model = MarketplaceConnectionModel(
            **connection_data,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Add to session and commit
        self.session.add(connection_model)
        await self.session.commit()
        await self.session.refresh(connection_model)

        return connection_model

    async def get_marketplace_connection_by_user_and_type(
        self, user_id: str, marketplace_type: str
    ) -> Optional[MarketplaceConnectionModel]:
        """Get a marketplace connection by user ID and marketplace type.

        Args:
            user_id: User ID
            marketplace_type: Marketplace type ('ebay', 'amazon', etc.)

        Returns:
            MarketplaceConnectionModel: Connection if found, None otherwise
        """
        result = await self.session.execute(
            select(MarketplaceConnectionModel).where(
                MarketplaceConnectionModel.user_id == user_id,
                MarketplaceConnectionModel.marketplace_type == marketplace_type,
                MarketplaceConnectionModel.is_active == True,
            )
        )
        return result.scalars().first()

    async def get_by_type(
        self, user_id: str, marketplace_type: str
    ) -> Optional[MarketplaceConnectionModel]:
        """Get a marketplace connection by user ID and marketplace type (alias for compatibility).

        Args:
            user_id: User ID
            marketplace_type: Marketplace type ('ebay', 'amazon', etc.)

        Returns:
            MarketplaceConnectionModel: Connection if found, None otherwise
        """
        return await self.get_marketplace_connection_by_user_and_type(
            user_id, marketplace_type
        )

    async def get_marketplace_connections_by_user(
        self, user_id: str
    ) -> List[MarketplaceConnectionModel]:
        """Get all marketplace connections for a user.

        Args:
            user_id: User ID

        Returns:
            List[MarketplaceConnectionModel]: List of connections
        """
        result = await self.session.execute(
            select(MarketplaceConnectionModel).where(
                MarketplaceConnectionModel.user_id == user_id,
                MarketplaceConnectionModel.is_active == True,
            )
        )
        return result.scalars().all()

    async def update_marketplace_connection(
        self, connection_id: str, connection_data: Dict[str, Any]
    ) -> Optional[MarketplaceConnectionModel]:
        """Update a marketplace connection.

        Args:
            connection_id: Connection ID
            connection_data: Connection data to update

        Returns:
            MarketplaceConnectionModel: Updated connection if found, None otherwise
        """
        result = await self.session.execute(
            select(MarketplaceConnectionModel).where(
                MarketplaceConnectionModel.id == connection_id
            )
        )
        connection_model = result.scalars().first()

        if not connection_model:
            return None

        # Update fields
        for key, value in connection_data.items():
            if hasattr(connection_model, key):
                setattr(connection_model, key, value)

        connection_model.updated_at = datetime.now(timezone.utc)

        # Commit changes
        await self.session.commit()
        await self.session.refresh(connection_model)

        return connection_model

    async def delete_marketplace_connection(self, connection_id: str) -> bool:
        """Delete a marketplace connection.

        Args:
            connection_id: Connection ID

        Returns:
            bool: True if connection was deleted, False otherwise
        """
        result = await self.session.execute(
            delete(MarketplaceConnectionModel).where(
                MarketplaceConnectionModel.id == connection_id
            )
        )
        await self.session.commit()

        return result.rowcount > 0 if hasattr(result, "rowcount") else True
