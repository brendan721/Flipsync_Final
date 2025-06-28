"""
Feature flag management system.

This module provides a feature flag management system for dynamically
enabling and disabling features without code deployment.
"""

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union

from pydantic import BaseModel, ConfigDict, Field, validator

logger = logging.getLogger(__name__)


class FeatureFlag(BaseModel):
    """Feature flag model."""

    key: str = Field(..., description="Unique key for the feature flag")
    enabled: bool = Field(False, description="Whether the feature is enabled")
    description: str = Field("", description="Description of the feature flag")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Last update timestamp"
    )
    group: str = Field("default", description="Feature flag group for organization")
    owner: str = Field("system", description="Owner of the feature flag")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @validator("updated_at", pre=True, always=True)
    def update_timestamps(cls, v: Any, values: Dict[str, Any]) -> datetime:
        """Update timestamps on validation."""
        return datetime.now()


class FeatureFlagStorage(BaseModel):
    """Feature flag storage model."""

    flags: Dict[str, FeatureFlag] = Field(
        default_factory=dict, description="Dictionary of feature flags"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Last update timestamp"
    )


class FeatureFlagService:
    """Service for managing feature flags."""

    def __init__(self, storage_path: Union[str, Path]):
        """Initialize the feature flag service.

        Args:
            storage_path: Path to the feature flag storage file
        """
        self.storage_path = Path(storage_path)
        self.storage: FeatureFlagStorage = FeatureFlagStorage()
        self._last_read_time: float = 0
        self._read_interval: float = 5.0  # seconds
        self._initialized: bool = False
        self._change_listeners: List[Callable[[Dict[str, Dict[str, Any]]], None]] = []
        self._load()

    def _load(self) -> None:
        """Load feature flags from storage."""
        if not self.storage_path.exists():
            logger.info(
                "Feature flag storage file %s does not exist, creating default storage",
                self.storage_path,
            )
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self._initialized = True
            self._save()
            return

        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)

                # Convert raw data to FeatureFlagStorage
                flags = {}
                for key, flag_data in data.get("flags", {}).items():
                    # Convert string timestamps to datetime
                    if "created_at" in flag_data and isinstance(
                        flag_data["created_at"], str
                    ):
                        flag_data["created_at"] = datetime.fromisoformat(
                            flag_data["created_at"]
                        )
                    if "updated_at" in flag_data and isinstance(
                        flag_data["updated_at"], str
                    ):
                        flag_data["updated_at"] = datetime.fromisoformat(
                            flag_data["updated_at"]
                        )

                    flags[key] = FeatureFlag(**flag_data)

                last_updated = data.get("last_updated")
                if last_updated and isinstance(last_updated, str):
                    last_updated = datetime.fromisoformat(last_updated)
                else:
                    last_updated = datetime.now()

                self.storage = FeatureFlagStorage(
                    flags=flags, last_updated=last_updated
                )

                self._last_read_time = time.time()
                self._initialized = True
                logger.info(
                    "Loaded %s feature flags from %s", len(flags), self.storage_path
                )
        except Exception as e:
            logger.error("Error loading feature flags: %s", str(e))
            # Create default storage if loading fails
            self._initialized = True
            self._save()

    def _save(self) -> None:
        """Save feature flags to storage."""
        try:
            # Update last_updated timestamp
            self.storage.last_updated = datetime.now()

            # Convert to serializable dict
            data = {
                "flags": {key: flag.dict() for key, flag in self.storage.flags.items()},
                "last_updated": self.storage.last_updated.isoformat(),
            }

            # Create parent directories if they don't exist
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to file
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(
                "Saved %s feature flags to %s",
                len(self.storage.flags),
                self.storage_path,
            )
        except Exception as e:
            logger.error("Error saving feature flags: %s", str(e))

    def _check_for_changes(self) -> None:
        """Check for changes in the feature flag storage file."""
        current_time = time.time()
        if current_time - self._last_read_time < self._read_interval:
            return

        if not self.storage_path.exists():
            logger.warning(
                "Feature flag storage file %s does not exist", self.storage_path
            )
            return

        file_mtime = self.storage_path.stat().st_mtime
        if file_mtime > self._last_read_time:
            logger.info("Feature flag storage file has changed, reloading")
            old_flags = {key: flag.enabled for key, flag in self.storage.flags.items()}
            self._load()

            # Notify listeners of changes
            new_flags = {key: flag.enabled for key, flag in self.storage.flags.items()}
            self._notify_listeners(old_flags, new_flags)

    def _notify_listeners(
        self, old_flags: Dict[str, bool], new_flags: Dict[str, bool]
    ) -> None:
        """Notify listeners of feature flag changes.

        Args:
            old_flags: Previous state of feature flags
            new_flags: New state of feature flags
        """
        changes = {}

        # Find added, removed, and toggled flags
        for key, enabled in new_flags.items():
            if key not in old_flags:
                changes[key] = {"type": "added", "enabled": enabled}
            elif old_flags[key] != enabled:
                changes[key] = {"type": "toggled", "enabled": enabled}

        for key, enabled in old_flags.items():
            if key not in new_flags:
                changes[key] = {"type": "removed", "enabled": enabled}

        if not changes:
            return

        # Notify listeners
        for listener in self._change_listeners:
            try:
                listener(changes)
            except Exception as e:
                logger.error("Error notifying feature flag listener: %s", str(e))

    def add_change_listener(
        self, listener: Callable[[Dict[str, Dict[str, Any]]], None]
    ) -> None:
        """Add a listener for feature flag changes.

        Args:
            listener: Function to call when feature flags change
        """
        if listener not in self._change_listeners:
            self._change_listeners.append(listener)

    def remove_change_listener(
        self, listener: Callable[[Dict[str, Dict[str, Any]]], None]
    ) -> None:
        """Remove a listener for feature flag changes.

        Args:
            listener: Function to remove from listeners
        """
        if listener in self._change_listeners:
            self._change_listeners.remove(listener)

    def get_flag(self, key: str) -> Optional[FeatureFlag]:
        """Get a feature flag by key.

        Args:
            key: Feature flag key

        Returns:
            Feature flag or None if not found
        """
        self._check_for_changes()
        return self.storage.flags.get(key)

    def is_enabled(self, key: str, default: bool = False) -> bool:
        """Check if a feature flag is enabled.

        Args:
            key: Feature flag key
            default: Default value if flag is not found

        Returns:
            True if feature is enabled, False otherwise
        """
        self._check_for_changes()

        flag = self.storage.flags.get(key)
        if flag is None:
            return bool(default)

        return flag.enabled

    def set_enabled(
        self,
        key: str,
        enabled: bool,
        description: str = "",
        group: str = "default",
        owner: str = "system",
    ) -> FeatureFlag:
        """Enable or disable a feature flag.

        Args:
            key: Feature flag key
            enabled: Whether to enable the feature
            description: Description of the feature flag
            group: Feature flag group
            owner: Owner of the feature flag

        Returns:
            Updated feature flag
        """
        flag = self.storage.flags.get(key)

        if flag is None:
            # Create new flag
            flag = FeatureFlag(
                key=key,
                enabled=enabled,
                description=description or key,
                group=group,
                owner=owner,
            )
        else:
            # Update existing flag
            old_enabled = flag.enabled
            flag.enabled = enabled
            flag.updated_at = datetime.now()

            if description:
                flag.description = description

            if group != "default":
                flag.group = group

            if owner != "system":
                flag.owner = owner

            # Notify listeners if enabled state changed
            if old_enabled != enabled:
                self._notify_listeners({key: old_enabled}, {key: enabled})

        # Update storage
        self.storage.flags[key] = flag
        self._save()

        return flag

    def delete_flag(self, key: str) -> bool:
        """Delete a feature flag.

        Args:
            key: Feature flag key

        Returns:
            True if flag was deleted, False otherwise
        """
        if key not in self.storage.flags:
            return False

        old_enabled = self.storage.flags[key].enabled
        del self.storage.flags[key]
        self._save()

        # Notify listeners
        self._notify_listeners({key: old_enabled}, {})

        return True

    def list_flags(self, group: Optional[str] = None) -> List[FeatureFlag]:
        """List all feature flags.

        Args:
            group: Filter by group (optional)

        Returns:
            List of feature flags
        """
        self._check_for_changes()

        if group is None:
            return list(self.storage.flags.values())

        return [flag for flag in self.storage.flags.values() if flag.group == group]

    def list_groups(self) -> Set[str]:
        """List all feature flag groups.

        Returns:
            Set of group names
        """
        self._check_for_changes()

        return {flag.group for flag in self.storage.flags.values()}

    def list_owners(self) -> Set[str]:
        """List all feature flag owners.

        Returns:
            Set of owner names
        """
        self._check_for_changes()

        return {flag.owner for flag in self.storage.flags.values()}


# Singleton instance for application-wide feature flags
_instance: Optional[FeatureFlagService] = None


def init_feature_flags(storage_path: Union[str, Path]) -> FeatureFlagService:
    """Initialize the feature flag service.

    Args:
        storage_path: Path to the feature flag storage file

    Returns:
        Feature flag service instance
    """
    global _instance

    if _instance is None:
        _instance = FeatureFlagService(storage_path)

    return _instance


def get_feature_flags() -> FeatureFlagService:
    """Get the feature flag service instance.

    Returns:
        Feature flag service instance

    Raises:
        RuntimeError: If feature flag service is not initialized
    """
    if _instance is None:
        raise RuntimeError(
            "Feature flag service not initialized, call init_feature_flags first"
        )

    return _instance
