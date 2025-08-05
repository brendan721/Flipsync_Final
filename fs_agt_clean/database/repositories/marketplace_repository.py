"""Repository for marketplace database operations."""

import logging
import base64
import httpx
from datetime import datetime, timezone, timedelta
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

    async def refresh_ebay_tokens(self, user_id: str) -> bool:
        """Refresh expired eBay OAuth tokens using the stored refresh token.

        Args:
            user_id: User ID to refresh tokens for

        Returns:
            bool: True if refresh was successful, False otherwise
        """
        try:
            # Get the marketplace connection
            marketplace = await self.get_by_type(
                user_id=user_id, marketplace_type="ebay"
            )
            if not marketplace or not marketplace.refresh_token:
                logger.error(
                    f"No eBay marketplace or refresh token found for user {user_id}"
                )
                return False

            # Get eBay credentials from connection metadata
            client_id = marketplace.connection_metadata.get("client_id")
            if not client_id:
                logger.error(
                    f"No client_id found in connection metadata for user {user_id}"
                )
                return False

            # Get client secret from environment (for security)
            import os

            client_secret = os.getenv("EBAY_CLIENT_SECRET")
            if not client_secret:
                logger.error("EBAY_CLIENT_SECRET not found in environment")
                return False

            logger.info(f"Attempting to refresh eBay tokens for user {user_id}")

            # Prepare refresh request
            credentials = f"{client_id}:{client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()

            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {encoded_credentials}",
            }

            data = {
                "grant_type": "refresh_token",
                "refresh_token": marketplace.refresh_token,
            }

            # Make refresh request to eBay
            token_url = "https://api.ebay.com/identity/v1/oauth2/token"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    token_url, headers=headers, data=data, timeout=30.0
                )

                if response.status_code != 200:
                    logger.error(
                        f"eBay token refresh failed for user {user_id}: "
                        f"HTTP {response.status_code} - {response.text}"
                    )
                    return False

                token_data = response.json()

            # Update marketplace connection with new tokens
            new_expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=token_data.get("expires_in", 7200)
            )

            marketplace.access_token = token_data["access_token"]
            marketplace.token_expires_at = new_expires_at
            marketplace.updated_at = datetime.now(timezone.utc)

            # Update refresh token if provided (eBay sometimes provides new refresh tokens)
            if token_data.get("refresh_token"):
                marketplace.refresh_token = token_data["refresh_token"]

            await self.session.commit()

            logger.info(
                f"Successfully refreshed eBay tokens for user {user_id}, "
                f"new expiry: {new_expires_at}"
            )
            return True

        except Exception as e:
            logger.error(f"Error refreshing eBay tokens for user {user_id}: {e}")
            await self.session.rollback()
            return False

    async def check_and_refresh_ebay_tokens(
        self, user_id: str, refresh_threshold_minutes: int = 30
    ) -> bool:
        """Check if eBay tokens need refresh and refresh them if necessary.

        Args:
            user_id: User ID to check tokens for
            refresh_threshold_minutes: Refresh tokens if they expire within this many minutes

        Returns:
            bool: True if tokens are valid (either already valid or successfully refreshed)
        """
        try:
            marketplace = await self.get_by_type(
                user_id=user_id, marketplace_type="ebay"
            )
            if not marketplace:
                logger.warning(f"No eBay marketplace found for user {user_id}")
                return False

            # Check if tokens are already expired or will expire soon
            if marketplace.token_expires_at:
                threshold_time = datetime.now(timezone.utc) + timedelta(
                    minutes=refresh_threshold_minutes
                )

                if marketplace.token_expires_at <= threshold_time:
                    logger.info(
                        f"eBay tokens for user {user_id} expire at {marketplace.token_expires_at}, "
                        f"refreshing proactively (threshold: {refresh_threshold_minutes} minutes)"
                    )
                    return await self.refresh_ebay_tokens(user_id)
                else:
                    logger.debug(
                        f"eBay tokens for user {user_id} are still valid until {marketplace.token_expires_at}"
                    )
                    return True
            else:
                logger.warning(f"No token expiry information for user {user_id}")
                return bool(marketplace.access_token)

        except Exception as e:
            logger.error(f"Error checking eBay tokens for user {user_id}: {e}")
            return False

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
