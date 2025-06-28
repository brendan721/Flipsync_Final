"""Memory management system for the brain service."""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class MemoryManager:
    """Manages different types of memory for the brain system including:
    - Short-term memory for recent events and data
    - Long-term memory for historical data
    - Working memory for active processing
    """

    def __init__(self):
        """Initialize memory storage."""
        self._short_term: List[Dict[str, Any]] = []
        self._long_term: List[Dict[str, Any]] = []
        self._working_memory: Dict[str, Any] = {}
        self._max_short_term = 1000

    async def store_short_term(self, data: Dict[str, Any]) -> None:
        """Store data in short-term memory."""
        data["timestamp"] = datetime.now()
        self._short_term.append(data)
        if len(self._short_term) > self._max_short_term:
            await self._archive_oldest_short_term()

    async def store_long_term(self, data: Dict[str, Any]) -> None:
        """Store data in long-term memory."""
        data["timestamp"] = datetime.now()
        self._long_term.append(data)

    async def get_short_term(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get recent items from short-term memory."""
        if limit is None:
            return self._short_term
        return self._short_term[-limit:]

    async def get_working_memory(self) -> Dict[str, Any]:
        """Get current working memory state."""
        return self._working_memory

    async def update_working_memory(self, data: Dict[str, Any]) -> None:
        """Update working memory with new data."""
        self._working_memory.update(data)

    async def get_memory_stats(self) -> Dict[str, float]:
        """Get memory usage statistics."""
        return {
            "short_term_size": len(self._short_term),
            "long_term_size": len(self._long_term),
            "working_memory_size": len(self._working_memory),
            "short_term_utilization": len(self._short_term) / self._max_short_term,
        }

    async def clear_all(self) -> None:
        """Clear all memory stores."""
        self._short_term.clear()
        self._long_term.clear()
        self._working_memory.clear()

    async def _archive_oldest_short_term(self) -> None:
        """Move oldest short-term memory to long-term storage."""
        oldest = self._short_term.pop(0)
        await self.store_long_term(oldest)
