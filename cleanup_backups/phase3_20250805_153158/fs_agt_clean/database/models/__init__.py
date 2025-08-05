"""
Unified Database Models for FlipSync
====================================

This module exports all unified database models, eliminating previous duplication.
"""

from .metrics import *

# Import additional models needed by services
from .notification import *
from .unified_agent import *
from .autonomous_agent import *

# Import unified models
from .unified_base import *
from .unified_user import *

# Export all unified models
__all__ = [
    # Base classes
    "Base",
    "BaseModel",
    "AuditableModel",
    "MetadataModel",
    "FullFeaturedModel",
    # User models
    "UnifiedUser",
    "Role",
    "UserAccount",
    "UserSession",
    "UserResponse",
    "UserCreate",
    "UserUpdate",
    "LoginRequest",
    "LoginResponse",
    # Agent models (Legacy)
    "AutonomousAgent",
    "AgentDecision",
    "AgentTask",
    "AgentCommunication",
    "AgentPerformanceMetric",
    "AgentResponse",
    "AgentCreate",
    "AgentUpdate",
    "TaskResponse",
    "TaskCreate",
    # Autonomous Agent models (4+1 Architecture)
    "AutonomousAgent",
    "ConversationalInterface",
    "AutonomousAgentDecision",
    "AutonomousAgentResponse",
    "ConversationalInterfaceResponse",
    "AutonomousAgentDecisionResponse",
    "ArchitectureComplianceResponse",
    "AutonomousAgentType",
    "ConversationalInterfaceType",
    "AutonomousAgentStatus",
    # Enums
    "UserRole",
    "UserStatus",
    "AccountType",
    "AccountStatus",
    "MfaType",
    "AgentType",
    "AgentStatus",
    "AgentPriority",
    "TaskStatus",
    "DecisionStatus",
    # Notification models
    "Notification",
    "NotificationPriority",
    "NotificationStatus",
    "NotificationCategory",
    # Metrics models
    "Metric",
    "MetricSeries",
    "MetricAggregation",
    "MetricType",
    "MetricCategory",
    "MetricDataPoint",
    "SystemMetrics",
    "AutonomousAgentMetrics",
    "MetricThreshold",
]
