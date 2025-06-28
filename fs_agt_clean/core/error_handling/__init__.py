"""
Standardized Error Handling

This module provides unified error handling, logging, and alerting
for FlipSync agents and services.
"""

from .standard_handler import (
    ErrorCategory,
    ErrorSeverity,
    StandardErrorHandler,
    create_validation_error,
    get_global_error_handler,
    handle_agent_error,
)

__all__ = [
    "StandardErrorHandler",
    "ErrorSeverity",
    "ErrorCategory",
    "get_global_error_handler",
    "handle_agent_error",
    "create_validation_error",
]
