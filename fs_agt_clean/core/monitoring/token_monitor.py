"""
Token monitor for FlipSync monitoring system.

This module provides token usage monitoring and rate limiting
functionality for API tokens and authentication.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class TokenMonitor:
    """
    Monitor for API token usage and rate limiting.

    Tracks token usage, enforces rate limits, and provides
    usage analytics for API tokens.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the token monitor.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.token_usage: Dict[str, List[Dict[str, Any]]] = {}
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the token monitor."""
        if not self._initialized:
            logger.info("Initializing token monitor")
            self._initialized = True

    async def record_token_usage(
        self,
        token_id: str,
        endpoint: str,
        method: str = "GET",
        response_code: int = 200,
        response_time_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record token usage.

        Args:
            token_id: Token identifier
            endpoint: API endpoint accessed
            method: HTTP method
            response_code: HTTP response code
            response_time_ms: Response time in milliseconds
            metadata: Additional metadata
        """
        if not self._initialized:
            await self.initialize()

        try:
            usage_record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "endpoint": endpoint,
                "method": method,
                "response_code": response_code,
                "response_time_ms": response_time_ms,
                "metadata": metadata or {},
            }

            if token_id not in self.token_usage:
                self.token_usage[token_id] = []

            self.token_usage[token_id].append(usage_record)

            # Keep only recent usage (last 24 hours)
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            self.token_usage[token_id] = [
                record
                for record in self.token_usage[token_id]
                if datetime.fromisoformat(record["timestamp"].replace("Z", "+00:00"))
                > cutoff_time
            ]

            logger.debug(f"Recorded token usage for {token_id}: {endpoint}")

        except Exception as e:
            logger.error(f"Error recording token usage: {e}")

    async def check_rate_limit(
        self,
        token_id: str,
        endpoint: str,
        window_minutes: int = 60,
        max_requests: int = 1000,
    ) -> Dict[str, Any]:
        """
        Check if token is within rate limits.

        Args:
            token_id: Token identifier
            endpoint: API endpoint
            window_minutes: Rate limit window in minutes
            max_requests: Maximum requests in window

        Returns:
            Rate limit status
        """
        if not self._initialized:
            await self.initialize()

        try:
            current_time = datetime.now(timezone.utc)
            window_start = current_time - timedelta(minutes=window_minutes)

            # Count requests in window
            usage_records = self.token_usage.get(token_id, [])
            requests_in_window = 0

            for record in usage_records:
                record_time = datetime.fromisoformat(
                    record["timestamp"].replace("Z", "+00:00")
                )
                if record_time > window_start and record["endpoint"] == endpoint:
                    requests_in_window += 1

            remaining_requests = max(0, max_requests - requests_in_window)
            is_within_limit = requests_in_window < max_requests

            # Calculate reset time
            reset_time = current_time + timedelta(minutes=window_minutes)

            result = {
                "token_id": token_id,
                "endpoint": endpoint,
                "within_limit": is_within_limit,
                "requests_made": requests_in_window,
                "requests_remaining": remaining_requests,
                "limit": max_requests,
                "window_minutes": window_minutes,
                "reset_time": reset_time.isoformat(),
                "checked_at": current_time.isoformat(),
            }

            if not is_within_limit:
                logger.warning(
                    f"Rate limit exceeded for token {token_id} on {endpoint}"
                )

            return result

        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return {
                "token_id": token_id,
                "endpoint": endpoint,
                "within_limit": True,  # Default to allowing request
                "error": str(e),
            }

    async def get_token_stats(
        self,
        token_id: str,
        hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Get token usage statistics.

        Args:
            token_id: Token identifier
            hours: Number of hours to analyze

        Returns:
            Token usage statistics
        """
        if not self._initialized:
            await self.initialize()

        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            usage_records = self.token_usage.get(token_id, [])

            # Filter records within time window
            recent_records = [
                record
                for record in usage_records
                if datetime.fromisoformat(record["timestamp"].replace("Z", "+00:00"))
                > cutoff_time
            ]

            if not recent_records:
                return {
                    "token_id": token_id,
                    "total_requests": 0,
                    "unique_endpoints": 0,
                    "avg_response_time_ms": 0.0,
                    "error_rate": 0.0,
                    "hours_analyzed": hours,
                }

            # Calculate statistics
            total_requests = len(recent_records)
            unique_endpoints = len(set(record["endpoint"] for record in recent_records))

            response_times = [record["response_time_ms"] for record in recent_records]
            avg_response_time = (
                sum(response_times) / len(response_times) if response_times else 0.0
            )

            error_requests = len(
                [r for r in recent_records if r["response_code"] >= 400]
            )
            error_rate = (
                (error_requests / total_requests) * 100 if total_requests > 0 else 0.0
            )

            # Endpoint breakdown
            endpoint_counts = {}
            for record in recent_records:
                endpoint = record["endpoint"]
                endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1

            # Method breakdown
            method_counts = {}
            for record in recent_records:
                method = record["method"]
                method_counts[method] = method_counts.get(method, 0) + 1

            return {
                "token_id": token_id,
                "total_requests": total_requests,
                "unique_endpoints": unique_endpoints,
                "avg_response_time_ms": round(avg_response_time, 2),
                "error_rate": round(error_rate, 2),
                "hours_analyzed": hours,
                "endpoint_breakdown": endpoint_counts,
                "method_breakdown": method_counts,
                "analyzed_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting token stats: {e}")
            return {
                "token_id": token_id,
                "error": str(e),
            }

    async def set_rate_limit(
        self,
        token_id: str,
        endpoint: str,
        max_requests: int,
        window_minutes: int = 60,
    ) -> None:
        """
        Set rate limit for a token and endpoint.

        Args:
            token_id: Token identifier
            endpoint: API endpoint
            max_requests: Maximum requests allowed
            window_minutes: Time window in minutes
        """
        if not self._initialized:
            await self.initialize()

        limit_key = f"{token_id}:{endpoint}"
        self.rate_limits[limit_key] = {
            "max_requests": max_requests,
            "window_minutes": window_minutes,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(
            f"Set rate limit for {token_id} on {endpoint}: {max_requests}/{window_minutes}min"
        )

    async def get_all_token_stats(self) -> List[Dict[str, Any]]:
        """
        Get statistics for all monitored tokens.

        Returns:
            List of token statistics
        """
        if not self._initialized:
            await self.initialize()

        stats = []
        for token_id in self.token_usage.keys():
            token_stats = await self.get_token_stats(token_id)
            stats.append(token_stats)

        return stats

    async def cleanup_old_usage(self, hours: int = 48) -> int:
        """
        Clean up old usage records.

        Args:
            hours: Age threshold in hours

        Returns:
            Number of records cleaned up
        """
        if not self._initialized:
            await self.initialize()

        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        cleaned_count = 0

        for token_id in list(self.token_usage.keys()):
            original_count = len(self.token_usage[token_id])

            self.token_usage[token_id] = [
                record
                for record in self.token_usage[token_id]
                if datetime.fromisoformat(record["timestamp"].replace("Z", "+00:00"))
                > cutoff_time
            ]

            new_count = len(self.token_usage[token_id])
            cleaned_count += original_count - new_count

            # Remove empty token entries
            if not self.token_usage[token_id]:
                del self.token_usage[token_id]

        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old usage records")

        return cleaned_count

    def get_monitor_info(self) -> Dict[str, Any]:
        """
        Get token monitor information.

        Returns:
            Monitor information dictionary
        """
        return {
            "monitor_name": "token_monitor",
            "initialized": self._initialized,
            "monitored_tokens": len(self.token_usage),
            "rate_limits": len(self.rate_limits),
            "config": self.config,
        }


class EbayTokenMonitor(TokenMonitor):
    """
    Specialized token monitor for eBay API tokens.

    Extends the base TokenMonitor with eBay-specific
    rate limiting and usage tracking.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the eBay token monitor.

        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)

        # eBay-specific rate limits
        self.ebay_rate_limits = {
            "trading_api": {"requests_per_day": 5000, "requests_per_hour": 1000},
            "finding_api": {"requests_per_day": 5000, "requests_per_hour": 1000},
            "shopping_api": {"requests_per_day": 5000, "requests_per_hour": 1000},
            "merchandising_api": {"requests_per_day": 10000, "requests_per_hour": 2000},
        }

    async def check_ebay_rate_limit(
        self,
        token_id: str,
        api_type: str = "trading_api",
    ) -> Dict[str, Any]:
        """
        Check eBay-specific rate limits.

        Args:
            token_id: eBay token identifier
            api_type: Type of eBay API (trading_api, finding_api, etc.)

        Returns:
            eBay rate limit status
        """
        if api_type not in self.ebay_rate_limits:
            api_type = "trading_api"  # Default

        limits = self.ebay_rate_limits[api_type]

        # Check hourly limit
        hourly_status = await self.check_rate_limit(
            token_id=token_id,
            endpoint=f"ebay_{api_type}",
            window_minutes=60,
            max_requests=limits["requests_per_hour"],
        )

        # Check daily limit
        daily_status = await self.check_rate_limit(
            token_id=token_id,
            endpoint=f"ebay_{api_type}",
            window_minutes=1440,  # 24 hours
            max_requests=limits["requests_per_day"],
        )

        return {
            "token_id": token_id,
            "api_type": api_type,
            "hourly_limit": hourly_status,
            "daily_limit": daily_status,
            "within_limits": hourly_status["within_limit"]
            and daily_status["within_limit"],
        }

    async def record_ebay_api_call(
        self,
        token_id: str,
        api_type: str,
        call_name: str,
        response_code: int = 200,
        response_time_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record eBay API call usage.

        Args:
            token_id: eBay token identifier
            api_type: Type of eBay API
            call_name: Specific API call name
            response_code: HTTP response code
            response_time_ms: Response time in milliseconds
            metadata: Additional metadata
        """
        endpoint = f"ebay_{api_type}_{call_name}"

        await self.record_token_usage(
            token_id=token_id,
            endpoint=endpoint,
            method="POST",  # Most eBay API calls are POST
            response_code=response_code,
            response_time_ms=response_time_ms,
            metadata={
                "api_type": api_type,
                "call_name": call_name,
                **(metadata or {}),
            },
        )
