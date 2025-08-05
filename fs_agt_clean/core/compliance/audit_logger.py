"""
Audit logging for compliance and security events.

This module provides functionality for logging security and compliance events
for audit purposes.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SecurityAuditLogger:
    """Logger for security audit events."""

    def __init__(self, log_to_file: bool = True, log_file: str = "security_audit.log"):
        """Initialize the security audit logger.

        Args:
            log_to_file: Whether to log to a file
            log_file: Path to the log file
        """
        self.log_to_file = log_to_file
        self.log_file = log_file

        # Set up file handler if needed
        if log_to_file:
            self.file_handler = logging.FileHandler(log_file)
            self.file_handler.setLevel(logging.INFO)
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            self.file_handler.setFormatter(formatter)

            # Create a separate logger for audit events
            self.audit_logger = logging.getLogger("security_audit")
            self.audit_logger.setLevel(logging.INFO)
            self.audit_logger.addHandler(self.file_handler)

            # Make sure audit logger doesn't propagate to root logger
            self.audit_logger.propagate = False

    async def log_security_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """Log a security event.

        Args:
            event_type: Type of security event
            user_id: ID of the user associated with the event
            details: Additional details about the event
            ip_address: IP address associated with the event
        """
        # Create event data
        event_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "ip_address": ip_address,
            "details": details or {},
        }

        # Log the event
        event_json = json.dumps(event_data)

        if self.log_to_file:
            self.audit_logger.info(event_json)

        # Also log to application logger at debug level
        logger.debug(f"Security event: {event_json}")
