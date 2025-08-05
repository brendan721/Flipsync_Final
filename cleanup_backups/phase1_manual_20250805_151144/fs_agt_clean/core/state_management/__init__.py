"""
State Management initialization module for FlipSync.

This module initializes the state management system for FlipSync.
"""

from fs_agt_clean.core.state_management.middleware import (
    StateMiddleware,
    cleanup_state,
    setup_state_middleware,
)
from fs_agt_clean.core.state_management.state_manager import (
    CacheEntry,
    StateChange,
    StateChangeType,
    StateManager,
    StateMigration,
)

__all__ = [
    "CacheEntry",
    "StateChange",
    "StateChangeType",
    "StateManager",
    "StateMigration",
    "StateMiddleware",
    "cleanup_state",
    "setup_state_middleware",
]
