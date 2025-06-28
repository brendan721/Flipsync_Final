import asyncio
import json
import logging
import zlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Set, Tuple

import msgpack
from fastapi import FastAPI, Query, Response, WebSocket
from fastapi.staticfiles import StaticFiles

from fs_agt_clean.core.config import get_settings
from fs_agt_clean.core.monitoring.aggregation import TimeWindow
from fs_agt_clean.core.monitoring.alerts.manager import AlertManager
from fs_agt_clean.core.monitoring.metrics import (
    HistoryStorage,
    MetricsHistory,
    MetricsStorage,
)
from fs_agt_clean.services.service import LRUCache, TTLCache

"\nMetric visualization dashboard service with performance optimizations.\nProvides real-time and historical metric visualization with mobile support.\n"
logging.basicConfig(level=logging.INFO)
logger: logging.Logger = logging.getLogger(__name__)


# Define TimeRange
class TimeRange(NamedTuple):
    start: datetime
    end: datetime


@dataclass
class MetricBatch:
    """Batch of metrics for efficient transmission."""

    metrics: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    batch_size: int = 0
    MAX_BATCH_SIZE: int = 100

    def add_metric(self, metric: Dict[str, Any]) -> bool:
        """Add metric to batch if not full."""
        if self.batch_size >= self.MAX_BATCH_SIZE:
            return bool(False)
        self.metrics.append(metric)
        self.batch_size += 1
        return True

    def serialize(self) -> bytes:
        """Serialize and compress batch."""
        data = {
            "metrics": self.metrics,
            "timestamp": self.timestamp.isoformat(),
            "size": self.batch_size,
        }
        return zlib.compress(msgpack.packb(data))


class DashboardCache:
    """Cache management for dashboard data."""

    def __init__(self):
        self.metric_cache = TTLCache(max_size=1000, ttl=60)
        self.history_cache = TTLCache(max_size=100, ttl=300)
        self.alert_cache = TTLCache(max_size=100, ttl=30)
        self.hot_metrics = LRUCache(max_size=100)

    def get_cached_metrics(
        self, metric_type: str, window: TimeWindow
    ) -> Optional[Dict[str, Any]]:
        """Get metrics from cache."""
        cache_key = f"{metric_type}:{window.name}"
        return self.metric_cache.get(cache_key)

    async def cache_metrics(
        self, metric_type: str, window: TimeWindow, data: Dict[str, Any]
    ):
        """Cache metric data."""
        cache_key = f"{metric_type}:{window.name}"
        self.metric_cache[cache_key] = data
        # Use the LRUCache correctly with async methods
        access_count = await self.hot_metrics.get(cache_key) or 0
        await self.hot_metrics.put(cache_key, access_count + 1)


