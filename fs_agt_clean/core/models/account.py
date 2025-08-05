"""
Account Models compatibility module.

This module provides backward compatibility for account model imports.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from fs_agt_clean.database.models.enums import AccountStatus, AccountType, UnifiedUserRole


@dataclass
class Account:
    """Account model."""

    id: str
    name: str
    type: AccountType = AccountType.BASIC
    status: AccountStatus = AccountStatus.ACTIVE
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class UnifiedUserAccount:
    """UnifiedUser account relationship model."""

    user_id: str
    account_id: str
    role: UnifiedUserRole = UnifiedUserRole.USER
    created_at: Optional[datetime] = None
    permissions: Optional[Dict[str, Any]] = None


# Re-export UnifiedUserRole for convenience
__all__ = ["Account", "UnifiedUserAccount", "UnifiedUserRole", "AccountStatus", "AccountType"]
