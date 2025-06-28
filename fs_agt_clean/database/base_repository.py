"""
Base repository class for database operations.
"""

import asyncio
import logging
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, cast

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from fs_agt_clean.core.config.config_manager import ConfigManager

# Import the correct database connection manager with async session support
from fs_agt_clean.core.db.connection_manager import DatabaseConnectionManager

# Initialize the database connection manager
config_manager = ConfigManager()
db_manager = DatabaseConnectionManager(config_manager)


# Ensure database is initialized
async def _ensure_db_initialized():
    """Ensure database connection manager is initialized."""
    if not db_manager._initialized:
        await db_manager.initialize()


# Initialize database on import (run in background)
try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # If loop is already running, schedule the initialization
        asyncio.create_task(_ensure_db_initialized())
    else:
        # If no loop is running, run the initialization
        asyncio.run(_ensure_db_initialized())
except Exception as e:
    logger.warning(f"Could not initialize database on import: {e}")
    # Database will be initialized on first use


# For testing
class TestSessionManager:
    def __init__(self, session_maker):
        self.session_maker = session_maker

    async def session(self):
        return self.session_maker()


from fs_agt_clean.database.error_handling import (
    TransactionContext,
    map_exception,
    with_metrics,
    with_retry,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Base repository class for database operations.

    This class provides a foundation for implementing the repository pattern,
    with common database operations and error handling.
    """

    def __init__(self, model_class: Type[T], table_name: str):
        """
        Initialize the repository.

        Args:
            model_class: The model class this repository handles
            table_name: The database table name
        """
        self.model_class = model_class
        self.table_name = table_name

    @with_retry(max_retries=3)
    @with_metrics("find_by_id")
    async def find_by_id(self, id: str) -> Optional[T]:
        """
        Find a record by ID.

        Args:
            id: The record ID

        Returns:
            The record if found, None otherwise
        """
        try:
            async with db_manager.get_session() as session:
                stmt = select(self.model_class).where(self.model_class.id == id)
                result = await session.execute(stmt)
                return result.scalars().first()
        except Exception as e:
            logger.error(f"Error finding {self.table_name} by ID {id}: {e}")
            raise map_exception(e)

    @with_retry(max_retries=3)
    @with_metrics("find_all")
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        Find all records with pagination.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            A list of records
        """
        try:
            async with db_manager.get_session() as session:
                stmt = select(self.model_class).limit(limit).offset(offset)
                result = await session.execute(stmt)
                return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error finding all {self.table_name}: {e}")
            raise map_exception(e)

    @with_retry(max_retries=3)
    @with_metrics("find_by_criteria")
    async def find_by_criteria(
        self, criteria: Dict[str, Any], limit: int = 100, offset: int = 0
    ) -> List[T]:
        """
        Find records by criteria.

        Args:
            criteria: Dictionary of field-value pairs to filter by
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            A list of matching records
        """
        try:
            async with db_manager.get_session() as session:
                stmt = select(self.model_class)

                # Apply criteria
                for key, value in criteria.items():
                    stmt = stmt.where(getattr(self.model_class, key) == value)

                # Apply pagination
                stmt = stmt.limit(limit).offset(offset)

                result = await session.execute(stmt)
                return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error finding {self.table_name} by criteria {criteria}: {e}")
            raise map_exception(e)

    @with_retry(max_retries=3)
    @with_metrics("create")
    async def create(self, data: Dict[str, Any]) -> T:
        """
        Create a new record.

        Args:
            data: The record data

        Returns:
            The created record
        """
        try:
            async with db_manager.get_session() as session:
                async with TransactionContext(session, f"create_{self.table_name}"):
                    # Create the model instance
                    instance = self.model_class(**data)

                    # Add to session
                    session.add(instance)

                    # Flush to get the ID
                    await session.flush()

                    # Return the instance
                    return instance
        except Exception as e:
            logger.error(f"Error creating {self.table_name}: {e}")
            raise map_exception(e)

    @with_retry(max_retries=3)
    @with_metrics("update")
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[T]:
        """
        Update a record.

        Args:
            id: The record ID
            data: The updated data

        Returns:
            The updated record if found, None otherwise
        """
        try:
            async with db_manager.get_session() as session:
                async with TransactionContext(session, f"update_{self.table_name}"):
                    # Get the instance
                    stmt = select(self.model_class).where(self.model_class.id == id)
                    result = await session.execute(stmt)
                    instance = result.scalars().first()

                    if not instance:
                        return None

                    # Update the instance
                    for key, value in data.items():
                        setattr(instance, key, value)

                    # Flush changes
                    await session.flush()

                    # Return the updated instance
                    return instance
        except Exception as e:
            logger.error(f"Error updating {self.table_name} with ID {id}: {e}")
            raise map_exception(e)

    @with_retry(max_retries=3)
    @with_metrics("delete")
    async def delete(self, id: str) -> bool:
        """
        Delete a record.

        Args:
            id: The record ID

        Returns:
            True if the record was deleted, False otherwise
        """
        try:
            async with db_manager.get_session() as session:
                async with TransactionContext(session, f"delete_{self.table_name}"):
                    # Get the instance
                    stmt = select(self.model_class).where(self.model_class.id == id)
                    result = await session.execute(stmt)
                    instance = result.scalars().first()

                    if not instance:
                        return False

                    # Delete the instance
                    await session.delete(instance)

                    # Flush changes
                    await session.flush()

                    return True
        except Exception as e:
            logger.error(f"Error deleting {self.table_name} with ID {id}: {e}")
            raise map_exception(e)

    @with_retry(max_retries=3)
    @with_metrics("count")
    async def count(self, criteria: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records, optionally filtered by criteria.

        Args:
            criteria: Dictionary of field-value pairs to filter by

        Returns:
            The number of matching records
        """
        try:
            async with db_manager.get_session() as session:
                stmt = select(func.count()).select_from(self.model_class)

                # Apply criteria
                if criteria:
                    for key, value in criteria.items():
                        stmt = stmt.where(getattr(self.model_class, key) == value)

                result = await session.execute(stmt)
                return cast(int, result.scalar())
        except Exception as e:
            logger.error(f"Error counting {self.table_name}: {e}")
            raise map_exception(e)

    @with_retry(max_retries=3)
    @with_metrics("bulk_create")
    async def bulk_create(self, data_list: List[Dict[str, Any]]) -> List[T]:
        """
        Create multiple records in a single transaction.

        Args:
            data_list: List of record data

        Returns:
            List of created records
        """
        if not data_list:
            return []

        try:
            async with db_manager.get_session() as session:
                async with TransactionContext(
                    session, f"bulk_create_{self.table_name}"
                ):
                    instances = []

                    for data in data_list:
                        instance = self.model_class(**data)
                        session.add(instance)
                        instances.append(instance)

                    # Flush to get IDs
                    await session.flush()

                    return instances
        except Exception as e:
            logger.error(f"Error bulk creating {self.table_name}: {e}")
            raise map_exception(e)

    @with_retry(max_retries=3)
    @with_metrics("bulk_update")
    async def bulk_update(self, id_data_map: Dict[str, Dict[str, Any]]) -> List[T]:
        """
        Update multiple records in a single transaction.

        Args:
            id_data_map: Dictionary mapping record IDs to update data

        Returns:
            List of updated records
        """
        if not id_data_map:
            return []

        try:
            async with db_manager.get_session() as session:
                async with TransactionContext(
                    session, f"bulk_update_{self.table_name}"
                ):
                    updated_instances = []

                    for id, data in id_data_map.items():
                        # Get the instance
                        stmt = select(self.model_class).where(self.model_class.id == id)
                        result = await session.execute(stmt)
                        instance = result.scalars().first()

                        if instance:
                            # Update the instance
                            for key, value in data.items():
                                setattr(instance, key, value)

                            updated_instances.append(instance)

                    # Flush changes
                    await session.flush()

                    return updated_instances
        except Exception as e:
            logger.error(f"Error bulk updating {self.table_name}: {e}")
            raise map_exception(e)

    @with_retry(max_retries=3)
    @with_metrics("bulk_delete")
    async def bulk_delete(self, ids: List[str]) -> int:
        """
        Delete multiple records in a single transaction.

        Args:
            ids: List of record IDs to delete

        Returns:
            Number of deleted records
        """
        if not ids:
            return 0

        try:
            async with db_manager.get_session() as session:
                async with TransactionContext(
                    session, f"bulk_delete_{self.table_name}"
                ):
                    # Delete the instances
                    stmt = delete(self.model_class).where(self.model_class.id.in_(ids))
                    result = await session.execute(stmt)

                    # Get the number of deleted rows
                    return result.rowcount
        except Exception as e:
            logger.error(f"Error bulk deleting {self.table_name}: {e}")
            raise map_exception(e)
