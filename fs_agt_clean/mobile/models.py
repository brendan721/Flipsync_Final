"""Mobile-specific models for FlipSync."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

from pydantic import BaseModel, ConfigDict, Field


class AccountType(str, Enum):
    """Account type enum."""

    SELLER = "seller"
    BUYER = "buyer"
    ADMIN = "admin"


class AccountStatus(str, Enum):
    """Account status enum."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    CLOSED = "closed"


class UnifiedUserRole(str, Enum):
    """UnifiedUser role enum."""

    ADMIN = "admin"
    USER = "user"
    AGENT = "agent"
    OWNER = "owner"
    MANAGER = "manager"
    VIEWER = "viewer"


class ResourceType(str, Enum):
    """Resource type enum."""

    API_CALLS = "api_calls"
    STORAGE = "storage"
    BANDWIDTH = "bandwidth"
    LISTINGS = "listings"
    ORDERS = "orders"
    INVENTORY = "inventory"
    REPORTS = "reports"
    ANALYTICS = "analytics"


class ResourceQuota(BaseModel):
    """Resource quota model."""

    resource_type: Union[str, ResourceType]
    limit: int
    used: int = 0
    last_updated: datetime = Field(default_factory=datetime.now)
    alerts_enabled: bool = True
    alert_threshold: float = 0.8


class ResourceUsage(BaseModel):
    """Resource usage model."""

    seller_id: str
    resource_type: Union[str, ResourceType]
    amount: int
    timestamp: datetime = Field(default_factory=datetime.now)
    success: bool = True
    details: Dict[str, Any] = Field(default_factory=dict)


class UnifiedUserAccount(BaseModel):
    """UnifiedUser account model."""

    id: str
    email: str
    role: Union[str, UnifiedUserRole] = UnifiedUserRole.USER
    status: Union[str, AccountStatus] = AccountStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    permissions: Set[str] = Field(default_factory=set)
    api_key: Optional[str] = None
    quota_multiplier: float = 1.0


class Account(BaseModel):
    """Simplified account model for mobile use.

    This is a simplified version of the Account model from
    fs_agt.core.models.account to avoid circular imports in mobile modules.
    """

    id: str
    email: str
    username: str = ""
    name: str = ""
    account_type: Union[str, AccountType] = AccountType.SELLER
    status: Union[str, AccountStatus] = AccountStatus.ACTIVE
    users: List[UnifiedUserAccount] = Field(default_factory=list)
    quotas: Dict[str, ResourceQuota] = Field(default_factory=dict)
    usage_metrics: Dict[str, List[ResourceUsage]] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    features_enabled: Set[str] = Field(default_factory=set)
    performance_score: float = 1.0
    settings: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True
