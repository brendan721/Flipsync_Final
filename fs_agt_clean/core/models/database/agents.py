"""Agent database models for FlipSync."""

import enum
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from .base import Base


class AgentType(enum.Enum):
    """Agent type enumeration."""

    MARKET_SPECIALIST = "MARKET_SPECIALIST"
    INVENTORY_MANAGER = "INVENTORY_MANAGER"
    PRICING_ANALYST = "PRICING_ANALYST"
    EXECUTIVE = "EXECUTIVE"
    AMAZON_AGENT = "AMAZON_AGENT"
    EBAY_AGENT = "EBAY_AGENT"
    ADVERTISING_AGENT = "ADVERTISING_AGENT"
    TREND_DETECTOR = "TREND_DETECTOR"
    COMPETITOR_ANALYZER = "COMPETITOR_ANALYZER"
    MARKET_ANALYZER = "MARKET_ANALYZER"
    STRATEGY_AGENT = "STRATEGY_AGENT"
    RESOURCE_AGENT = "RESOURCE_AGENT"
    ORCHESTRATOR = "ORCHESTRATOR"
    DECISION_ENGINE = "DECISION_ENGINE"
    SHIPPING_AGENT = "SHIPPING_AGENT"
    WAREHOUSE_AGENT = "WAREHOUSE_AGENT"
    LISTING_AGENT = "LISTING_AGENT"
    IMAGE_AGENT = "IMAGE_AGENT"


class AgentStatus(enum.Enum):
    """Agent status enumeration."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    INITIALIZING = "INITIALIZING"
    ERROR = "ERROR"
    MAINTENANCE = "MAINTENANCE"


class AgentPriority(enum.Enum):
    """Agent priority enumeration."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AgentModel(Base):
    """SQLAlchemy model for agents."""

    __tablename__ = "agents"

    # Primary key
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Basic agent information
    name = Column(String(255), nullable=False)
    agent_type = Column(Enum(AgentType), nullable=False)
    status = Column(Enum(AgentStatus), nullable=False, default=AgentStatus.INITIALIZING)
    priority = Column(Enum(AgentPriority), nullable=False, default=AgentPriority.MEDIUM)

    # Agent configuration
    capabilities = Column(JSON, nullable=True, default=list)
    configuration = Column(JSON, nullable=True, default=dict)
    authority_level = Column(
        Enum(AgentPriority), nullable=False, default=AgentPriority.MEDIUM
    )

    # Agent state and metrics
    last_activity = Column(DateTime(timezone=True), nullable=True)
    health_status = Column(String(50), nullable=True, default="unknown")
    error_count = Column(Integer, nullable=False, default=0)
    success_count = Column(Integer, nullable=False, default=0)

    # Performance metrics
    average_response_time = Column(Float, nullable=True)
    total_tasks_completed = Column(Integer, nullable=False, default=0)
    total_decisions_made = Column(Integer, nullable=False, default=0)

    # Agent metadata
    description = Column(Text, nullable=True)
    version = Column(String(50), nullable=True, default="1.0.0")
    tags = Column(JSON, nullable=True, default=list)

    # Relationships and dependencies
    parent_agent_id = Column(String(255), nullable=True)
    managed_resources = Column(JSON, nullable=True, default=list)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self):
        return f"<AgentModel(id='{self.id}', name='{self.name}', type='{self.agent_type}', status='{self.status}')>"

    def to_dict(self) -> Dict:
        """Convert agent model to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "agent_type": self.agent_type.value if self.agent_type else None,
            "status": self.status.value if self.status else None,
            "priority": self.priority.value if self.priority else None,
            "capabilities": self.capabilities or [],
            "configuration": self.configuration or {},
            "authority_level": (
                self.authority_level.value if self.authority_level else None
            ),
            "last_activity": (
                self.last_activity.isoformat() if self.last_activity else None
            ),
            "health_status": self.health_status,
            "error_count": self.error_count,
            "success_count": self.success_count,
            "average_response_time": self.average_response_time,
            "total_tasks_completed": self.total_tasks_completed,
            "total_decisions_made": self.total_decisions_made,
            "description": self.description,
            "version": self.version,
            "tags": self.tags or [],
            "parent_agent_id": self.parent_agent_id,
            "managed_resources": self.managed_resources or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "AgentModel":
        """Create agent model from dictionary."""
        agent = cls()

        # Set basic fields
        if "id" in data:
            agent.id = data["id"]
        if "name" in data:
            agent.name = data["name"]
        if "agent_type" in data:
            agent.agent_type = AgentType(data["agent_type"])
        if "status" in data:
            agent.status = AgentStatus(data["status"])
        if "priority" in data:
            agent.priority = AgentPriority(data["priority"])

        # Set configuration fields
        if "capabilities" in data:
            agent.capabilities = data["capabilities"]
        if "configuration" in data:
            agent.configuration = data["configuration"]
        if "authority_level" in data:
            agent.authority_level = AgentPriority(data["authority_level"])

        # Set metadata fields
        if "description" in data:
            agent.description = data["description"]
        if "version" in data:
            agent.version = data["version"]
        if "tags" in data:
            agent.tags = data["tags"]
        if "parent_agent_id" in data:
            agent.parent_agent_id = data["parent_agent_id"]
        if "managed_resources" in data:
            agent.managed_resources = data["managed_resources"]

        return agent

    def update_metrics(
        self, response_time: Optional[float] = None, success: bool = True
    ):
        """Update agent performance metrics."""
        if success:
            self.success_count += 1
        else:
            self.error_count += 1

        if response_time is not None:
            if self.average_response_time is None:
                self.average_response_time = response_time
            else:
                # Calculate rolling average
                total_calls = self.success_count + self.error_count
                self.average_response_time = (
                    self.average_response_time * (total_calls - 1) + response_time
                ) / total_calls

        self.last_activity = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def update_status(self, status: AgentStatus, health_status: Optional[str] = None):
        """Update agent status and health."""
        self.status = status
        if health_status:
            self.health_status = health_status
        self.last_activity = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
