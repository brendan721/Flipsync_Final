"""Security audit logging system for tracking security-related events."""

import json
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union
from uuid import uuid4

from pydantic import BaseModel, ConfigDict


# Simple VaultClient interface for audit logging
class VaultClient:
    def __init__(self):
        pass

    async def write_secret(self, path: str, data: dict) -> bool:
        return True

    async def read_secret(self, path: str) -> dict:
        return {}

    async def list_secrets(self, path: str) -> list:
        return []

    async def delete_secret(self, path: str) -> bool:
        return True


# For now, create a simple Permission enum until RBAC is migrated
from enum import Enum


class Permission(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


# Simple logger setup
import logging


def get_logger(name):
    return logging.getLogger(name)


logger = get_logger(__name__)


class AuditEventType(str, Enum):
    """Security audit event types."""

    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"

    # Authorization events
    ACCESS_DENIED = "access_denied"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REVOKED = "role_revoked"

    # Token events
    TOKEN_ISSUED = "token_issued"
    TOKEN_REVOKED = "token_revoked"
    TOKEN_REFRESH = "token_refresh"
    SECRET_ROTATED = "secret_rotated"

    # Resource events
    RESOURCE_ACCESS = "resource_access"
    RESOURCE_MODIFIED = "resource_modified"
    RESOURCE_DELETED = "resource_deleted"

    # System events
    CONFIG_CHANGE = "config_change"
    SYSTEM_ERROR = "system_error"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SECURITY_ALERT = "security_alert"


class AuditEvent(BaseModel):
    """Security audit event model."""

    id: str = str(uuid4())
    timestamp: datetime
    event_type: AuditEventType
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    resource: Optional[str] = None
    action: str
    status: str
    details: Dict[str, Any]
    metadata: Dict[str, Any] = {}


class SecurityAuditLogger:
    """Security audit logging service."""

    def __init__(self, vault_client: Optional[VaultClient] = None):
        """Initialize the security audit logger.

        Args:
            vault_client: Vault client for storing audit logs. If None, logs only to application logs.
        """
        self.vault_client = vault_client
        self.dev_mode = vault_client is None
        if self.dev_mode:
            logger.warning(
                "SecurityAuditLogger initialized in development mode - audit logs will not be stored in Vault"
            )

    async def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
        source_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """Log a security audit event.

        Args:
            event_type: Type of event
            user_id: ID of user performing action
            resource_id: ID of resource being accessed
            action: Specific action being performed
            status: Status of the event (success/error)
            details: Additional event details
            source_ip: Source IP address
            user_agent: UnifiedUser agent string

        Returns:
            bool: True if event was logged successfully
        """
        try:
            # Create audit log entry
            timestamp = datetime.now(timezone.utc).isoformat()

            event = {
                "timestamp": timestamp,
                "event_type": event_type,
                "status": status,
                "user_id": user_id,
                "resource_id": resource_id,
                "action": action,
                "source_ip": source_ip,
                "user_agent": user_agent,
                "details": details or {},
            }

            # Store in vault if available
            if not self.dev_mode and self.vault_client:
                await self.vault_client.write_secret(f"audit/logs/{timestamp}", event)

            # Also log to application logs
            log_msg = f"AUDIT: {event_type} - " f"Status: {status}" + (
                f", UnifiedUser: {user_id}" if user_id else ""
            ) + (f", Resource: {resource_id}" if resource_id else "") + (
                f", Action: {action}" if action else ""
            ) + (
                f", IP: {source_ip}" if source_ip else ""
            )

            if status == "success":
                logger.info(log_msg)
            else:
                logger.warning(log_msg)

            return True

        except Exception as e:
            logger.error("Failed to log audit event: %s", str(e))
            return False

    async def get_user_events(
        self,
        user_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_types: Optional[list[AuditEventType]] = None,
    ) -> list[Dict[str, Any]]:
        """Get audit events for a specific user.

        Args:
            user_id: UnifiedUser ID to get events for
            start_time: Optional start time filter
            end_time: Optional end time filter
            event_types: Optional list of event types to filter by

        Returns:
            List of audit events
        """
        if self.dev_mode or not self.vault_client:
            logger.warning("Cannot retrieve user events in development mode")
            return []

        try:
            # List all audit logs
            logs = await self.vault_client.list_secrets("audit/logs")
            events = []

            for log_id in logs:
                # Get log entry
                event = await self.vault_client.read_secret(f"audit/logs/{log_id}")
                if not event:
                    continue

                # Check if event matches filters
                if event.get("user_id") != user_id:
                    continue

                event_time = datetime.fromisoformat(event["timestamp"])

                if start_time and event_time < start_time:
                    continue

                if end_time and event_time > end_time:
                    continue

                if event_types and event["event_type"] not in event_types:
                    continue

                events.append(event)

            return sorted(events, key=lambda e: e["timestamp"])

        except Exception as e:
            logger.error("Failed to get user audit events: %s", str(e))
            return []

    async def get_resource_events(
        self,
        resource_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_types: Optional[list[AuditEventType]] = None,
    ) -> list[Dict[str, Any]]:
        """Get audit events for a specific resource.

        Args:
            resource_id: Resource ID to get events for
            start_time: Optional start time filter
            end_time: Optional end time filter
            event_types: Optional list of event types to filter by

        Returns:
            List of audit events
        """
        if self.dev_mode or not self.vault_client:
            logger.warning("Cannot retrieve resource events in development mode")
            return []

        try:
            # List all audit logs
            logs = await self.vault_client.list_secrets("audit/logs")
            events = []

            for log_id in logs:
                # Get log entry
                event = await self.vault_client.read_secret(f"audit/logs/{log_id}")
                if not event:
                    continue

                # Check if event matches filters
                if event.get("resource_id") != resource_id:
                    continue

                event_time = datetime.fromisoformat(event["timestamp"])

                if start_time and event_time < start_time:
                    continue

                if end_time and event_time > end_time:
                    continue

                if event_types and event["event_type"] not in event_types:
                    continue

                events.append(event)

            return sorted(events, key=lambda e: e["timestamp"])

        except Exception as e:
            logger.error("Failed to get resource audit events: %s", str(e))
            return []

    async def cleanup_old_logs(self, retention_days: int) -> bool:
        """Clean up audit logs older than retention period.

        Args:
            retention_days: Number of days to retain logs for

        Returns:
            True if cleanup successful
        """
        if self.dev_mode or not self.vault_client:
            logger.warning("Cannot clean up logs in development mode")
            return True

        try:
            # Calculate retention date
            retention_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

            # List all audit logs
            logs = await self.vault_client.list_secrets("audit/logs")
            deleted_count = 0

            for log_id in logs:
                try:
                    # Extract timestamp from log ID
                    log_timestamp = datetime.fromisoformat(log_id)

                    # Check if log is older than retention period
                    if log_timestamp < retention_date:
                        # Delete the log
                        await self.vault_client.delete_secret(f"audit/logs/{log_id}")
                        deleted_count += 1
                except (ValueError, TypeError):
                    logger.warning("Failed to parse timestamp from log ID: %s", log_id)
                    continue

            logger.info(
                "Cleaned up %d audit logs older than %d days",
                deleted_count,
                retention_days,
            )
            return True

        except Exception as e:
            logger.error("Failed to clean up old audit logs: %s", str(e))
            return False


class ComplianceAuditLogger(SecurityAuditLogger):
    """Compliance-focused audit logger for regulatory requirements."""

    def __init__(self, vault_client: Optional[VaultClient] = None):
        """Initialize the compliance audit logger.

        Args:
            vault_client: Vault client for storing audit logs.
        """
        super().__init__(vault_client)
        self.compliance_standards = {
            "gdpr": True,
            "hipaa": False,
            "pci_dss": False,
            "sox": False,
        }

    async def log_permission_change(
        self,
        user_id: str,
        permission: Permission,
        action: str,
        target_user_id: str,
        admin_id: str,
        source_ip: Optional[str] = None,
    ) -> bool:
        """Log permission change events for compliance purposes.

        Args:
            user_id: ID of user performing the action
            permission: Permission being modified
            action: Action being performed (grant/revoke)
            target_user_id: ID of user whose permissions are changing
            admin_id: ID of admin authorizing the change
            source_ip: Source IP address

        Returns:
            bool: True if event was logged successfully
        """
        details = {
            "permission": permission,
            "target_user_id": target_user_id,
            "admin_id": admin_id,
            "reason": "UnifiedUser permission change",
        }

        event_type = (
            AuditEventType.PERMISSION_GRANTED
            if action == "grant"
            else AuditEventType.PERMISSION_REVOKED
        )

        return await self.log_event(
            event_type=event_type,
            user_id=user_id,
            action=action,
            details=details,
            source_ip=source_ip,
        )

    async def log_data_access(
        self,
        user_id: str,
        data_type: str,
        resource_id: str,
        access_type: str,
        source_ip: Optional[str] = None,
    ) -> bool:
        """Log data access events for compliance purposes.

        Args:
            user_id: ID of user accessing data
            data_type: Type of data being accessed
            resource_id: ID of resource being accessed
            access_type: Type of access (read/write/delete)
            source_ip: Source IP address

        Returns:
            bool: True if event was logged successfully
        """
        details = {
            "data_type": data_type,
            "access_type": access_type,
        }

        return await self.log_event(
            event_type=AuditEventType.RESOURCE_ACCESS,
            user_id=user_id,
            resource_id=resource_id,
            action=access_type,
            details=details,
            source_ip=source_ip,
        )

    async def generate_compliance_report(
        self,
        start_time: datetime,
        end_time: datetime,
        compliance_standard: str = "gdpr",
    ) -> Dict[str, Any]:
        """Generate a compliance report for a specific standard.

        Args:
            start_time: Start time for report period
            end_time: End time for report period
            compliance_standard: Compliance standard to report on

        Returns:
            Compliance report data
        """
        if self.dev_mode or not self.vault_client:
            logger.warning("Cannot generate compliance report in development mode")
            return {"error": "Development mode active"}

        if compliance_standard not in self.compliance_standards:
            return {"error": f"Unknown compliance standard: {compliance_standard}"}

        if not self.compliance_standards[compliance_standard]:
            return {
                "error": f"Compliance standard {compliance_standard} is not enabled"
            }

        try:
            # List all audit logs
            logs = await self.vault_client.list_secrets("audit/logs")
            events = []

            for log_id in logs:
                # Get log entry
                event = await self.vault_client.read_secret(f"audit/logs/{log_id}")
                if not event:
                    continue

                event_time = datetime.fromisoformat(event["timestamp"])

                if event_time < start_time or event_time > end_time:
                    continue

                events.append(event)

            # Sort events by timestamp
            events.sort(key=lambda e: e["timestamp"])

            # Generate report
            report = {
                "compliance_standard": compliance_standard,
                "report_period": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                },
                "total_events": len(events),
                "event_types": {},
                "user_activity": {},
                "resource_access": {},
                "events": events,
            }

            # Analyze events
            for event in events:
                # Count event types
                event_type = event["event_type"]
                if event_type not in report["event_types"]:
                    report["event_types"][event_type] = 0
                report["event_types"][event_type] += 1

                # Track user activity
                user_id = event.get("user_id")
                if user_id:
                    if user_id not in report["user_activity"]:
                        report["user_activity"][user_id] = {
                            "total_actions": 0,
                            "actions": {},
                        }
                    report["user_activity"][user_id]["total_actions"] += 1

                    action = event.get("action")
                    if action:
                        if action not in report["user_activity"][user_id]["actions"]:
                            report["user_activity"][user_id]["actions"][action] = 0
                        report["user_activity"][user_id]["actions"][action] += 1

                # Track resource access
                resource_id = event.get("resource_id")
                if resource_id:
                    if resource_id not in report["resource_access"]:
                        report["resource_access"][resource_id] = {
                            "total_access": 0,
                            "access_types": {},
                        }
                    report["resource_access"][resource_id]["total_access"] += 1

                    access_type = event.get("action")
                    if access_type:
                        if (
                            access_type
                            not in report["resource_access"][resource_id][
                                "access_types"
                            ]
                        ):
                            report["resource_access"][resource_id]["access_types"][
                                access_type
                            ] = 0
                        report["resource_access"][resource_id]["access_types"][
                            access_type
                        ] += 1

            return report

        except Exception as e:
            logger.error("Failed to generate compliance report: %s", str(e))
            return {"error": f"Failed to generate report: {str(e)}"}
