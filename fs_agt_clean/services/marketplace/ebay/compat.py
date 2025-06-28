"""
eBay service compatibility layer.

This module provides compatibility functions for accessing eBay services
across different parts of the application.
"""

from typing import Optional

from .service import EbayService
from fs_agt_clean.core.marketplace.ebay.config import EbayConfig
from fs_agt_clean.core.marketplace.ebay.api_client import EbayAPIClient
from fs_agt_clean.core.metrics.compat import get_metrics_service
from fs_agt_clean.services.notifications.compat import get_notification_service

# Global eBay service instance
_ebay_service: Optional[EbayService] = None


def get_ebay_service(
    config=None, api_client=None, metrics_service=None, notification_service=None
) -> EbayService:
    """
    Get the global eBay service instance.

    Returns:
        EbayService: The eBay service instance

    Raises:
        RuntimeError: If eBay service is not initialized
    """
    global _ebay_service

    if _ebay_service is None:
        # Initialize with default configuration if not provided
        if config is None:
            config = EbayConfig(
                client_id="default_client_id",
                client_secret="default_client_secret",
                scopes=["https://api.ebay.com/oauth/api_scope"],
            )

        if api_client is None:
            api_client = EbayAPIClient(config.api_base_url)

        if metrics_service is None:
            try:
                metrics_service = get_metrics_service()
            except:
                metrics_service = None

        if notification_service is None:
            try:
                notification_service = get_notification_service()
            except:
                notification_service = None

        _ebay_service = EbayService(
            config, api_client, metrics_service, notification_service
        )

    return _ebay_service


def set_ebay_service(service: EbayService) -> None:
    """
    Set the global eBay service instance.

    Args:
        service: The eBay service instance to set
    """
    global _ebay_service
    _ebay_service = service


def reset_ebay_service() -> None:
    """Reset the global eBay service instance."""
    global _ebay_service
    _ebay_service = None


__all__ = ["get_ebay_service", "set_ebay_service", "reset_ebay_service"]
