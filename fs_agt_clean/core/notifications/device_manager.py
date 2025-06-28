"""
Device Manager compatibility module.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DeviceManager:
    """Simple device manager for compatibility."""

    def __init__(self):
        """Initialize device manager."""
        self._devices = {}

    async def register_device(
        self, device_id: str, device_info: Dict[str, Any]
    ) -> bool:
        """Register a device."""
        self._devices[device_id] = device_info
        return True

    async def unregister_device(self, device_id: str) -> bool:
        """Unregister a device."""
        return self._devices.pop(device_id, None) is not None

    async def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get device information."""
        return self._devices.get(device_id)

    async def list_devices(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List devices."""
        devices = list(self._devices.values())
        if user_id:
            devices = [d for d in devices if d.get("user_id") == user_id]
        return devices
