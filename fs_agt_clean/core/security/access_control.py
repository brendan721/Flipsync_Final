"""Access control service for managing roles, permissions, and security policies."""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from fs_agt_clean.core.utils.config import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass
class UnifiedUserSession:
    """Track user session information."""

    user_id: str
    roles: List[str]
    mfa_verified: bool = False
    mfa_grace_until: Optional[float] = None
    last_activity: float = field(default_factory=time.time)
    permissions_cache: Dict[str, bool] = field(default_factory=dict)


class AccessControlService:
    """Service for managing user permissions and access control."""

    def __init__(self):
        """Initialize the access control service."""
        self.logger = logging.getLogger(__name__)
        self.settings: Settings = get_settings()
        self.rules: Dict[str, Any] = getattr(self.settings, "access_control_rules", {})
        if not self.rules:
            raise ValueError("Access control configuration not found")
        self.active_sessions: Dict[str, UnifiedUserSession] = {}
        self.roles: Dict[str, Any] = {}
        self.permissions: Dict[str, Any] = {}
        self.resources: Dict[str, Any] = {}
        self.policies: Dict[str, Any] = {}
        self._load_rbac_config()

    def _load_rbac_config(self) -> None:
        """Load RBAC configuration."""
        self.roles = self.rules.get("roles", {})
        self.permissions = self.rules.get("permissions", {})
        self.resources = self.rules.get("resources", {})
        self.policies = self.rules.get("policies", {})

    def create_session(self, user_id: str, roles: List[str]) -> UnifiedUserSession:
        """Create a new user session.

        Args:
            user_id: UnifiedUser identifier
            roles: List of role names assigned to user

        Returns:
            New user session
        """
        session = UnifiedUserSession(user_id=user_id, roles=roles)
        self.active_sessions[user_id] = session
        return session

    def check_permission(
        self, session: UnifiedUserSession, permission: str, resource: Optional[str] = None
    ) -> bool:
        """Check if user has required permission.

        Args:
            session: UnifiedUser session
            permission: Permission to check (format: "category:action")
            resource: Optional specific resource to check

        Returns:
            True if user has permission, False otherwise
        """
        # Check MFA requirements first
        requires_mfa = self._requires_mfa(session.roles, permission)
        if requires_mfa:
            if not session.mfa_verified:
                if not self._check_mfa_grace_period(session):
                    logger.warning("MFA required for %s but not verified", permission)
                    # Clear any cached permission when MFA is required but not verified
                    cache_key = f"{permission}:{resource}" if resource else permission
                    session.permissions_cache.pop(cache_key, None)
                    return False

        # Check cache after MFA verification
        cache_key = f"{permission}:{resource}" if resource else permission
        if cache_key in session.permissions_cache:
            # If MFA is required, verify it's still valid
            if requires_mfa and not session.mfa_verified:
                if not self._check_mfa_grace_period(session):
                    session.permissions_cache.pop(cache_key, None)
                    return False
            return session.permissions_cache[cache_key]

        has_permission = False

        # Admin role check
        if "admin" in session.roles:
            has_permission = True
        else:
            # Check role permissions
            for role in session.roles:
                role_config = self.roles.get(role)
                if not role_config:
                    continue

                # Check for global wildcard
                if "*" in role_config["permissions"]:
                    has_permission = True
                    break

                # Check for category wildcard
                category = permission.split(":")[0]
                if f"{category}:*" in role_config["permissions"]:
                    if not resource or self._check_resource_access(
                        permission, resource
                    ):
                        has_permission = True
                        break

                # Check specific permission
                if permission in role_config["permissions"]:
                    if not resource or self._check_resource_access(
                        permission, resource
                    ):
                        has_permission = True
                        break

        # Only cache and return true if MFA requirements are met
        if has_permission:
            if (
                requires_mfa
                and not session.mfa_verified
                and not self._check_mfa_grace_period(session)
            ):
                return False
            session.permissions_cache[cache_key] = True
            return True

        session.permissions_cache[cache_key] = False
        return False

    def _check_resource_access(self, permission: str, resource: str) -> bool:
        """Check if resource access is allowed.

        Args:
            permission: Permission being checked
            resource: Resource being accessed

        Returns:
            True if access is allowed, False otherwise
        """
        category, action = permission.split(":")
        perm_config = self.permissions.get(category, {}).get(action, {})
        if not perm_config or "resources" not in perm_config:
            return False
        return resource in perm_config["resources"] or "*" in perm_config["resources"]

    def _requires_mfa(self, roles: List[str], permission: str) -> bool:
        """Check if MFA is required for the given roles and permission.

        Args:
            roles: UnifiedUser roles
            permission: Permission being checked

        Returns:
            True if MFA is required, False otherwise
        """
        if not self.rules["session"]["mfa"]["enabled"]:
            return False

        # Check role-based MFA requirements
        required_roles = set(self.policies["mfa"]["required_for_roles"])
        if any(role in required_roles for role in roles):
            return True

        # Check action-based MFA requirements
        required_actions = set(self.policies["mfa"]["required_for_actions"])

        # Check exact permission match
        if permission in required_actions:
            return True

        # Check category wildcard match
        category = permission.split(":")[0]
        return f"{category}:*" in required_actions

    def _check_mfa_grace_period(self, session: UnifiedUserSession) -> bool:
        """Check if user is within MFA grace period.

        Args:
            session: UnifiedUser session

        Returns:
            True if within grace period, False otherwise
        """
        if not session.mfa_grace_until:
            grace_period = self.policies["mfa"]["grace_period"]
            session.mfa_grace_until = time.time() + grace_period
            return True

        # Clear permission cache if grace period expires
        if time.time() >= session.mfa_grace_until:
            session.permissions_cache.clear()
            return False

        return True

    def verify_mfa(self, session: UnifiedUserSession) -> None:
        """Mark MFA as verified for the session.

        Args:
            session: UnifiedUser session
        """
        # Clear permission cache since MFA status is changing
        session.permissions_cache.clear()
        session.mfa_verified = True
        session.mfa_grace_until = None

    def get_user_permissions(self, session: UnifiedUserSession) -> Set[str]:
        """Get all permissions for a user.

        Args:
            session: UnifiedUser session

        Returns:
            Set of permissions
        """
        permissions = set()
        for role in session.roles:
            role_config = self.roles.get(role)
            if not role_config:
                continue

            # Handle global wildcard
            if "*" in role_config["permissions"]:
                for category, actions in self.permissions.items():
                    for action in actions:
                        permissions.add(f"{category}:{action}")
                continue

            # Handle category wildcards and specific permissions
            for permission in role_config["permissions"]:
                if permission.endswith(":*"):
                    category = permission.split(":")[0]
                    if category in self.permissions:
                        for action in self.permissions[category]:
                            permissions.add(f"{category}:{action}")
                elif permission in self.permissions.get(permission.split(":")[0], {}):
                    permissions.add(permission)

        return permissions

    def check_password_policy(self, password: str) -> Tuple[bool, Optional[str]]:
        """Check if password meets policy requirements.

        Args:
            password: Password to check

        Returns:
            Tuple of (valid, reason)
        """
        policy = self.policies["password"]
        if len(password) < policy["min_length"]:
            return (
                False,
                f"Password must be at least {policy['min_length']} characters",
            )
        if policy["require_uppercase"] and (not any((c.isupper() for c in password))):
            return (False, "Password must contain uppercase letters")
        if policy["require_lowercase"] and (not any((c.islower() for c in password))):
            return (False, "Password must contain lowercase letters")
        if policy["require_numbers"] and (not any((c.isdigit() for c in password))):
            return (False, "Password must contain numbers")
        if policy["require_special"] and (not any((not c.isalnum() for c in password))):
            return (False, "Password must contain special characters")
        return (True, None)

    def check_lockout_status(
        self, user_id: str, failed_attempts: int
    ) -> Tuple[bool, Optional[int]]:
        """Check if account should be locked.

        Args:
            user_id: UnifiedUser identifier
            failed_attempts: Number of failed login attempts

        Returns:
            Tuple of (should_lock, lockout_duration)
        """
        policy = self.policies["lockout"]
        if failed_attempts >= policy["max_attempts"]:
            return (True, policy["lockout_duration"])
        return (False, None)
