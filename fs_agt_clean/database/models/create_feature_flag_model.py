#!/usr/bin/env python3
"""
Script to create feature flag model and repository.
"""

import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_feature_flag_model():
    """Create feature flag model."""
    model_dir = "fs_agt/core/models/database"
    os.makedirs(model_dir, exist_ok=True)

    model_content = """\"\"\"Database model for feature flags.\"\"\"

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, DateTime, String, Text, Boolean, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY
from sqlalchemy.orm import relationship

from fs_agt_clean.database.models.unified_base import Base


class FeatureFlagModel(Base):
    \"\"\"Database model for feature flags.\"\"\"

    __tablename__ = "feature_flags"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    enabled = Column(Boolean, default=False)
    environment = Column(String(50), nullable=False, default="development")
    owner = Column(String(255))
    tags = Column(ARRAY(String), default=[])
    conditions = Column(JSONB, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def __init__(
        self,
        id: Optional[str] = None,
        key: str = "",
        name: str = "",
        description: Optional[str] = None,
        enabled: bool = False,
        environment: str = "development",
        owner: Optional[str] = None,
        tags: Optional[List[str]] = None,
        conditions: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        \"\"\"Initialize a feature flag model.

        Args:
            id: Feature flag ID (defaults to a new UUID)
            key: Feature flag key (unique identifier)
            name: Feature flag name
            description: Feature flag description
            enabled: Whether the feature flag is enabled
            environment: Environment (development, staging, production)
            owner: Owner of the feature flag
            tags: Tags for the feature flag
            conditions: Conditions for the feature flag
            created_at: Creation timestamp
            updated_at: Last update timestamp
        \"\"\"
        self.id = id or str(uuid.uuid4())
        self.key = key
        self.name = name
        self.description = description
        self.enabled = enabled
        self.environment = environment
        self.owner = owner
        self.tags = tags or []
        self.conditions = conditions
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        \"\"\"Convert to dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation
        \"\"\"
        return {
            "id": self.id,
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "environment": self.environment,
            "owner": self.owner,
            "tags": self.tags,
            "conditions": self.conditions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
"""

    model_path = os.path.join(model_dir, "feature_flags.py")
    with open(model_path, "w", encoding="utf-8") as f:
        f.write(model_content)

    logger.info(f"Created feature flag model: {model_path}")


