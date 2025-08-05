"""
Logistics AutonomousAgents for FlipSync.

This module contains logistics-related agents including shipping and warehouse management.
"""

# AI Logistics AutonomousAgent removed - redundant conversational wrapper
AI_LOGISTICS_AVAILABLE = False

# Import legacy agents with fallback handling
try:
    pass

    LOGISTICS_AGENT_AVAILABLE = True
except ImportError:
    LOGISTICS_AGENT_AVAILABLE = False

try:
    pass

    WAREHOUSE_AGENT_AVAILABLE = True
except ImportError:
    WAREHOUSE_AGENT_AVAILABLE = False

# Only import shipping agent if dependencies are available
try:
    pass

    SHIPPING_AGENT_AVAILABLE = True
except ImportError:
    SHIPPING_AGENT_AVAILABLE = False

# Import sync agent for cross-platform synchronization
try:
    pass

    SYNC_AGENT_AVAILABLE = True
except ImportError:
    SYNC_AGENT_AVAILABLE = False

# Build __all__ list based on available imports
__all__ = []
# AI_LOGISTICS_AVAILABLE removed - redundant conversational wrapper
if LOGISTICS_AGENT_AVAILABLE:
    __all__.append("LogisticsAutonomousAgent")
if WAREHOUSE_AGENT_AVAILABLE:
    __all__.append("WarehouseAutonomousAgent")
if SHIPPING_AGENT_AVAILABLE:
    __all__.append("ShippingAutonomousAgent")
if SYNC_AGENT_AVAILABLE:
    __all__.append("SyncAutonomousAgent")
