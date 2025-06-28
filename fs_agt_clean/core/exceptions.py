"""Core exceptions for FlipSync."""

from typing import Any, Dict, Optional


class FlipSyncError(Exception):
    """Base exception for FlipSync errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(FlipSyncError):
    """Raised when validation fails."""

    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        super().__init__(message)
        self.field = field
        self.value = value


class ConfigurationError(FlipSyncError):
    """Raised when configuration is invalid."""

    pass


class AuthenticationError(FlipSyncError):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str,
        marketplace: Optional[str] = None,
        status_code: Optional[int] = None,
    ):
        super().__init__(message)
        self.marketplace = marketplace
        self.status_code = status_code


class AuthorizationError(FlipSyncError):
    """Raised when authorization fails."""

    pass


class MarketplaceError(FlipSyncError):
    """Raised when marketplace operations fail."""

    def __init__(
        self,
        message: str,
        marketplace: Optional[str] = None,
        status_code: Optional[int] = None,
    ):
        super().__init__(message)
        self.marketplace = marketplace
        self.status_code = status_code


class DatabaseError(FlipSyncError):
    """Raised when database operations fail."""

    pass


class ExternalServiceError(FlipSyncError):
    """Raised when external service calls fail."""

    pass


class RateLimitError(FlipSyncError):
    """Raised when rate limits are exceeded."""

    pass
