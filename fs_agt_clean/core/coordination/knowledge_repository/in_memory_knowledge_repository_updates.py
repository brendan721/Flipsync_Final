"""
Implementation of the new methods for the InMemoryKnowledgeRepository class.
"""


async def get_all_knowledge(self) -> List[KnowledgeItem]:
    """
    Get all knowledge items in the repository.

    Returns:
        List of all knowledge items

    Raises:
        KnowledgeError: If the knowledge items cannot be retrieved
    """
    try:
        # Try to get from cache first
        cached_items = await self.cache.get_all()
        if cached_items and len(cached_items) == len(self.knowledge_items):
            return cached_items

        # Get all knowledge items
        items = list(self.knowledge_items.values())

        # Add to cache
        for item in items:
            await self.cache.add(item)

        return items
    except Exception as e:
        error_msg = f"Failed to get all knowledge items: {str(e)}"
        self.logger.error(error_msg, exc_info=True)
        raise KnowledgeError(error_msg, cause=e)


async def get_knowledge_updates(self, since_timestamp: datetime) -> List[KnowledgeItem]:
    """
    Get knowledge items updated since a timestamp.

    Args:
        since_timestamp: Timestamp to get updates since

    Returns:
        List of knowledge items updated since the timestamp

    Raises:
        KnowledgeError: If the knowledge items cannot be retrieved
    """
    try:
        # Get all knowledge items
        items = list(self.knowledge_items.values())

        # Filter by update timestamp
        updated_items = [item for item in items if item.updated_at > since_timestamp]

        # Add to cache
        for item in updated_items:
            await self.cache.add(item)

        return updated_items
    except Exception as e:
        error_msg = f"Failed to get knowledge updates since {since_timestamp}: {str(e)}"
        self.logger.error(error_msg, exc_info=True)
        raise KnowledgeError(error_msg, cause=e)


async def get_critical_updates(
    self, since_timestamp: datetime, priority_threshold: float = 0.5
) -> List[KnowledgeItem]:
    """
    Get critical knowledge updates since a timestamp.

    This method is optimized for mobile devices with limited bandwidth.
    It returns only high-priority knowledge updates.

    Args:
        since_timestamp: Timestamp to get updates since
        priority_threshold: Priority threshold (0.0 to 1.0)

    Returns:
        List of critical knowledge items updated since the timestamp

    Raises:
        KnowledgeError: If the knowledge items cannot be retrieved
    """
    try:
        # Get all knowledge items updated since the timestamp
        updated_items = await self.get_knowledge_updates(since_timestamp)

        # Filter by priority
        critical_items = []
        for item in updated_items:
            # Calculate priority based on metadata, type, and status
            priority = 0.0

            # Knowledge type priority
            if item.knowledge_type == KnowledgeType.RULE:
                priority += 0.3  # Rules are important
            elif item.knowledge_type == KnowledgeType.PROCEDURE:
                priority += 0.2  # Procedures are somewhat important

            # Status priority
            if item.status == KnowledgeStatus.ACTIVE:
                priority += 0.2  # Active items are important
            elif item.status == KnowledgeStatus.DEPRECATED:
                priority += 0.1  # Deprecated items are somewhat important

            # Metadata priority
            if item.metadata:
                # Check for priority in metadata
                if "priority" in item.metadata:
                    try:
                        metadata_priority = float(item.metadata["priority"])
                        priority += metadata_priority
                    except (ValueError, TypeError):
                        pass

                # Check for critical flag in metadata
                if "critical" in item.metadata and item.metadata["critical"]:
                    priority += 0.3

            # Normalize priority to 0.0-1.0 range
            priority = min(1.0, priority)

            # Add to critical items if priority is above threshold
            if priority >= priority_threshold:
                critical_items.append(item)
                # Add to cache
                await self.cache.add(item)

        return critical_items
    except Exception as e:
        error_msg = f"Failed to get critical knowledge updates since {since_timestamp}: {str(e)}"
        self.logger.error(error_msg, exc_info=True)
        raise KnowledgeError(error_msg, cause=e)
