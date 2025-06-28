"""Service for marketplace operations."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fs_agt_clean.core.db.database import Database
from fs_agt_clean.core.db.marketplace_repository import MarketplaceRepository
from fs_agt_clean.core.models.database.marketplaces import MarketplaceModel

logger = logging.getLogger(__name__)


class MarketplaceService:
    """Service for marketplace operations."""

    def __init__(self, database: Database):
        """Initialize the service.

        Args:
            database: Database instance
        """
        self.database = database

    async def create_marketplace(
        self, marketplace_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new marketplace.

        Args:
            marketplace_data: Marketplace data

        Returns:
            Dict[str, Any]: Created marketplace data
        """
        async with self.database.get_session() as session:
            repository = MarketplaceRepository(session)
            marketplace_model = await repository.create_marketplace(marketplace_data)
            return marketplace_model.to_dict()

    async def get_marketplace_by_id(
        self, marketplace_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a marketplace by ID.

        Args:
            marketplace_id: Marketplace ID

        Returns:
            Optional[Dict[str, Any]]: Marketplace data if found, None otherwise
        """
        async with self.database.get_session() as session:
            repository = MarketplaceRepository(session)
            marketplace_model = await repository.get_marketplace_by_id(marketplace_id)
            if marketplace_model:
                return marketplace_model.to_dict()
            return None

    async def get_all_marketplaces(self) -> List[Dict[str, Any]]:
        """Get all marketplaces.

        Returns:
            List[Dict[str, Any]]: List of marketplace data
        """
        async with self.database.get_session() as session:
            repository = MarketplaceRepository(session)
            marketplace_models = await repository.get_all_marketplaces()
            return [
                marketplace_model.to_dict() for marketplace_model in marketplace_models
            ]

    async def update_marketplace(
        self, marketplace_id: str, marketplace_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a marketplace.

        Args:
            marketplace_id: Marketplace ID
            marketplace_data: Marketplace data to update

        Returns:
            Optional[Dict[str, Any]]: Updated marketplace data if found, None otherwise
        """
        async with self.database.get_session() as session:
            repository = MarketplaceRepository(session)
            marketplace_model = await repository.update_marketplace(
                marketplace_id, marketplace_data
            )
            if marketplace_model:
                return marketplace_model.to_dict()
            return None

    async def delete_marketplace(self, marketplace_id: str) -> bool:
        """Delete a marketplace.

        Args:
            marketplace_id: Marketplace ID

        Returns:
            bool: True if marketplace was deleted, False otherwise
        """
        async with self.database.get_session() as session:
            repository = MarketplaceRepository(session)
            return await repository.delete_marketplace(marketplace_id)
