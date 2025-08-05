"""
Metrics compatibility layer.

This module provides compatibility functions for accessing metrics services
across different parts of the application.
"""

from typing import Optional

from .service import MetricsService

# Global metrics service instance
_metrics_service: Optional[MetricsService] = None


def get_metrics_service() -> MetricsService:
    """
    Get the global metrics service instance.

    Returns:
        MetricsService: The metrics service instance

    Raises:
        RuntimeError: If metrics service is not initialized
    """
    global _metrics_service

    if _metrics_service is None:
        # Initialize with default configuration
        _metrics_service = MetricsService()

    return _metrics_service


def set_metrics_service(service: MetricsService) -> None:
    """
    Set the global metrics service instance.

    Args:
        service: The metrics service instance to set
    """
    global _metrics_service
    _metrics_service = service


def reset_metrics_service() -> None:
    """Reset the global metrics service instance."""
    global _metrics_service
    _metrics_service = None


__all__ = ["get_metrics_service", "set_metrics_service", "reset_metrics_service"]
