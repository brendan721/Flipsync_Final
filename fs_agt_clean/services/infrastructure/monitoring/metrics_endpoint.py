"""Metrics endpoints for FlipSync API.

This module provides metrics endpoints for monitoring the API's performance.
"""

import logging
from typing import Any, Dict

from fastapi import Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    generate_latest,
    multiprocess,
)

from fs_agt_clean.core.config.manager import manager as config_manager

logger = logging.getLogger(__name__)


async def metrics_endpoint() -> Response:
    """Prometheus metrics endpoint.

    Returns:
        Response with Prometheus metrics.
    """
    # Check if multiprocess mode is enabled
    multiproc_dir = config_manager.get("metrics.prometheus_multiproc_dir")

    if multiproc_dir:
        # Use multiprocess registry
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
    else:
        # Use default registry
        from prometheus_client import REGISTRY as registry

    # Generate metrics
    metrics_data = generate_latest(registry)

    # Return metrics response
    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST,
    )