def create_feature_flag_repository():
    """Create feature flag repository."""
    repo_dir = "fs_agt/core/db"
    os.makedirs(repo_dir, exist_ok=True)

    repo_content = """\"\"\"Repository for feature flag database operations.\"\"\"

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from fs_agt_clean.core.models.database.feature_flags import FeatureFlagModel

logger = logging.getLogger(__name__)


class FeatureFlagRepository:
    \"\"\"Repository for feature flag-related database operations.\"\"\"

    def __init__(self, session: AsyncSession):
        \"\"\"Initialize the repository with a database session.

        Args:
            session: SQLAlchemy async session
        \"\"\"
        self.session = session

    async def create_feature_flag(self, feature_flag_data: Dict[str, Any]) -> FeatureFlagModel:
        \"\"\"Create a new feature flag.

        Args:
            feature_flag_data: Feature flag data

        Returns:
            FeatureFlagModel: Created feature flag
        \"\"\"
        # Create a new feature flag model
        feature_flag_model = FeatureFlagModel(
            **feature_flag_data,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Add to session and commit
        self.session.add(feature_flag_model)
        await self.session.commit()
        await self.session.refresh(feature_flag_model)

        return feature_flag_model

    async def get_feature_flag_by_id(self, feature_flag_id: str) -> Optional[FeatureFlagModel]:
        \"\"\"Get a feature flag by ID.

        Args:
            feature_flag_id: Feature flag ID

        Returns:
            FeatureFlagModel: Feature flag if found, None otherwise
        \"\"\"
        # Query the database
        result = await self.session.execute(
            select(FeatureFlagModel).where(FeatureFlagModel.id == feature_flag_id)
        )
        return result.scalars().first()

    async def get_feature_flag_by_key(self, key: str) -> Optional[FeatureFlagModel]:
        \"\"\"Get a feature flag by key.

        Args:
            key: Feature flag key

        Returns:
            FeatureFlagModel: Feature flag if found, None otherwise
        \"\"\"
        # Query the database
        result = await self.session.execute(
            select(FeatureFlagModel).where(FeatureFlagModel.key == key)
        )
        return result.scalars().first()

    async def get_feature_flags_by_environment(self, environment: str) -> List[FeatureFlagModel]:
        \"\"\"Get feature flags by environment.

        Args:
            environment: Environment

        Returns:
            List[FeatureFlagModel]: List of feature flags
        \"\"\"
        # Query the database
        result = await self.session.execute(
            select(FeatureFlagModel).where(FeatureFlagModel.environment == environment)
        )
        return result.scalars().all()

    async def get_feature_flags_by_tag(self, tag: str) -> List[FeatureFlagModel]:
        \"\"\"Get feature flags by tag.

        Args:
            tag: Tag

        Returns:
            List[FeatureFlagModel]: List of feature flags
        \"\"\"
        # Query the database
        result = await self.session.execute(
            select(FeatureFlagModel).where(FeatureFlagModel.tags.contains([tag]))
        )
        return result.scalars().all()

    async def get_all_feature_flags(self) -> List[FeatureFlagModel]:
        \"\"\"Get all feature flags.

        Returns:
            List[FeatureFlagModel]: List of feature flags
        \"\"\"
        # Query the database
        result = await self.session.execute(select(FeatureFlagModel))
        return result.scalars().all()

    async def update_feature_flag(
        self, feature_flag_id: str, feature_flag_data: Dict[str, Any]
    ) -> Optional[FeatureFlagModel]:
        \"\"\"Update a feature flag.

        Args:
            feature_flag_id: Feature flag ID
            feature_flag_data: Feature flag data to update

        Returns:
            FeatureFlagModel: Updated feature flag if found, None otherwise
        \"\"\"
        # Query the database
        result = await self.session.execute(
            select(FeatureFlagModel).where(FeatureFlagModel.id == feature_flag_id)
        )
        feature_flag_model = result.scalars().first()

        if not feature_flag_model:
            return None

        # Update fields
        for key, value in feature_flag_data.items():
            if hasattr(feature_flag_model, key):
                setattr(feature_flag_model, key, value)

        feature_flag_model.updated_at = datetime.now(timezone.utc)

        # Commit changes
        await self.session.commit()
        await self.session.refresh(feature_flag_model)

        return feature_flag_model

    async def delete_feature_flag(self, feature_flag_id: str) -> bool:
        \"\"\"Delete a feature flag.

        Args:
            feature_flag_id: Feature flag ID

        Returns:
            bool: True if feature flag was deleted, False otherwise
        \"\"\"
        # Delete the feature flag
        result = await self.session.execute(
            delete(FeatureFlagModel).where(FeatureFlagModel.id == feature_flag_id)
        )
        await self.session.commit()

        # Check if any rows were deleted
        return result.rowcount > 0 if hasattr(result, 'rowcount') else True
"""

    repo_path = os.path.join(repo_dir, "feature_flag_repository.py")
    with open(repo_path, "w", encoding="utf-8") as f:
        f.write(repo_content)

    logger.info(f"Created feature flag repository: {repo_path}")


