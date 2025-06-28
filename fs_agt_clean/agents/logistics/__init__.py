"""
Logistics UnifiedAgents for FlipSync.

This module contains logistics-related agents including shipping and warehouse management.
"""

# Import AI Logistics UnifiedAgent (Phase 2 implementation)
try:
    from .ai_logistics_agent import AILogisticsUnifiedAgent

    AI_LOGISTICS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: AI Logistics UnifiedAgent not available: {e}")
    AI_LOGISTICS_AVAILABLE = False

# Import legacy agents with fallback handling
try:
    from .logistics_agent import LogisticsUnifiedAgent

    LOGISTICS_AGENT_AVAILABLE = True
except ImportError:
    LOGISTICS_AGENT_AVAILABLE = False

try:
    from .warehouse_agent import WarehouseUnifiedAgent

    WAREHOUSE_AGENT_AVAILABLE = True
except ImportError:
    WAREHOUSE_AGENT_AVAILABLE = False

# Only import shipping agent if dependencies are available
try:
    from .shipping_agent import ShippingUnifiedAgent

    SHIPPING_AGENT_AVAILABLE = True
except ImportError:
    SHIPPING_AGENT_AVAILABLE = False

# Import sync agent for cross-platform synchronization
try:
    from .sync_agent import SyncUnifiedAgent

    SYNC_AGENT_AVAILABLE = True
except ImportError:
    SYNC_AGENT_AVAILABLE = False

# Build __all__ list based on available imports
__all__ = []
if AI_LOGISTICS_AVAILABLE:
    __all__.append("AILogisticsUnifiedAgent")
if LOGISTICS_AGENT_AVAILABLE:
    __all__.append("LogisticsUnifiedAgent")
if WAREHOUSE_AGENT_AVAILABLE:
    __all__.append("WarehouseUnifiedAgent")
if SHIPPING_AGENT_AVAILABLE:
    __all__.append("ShippingUnifiedAgent")
if SYNC_AGENT_AVAILABLE:
    __all__.append("SyncUnifiedAgent")
