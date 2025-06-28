import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from fs_agt_clean.core.knowledge.config import default_config
from fs_agt_clean.core.knowledge.metrics import KnowledgeSharingMetrics, MetricEventType
from fs_agt_clean.core.knowledge.models import (
    KnowledgeEntry,
    KnowledgeNotification,
    KnowledgeStatus,
    KnowledgeSubscription,
    KnowledgeType,
    ValidationRecord,
)
from fs_agt_clean.core.knowledge.repository import KnowledgeRepository

logger = logging.getLogger(__name__)


class KnowledgeSharingService:
    """Service for sharing knowledge between agents."""

    def __init__(
        self,
        vector_store: Any,
        collection_name: str = "shared_knowledge",
        metrics_callback: Optional[callable] = None,
        validation_threshold: float = 0.7,
        rejection_threshold: float = 0.3,
        min_validators: int = 2,
    ):
        """Initialize the knowledge sharing service.

        Args:
            vector_store: Vector store client for storing and retrieving knowledge
            collection_name: Name of the collection in the vector store
            metrics_callback: Callback for reporting metrics
            validation_threshold: Threshold for validating knowledge (0.0-1.0)
            rejection_threshold: Threshold for rejecting knowledge (0.0-1.0)
            min_validators: Minimum number of validators required for knowledge to be validated
        """
        self.repository = KnowledgeRepository(
            vector_store=vector_store,
            collection_name=collection_name,
            metrics_callback=metrics_callback,
        )
        self.metrics_callback = metrics_callback
        self.validation_threshold = validation_threshold
        self.rejection_threshold = rejection_threshold
        self.min_validators = min_validators
        self._agent_subscriptions: Dict[str, Set[str]] = (
            {}
        )  # agent_id -> set of subscription_ids
        self._notification_queue = asyncio.Queue()
        self._notification_task = None
        self._running = False
        self.metrics = KnowledgeSharingMetrics(
            window_seconds=default_config.metrics_window_seconds,
            callback=metrics_callback,
        )

    async def initialize(self) -> None:
        """Initialize the knowledge sharing service."""
        await self.repository.initialize()
        self._running = True
        self._notification_task = asyncio.create_task(self._process_notifications())
        logger.info("Knowledge sharing service initialized")

    async def cleanup(self) -> None:
        """Clean up resources."""
        self._running = False
        if self._notification_task:
            self._notification_task.cancel()
            try:
                await self._notification_task
            except asyncio.CancelledError:
                pass

    async def publish_knowledge(
        self,
        title: str,
        content: Dict[str, Any],
        knowledge_type: KnowledgeType,
        source_agent_id: str,
        confidence: float = 0.0,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        vector: Optional[List[float]] = None,
    ) -> str:
        """Publish knowledge to the repository.

        Args:
            title: Title of the knowledge entry
            content: Content of the knowledge entry
            knowledge_type: Type of knowledge
            source_agent_id: ID of the agent publishing the knowledge
            confidence: Confidence score for the knowledge (0.0-1.0)
            tags: Tags for categorizing the knowledge
            metadata: Additional metadata for the knowledge
            vector: Vector representation of the knowledge

        Returns:
            ID of the published knowledge entry
        """
        start_time = datetime.now()

        # Create knowledge entry
        entry = KnowledgeEntry(
            id=str(uuid.uuid4()),
            title=title,
            content=content,
            knowledge_type=knowledge_type,
            source_agent_id=source_agent_id,
            confidence=confidence,
            tags=tags or [],
            metadata=metadata or {},
            vector=vector,
            status=KnowledgeStatus.PENDING,
        )

        # Add to repository
        await self.repository.add_entry(entry)

        # Find matching subscriptions and create notifications
        matching_subscriptions = await self.repository.get_matching_subscriptions(entry)
        for subscription in matching_subscriptions:
            notification = KnowledgeNotification(
                entry_id=entry.id,
                subscription_id=subscription.id,
                agent_id=subscription.agent_id,
            )
            await self._notification_queue.put(notification)

        # Record metrics
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        self.metrics.record_event(
            MetricEventType.KNOWLEDGE_PUBLISHED,
            {
                "agent_id": source_agent_id,
                "knowledge_type": knowledge_type.value,
                "entry_id": entry.id,
                "tags": tags or [],
                "duration_ms": duration_ms,
            },
        )

        logger.info(
            "UnifiedAgent %s published knowledge entry %s: %s",
            source_agent_id,
            entry.id,
            title,
        )

        return entry.id

    async def validate_knowledge(
        self,
        entry_id: str,
        validator_agent_id: str,
        validation_score: float,
        validation_notes: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Validate a knowledge entry.

        Args:
            entry_id: ID of the knowledge entry to validate
            validator_agent_id: ID of the agent validating the knowledge
            validation_score: Validation score (0.0-1.0)
            validation_notes: Notes from the validation process

        Returns:
            True if validation was successful, False otherwise
        """
        start_time = datetime.now()

        # Get the entry
        entry = await self.repository.get_entry(entry_id)
        if not entry:
            logger.warning("Knowledge entry %s not found for validation", entry_id)
            return bool(False)

        # Don't validate your own knowledge
        if entry.source_agent_id == validator_agent_id:
            logger.warning(
                "UnifiedAgent %s attempted to validate its own knowledge entry %s",
                validator_agent_id,
                entry_id,
            )
            return False

        # Create validation record
        validation = ValidationRecord(
            validator_agent_id=validator_agent_id,
            validation_score=validation_score,
            validated_at=datetime.now(),
            notes=validation_notes or {},
        )

        # Add validation record
        result = await self.repository.add_validation_record(entry_id, validation)
        if not result:
            return False

        # Check if entry should be validated or rejected based on validations
        entry = await self.repository.get_entry(entry_id)
        if entry and len(entry.validations) >= self.min_validators:
            # Calculate average validation score
            avg_score = entry.get_average_validation_score()

            if avg_score >= self.validation_threshold:
                await self.repository.update_knowledge_status(
                    entry_id, KnowledgeStatus.VALIDATED
                )
                logger.info(
                    "Knowledge entry %s validated with average score %s",
                    entry_id,
                    avg_score,
                )
            elif avg_score <= self.rejection_threshold:
                await self.repository.update_knowledge_status(
                    entry_id, KnowledgeStatus.REJECTED
                )
                logger.info(
                    "Knowledge entry %s rejected with average score %s",
                    entry_id,
                    avg_score,
                )

        # Record metrics
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        self.metrics.record_event(
            MetricEventType.KNOWLEDGE_VALIDATED,
            {
                "agent_id": validator_agent_id,
                "knowledge_type": entry.knowledge_type.value,
                "entry_id": entry_id,
                "duration_ms": duration_ms,
            },
        )

        logger.info(
            "UnifiedAgent %s validated knowledge entry %s with score %s",
            validator_agent_id,
            entry_id,
            validation_score,
        )

        return True

    async def get_knowledge(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Get a knowledge entry by ID.

        Args:
            entry_id: ID of the knowledge entry

        Returns:
            Knowledge entry if found, None otherwise
        """
        return await self.repository.get_entry(entry_id)

    async def search_knowledge(
        self,
        query_text: Optional[str] = None,
        query_vector: Optional[List[float]] = None,
        knowledge_types: Optional[List[KnowledgeType]] = None,
        tags: Optional[List[str]] = None,
        min_confidence: float = 0.0,
        status: Optional[List[KnowledgeStatus]] = None,
        limit: int = 10,
    ) -> List[KnowledgeEntry]:
        """Search for knowledge entries.

        Args:
            query_text: Text to search for
            query_vector: Vector to search for similar knowledge
            knowledge_types: Types of knowledge to search for
            tags: Tags to filter by
            min_confidence: Minimum confidence score
            status: Status to filter by
            limit: Maximum number of results to return

        Returns:
            List of matching knowledge entries
        """
        start_time = datetime.now()

        results = []

        # If multiple knowledge types or statuses are specified, we need to search for each one
        if knowledge_types and len(knowledge_types) > 1:
            for knowledge_type in knowledge_types:
                type_results = await self.repository.search_entries(
                    query_text=query_text,
                    query_vector=query_vector,
                    knowledge_type=knowledge_type,
                    tags=tags,
                    min_confidence=min_confidence,
                    status=status[0] if status and len(status) == 1 else None,
                    limit=limit,
                )
                results.extend(type_results)

            # Limit results to the requested number
            results = results[:limit]
        elif status and len(status) > 1:
            for status_value in status:
                status_results = await self.repository.search_entries(
                    query_text=query_text,
                    query_vector=query_vector,
                    knowledge_type=(
                        knowledge_types[0]
                        if knowledge_types and len(knowledge_types) == 1
                        else None
                    ),
                    tags=tags,
                    min_confidence=min_confidence,
                    status=status_value,
                    limit=limit,
                )
                results.extend(status_results)

            # Limit results to the requested number
            results = results[:limit]
        else:
            # Simple case - single knowledge type and status
            results = await self.repository.search_entries(
                query_text=query_text,
                query_vector=query_vector,
                knowledge_type=(
                    knowledge_types[0]
                    if knowledge_types and len(knowledge_types) == 1
                    else None
                ),
                tags=tags,
                min_confidence=min_confidence,
                status=status[0] if status and len(status) == 1 else None,
                limit=limit,
            )

        # Record metrics
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        self.metrics.record_event(
            MetricEventType.SEARCH_PERFORMED,
            {
                "knowledge_type": (
                    knowledge_types[0].value
                    if knowledge_types and len(knowledge_types) == 1
                    else None
                ),
                "duration_ms": duration_ms,
            },
        )

        return results

    async def subscribe(
        self,
        agent_id: str,
        knowledge_types: Optional[List[KnowledgeType]] = None,
        tags: Optional[List[str]] = None,
        min_confidence: float = 0.0,
    ) -> str:
        """Subscribe to knowledge updates.

        Args:
            agent_id: ID of the agent subscribing
            knowledge_types: Types of knowledge to subscribe to
            tags: Tags to filter by
            min_confidence: Minimum confidence score for notifications

        Returns:
            Subscription ID
        """
        start_time = datetime.now()

        # Create subscription
        subscription = KnowledgeSubscription(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            knowledge_types=knowledge_types or [],
            tags=tags or [],
            min_confidence=min_confidence,
        )

        # Add to repository
        await self.repository.add_subscription(subscription)

        # Track agent subscriptions
        if agent_id not in self._agent_subscriptions:
            self._agent_subscriptions[agent_id] = set()
        self._agent_subscriptions[agent_id].add(subscription.id)

        # Record metrics
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        self.metrics.record_event(
            MetricEventType.SUBSCRIPTION_CREATED,
            {
                "agent_id": agent_id,
                "duration_ms": duration_ms,
            },
        )

        logger.info(
            "UnifiedAgent %s subscribed to knowledge updates: %s", agent_id, subscription.id
        )

        return subscription.id

    async def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from knowledge updates.

        Args:
            subscription_id: ID of the subscription

        Returns:
            True if unsubscribed successfully, False otherwise
        """
        start_time = datetime.now()

        # Get the subscription
        subscription = await self.repository.get_subscription(subscription_id)
        if not subscription:
            return False

        # Update subscription to inactive
        subscription.active = False
        subscription.updated_at = datetime.now()
        await self.repository.update_subscription(subscription)

        # Remove from agent subscriptions
        if subscription.agent_id in self._agent_subscriptions:
            self._agent_subscriptions[subscription.agent_id].discard(subscription_id)

        # Record metrics
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        self.metrics.record_event(
            MetricEventType.SUBSCRIPTION_DELETED,
            {
                "agent_id": subscription.agent_id,
                "subscription_id": subscription_id,
                "duration_ms": duration_ms,
            },
        )

        logger.info(
            "UnifiedAgent %s unsubscribed from knowledge updates: %s",
            subscription.agent_id,
            subscription_id,
        )

        return True

    async def unsubscribe_agent(self, agent_id: str) -> int:
        """Unsubscribe an agent from all knowledge updates.

        Args:
            agent_id: ID of the agent

        Returns:
            Number of subscriptions cancelled
        """
        if agent_id not in self._agent_subscriptions:
            return 0

        subscriptions = list(self._agent_subscriptions[agent_id])
        count = 0

        for subscription_id in subscriptions:
            if await self.unsubscribe(subscription_id):
                count += 1

        logger.info(
            "UnifiedAgent %s unsubscribed from all knowledge updates: %s subscriptions cancelled",
            agent_id,
            count,
        )

        return count

    async def get_agent_subscriptions(self, agent_id: str) -> List[str]:
        """Get all subscription IDs for an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            List of subscription IDs
        """
        if agent_id not in self._agent_subscriptions:
            return []

        return list(self._agent_subscriptions[agent_id])

    async def _process_notifications(self) -> None:
        """Process notifications from the queue."""
        while self._running:
            try:
                # Get notification from queue with timeout
                try:
                    notification = await asyncio.wait_for(
                        self._notification_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # Process notification
                try:
                    # In a real implementation, this would call the agent's notification handler
                    # For now, just log it
                    logger.info(
                        "Notifying agent %s about knowledge entry %s",
                        notification.agent_id,
                        notification.entry_id,
                    )

                    # Mark as delivered and processed
                    notification.mark_delivered()
                    notification.mark_processed()

                    # Record metrics
                    self.metrics.record_event(
                        MetricEventType.NOTIFICATION_SENT,
                        {
                            "agent_id": notification.agent_id,
                            "entry_id": notification.entry_id,
                            "subscription_id": notification.subscription_id,
                        },
                    )
                except Exception as e:
                    logger.error("Error processing notification: %s", e)

                    # Record error
                    self.metrics.record_event(
                        MetricEventType.NOTIFICATION_ERROR,
                        {
                            "agent_id": notification.agent_id,
                            "entry_id": notification.entry_id,
                            "subscription_id": notification.subscription_id,
                            "success": False,
                            "error_message": str(e),
                        },
                    )
                finally:
                    self._notification_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in notification processing loop: %s", e)

    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge sharing service.

        Returns:
            Dictionary of statistics
        """
        repo_stats = await self.repository.get_stats()
        metrics_summary = self.metrics.get_summary()

        # Add service-specific stats
        service_stats = {
            "agent_subscription_count": len(self._agent_subscriptions),
            "total_agent_subscriptions": sum(
                len(subs) for subs in self._agent_subscriptions.values()
            ),
            "validation_threshold": self.validation_threshold,
            "rejection_threshold": self.rejection_threshold,
            "min_validators": self.min_validators,
            "notification_queue_size": self._notification_queue.qsize(),
            "metrics": metrics_summary,
        }

        return {**repo_stats, **service_stats}