class DashboardService:
    """Enhanced service for managing dashboard operations and state."""

    def __init__(self):
        self.alert_manager = AlertManager()
        self.active_clients: Dict[str, Tuple[WebSocket, Set[str]]] = {}
        self.settings = get_settings()
        self.cache = DashboardCache()
        self.current_batch: Optional[MetricBatch] = None
        self.BATCH_INTERVAL = 1.0
        self.COMPRESSION_THRESHOLD = 1024
        self.MAX_PAYLOAD_SIZE = 1024 * 1024
        self.storage = MetricsStorage()

    async def start(self):
        """Start the dashboard service."""
        self.batch_task = asyncio.create_task(self._process_metric_batches())
        logger.info("Dashboard service started with optimizations")

    async def stop(self):
        """Stop the dashboard service."""
        if hasattr(self, "batch_task"):
            self.batch_task.cancel()
        for client_id, (websocket, _) in self.active_clients.items():
            await websocket.close()
        self.active_clients.clear()
        logger.info("Dashboard service stopped")

    async def _process_metric_batches(self):
        """Process and send metric batches periodically."""
        while True:
            try:
                await asyncio.sleep(self.BATCH_INTERVAL)
                if self.current_batch and self.current_batch.batch_size > 0:
                    await self._send_batch_to_clients(self.current_batch)
                    self.current_batch = MetricBatch()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error processing metric batch: %s", str(e))

    async def _send_batch_to_clients(self, batch: MetricBatch):
        """Send compressed batch to all clients."""
        payload = batch.serialize()
        disconnected_clients = []
        for client_id, (websocket, filters) in self.active_clients.items():
            try:
                filtered_metrics = [
                    m for m in batch.metrics if not filters or m.get("type") in filters
                ]
                if filtered_metrics:
                    filtered_batch = MetricBatch()
                    for metric in filtered_metrics:
                        filtered_batch.add_metric(metric)
                    await websocket.send_bytes(filtered_batch.serialize())
            except Exception as e:
                logger.error("Error sending to client %s: %s", client_id, str(e))
                disconnected_clients.append(client_id)
        for client_id in disconnected_clients:
            await self.disconnect_client(client_id)

    async def get_historical_data(
        self,
        metric_type: str,
        window: TimeWindow,
        start_time: datetime,
        end_time: datetime,
        page: int = 1,
        page_size: int = 100,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Get paginated historical data with caching."""
        cache_key = f"{metric_type}:{window.name}:{start_time.isoformat()}:{end_time.isoformat()}:{page}"
        cached_data = self.cache.history_cache.get(cache_key)
        if cached_data:
            return cached_data
        offset = (page - 1) * page_size
        data = await self.storage.get_metrics(
            metric_type, TimeRange(start_time, end_time), window, filters
        )
        total_items = len(data)
        paginated_data = data[offset : offset + page_size]
        result = {
            "data": paginated_data,
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": (total_items + page_size - 1) // page_size,
        }
        self.cache.history_cache[cache_key] = result
        return result

    async def connect_client(
        self, websocket: WebSocket, client_id: str, filters: Optional[Set[str]] = None
    ):
        """Handle new client connection with filtering."""
        await websocket.accept()
        self.active_clients[client_id] = (websocket, filters or set())
        logger.info("Client %s connected with filters: %s", client_id, filters)

    async def disconnect_client(self, client_id: str):
        """Handle client disconnection."""
        if client_id in self.active_clients:
            del self.active_clients[client_id]
            logger.info("Client %s disconnected", client_id)

    async def update_client_filters(self, client_id: str, filters: Set[str]):
        """Update metric filters for a client."""
        if client_id in self.active_clients:
            websocket, _ = self.active_clients[client_id]
            self.active_clients[client_id] = (websocket, filters)


dashboard = DashboardService()
app = FastAPI(title="Metrics Dashboard")


@app.get("/api/metrics/{metric_type}/history")
async def get_metric_history(
    metric_type: str,
    window: TimeWindow,
    start_time: datetime,
    end_time: datetime,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    filters: Optional[str] = None,
):
    """Get paginated historical metric data."""
    filter_dict = json.loads(filters) if filters else None
    return await dashboard.get_historical_data(
        metric_type, window, start_time, end_time, page, page_size, filter_dict
    )


@app.websocket("/ws/dashboard/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket, client_id: str, filters: Optional[str] = None
):
    """WebSocket endpoint with optimized data transfer."""
    filter_set = set(filters.split(",")) if filters else None
    await dashboard.connect_client(websocket, client_id, filter_set)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "update_filters":
                    new_filters = set(message.get("filters", []))
                    await dashboard.update_client_filters(client_id, new_filters)
            except json.JSONDecodeError:
                logger.warning("Invalid message from client %s", client_id)
    except Exception as e:
        logger.error("WebSocket error: %s", str(e))
    finally:
        await dashboard.disconnect_client(client_id)


async def start_dashboard():
    """Start the optimized dashboard service."""
    await dashboard.start()


async def stop_dashboard():
    """Stop the dashboard service."""
    await dashboard.stop()


static_path = Path(__file__).parent / "static"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/")
async def get_dashboard():
    """Serve the dashboard HTML page."""
    return Response(content=_get_dashboard_html(), media_type="text/html")


def _get_dashboard_html() -> str:
    """Generate the dashboard HTML content."""
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        "<title>Metrics Dashboard</title>\n"
        '<link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">\n'
        '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>\n'
        '<script src="https://cdn.jsdelivr.net/npm/moment"></script>\n'
        '</head>\n<body class="bg-gray-100">\n'
        '    <div class="container mx-auto px-4 py-8">\n'
        "        <!-- Status Overview Panel -->\n"
        '        <div class="bg-white rounded-lg shadow-lg p-6 mb-8">\n'
        '            <h2 class="text-2xl font-bold mb-4">System Overview</h2>\n'
        '            <div class="grid grid-cols-1 md:grid-cols-3 gap-4" id="overview-panel">\n'
        "                <!-- Filled dynamically -->\n"
        "            </div>\n"
        "        </div>\n"
        "    </div>\n"
        "</body>\n"
        "</html>"
    )