def create_feature_flag_service():
    """Create feature flag service."""
    service_dir = "fs_agt/core/services"
    os.makedirs(service_dir, exist_ok=True)

    service_content = """\"\"\"Service for feature flag operations.\"\"\"

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.db.database import Database
from fs_agt_clean.core.db.feature_flag_repository import FeatureFlagRepository
from fs_agt_clean.core.models.database.feature_flags import FeatureFlagModel

logger = logging.getLogger(__name__)


class FeatureFlagService:
    \"\"\"Service for feature flag operations.\"\"\"

    def __init__(
        self,
        config_manager: ConfigManager,
        database: Optional[Database] = None,
    ):
        \"\"\"Initialize the service.

        Args:
            config_manager: Configuration manager
            database: Database instance
        \"\"\"
        self.config_manager = config_manager
        self.database = database or Database(config_manager)

    async def initialize(self) -> None:
        \"\"\"Initialize the service.\"\"\"
        # Ensure database tables exist
        await self.database.create_tables()
        logger.info("Feature flag service initialized successfully")

    async def create_feature_flag(self, feature_flag_data: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Create a new feature flag.

        Args:
            feature_flag_data: Feature flag data

        Returns:
            Dict[str, Any]: Created feature flag data
        \"\"\"
        async with self.database.get_session() as session:
            repository = FeatureFlagRepository(session)
            feature_flag_model = await repository.create_feature_flag(feature_flag_data)
            return feature_flag_model.to_dict()

    async def get_feature_flag(self, feature_flag_id: str) -> Optional[Dict[str, Any]]:
        \"\"\"Get a feature flag by ID.

        Args:
            feature_flag_id: Feature flag ID

        Returns:
            Optional[Dict[str, Any]]: Feature flag data if found, None otherwise
        \"\"\"
        async with self.database.get_session() as session:
            repository = FeatureFlagRepository(session)
            feature_flag_model = await repository.get_feature_flag_by_id(feature_flag_id)
            if feature_flag_model:
                return feature_flag_model.to_dict()
            return None

    async def get_feature_flag_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        \"\"\"Get a feature flag by key.

        Args:
            key: Feature flag key

        Returns:
            Optional[Dict[str, Any]]: Feature flag data if found, None otherwise
        \"\"\"
        async with self.database.get_session() as session:
            repository = FeatureFlagRepository(session)
            feature_flag_model = await repository.get_feature_flag_by_key(key)
            if feature_flag_model:
                return feature_flag_model.to_dict()
            return None

    async def get_feature_flags_by_environment(self, environment: str) -> List[Dict[str, Any]]:
        \"\"\"Get feature flags by environment.

        Args:
            environment: Environment

        Returns:
            List[Dict[str, Any]]: List of feature flag data
        \"\"\"
        async with self.database.get_session() as session:
            repository = FeatureFlagRepository(session)
            feature_flag_models = await repository.get_feature_flags_by_environment(environment)
            return [feature_flag_model.to_dict() for feature_flag_model in feature_flag_models]

    async def get_feature_flags_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        \"\"\"Get feature flags by tag.

        Args:
            tag: Tag

        Returns:
            List[Dict[str, Any]]: List of feature flag data
        \"\"\"
        async with self.database.get_session() as session:
            repository = FeatureFlagRepository(session)
            feature_flag_models = await repository.get_feature_flags_by_tag(tag)
            return [feature_flag_model.to_dict() for feature_flag_model in feature_flag_models]

    async def list_feature_flags(self) -> List[Dict[str, Any]]:
        \"\"\"Get all feature flags.

        Returns:
            List[Dict[str, Any]]: List of feature flag data
        \"\"\"
        async with self.database.get_session() as session:
            repository = FeatureFlagRepository(session)
            feature_flag_models = await repository.get_all_feature_flags()
            return [feature_flag_model.to_dict() for feature_flag_model in feature_flag_models]

    async def update_feature_flag(
        self, feature_flag_id: str, feature_flag_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        \"\"\"Update a feature flag.

        Args:
            feature_flag_id: Feature flag ID
            feature_flag_data: Feature flag data to update

        Returns:
            Optional[Dict[str, Any]]: Updated feature flag data if found, None otherwise
        \"\"\"
        async with self.database.get_session() as session:
            repository = FeatureFlagRepository(session)
            feature_flag_model = await repository.update_feature_flag(feature_flag_id, feature_flag_data)
            if feature_flag_model:
                return feature_flag_model.to_dict()
            return None

    async def delete_feature_flag(self, feature_flag_id: str) -> bool:
        \"\"\"Delete a feature flag.

        Args:
            feature_flag_id: Feature flag ID

        Returns:
            bool: True if feature flag was deleted, False otherwise
        \"\"\"
        async with self.database.get_session() as session:
            repository = FeatureFlagRepository(session)
            return await repository.delete_feature_flag(feature_flag_id)

    async def shutdown(self) -> None:
        \"\"\"Shutdown the service.\"\"\"
        # Close database connection
        await self.database.close()
        logger.info("Feature flag service shutdown successfully")
"""

    service_path = os.path.join(service_dir, "feature_flag_service.py")
    with open(service_path, "w", encoding="utf-8") as f:
        f.write(service_content)

    logger.info(f"Created feature flag service: {service_path}")


def main():
    """Main function."""
    create_feature_flag_model()
    create_feature_flag_repository()
    create_feature_flag_service()

    logger.info("Feature flag implementation created successfully")


if __name__ == "__main__":
    main()
