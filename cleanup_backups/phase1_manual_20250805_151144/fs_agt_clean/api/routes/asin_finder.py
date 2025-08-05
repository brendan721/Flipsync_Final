"""
ASIN Finder API routes.

This module provides API endpoints for ASIN discovery, synchronization,
and data retrieval across marketplaces.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

# Use the compatibility layer for config manager
from fs_agt_clean.core.config import get_settings
from fs_agt_clean.core.marketplace.ebay.api_client import EbayAPIClient
from fs_agt_clean.core.marketplace.ebay.config import EbayConfig
from fs_agt_clean.core.metrics.compat import get_metrics_service

# Corrected import for ASIN models and manager
# ASIN models are now imported from their actual location
from fs_agt_clean.core.service.asin_finder.models import (
    ASINData,
    ASINSyncRequest,
    ASINSyncResponse,
    ASINSyncStatus,
)
from fs_agt_clean.core.sync.compat import ASINSyncManager
from fs_agt_clean.core.utils.caching import CacheService
from fs_agt_clean.services.marketplace.amazon.compat import get_amazon_service
from fs_agt_clean.services.marketplace.ebay.compat import get_ebay_service
from fs_agt_clean.services.notifications.compat import get_notification_service

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")
router = APIRouter(prefix="/asin", tags=["asin-finder"])


async def get_sync_manager() -> ASINSyncManager:
    """Get ASIN sync manager instance."""
    # Get the config manager instance via the function
    config_manager = get_settings()

    # Load marketplace credentials from config
    amazon_client_id = config_manager.get("amazon.client_id")
    amazon_client_secret = config_manager.get("amazon.client_secret")
    amazon_refresh_token = config_manager.get("amazon.refresh_token")
    ebay_client_id = config_manager.get("ebay.client_id")
    ebay_client_secret = config_manager.get("ebay.client_secret")
    ebay_base_url = config_manager.get("ebay.base_url", "https://api.ebay.com")

    # Initialize services with compatibility layers
    metrics_service = get_metrics_service(config_manager=config_manager)
    notification_service = get_notification_service(config_manager=config_manager)

    # Initialize marketplace services
    sp_api_config = {
        "base_url": "https://sellingpartnerapi.amazon.com",
        "client_id": amazon_client_id,
        "client_secret": amazon_client_secret,
        "refresh_token": amazon_refresh_token,
    }
    amazon_service = get_amazon_service(
        metrics_service=metrics_service,
        notification_service=notification_service,
        sp_api_config=sp_api_config,
    )

    ebay_client = EbayAPIClient(base_url=ebay_base_url)
    # Assuming authenticate method exists and works
    # await ebay_client.authenticate(
    #     client_id=ebay_client_id,
    #     client_secret=ebay_client_secret,
    # )
    ebay_config = EbayConfig(
        client_id=ebay_client_id,
        client_secret=ebay_client_secret,
        api_base_url=ebay_base_url,
    )
    ebay_service = get_ebay_service(
        config=ebay_config,
        api_client=ebay_client,
        metrics_service=metrics_service,
        notification_service=notification_service,
    )

    # Initialize cache service
    cache_service = CacheService()  # No args needed

    return ASINSyncManager(
        amazon_service=amazon_service,
        ebay_service=ebay_service,
        cache_service=cache_service,
        metrics_service=metrics_service,
        notification_service=notification_service,
    )


async def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    """Verify API key and return client ID."""
    if not api_key or len(api_key) < 32:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key[:8]


@router.post("/sync", response_model=ASINSyncResponse)
async def sync_asins(
    request: ASINSyncRequest,
    sync_manager: ASINSyncManager = Depends(get_sync_manager),
    client_id: str = Depends(verify_api_key),
):
    """Initiate ASIN synchronization."""
    await sync_manager.metrics_service.record_metric(
        name="asin_sync_request_count", value=1.0, labels={"client_id": client_id}
    )
    try:
        valid_asins = []
        rejected_asins = []
        for asin in request.asins:
            if not sync_manager.is_valid_asin(asin):
                rejected_asins.append({"asin": asin, "reason": "Invalid ASIN format"})
                continue
            if not request.force and await sync_manager.is_recently_synced(asin):
                rejected_asins.append({"asin": asin, "reason": "Recently synced"})
                continue
            valid_asins.append(asin)
        if not valid_asins:
            raise HTTPException(status_code=400, detail="No valid ASINs provided")
        request_id = str(uuid4())
        estimated_completion = datetime.now() + timedelta(seconds=len(valid_asins) * 2)
        await sync_manager.queue_sync_tasks(
            request_id=request_id,
            asins=valid_asins,
            priority=request.priority,
            client_id=client_id,
        )
        return ASINSyncResponse(
            request_id=request_id,
            accepted_asins=valid_asins,
            rejected_asins=rejected_asins,
            estimated_completion=estimated_completion,
        )
    except Exception as e:
        await sync_manager.metrics_service.increment_counter(
            name="asin_finder_api_error",
            labels={
                "source": "sync_asins",
                "client_id": client_id,
                "error_type": type(e).__name__,
            },
        )
        raise HTTPException(status_code=500, detail=f"Sync request failed: {str(e)}")


@router.get("/status/{request_id}", response_model=List[ASINSyncStatus])
async def get_sync_status(
    request_id: str,
    asins: Optional[List[str]] = None,
    sync_manager: ASINSyncManager = Depends(get_sync_manager),
    client_id: str = Depends(verify_api_key),
):
    """Get status of ASIN synchronization."""
    try:
        statuses = await sync_manager.get_sync_status(
            request_id=request_id, asins=asins
        )
        if not statuses:
            raise HTTPException(
                status_code=404, detail=f"No sync status found for request {request_id}"
            )
        return statuses
    except HTTPException:
        raise
    except Exception as e:
        await sync_manager.metrics_service.increment_counter(
            name="asin_finder_api_error",
            labels={
                "source": "get_sync_status",
                "client_id": client_id,
                "request_id": request_id,
                "error_type": type(e).__name__,
            },
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to get sync status: {str(e)}"
        )


@router.get("/{asin}", response_model=ASINData)
async def get_asin_data(
    asin: str,
    sync_manager: ASINSyncManager = Depends(get_sync_manager),
    client_id: str = Depends(verify_api_key),
):
    """Get synchronized data for an ASIN."""
    try:
        if not sync_manager.is_valid_asin(asin):
            raise HTTPException(status_code=400, detail="Invalid ASIN format")
        data = await sync_manager.get_asin_data(asin=asin)
        if not data:
            raise HTTPException(
                status_code=404, detail=f"No data found for ASIN {asin}"
            )
        return data
    except HTTPException:
        raise
    except Exception as e:
        await sync_manager.metrics_service.increment_counter(
            name="asin_finder_api_error",
            labels={
                "source": "get_asin_data",
                "client_id": client_id,
                "asin": asin,
                "error_type": type(e).__name__,
            },
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to get ASIN data: {str(e)}"
        )


@router.delete("/{asin}")
async def delete_asin_data(
    asin: str,
    sync_manager: ASINSyncManager = Depends(get_sync_manager),
    client_id: str = Depends(verify_api_key),
):
    """Delete cached data for an ASIN."""
    try:
        if not sync_manager.is_valid_asin(asin):
            raise HTTPException(status_code=400, detail="Invalid ASIN format")

        deleted = await sync_manager.delete_asin_data(asin=asin)

        if not deleted:
            # Optionally, you could return 404 if data didn't exist to be deleted
            pass  # Or raise HTTPException(status_code=404, detail=f"No data found for ASIN {asin} to delete")

        # Record success metric if needed via sync_manager.metrics_service
        await sync_manager.metrics_service.record_metric(
            name="asin_data_deleted_count",
            value=1.0,
            labels={"client_id": client_id, "asin": asin},
        )

        return {"message": f"Data for ASIN {asin} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        # Record error using metrics_service
        await sync_manager.metrics_service.increment_counter(
            name="asin_finder_api_error",
            labels={
                "source": "delete_asin_data",
                "client_id": client_id,
                "asin": asin,
                "error_type": type(e).__name__,
            },
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to delete ASIN data: {str(e)}"
        )
