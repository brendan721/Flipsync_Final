import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field
from qdrant_client import QdrantClient

from fs_agt_clean.core.knowledge.config import default_config
from fs_agt_clean.core.knowledge.models import (
    KnowledgeEntry,
    KnowledgeStatus,
    KnowledgeSubscription,
    KnowledgeType,
    ValidationRecord,
)
from fs_agt_clean.services.infrastructure.monitoring.metrics_models import MetricUpdate

logger = logging.getLogger(__name__)


class KnowledgeRepository:
    """Repository for shared knowledge between agents."""

    def __init__(
        self,
        vector_store: Any,
        collection_name: str = "shared_knowledge",
        metrics_callback: Optional[callable] = None,
    ):
        """Initialize the knowledge repository.

        Args:
            vector_store: Vector store client for storing and retrieving knowledge
            collection_name: Name of the collection in the vector store
            metrics_callback: Callback for reporting metrics
        """
        self.vector_store = vector_store
        self.collection_name = collection_name
        self.metrics_callback = metrics_callback
        self._entries: Dict[str, KnowledgeEntry] = {}
        self._subscriptions: Dict[str, KnowledgeSubscription] = {}
        self._knowledge_lock = asyncio.Lock()
        self._subscription_lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize the knowledge repository."""
        # Ensure the collection exists
        if hasattr(self.vector_store, "_ensure_collection"):
            await self.vector_store._ensure_collection()

        # Load existing entries from vector store
        await self._load_entries()

        logger.info(
            "Initialized knowledge repository with %s entries", len(self._entries)
        )

    async def _load_entries(self) -> None:
        """Load existing entries from the vector store."""
        try:
            # This is a simplified implementation - in a real system, you would
            # need to handle pagination and proper querying based on your vector store
            results = await self.vector_store.search(
                query_vector=None, limit=1000, filter_dict={}
            )

            async with self._knowledge_lock:
                for result in results:
                    # Convert from vector store format to KnowledgeEntry
                    payload = result.get("payload", {})
                    if not payload:
                        continue

                    try:
                        # Convert knowledge_type and status from string to enum
                        if "knowledge_type" in payload and isinstance(
                            payload["knowledge_type"], str
                        ):
                            payload["knowledge_type"] = KnowledgeType(
                                payload["knowledge_type"]
                            )
                        if "status" in payload and isinstance(payload["status"], str):
                            payload["status"] = KnowledgeStatus(payload["status"])

                        # Convert validations from dict to ValidationRecord
                        if "validations" in payload and isinstance(
                            payload["validations"], list
                        ):
                            validations = []
                            for v in payload["validations"]:
                                validations.append(ValidationRecord(**v))
                            payload["validations"] = validations

                        entry = KnowledgeEntry(**payload)
                        self._entries[entry.id] = entry
                    except Exception as e:
                        logger.error(f"Error converting entry {payload.get('id')}: {e}")

            if self.metrics_callback:
                await self.metrics_callback(
                    {
                        "type": "knowledge_entries_loaded",
                        "count": len(self._entries),
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
        except Exception as e:
            logger.error("Error loading knowledge entries: %s", e)
            raise

    async def add_entry(self, entry: KnowledgeEntry) -> None:
        """Add a knowledge entry to the repository.

        Args:
            entry: The knowledge entry to add
        """
        async with self._knowledge_lock:
            self._entries[entry.id] = entry

        # Store in vector store
        try:
            # Convert entry to dict for storage
            entry_dict = entry.model_dump()

            # Store with vector if available
            if entry.vector:
                await self.vector_store.add_entry(
                    entry_id=entry.id, entry=entry_dict, vector=entry.vector
                )
            else:
                # Generate vector from content if needed
                # This is a placeholder - in a real implementation, you would
                # use an embedding model to generate the vector
                await self.vector_store.add_entry(
                    entry_id=entry.id,
                    entry=entry_dict,
                    vector=[0.0] * default_config.vector_dimensions,
                )
        except Exception as e:
            logger.error("Error storing knowledge entry in vector store: %s", e)
            # Remove from local cache if vector store storage fails
            async with self._knowledge_lock:
                if entry.id in self._entries:
                    del self._entries[entry.id]
            raise

        if self.metrics_callback:
            await self.metrics_callback(
                {
                    "type": "knowledge_entry_added",
                    "entry_id": entry.id,
                    "knowledge_type": entry.knowledge_type.value,
                    "source_agent_id": entry.source_agent_id,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

    async def get_entry(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Get a knowledge entry by ID.

        Args:
            entry_id: ID of the knowledge entry

        Returns:
            Knowledge entry if found, None otherwise
        """
        async with self._knowledge_lock:
            return self._entries.get(entry_id)

    async def update_entry(self, entry: KnowledgeEntry) -> None:
        """Update a knowledge entry.

        Args:
            entry: The updated knowledge entry
        """
        async with self._knowledge_lock:
            if entry.id not in self._entries:
                raise ValueError(f"Knowledge entry {entry.id} not found")

            self._entries[entry.id] = entry

        # Update in vector store
        try:
            entry_dict = entry.model_dump()

            if entry.vector:
                await self.vector_store.update_entry(
                    entry_id=entry.id, entry=entry_dict
                )
        except Exception as e:
            logger.error("Error updating knowledge entry in vector store: %s", e)
            # Don't revert local changes - we'll try again later

        if self.metrics_callback:
            await self.metrics_callback(
                {
                    "type": "knowledge_entry_updated",
                    "entry_id": entry.id,
                    "knowledge_type": entry.knowledge_type.value,
                    "status": entry.status.value,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

    async def delete_entry(self, entry_id: str) -> bool:
        """Delete a knowledge entry.

        Args:
            entry_id: ID of the knowledge entry to delete

        Returns:
            True if deleted, False if not found
        """
        async with self._knowledge_lock:
            if entry_id not in self._entries:
                return bool(False)

            entry = self._entries[entry_id]
            del self._entries[entry_id]

        # Delete from vector store
        try:
            await self.vector_store.delete_entry(entry_id)
        except Exception as e:
            logger.error("Error deleting knowledge entry from vector store: %s", e)
            # Add back to local cache if vector store deletion fails
            async with self._knowledge_lock:
                self._entries[entry_id] = entry
            raise

        if self.metrics_callback:
            await self.metrics_callback(
                {
                    "type": "knowledge_entry_deleted",
                    "entry_id": entry_id,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        return True

    async def add_validation_record(
        self, entry_id: str, validation: ValidationRecord
    ) -> bool:
        """Add a validation record to a knowledge entry.

        Args:
            entry_id: ID of the knowledge entry
            validation: Validation record to add

        Returns:
            True if added, False if entry not found
        """
        async with self._knowledge_lock:
            if entry_id not in self._entries:
                return False

            entry = self._entries[entry_id]
            entry.validations.append(validation)
            entry.updated_at = datetime.utcnow()

        # Update in vector store
        await self.update_entry(entry)

        if self.metrics_callback:
            await self.metrics_callback(
                {
                    "type": "validation_record_added",
                    "entry_id": entry_id,
                    "validator_agent_id": validation.validator_agent_id,
                    "validation_score": validation.validation_score,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        return True

    async def update_knowledge_status(
        self, entry_id: str, status: KnowledgeStatus
    ) -> bool:
        """Update the status of a knowledge entry.

        Args:
            entry_id: ID of the knowledge entry
            status: New status

        Returns:
            True if updated, False if entry not found
        """
        async with self._knowledge_lock:
            if entry_id not in self._entries:
                return False

            entry = self._entries[entry_id]
            entry.status = status
            entry.updated_at = datetime.utcnow()

        # Update in vector store
        await self.update_entry(entry)

        if self.metrics_callback:
            await self.metrics_callback(
                {
                    "type": "knowledge_status_updated",
                    "entry_id": entry_id,
                    "status": status.value,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        return True

    async def search_entries(
        self,
        query_text: Optional[str] = None,
        query_vector: Optional[List[float]] = None,
        knowledge_type: Optional[KnowledgeType] = None,
        source_agent_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_confidence: float = 0.0,
        status: Optional[KnowledgeStatus] = None,
        limit: int = 10,
    ) -> List[KnowledgeEntry]:
        """Search for knowledge entries.

        Args:
            query_text: Text to search for
            query_vector: Vector to search for similar knowledge
            knowledge_type: Type of knowledge to search for
            source_agent_id: ID of the agent that published the knowledge
            tags: Tags to filter by
            min_confidence: Minimum confidence score
            status: Status to filter by
            limit: Maximum number of results to return

        Returns:
            List of matching knowledge entries
        """
        # Build filter dict for vector store
        filter_dict = {}

        if knowledge_type:
            filter_dict["knowledge_type"] = knowledge_type.value

        if source_agent_id:
            filter_dict["source_agent_id"] = source_agent_id

        if min_confidence > 0:
            filter_dict["confidence"] = {"$gte": min_confidence}

        if status:
            filter_dict["status"] = status.value

        # Tags filtering is more complex and may need special handling
        # depending on the vector store implementation

        try:
            # Search in vector store
            if query_vector:
                results = await self.vector_store.search(
                    query_vector=query_vector, limit=limit, filter_dict=filter_dict
                )
            elif query_text:
                # This is a placeholder - in a real implementation, you would
                # generate a vector from the query text and search with that
                results = await self.vector_store.search(
                    query_text=query_text, limit=limit, filter_dict=filter_dict
                )
            else:
                # Simple filtering without vector search
                results = await self.vector_store.search(
                    query_vector=None, limit=limit, filter_dict=filter_dict
                )

            # Convert results to KnowledgeEntry objects
            entries = []
            for result in results:
                entry_id = result.get("id")

                # Try to get from local cache first
                async with self._knowledge_lock:
                    if entry_id in self._entries:
                        entry = self._entries[entry_id]
                    else:
                        # Convert from vector store format
                        payload = result.get("payload", {})
                        if not payload:
                            continue

                        try:
                            # Convert knowledge_type and status from string to enum
                            if "knowledge_type" in payload and isinstance(
                                payload["knowledge_type"], str
                            ):
                                payload["knowledge_type"] = KnowledgeType(
                                    payload["knowledge_type"]
                                )
                            if "status" in payload and isinstance(
                                payload["status"], str
                            ):
                                payload["status"] = KnowledgeStatus(payload["status"])

                            # Convert validations from dict to ValidationRecord
                            if "validations" in payload and isinstance(
                                payload["validations"], list
                            ):
                                validations = []
                                for v in payload["validations"]:
                                    validations.append(ValidationRecord(**v))
                                payload["validations"] = validations

                            entry = KnowledgeEntry(**payload)
                            self._entries[entry.id] = entry
                        except Exception as e:
                            logger.error(
                                f"Error converting entry {payload.get('id')}: {e}"
                            )
                            continue

                # Apply additional filters that may not be supported by the vector store
                if tags and not any(tag in entry.tags for tag in tags):
                    continue

                entries.append(entry)

            if self.metrics_callback:
                await self.metrics_callback(
                    {
                        "type": "knowledge_search",
                        "result_count": len(entries),
                        "query_type": (
                            "vector"
                            if query_vector
                            else "text" if query_text else "filter"
                        ),
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

            return entries
        except Exception as e:
            logger.error("Error searching knowledge: %s", e)
            raise

    async def get_entries_by_agent(self, agent_id: str) -> List[KnowledgeEntry]:
        """Get knowledge entries by source agent.

        Args:
            agent_id: ID of the agent

        Returns:
            List of knowledge entries
        """
        return await self.search_entries(source_agent_id=agent_id)

    async def get_entries_by_status(
        self, status: KnowledgeStatus
    ) -> List[KnowledgeEntry]:
        """Get knowledge entries by status.

        Args:
            status: Status to filter by

        Returns:
            List of knowledge entries
        """
        return await self.search_entries(status=status)

    async def add_subscription(self, subscription: KnowledgeSubscription) -> None:
        """Add a subscription to the repository.

        Args:
            subscription: The subscription to add
        """
        async with self._subscription_lock:
            self._subscriptions[subscription.id] = subscription

        if self.metrics_callback:
            await self.metrics_callback(
                {
                    "type": "subscription_added",
                    "subscription_id": subscription.id,
                    "agent_id": subscription.agent_id,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

    async def get_subscription(
        self, subscription_id: str
    ) -> Optional[KnowledgeSubscription]:
        """Get a subscription by ID.

        Args:
            subscription_id: ID of the subscription

        Returns:
            Subscription if found, None otherwise
        """
        async with self._subscription_lock:
            return self._subscriptions.get(subscription_id)

    async def update_subscription(self, subscription: KnowledgeSubscription) -> None:
        """Update a subscription.

        Args:
            subscription: The updated subscription
        """
        async with self._subscription_lock:
            if subscription.id not in self._subscriptions:
                raise ValueError(f"Subscription {subscription.id} not found")

            self._subscriptions[subscription.id] = subscription

        if self.metrics_callback:
            await self.metrics_callback(
                {
                    "type": "subscription_updated",
                    "subscription_id": subscription.id,
                    "agent_id": subscription.agent_id,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

    async def delete_subscription(self, subscription_id: str) -> bool:
        """Delete a subscription.

        Args:
            subscription_id: ID of the subscription to delete

        Returns:
            True if deleted, False if not found
        """
        async with self._subscription_lock:
            if subscription_id not in self._subscriptions:
                return False

            del self._subscriptions[subscription_id]

        if self.metrics_callback:
            await self.metrics_callback(
                {
                    "type": "subscription_deleted",
                    "subscription_id": subscription_id,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        return True

    async def get_subscriptions_by_agent(
        self, agent_id: str
    ) -> List[KnowledgeSubscription]:
        """Get subscriptions by agent.

        Args:
            agent_id: ID of the agent

        Returns:
            List of subscriptions
        """
        async with self._subscription_lock:
            return [
                subscription
                for subscription in self._subscriptions.values()
                if subscription.agent_id == agent_id and subscription.active
            ]

    async def get_matching_subscriptions(
        self, entry: KnowledgeEntry
    ) -> List[KnowledgeSubscription]:
        """Get subscriptions that match a knowledge entry.

        Args:
            entry: Knowledge entry to match

        Returns:
            List of matching subscriptions
        """
        async with self._subscription_lock:
            return [
                subscription
                for subscription in self._subscriptions.values()
                if subscription.active and subscription.matches_entry(entry)
            ]

    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge repository.

        Returns:
            Dictionary of statistics
        """
        async with self._knowledge_lock, self._subscription_lock:
            # Count entries by status
            status_counts = {status: 0 for status in KnowledgeStatus}

            # Count entries by type
            type_counts = {knowledge_type: 0 for knowledge_type in KnowledgeType}

            # Count validations
            total_validations = 0
            validation_scores = []

            for entry in self._entries.values():
                status_counts[entry.status] += 1
                type_counts[entry.knowledge_type] += 1
                total_validations += len(entry.validations)

                for validation in entry.validations:
                    validation_scores.append(validation.validation_score)

            # Calculate average validation score
            avg_validation_score = (
                sum(validation_scores) / len(validation_scores)
                if validation_scores
                else 0.0
            )

            # Count active subscriptions
            active_subscriptions = sum(
                1 for sub in self._subscriptions.values() if sub.active
            )

            return {
                "total_entries": len(self._entries),
                "entries_by_status": {k.value: v for k, v in status_counts.items()},
                "entries_by_type": {k.value: v for k, v in type_counts.items()},
                "total_subscriptions": len(self._subscriptions),
                "active_subscriptions": active_subscriptions,
                "total_validations": total_validations,
                "average_validation_score": avg_validation_score,
                "timestamp": datetime.utcnow().isoformat(),
            }
