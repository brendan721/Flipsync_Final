import asyncio
import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

import jwt
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.security import HTTPBearer

from fs_agt_clean.core.config.manager import ConfigManager
from fs_agt_clean.core.monitoring.log_manager import LogManager
from fs_agt_clean.core.monitoring.metrics.models import MetricDataPoint
from fs_agt_clean.core.utils.config import Settings, get_settings
from fs_agt_clean.services.metrics.service import MetricsService

logging.basicConfig(level=logging.INFO)

logger: logging.Logger = logging.getLogger(__name__)
app = FastAPI()
security = HTTPBearer()


@dataclass
class ClientConnection:
    """Represents a connected client with rate limiting info."""

    websocket: WebSocket
    connected_at: datetime
    message_count: int = 0
    last_message_time: Optional[datetime] = None
    filters: Set[str] = field(default_factory=set)


class RealtimeMetricsService(MetricsService):
    """Real-time metrics service with WebSocket support."""

    def __init__(self):
        """Initialize the real-time metrics service."""
        config_manager = ConfigManager(config_path="config/metrics.json")
        super().__init__(config_manager)
        self.log_manager = LogManager()
        self.active_connections: Dict[str, ClientConnection] = {}
        self.rate_limits: Dict[str, int] = defaultdict(int)
        self.settings = get_settings()
        self.RATE_LIMIT_MESSAGES = 100
        self.RATE_LIMIT_WINDOW = 60
        self.analytics_service = None
        self.metrics: Dict[str, List[MetricDataPoint]] = {}
        self._lock = asyncio.Lock()

    async def collect_metrics(
        self, metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Collect and process metrics.

        Args:
            metrics: Optional metrics to process

        Returns:
            Dict containing processed metrics
        """
        # First collect base metrics from parent class
        base_metrics = await super().collect_metrics()

        async with self._lock:
            if metrics:
                # Process and store new metrics
                processed = {
                    "timestamp": datetime.now(timezone.utc),
                    "metrics": {**base_metrics, **metrics},
                    "connections": len(self.active_connections),
                    "rate_limits": dict(self.rate_limits),
                }

                # Store metrics by category
                for category, value in metrics.items():
                    if isinstance(value, (int, float)):  # Only store numeric values
                        if category not in self.metrics:
                            self.metrics[category] = []
                        self.metrics[category].append(
                            MetricDataPoint(
                                name=category,
                                value=float(value),
                                timestamp=processed["timestamp"],
                                labels={"service": "realtime"},
                            )
                        )

                        # Keep only recent metrics
                        cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
                        self.metrics[category] = [
                            m for m in self.metrics[category] if m.timestamp > cutoff
                        ]

                return processed

            # Return current metrics state if no new metrics provided
            return {
                "timestamp": datetime.now(timezone.utc),
                "connections": len(self.active_connections),
                "rate_limits": dict(self.rate_limits),
                "metrics": {
                    **base_metrics,
                    **{
                        category: [m.value for m in metrics_list]
                        for category, metrics_list in self.metrics.items()
                    },
                },
            }

    async def authenticate_connection(self, token: str) -> str:
        """Validate JWT token and return client_id."""
        try:
            payload = jwt.decode(
                token, str(self.settings.jwt_secret_key), algorithms=["HS256"]
            )
            client_id = payload.get("client_id")
            if not client_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid client_id in token",
                )
            return str(client_id)
        except jwt.InvalidTokenError as e:
            logger.error("Token validation failed: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
            )

    async def connect(
        self, websocket: WebSocket, client_id: str, filters: Optional[Set[str]] = None
    ):
        """Handle new client connection."""
        await websocket.accept()
        self.active_connections[client_id] = ClientConnection(
            websocket=websocket,
            connected_at=datetime.utcnow(),
            filters=filters or set(),
        )
        logger.info(
            "Client %s connected. Active connections: %s",
            client_id,
            len(self.active_connections),
        )

    async def disconnect(self, client_id: str):
        """Handle client disconnection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(
                "Client %s disconnected. Active connections: %s",
                client_id,
                len(self.active_connections),
            )

    def check_rate_limit(self, client_id: str) -> bool:
        """Check if client has exceeded rate limit."""
        client = self.active_connections.get(client_id)
        if not client:
            return bool(False)
        now = datetime.utcnow()
        if client.last_message_time:
            if (
                now - client.last_message_time
            ).total_seconds() > self.RATE_LIMIT_WINDOW:
                client.message_count = 0
        client.message_count += 1
        client.last_message_time = now
        return client.message_count <= self.RATE_LIMIT_MESSAGES

    async def broadcast_metric(self, metric: Dict[str, Any]):
        """Broadcast metric to all connected clients with filtering."""
        disconnected_clients = []
        for client_id, client in self.active_connections.items():
            try:
                if not self.check_rate_limit(client_id):
                    await client.websocket.send_text(
                        json.dumps(
                            {
                                "error": "Rate limit exceeded",
                                "retry_after": self.RATE_LIMIT_WINDOW,
                            }
                        )
                    )
                    continue
                if client.filters and (
                    not any(
                        metric.get("type", "") == filter_type
                        for filter_type in client.filters
                    )
                ):
                    continue
                await client.websocket.send_text(json.dumps(metric))
            except WebSocketDisconnect:
                disconnected_clients.append(client_id)
            except Exception as e:
                logger.error("Error broadcasting to client %s: %s", client_id, str(e))
                disconnected_clients.append(client_id)
        for client_id in disconnected_clients:
            await self.disconnect(client_id)


metrics_service = RealtimeMetricsService()


@app.websocket("/ws/metrics/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    token: str,
    filters: Optional[str] = None,
):
    """WebSocket endpoint for real-time metrics streaming."""
    try:
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        authenticated_client_id = await metrics_service.authenticate_connection(token)
        if authenticated_client_id != client_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        filter_set = set(filters.split(",")) if filters else None
        await metrics_service.connect(websocket, client_id, filter_set)
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    command = json.loads(data)
                    if command.get("type") == "update_filters":
                        new_filters = set(command.get("filters", []))
                        if client_id in metrics_service.active_connections:
                            metrics_service.active_connections[client_id].filters = (
                                new_filters
                            )
                except json.JSONDecodeError:
                    logger.warning("Invalid command from client %s", client_id)
        except WebSocketDisconnect:
            await metrics_service.disconnect(client_id)
    except Exception as e:
        logger.error("Error in websocket connection: %s", str(e))
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


async def publish_metric(metric_type: str, metric_data: Dict[str, Any]):
    """Publish a metric to all connected clients."""
    metric = {
        "type": metric_type,
        "timestamp": datetime.utcnow().isoformat(),
        "data": metric_data,
    }
    await metrics_service.broadcast_metric(metric)
