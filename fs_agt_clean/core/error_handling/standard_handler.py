"""
Standardized Error Handling for FlipSync UnifiedAgents

This module provides unified error handling, logging, and alerting
to eliminate inconsistencies across different agent implementations.
"""

import logging
import traceback
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

# Import alert system components with fallback
try:
    from fs_agt_clean.core.monitoring.alert_manager import (
        Alert,
        AlertManager,
        AlertSeverity,
        AlertType,
    )
except ImportError:
    AlertManager = None
    Alert = None
    AlertType = None
    AlertSeverity = None

logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    """Standardized error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Standardized error categories."""

    AGENT_ERROR = "agent_error"
    PROCESSING_ERROR = "processing_error"
    COMMUNICATION_ERROR = "communication_error"
    DATA_ERROR = "data_error"
    CONFIGURATION_ERROR = "configuration_error"
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    VALIDATION_ERROR = "validation_error"
    TIMEOUT_ERROR = "timeout_error"


class StandardErrorHandler:
    """
    Standardized error handling for FlipSync agents.

    Provides unified error logging, alerting, and response formatting
    to eliminate inconsistencies across agent implementations.
    """

    def __init__(self, alert_manager: Optional[AlertManager] = None):
        """Initialize the error handler."""
        self.alert_manager = alert_manager

        # Error severity mapping
        self.severity_mapping = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL,
        }

        # Alert severity mapping (if alert system is available)
        if AlertSeverity:
            self.alert_severity_mapping = {
                ErrorSeverity.LOW: AlertSeverity.LOW,
                ErrorSeverity.MEDIUM: AlertSeverity.MEDIUM,
                ErrorSeverity.HIGH: AlertSeverity.HIGH,
                ErrorSeverity.CRITICAL: AlertSeverity.CRITICAL,
            }
        else:
            self.alert_severity_mapping = {}

    async def handle_agent_error(
        self,
        error: Exception,
        agent_id: str,
        operation: str,
        agent_type: str = "unknown",
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.AGENT_ERROR,
        context: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Handle agent errors with standardized logging, alerting, and response formatting.

        Args:
            error: The exception that occurred
            agent_id: Identifier of the agent
            operation: Operation being performed when error occurred
            agent_type: Type of agent (content, logistics, executive, etc.)
            severity: Error severity level
            category: Error category
            context: Additional context information
            user_message: Optional user-friendly error message

        Returns:
            Standardized error response dictionary
        """
        try:
            # Generate error ID for tracking
            error_id = (
                f"{agent_type}_{agent_id}_{operation}_{int(datetime.now().timestamp())}"
            )

            # Prepare error details
            error_details = {
                "error_id": error_id,
                "agent_id": agent_id,
                "agent_type": agent_type,
                "operation": operation,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "severity": severity.value,
                "category": category.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "context": context or {},
                "traceback": traceback.format_exc(),
            }

            # Log the error
            await self._log_error(error_details, severity)

            # Send alert if alert manager is available
            if self.alert_manager:
                await self._send_alert(error_details, severity)

            # Create user-friendly response
            user_response = self._create_user_response(
                error_details, user_message, severity
            )

            return {
                "success": False,
                "error_id": error_id,
                "error_type": category.value,
                "message": user_response,
                "severity": severity.value,
                "timestamp": error_details["timestamp"],
                "details": (
                    error_details
                    if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]
                    else None
                ),
            }

        except Exception as handler_error:
            # Fallback error handling
            logger.critical(f"Error in error handler: {handler_error}")
            return {
                "success": False,
                "error_id": "handler_error",
                "error_type": "error_handler_failure",
                "message": "An unexpected error occurred. Please try again.",
                "severity": ErrorSeverity.CRITICAL.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    async def _log_error(self, error_details: Dict[str, Any], severity: ErrorSeverity):
        """Log error with appropriate severity level."""
        try:
            log_level = self.severity_mapping.get(severity, logging.ERROR)

            # Format log message
            log_message = (
                f"UnifiedAgent Error [{error_details['error_id']}] - "
                f"UnifiedAgent: {error_details['agent_type']}/{error_details['agent_id']} - "
                f"Operation: {error_details['operation']} - "
                f"Error: {error_details['error_message']}"
            )

            # Add context if available
            if error_details.get("context"):
                log_message += f" - Context: {error_details['context']}"

            # Log with appropriate level
            logger.log(log_level, log_message)

            # Log full traceback for high/critical errors
            if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                logger.log(
                    log_level,
                    f"Traceback for {error_details['error_id']}:\n{error_details['traceback']}",
                )

        except Exception as e:
            logger.error(f"Failed to log error: {e}")

    async def _send_alert(self, error_details: Dict[str, Any], severity: ErrorSeverity):
        """Send alert through alert manager if available."""
        try:
            if not self.alert_manager or not Alert or not AlertType:
                return

            # Map severity to alert severity
            alert_severity = self.alert_severity_mapping.get(
                severity, AlertSeverity.MEDIUM
            )

            # Create alert
            alert = Alert(
                alert_id=error_details["error_id"],
                alert_type=AlertType.CUSTOM,
                message=f"UnifiedAgent {error_details['agent_type']} error: {error_details['error_message']}",
                severity=alert_severity,
                metric_type="counter",
                metric_value=1,
                threshold=0,
                timestamp=datetime.now(timezone.utc),
                metadata={
                    "agent_id": error_details["agent_id"],
                    "agent_type": error_details["agent_type"],
                    "operation": error_details["operation"],
                    "error_type": error_details["error_type"],
                    "category": error_details["category"],
                },
            )

            # Process alert
            await self.alert_manager.process_alert(alert)

        except Exception as e:
            logger.error(f"Failed to send alert: {e}")

    def _create_user_response(
        self,
        error_details: Dict[str, Any],
        user_message: Optional[str],
        severity: ErrorSeverity,
    ) -> str:
        """Create user-friendly error response message."""
        try:
            if user_message:
                return user_message

            # Default messages based on severity and category
            agent_type = error_details.get("agent_type", "system")
            category = error_details.get("category", "unknown")

            if severity == ErrorSeverity.CRITICAL:
                return f"A critical error occurred in the {agent_type} agent. Please contact support with error ID: {error_details['error_id']}"

            elif severity == ErrorSeverity.HIGH:
                return f"The {agent_type} agent encountered an error and cannot complete this request. Please try again or contact support."

            elif severity == ErrorSeverity.MEDIUM:
                if category == ErrorCategory.TIMEOUT_ERROR.value:
                    return f"The {agent_type} agent is taking longer than expected. Please try again."
                elif category == ErrorCategory.EXTERNAL_SERVICE_ERROR.value:
                    return f"The {agent_type} agent is experiencing connectivity issues. Please try again in a moment."
                else:
                    return f"The {agent_type} agent encountered an issue processing your request. Please try again."

            else:  # LOW severity
                return f"The {agent_type} agent completed with minor issues. Results may be limited."

        except Exception as e:
            logger.error(f"Failed to create user response: {e}")
            return "An error occurred. Please try again."

    @classmethod
    def create_validation_error(
        cls,
        field_name: str,
        field_value: Any,
        expected_type: str,
        agent_id: str,
        operation: str,
    ) -> Dict[str, Any]:
        """Create standardized validation error response."""
        return {
            "success": False,
            "error_type": ErrorCategory.VALIDATION_ERROR.value,
            "message": f"Invalid {field_name}: expected {expected_type}, got {type(field_value).__name__}",
            "field": field_name,
            "value": str(field_value),
            "expected_type": expected_type,
            "agent_id": agent_id,
            "operation": operation,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def create_timeout_error(
        cls, operation: str, timeout_duration: float, agent_id: str, agent_type: str
    ) -> Dict[str, Any]:
        """Create standardized timeout error response."""
        return {
            "success": False,
            "error_type": ErrorCategory.TIMEOUT_ERROR.value,
            "message": f"Operation '{operation}' timed out after {timeout_duration} seconds",
            "operation": operation,
            "timeout_duration": timeout_duration,
            "agent_id": agent_id,
            "agent_type": agent_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def create_external_service_error(
        cls,
        service_name: str,
        error_message: str,
        agent_id: str,
        operation: str,
        status_code: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create standardized external service error response."""
        return {
            "success": False,
            "error_type": ErrorCategory.EXTERNAL_SERVICE_ERROR.value,
            "message": f"External service '{service_name}' error: {error_message}",
            "service_name": service_name,
            "status_code": status_code,
            "agent_id": agent_id,
            "operation": operation,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def wrap_agent_operation(cls, error_handler: "StandardErrorHandler"):
        """
        Decorator to wrap agent operations with standardized error handling.

        Usage:
        @StandardErrorHandler.wrap_agent_operation(error_handler)
        async def my_agent_method(self, ...):
            # Method implementation
        """

        def decorator(func):
            async def wrapper(self, *args, **kwargs):
                try:
                    return await func(self, *args, **kwargs)
                except Exception as e:
                    # Extract agent info from self
                    agent_id = getattr(self, "agent_id", "unknown")
                    agent_type = getattr(self, "agent_type", type(self).__name__)
                    operation = func.__name__

                    # Handle error
                    return await error_handler.handle_agent_error(
                        error=e,
                        agent_id=agent_id,
                        operation=operation,
                        agent_type=agent_type,
                        severity=ErrorSeverity.MEDIUM,
                        category=ErrorCategory.AGENT_ERROR,
                    )

            return wrapper

        return decorator


# Global error handler instance
_global_error_handler = None


def get_global_error_handler() -> StandardErrorHandler:
    """Get or create global error handler instance."""
    global _global_error_handler
    if _global_error_handler is None:
        try:
            # Try to create with alert manager
            if AlertManager:
                alert_manager = AlertManager()
                _global_error_handler = StandardErrorHandler(alert_manager)
            else:
                _global_error_handler = StandardErrorHandler()
        except Exception as e:
            logger.warning(f"Failed to create error handler with alert manager: {e}")
            _global_error_handler = StandardErrorHandler()

    return _global_error_handler


# Convenience functions for common error types
async def handle_agent_error(
    error: Exception,
    agent_id: str,
    operation: str,
    agent_type: str = "unknown",
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
) -> Dict[str, Any]:
    """Convenience function for handling agent errors."""
    handler = get_global_error_handler()
    return await handler.handle_agent_error(
        error=error,
        agent_id=agent_id,
        operation=operation,
        agent_type=agent_type,
        severity=severity,
    )


def create_validation_error(
    field_name: str, field_value: Any, expected_type: str, agent_id: str, operation: str
) -> Dict[str, Any]:
    """Convenience function for creating validation errors."""
    return StandardErrorHandler.create_validation_error(
        field_name=field_name,
        field_value=field_value,
        expected_type=expected_type,
        agent_id=agent_id,
        operation=operation,
    )
