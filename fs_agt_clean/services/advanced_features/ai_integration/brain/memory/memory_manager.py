from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

"Memory management system for brain module."


@dataclass
class Memory:
    """Memory data structure."""

    id: str
    content: str
    context: Dict
    created_at: datetime
    last_accessed: datetime
    importance: float = 0.0
    metadata: Optional[Dict] = None


class MemoryManager:
    """Manages brain memory system."""

    def __init__(self):
        """Initialize memory manager."""
        self._memories: List[Memory] = []
        self._indices: Dict[str, List[Memory]] = {}

    def store(
        self,
        content: str,
        context: Dict,
        importance: float = 0.0,
        metadata: Optional[Dict] = None,
    ) -> Memory:
        """Store a new memory.

        Args:
            content: Memory content
            context: Memory context
            importance: Memory importance score
            metadata: Optional metadata

        Returns:
            Created memory
        """
        memory = Memory(
            id=f"mem_{datetime.now().timestamp()}",
            content=content,
            context=context,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            importance=importance,
            metadata=metadata,
        )
        self._memories.append(memory)
        self._index_memory(memory)
        return memory

    def retrieve(self, context: Dict, limit: int = 10) -> List[Memory]:
        """Retrieve memories matching context.

        Args:
            context: Memory context to match
            limit: Maximum number of memories to return

        Returns:
            List of matching memories
        """
        matches = []
        for key, value in context.items():
            if key in self._indices:
                matches.extend(self._indices[key])
        matches = sorted(matches, key=lambda m: m.importance, reverse=True)
        return matches[:limit]

    def update(
        self,
        memory_id: str,
        content: Optional[str] = None,
        context: Optional[Dict] = None,
        importance: Optional[float] = None,
    ) -> Optional[Memory]:
        """Update a memory.

        Args:
            memory_id: Memory identifier
            content: Optional new content
            context: Optional new context
            importance: Optional new importance score

        Returns:
            Updated memory if found
        """
        memory = self._get_memory(memory_id)
        if memory:
            if content is not None:
                memory.content = content
            if context is not None:
                memory.context = context
            if importance is not None:
                memory.importance = importance
            memory.last_accessed = datetime.now()
            return memory
        return None

    def forget(self, memory_id: str) -> None:
        """Remove a memory.

        Args:
            memory_id: Memory identifier
        """
        memory = self._get_memory(memory_id)
        if memory:
            self._memories.remove(memory)
            self._remove_from_indices(memory)

    def _get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get a memory by ID.

        Args:
            memory_id: Memory identifier

        Returns:
            Memory if found, None otherwise
        """
        for memory in self._memories:
            if memory.id == memory_id:
                return memory
        return None

    def _index_memory(self, memory: Memory) -> None:
        """Index a memory by context keys.

        Args:
            memory: Memory to index
        """
        for key in memory.context:
            if key not in self._indices:
                self._indices[key] = []
            self._indices[key].append(memory)

    def _remove_from_indices(self, memory: Memory) -> None:
        """Remove a memory from indices.

        Args:
            memory: Memory to remove
        """
        for memories in self._indices.values():
            if memory in memories:
                memories.remove(memory)
