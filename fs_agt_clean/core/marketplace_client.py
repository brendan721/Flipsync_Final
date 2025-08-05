"""
Marketplace API client for FlipSync.

This module provides a specialized API client for marketplace operations,
extending the base APIClient with marketplace-specific functionality.
"""

import logging
from typing import Any, Dict, Optional

from fs_agt_clean.core.api_client import APIClient

logger = logging.getLogger(__name__)


class MarketplaceAPIClient(APIClient):
    """
    Specialized API client for marketplace operations.

    Extends the base APIClient with marketplace-specific functionality
    like authentication, rate limiting, and error handling.
    """

    def __init__(self, base_url: str, marketplace: str = "unknown"):
        """
        Initialize the marketplace API client.

        Args:
            base_url: Base URL for the marketplace API
            marketplace: Name of the marketplace (e.g., 'amazon', 'ebay')
        """
        super().__init__(base_url)
        self.marketplace = marketplace
        self.default_headers = {
            "UnifiedUser-UnifiedAgent": f"FlipSync-{marketplace.title()}Client/1.0",
            "Content-Type": "application/json",
        }
        self._access_token = None
        self._token_expiry = None

    async def _get_access_token(self, scope: Optional[str] = None) -> str:
        """
        Get access token for API authentication.

        This is a base implementation that should be overridden by
        marketplace-specific clients.

        Args:
            scope: Optional scope for the token

        Returns:
            Access token string

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement _get_access_token")

    async def _prepare_headers(
        self, headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Prepare headers for API requests.

        Args:
            headers: Optional additional headers

        Returns:
            Complete headers dictionary
        """
        request_headers = self.default_headers.copy()
        if headers:
            request_headers.update(headers)
        return request_headers

    async def get_with_retry(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Send GET request with marketplace-specific retry logic.

        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Request headers
            max_retries: Maximum number of retries

        Returns:
            Response data
        """
        request_headers = await self._prepare_headers(headers)

        for attempt in range(max_retries + 1):
            try:
                response = await self.get(
                    endpoint, params=params, headers=request_headers
                )
                return response
            except Exception as e:
                if attempt == max_retries:
                    logger.error(
                        f"Failed to GET {endpoint} after {max_retries} retries: {e}"
                    )
                    raise
                logger.warning(f"GET {endpoint} attempt {attempt + 1} failed: {e}")
                await self._handle_retry_delay(attempt)

    async def post_with_retry(
        self,
        endpoint: str,
        json: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Send POST request with marketplace-specific retry logic.

        Args:
            endpoint: API endpoint
            json: JSON payload
            data: Form data
            headers: Request headers
            max_retries: Maximum number of retries

        Returns:
            Response data
        """
        request_headers = await self._prepare_headers(headers)

        for attempt in range(max_retries + 1):
            try:
                response = await self.post(
                    endpoint, json=json, data=data, headers=request_headers
                )
                return response
            except Exception as e:
                if attempt == max_retries:
                    logger.error(
                        f"Failed to POST {endpoint} after {max_retries} retries: {e}"
                    )
                    raise
                logger.warning(f"POST {endpoint} attempt {attempt + 1} failed: {e}")
                await self._handle_retry_delay(attempt)

    async def put_with_retry(
        self,
        endpoint: str,
        json: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Send PUT request with marketplace-specific retry logic.

        Args:
            endpoint: API endpoint
            json: JSON payload
            headers: Request headers
            max_retries: Maximum number of retries

        Returns:
            Response data
        """
        request_headers = await self._prepare_headers(headers)

        for attempt in range(max_retries + 1):
            try:
                response = await self.put(endpoint, json=json, headers=request_headers)
                return response
            except Exception as e:
                if attempt == max_retries:
                    logger.error(
                        f"Failed to PUT {endpoint} after {max_retries} retries: {e}"
                    )
                    raise
                logger.warning(f"PUT {endpoint} attempt {attempt + 1} failed: {e}")
                await self._handle_retry_delay(attempt)

    async def _handle_retry_delay(self, attempt: int) -> None:
        """
        Handle delay between retry attempts.

        Args:
            attempt: Current attempt number (0-based)
        """
        import asyncio

        delay = min(2**attempt, 10)  # Exponential backoff with max 10 seconds
        await asyncio.sleep(delay)

    def get_marketplace_info(self) -> Dict[str, Any]:
        """
        Get information about the marketplace.

        Returns:
            Marketplace information dictionary
        """
        return {
            "marketplace": self.marketplace,
            "base_url": self.base_url,
            "connection_errors": self.connection_errors,
            "ssl_errors": self.ssl_errors,
            "retry_count": self.retry_count,
            "last_error": self.last_error,
        }
