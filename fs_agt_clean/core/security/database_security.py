"""
Database Security Module

This module provides security features for database operations, including:
1. Row-level security
2. Data access auditing
3. Permission checking
4. Query sanitization
5. Sensitive data masking
"""

import asyncio
import functools
import inspect
import logging
import time
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

from sqlalchemy import Column, String, event, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Session

from fs_agt_clean.core.security.access_control import AccessControl, UnifiedUserSession
from fs_agt_clean.core.utils.logging import get_logger

logger = get_logger(__name__)

# Type variables for generic functions
T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


class SecurityLevel(str, Enum):
    """Security levels for database operations."""

    PUBLIC = "public"
    PROTECTED = "protected"
    PRIVATE = "private"
    SENSITIVE = "sensitive"


class DataCategory(str, Enum):
    """Data categories for compliance and auditing."""

    GENERAL = "general"
    PERSONAL = "personal"
    FINANCIAL = "financial"
    HEALTH = "health"
    CONFIDENTIAL = "confidential"


class DatabaseAction(str, Enum):
    """Database actions for permission checking."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    SEARCH = "search"


class DatabaseSecurityManager:
    """
    Database security manager for enforcing security policies.

    This class provides methods for enforcing security policies on database operations,
    including row-level security, data access auditing, and permission checking.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure only one security manager exists."""
        if cls._instance is None:
            cls._instance = super(DatabaseSecurityManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        access_control: Optional[AccessControl] = None,
        enable_row_level_security: bool = True,
        enable_auditing: bool = True,
        enable_permission_checking: bool = True,
        enable_data_masking: bool = True,
    ):
        """
        Initialize the database security manager.

        Args:
            access_control: Access control manager
            enable_row_level_security: Whether to enable row-level security
            enable_auditing: Whether to enable data access auditing
            enable_permission_checking: Whether to enable permission checking
            enable_data_masking: Whether to enable sensitive data masking
        """
        if self._initialized:
            return

        self.access_control = access_control or AccessControl()
        self.enable_row_level_security = enable_row_level_security
        self.enable_auditing = enable_auditing
        self.enable_permission_checking = enable_permission_checking
        self.enable_data_masking = enable_data_masking

        # Security policies by model
        self._security_policies: Dict[str, Dict[str, Any]] = {}

        # Audit log queue
        self._audit_queue: asyncio.Queue = asyncio.Queue()

        # Start audit log processor
        if self.enable_auditing:
            self._start_audit_processor()

        self._initialized = True
        logger.info("Database security manager initialized")

    def _start_audit_processor(self) -> None:
        """Start the audit log processor."""
        asyncio.create_task(self._process_audit_logs())
        logger.info("Audit log processor started")

    async def _process_audit_logs(self) -> None:
        """Process audit logs from the queue."""
        while True:
            try:
                # Get audit log from queue
                audit_log = await self._audit_queue.get()

                # Process audit log (in a real implementation, this would write to a database or log file)
                logger.info("Audit log: %s", audit_log)

                # Mark task as done
                self._audit_queue.task_done()
            except Exception as e:
                logger.error("Error processing audit log: %s", e)
                await asyncio.sleep(1)  # Avoid tight loop on error

    def register_security_policy(
        self,
        model_class: Type[DeclarativeBase],
        owner_column: Optional[str] = None,
        security_level: SecurityLevel = SecurityLevel.PROTECTED,
        data_category: DataCategory = DataCategory.GENERAL,
        permission_prefix: Optional[str] = None,
        sensitive_columns: Optional[List[str]] = None,
    ) -> None:
        """
        Register a security policy for a model.

        Args:
            model_class: The model class
            owner_column: The column that identifies the owner of the record
            security_level: The security level of the model
            data_category: The data category of the model
            permission_prefix: The permission prefix for the model
            sensitive_columns: List of sensitive columns to mask
        """
        model_name = model_class.__name__

        # Create security policy
        policy = {
            "model_class": model_class,
            "owner_column": owner_column,
            "security_level": security_level,
            "data_category": data_category,
            "permission_prefix": permission_prefix or model_name.lower(),
            "sensitive_columns": sensitive_columns or [],
        }

        # Register policy
        self._security_policies[model_name] = policy
        logger.info("Registered security policy for %s", model_name)

    def get_security_policy(self, model_class: Type[DeclarativeBase]) -> Dict[str, Any]:
        """
        Get the security policy for a model.

        Args:
            model_class: The model class

        Returns:
            The security policy
        """
        model_name = model_class.__name__

        # Get policy
        policy = self._security_policies.get(model_name)

        # If no policy exists, create a default one
        if not policy:
            policy = {
                "model_class": model_class,
                "owner_column": None,
                "security_level": SecurityLevel.PROTECTED,
                "data_category": DataCategory.GENERAL,
                "permission_prefix": model_name.lower(),
                "sensitive_columns": [],
            }
            self._security_policies[model_name] = policy

        return policy

    async def check_permission(
        self,
        session: UnifiedUserSession,
        model_class: Type[DeclarativeBase],
        action: DatabaseAction,
        resource_id: Optional[str] = None,
    ) -> bool:
        """
        Check if a user has permission to perform an action on a model.

        Args:
            session: The user session
            model_class: The model class
            action: The database action
            resource_id: Optional resource ID for specific resource checks

        Returns:
            True if the user has permission, False otherwise
        """
        if not self.enable_permission_checking:
            return True

        # Get security policy
        policy = self.get_security_policy(model_class)

        # Build permission string
        permission = f"{policy['permission_prefix']}:{action.value}"

        # Check permission
        return await self.access_control.has_permission(
            session, permission, resource_id
        )

    async def apply_row_level_security(
        self,
        session: UnifiedUserSession,
        model_class: Type[DeclarativeBase],
        query: Any,
    ) -> Any:
        """
        Apply row-level security to a query.

        Args:
            session: The user session
            model_class: The model class
            query: The query to modify

        Returns:
            The modified query
        """
        if not self.enable_row_level_security:
            return query

        # Get security policy
        policy = self.get_security_policy(model_class)

        # If no owner column, return query as is
        if not policy["owner_column"]:
            return query

        # If user is admin, return query as is
        if "admin" in session.roles:
            return query

        # Apply row-level security
        owner_column = getattr(model_class, policy["owner_column"])
        return query.where(owner_column == session.user_id)

    def mask_sensitive_data(
        self,
        session: UnifiedUserSession,
        model_class: Type[DeclarativeBase],
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Mask sensitive data in a record.

        Args:
            session: The user session
            model_class: The model class
            data: The record data

        Returns:
            The masked data
        """
        if not self.enable_data_masking:
            return data

        # Get security policy
        policy = self.get_security_policy(model_class)

        # If no sensitive columns, return data as is
        if not policy["sensitive_columns"]:
            return data

        # If user is admin, return data as is
        if "admin" in session.roles:
            return data

        # Create a copy of the data
        masked_data = data.copy()

        # Mask sensitive columns
        for column in policy["sensitive_columns"]:
            if column in masked_data:
                masked_data[column] = "********"

        return masked_data

    async def audit_access(
        self,
        session: UnifiedUserSession,
        model_class: Type[DeclarativeBase],
        action: DatabaseAction,
        resource_id: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Audit a database access.

        Args:
            session: The user session
            model_class: The model class
            action: The database action
            resource_id: Optional resource ID
            success: Whether the access was successful
            details: Optional additional details
        """
        if not self.enable_auditing:
            return

        # Get security policy
        policy = self.get_security_policy(model_class)

        # Create audit log
        audit_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": session.user_id,
            "action": action.value,
            "model": model_class.__name__,
            "resource_id": resource_id,
            "security_level": policy["security_level"],
            "data_category": policy["data_category"],
            "success": success,
            "details": details or {},
        }

        # Add to audit queue
        await self._audit_queue.put(audit_log)


# Decorator for securing repository methods
def secure_operation(
    action: DatabaseAction,
    audit: bool = True,
    check_permission: bool = True,
    apply_rls: bool = True,
    mask_data: bool = True,
) -> Callable[[F], F]:
    """
    Decorator for securing repository methods.

    Args:
        action: The database action
        audit: Whether to audit the operation
        check_permission: Whether to check permission
        apply_rls: Whether to apply row-level security
        mask_data: Whether to mask sensitive data

    Returns:
        The decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Get security manager
            security_manager = DatabaseSecurityManager()

            # Get user session from repository
            session = getattr(self, "user_session", None)
            if not session:
                # If no user session, proceed without security
                return await func(self, *args, **kwargs)

            # Get model class from repository
            model_class = getattr(self, "model_class", None)
            if not model_class:
                # If no model class, proceed without security
                return await func(self, *args, **kwargs)

            # Get resource ID if available
            resource_id = None
            if args and isinstance(args[0], str):
                resource_id = args[0]
            elif "id" in kwargs:
                resource_id = kwargs["id"]

            # Check permission
            if check_permission:
                has_permission = await security_manager.check_permission(
                    session, model_class, action, resource_id
                )
                if not has_permission:
                    if audit:
                        await security_manager.audit_access(
                            session,
                            model_class,
                            action,
                            resource_id,
                            False,
                            {"error": "Permission denied"},
                        )
                    raise PermissionError(
                        f"Permission denied: {action.value} {model_class.__name__}"
                    )

            try:
                # Apply row-level security if needed
                if apply_rls and action in [
                    DatabaseAction.READ,
                    DatabaseAction.LIST,
                    DatabaseAction.SEARCH,
                ]:
                    # Get the query argument
                    sig = inspect.signature(func)
                    param_names = list(sig.parameters.keys())

                    # If the function has a query parameter, apply RLS
                    if "query" in param_names:
                        query_index = param_names.index("query")
                        if query_index < len(args):
                            # Query is in args
                            args_list = list(args)
                            args_list[query_index] = (
                                await security_manager.apply_row_level_security(
                                    session, model_class, args_list[query_index]
                                )
                            )
                            args = tuple(args_list)
                        elif "query" in kwargs:
                            # Query is in kwargs
                            kwargs["query"] = (
                                await security_manager.apply_row_level_security(
                                    session, model_class, kwargs["query"]
                                )
                            )

                # Execute the function
                result = await func(self, *args, **kwargs)

                # Mask sensitive data if needed
                if mask_data and result:
                    if isinstance(result, dict):
                        result = security_manager.mask_sensitive_data(
                            session, model_class, result
                        )
                    elif isinstance(result, list):
                        result = [
                            (
                                security_manager.mask_sensitive_data(
                                    session, model_class, item
                                )
                                if isinstance(item, dict)
                                else item
                            )
                            for item in result
                        ]
                    elif hasattr(result, "to_dict"):
                        # If result has a to_dict method, use it
                        data = result.to_dict()
                        masked_data = security_manager.mask_sensitive_data(
                            session, model_class, data
                        )

                        # Apply masked data back to result if possible
                        for key, value in masked_data.items():
                            if hasattr(result, key):
                                setattr(result, key, value)

                # Audit access
                if audit:
                    await security_manager.audit_access(
                        session, model_class, action, resource_id, True
                    )

                return result
            except Exception as e:
                # Audit access failure
                if audit:
                    await security_manager.audit_access(
                        session,
                        model_class,
                        action,
                        resource_id,
                        False,
                        {"error": str(e)},
                    )
                raise

        return cast(F, wrapper)

    return decorator


# Permission errors
class PermissionError(Exception):
    """Exception raised when a user does not have permission to perform an action."""

    pass


# Row-level security errors
class RowLevelSecurityError(Exception):
    """Exception raised when row-level security prevents an action."""

    pass
