"""
Inventory Service compatibility module.

This module provides backward compatibility for imports that expect
the InventoryService to be in fs_agt_clean.services.inventory_service.
"""

# Import from the actual location and create alias
from fs_agt_clean.services.inventory.service import InventoryManagementService

# Create alias for backward compatibility
InventoryService = InventoryManagementService

# Export for wildcard imports
__all__ = ["InventoryService", "InventoryManagementService"]
