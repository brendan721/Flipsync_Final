"""
Real-time Agent Monitoring API for 4+1 Architecture
==================================================

Provides comprehensive monitoring for all 4 autonomous agents:
- Content Agent
- Executive Agent
- Logistics Agent
- Market Agent

Features:
- Real-time performance metrics
- Decision time tracking
- Success rate monitoring
- Confidence score analysis
- WebSocket live updates
- Alerting for performance thresholds
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Import resilience service
from fs_agt_clean.core.resilience.agent_resilience_service import resilience_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-monitoring", tags=["agent-monitoring"])


class AgentMetrics(BaseModel):
    """Agent performance metrics model."""

    agent_id: str
    agent_type: str
    status: str
    last_decision_time_ms: float
    average_decision_time_ms: float
    success_rate: float
    confidence_score: float
    decisions_made: int
    last_activity: str
    health_status: str


class AgentMonitoringService:
    """Service for monitoring autonomous agents."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        self.monitoring_active = False
        self.performance_thresholds = {
            "max_decision_time_ms": 1000,
            "min_success_rate": 0.95,
            "min_confidence_score": 0.5,
        }

    async def start_monitoring(self):
        """Start real-time monitoring of all agents."""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        asyncio.create_task(self._monitor_agents())
        logger.info("🔍 Started real-time agent monitoring")

    async def stop_monitoring(self):
        """Stop real-time monitoring."""
        self.monitoring_active = False
        logger.info("🔍 Stopped real-time agent monitoring")

    async def _monitor_agents(self):
        """Continuous monitoring loop for all agents."""
        while self.monitoring_active:
            try:
                # Test all 4 agents
                await self._test_content_agent()
                await self._test_executive_agent()
                await self._test_logistics_agent()
                await self._test_market_agent()

                # Broadcast metrics to WebSocket clients
                await self._broadcast_metrics()

                # Check for alerts
                await self._check_performance_alerts()

                # Wait 5 seconds before next monitoring cycle
                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"Error in agent monitoring: {e}")
                await asyncio.sleep(10)

    async def _test_content_agent(self):
        """Test Content Agent performance."""
        try:
            import aiohttp

            start_time = time.perf_counter()

            async with aiohttp.ClientSession() as session:
                base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
                async with session.post(
                    f"{base_url}/api/v1/agents/tasks/trigger",
                    json={
                        "agent_id": "content_autonomous_agent",
                        "task_type": "content_optimization",
                        "parameters": {
                            "product_name": "Monitor Test",
                            "marketplace": "ebay",
                        },
                    },
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    result = await response.json()

            decision_time = (time.perf_counter() - start_time) * 1000

            # Update metrics
            self.agent_metrics["content_autonomous_agent"] = AgentMetrics(
                agent_id="content_autonomous_agent",
                agent_type="content",
                status="active",
                last_decision_time_ms=decision_time,
                average_decision_time_ms=self._update_average("content", decision_time),
                success_rate=self._update_success_rate(
                    "content", result.get("success", False)
                ),
                confidence_score=result.get("result", {}).get("confidence", 0.0),
                decisions_made=self._increment_decisions("content"),
                last_activity=datetime.now(timezone.utc).isoformat(),
                health_status=self._calculate_health(
                    "content", decision_time, result.get("success", False)
                ),
            )

        except Exception as e:
            logger.error(f"Error testing Content Agent: {e}")
            self._mark_agent_error("content_autonomous_agent", "content")

    async def _test_executive_agent(self):
        """Test Executive Agent performance."""
        try:
            import aiohttp

            start_time = time.perf_counter()

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://174.138.77.110:8000/api/v1/agents/tasks/trigger",
                    json={
                        "agent_id": "executive_autonomous_agent",
                        "task_type": "strategic_planning",
                        "parameters": {
                            "business_goal": "monitor_test",
                            "budget": 100000,
                        },
                    },
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    result = await response.json()

            decision_time = (time.perf_counter() - start_time) * 1000

            # Update metrics
            self.agent_metrics["executive_autonomous_agent"] = AgentMetrics(
                agent_id="executive_autonomous_agent",
                agent_type="executive",
                status="active",
                last_decision_time_ms=decision_time,
                average_decision_time_ms=self._update_average(
                    "executive", decision_time
                ),
                success_rate=self._update_success_rate(
                    "executive", result.get("success", False)
                ),
                confidence_score=result.get("result", {}).get("confidence", 0.0),
                decisions_made=self._increment_decisions("executive"),
                last_activity=datetime.now(timezone.utc).isoformat(),
                health_status=self._calculate_health(
                    "executive", decision_time, result.get("success", False)
                ),
            )

        except Exception as e:
            logger.error(f"Error testing Executive Agent: {e}")
            self._mark_agent_error("executive_autonomous_agent", "executive")

    async def _test_logistics_agent(self):
        """Test Logistics Agent performance."""
        try:
            import aiohttp

            start_time = time.perf_counter()

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://174.138.77.110:8000/api/v1/agents/tasks/trigger",
                    json={
                        "agent_id": "logistics_autonomous_agent",
                        "task_type": "shipping_optimization",
                        "parameters": {"weight": 1.5, "distance": 300},
                    },
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    result = await response.json()

            decision_time = (time.perf_counter() - start_time) * 1000

            # Update metrics
            self.agent_metrics["logistics_autonomous_agent"] = AgentMetrics(
                agent_id="logistics_autonomous_agent",
                agent_type="logistics",
                status="active",
                last_decision_time_ms=decision_time,
                average_decision_time_ms=self._update_average(
                    "logistics", decision_time
                ),
                success_rate=self._update_success_rate(
                    "logistics", result.get("success", False)
                ),
                confidence_score=result.get("result", {}).get("confidence", 0.0),
                decisions_made=self._increment_decisions("logistics"),
                last_activity=datetime.now(timezone.utc).isoformat(),
                health_status=self._calculate_health(
                    "logistics", decision_time, result.get("success", False)
                ),
            )

        except Exception as e:
            logger.error(f"Error testing Logistics Agent: {e}")
            self._mark_agent_error("logistics_autonomous_agent", "logistics")

    async def _test_market_agent(self):
        """Test Market Agent performance."""
        try:
            import aiohttp

            start_time = time.perf_counter()

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://174.138.77.110:8000/api/v1/agents/tasks/trigger",
                    json={
                        "agent_id": "market_autonomous_agent",
                        "task_type": "pricing_optimization",
                        "parameters": {
                            "product_name": "Monitor Test",
                            "current_price": 99.99,
                        },
                    },
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    result = await response.json()

            decision_time = (time.perf_counter() - start_time) * 1000

            # Update metrics
            self.agent_metrics["market_autonomous_agent"] = AgentMetrics(
                agent_id="market_autonomous_agent",
                agent_type="market",
                status="active",
                last_decision_time_ms=decision_time,
                average_decision_time_ms=self._update_average("market", decision_time),
                success_rate=self._update_success_rate(
                    "market", result.get("success", False)
                ),
                confidence_score=result.get("result", {}).get("confidence", 0.0),
                decisions_made=self._increment_decisions("market"),
                last_activity=datetime.now(timezone.utc).isoformat(),
                health_status=self._calculate_health(
                    "market", decision_time, result.get("success", False)
                ),
            )

        except Exception as e:
            logger.error(f"Error testing Market Agent: {e}")
            self._mark_agent_error("market_autonomous_agent", "market")

    def _update_average(self, agent_type: str, new_time: float) -> float:
        """Update rolling average decision time."""
        # Simple implementation - in production, use proper rolling average
        return new_time

    def _update_success_rate(self, agent_type: str, success: bool) -> float:
        """Update success rate for agent."""
        # Simple implementation - in production, track over time window
        return 1.0 if success else 0.0

    def _increment_decisions(self, agent_type: str) -> int:
        """Increment decision counter."""
        # Simple implementation - in production, use persistent storage
        return 1

    def _calculate_health(
        self, agent_type: str, decision_time: float, success: bool
    ) -> str:
        """Calculate agent health status."""
        if not success:
            return "critical"
        elif decision_time > self.performance_thresholds["max_decision_time_ms"]:
            return "warning"
        else:
            return "healthy"

    def _mark_agent_error(self, agent_id: str, agent_type: str):
        """Mark agent as having an error."""
        self.agent_metrics[agent_id] = AgentMetrics(
            agent_id=agent_id,
            agent_type=agent_type,
            status="error",
            last_decision_time_ms=0.0,
            average_decision_time_ms=0.0,
            success_rate=0.0,
            confidence_score=0.0,
            decisions_made=0,
            last_activity=datetime.now(timezone.utc).isoformat(),
            health_status="critical",
        )

    async def _broadcast_metrics(self):
        """Broadcast metrics to all WebSocket connections."""
        if not self.active_connections:
            return

        metrics_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agents": [metrics.dict() for metrics in self.agent_metrics.values()],
            "summary": {
                "total_agents": len(self.agent_metrics),
                "healthy_agents": len(
                    [
                        m
                        for m in self.agent_metrics.values()
                        if m.health_status == "healthy"
                    ]
                ),
                "average_decision_time": (
                    sum(m.last_decision_time_ms for m in self.agent_metrics.values())
                    / len(self.agent_metrics)
                    if self.agent_metrics
                    else 0
                ),
            },
        }

        # Send to all connected clients
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(metrics_data)
            except Exception:
                disconnected.append(connection)

        # Remove disconnected clients
        for connection in disconnected:
            self.active_connections.remove(connection)

    async def _check_performance_alerts(self):
        """Check for performance threshold violations and trigger alerts."""
        for agent_id, metrics in self.agent_metrics.items():
            if (
                metrics.last_decision_time_ms
                > self.performance_thresholds["max_decision_time_ms"]
            ):
                logger.warning(
                    f"🚨 Agent {agent_id} exceeded decision time threshold: {metrics.last_decision_time_ms}ms"
                )

            if metrics.success_rate < self.performance_thresholds["min_success_rate"]:
                logger.warning(
                    f"🚨 Agent {agent_id} below success rate threshold: {metrics.success_rate}"
                )


# Global monitoring service instance
monitoring_service = AgentMonitoringService()


@router.get("/dashboard", response_class=HTMLResponse)
async def get_monitoring_dashboard():
    """Serve the agent monitoring dashboard."""
    try:
        with open("fs_agt_clean/static/agent_monitoring_dashboard.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Dashboard not found</h1>", status_code=404)


@router.get("/status")
async def get_monitoring_status():
    """Get current monitoring status."""
    return {
        "monitoring_active": monitoring_service.monitoring_active,
        "connected_clients": len(monitoring_service.active_connections),
        "monitored_agents": len(monitoring_service.agent_metrics),
        "performance_thresholds": monitoring_service.performance_thresholds,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/start")
async def start_monitoring():
    """Start real-time agent monitoring."""
    await monitoring_service.start_monitoring()
    return {"success": True, "message": "Agent monitoring started"}


@router.post("/stop")
async def stop_monitoring():
    """Stop real-time agent monitoring."""
    await monitoring_service.stop_monitoring()
    return {"success": True, "message": "Agent monitoring stopped"}


@router.get("/metrics")
async def get_current_metrics():
    """Get current agent metrics."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agents": [
            metrics.dict() for metrics in monitoring_service.agent_metrics.values()
        ],
        "summary": {
            "total_agents": len(monitoring_service.agent_metrics),
            "healthy_agents": len(
                [
                    m
                    for m in monitoring_service.agent_metrics.values()
                    if m.health_status == "healthy"
                ]
            ),
            "average_decision_time": (
                sum(
                    m.last_decision_time_ms
                    for m in monitoring_service.agent_metrics.values()
                )
                / len(monitoring_service.agent_metrics)
                if monitoring_service.agent_metrics
                else 0
            ),
        },
    }


@router.get("/resilience")
async def get_resilience_status():
    """Get resilience status for all agents."""
    agent_health = resilience_service.get_all_agent_health()
    circuit_breakers = {}

    for agent_id in [
        "content_autonomous_agent",
        "executive_autonomous_agent",
        "logistics_autonomous_agent",
        "market_autonomous_agent",
    ]:
        circuit_breakers[agent_id] = resilience_service.get_circuit_breaker_status(
            agent_id
        )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_health": {
            agent_id: {
                "agent_id": health.agent_id,
                "agent_type": health.agent_type,
                "status": health.status.value,
                "last_success": (
                    health.last_success.isoformat() if health.last_success else None
                ),
                "last_failure": (
                    health.last_failure.isoformat() if health.last_failure else None
                ),
                "failure_count": health.failure_count,
                "success_count": health.success_count,
                "average_response_time": health.average_response_time,
                "confidence_score": health.confidence_score,
            }
            for agent_id, health in agent_health.items()
        },
        "circuit_breakers": circuit_breakers,
        "summary": {
            "healthy_agents": len(
                [h for h in agent_health.values() if h.status.value == "healthy"]
            ),
            "degraded_agents": len(
                [h for h in agent_health.values() if h.status.value == "degraded"]
            ),
            "critical_agents": len(
                [h for h in agent_health.values() if h.status.value == "critical"]
            ),
            "total_monitored": len(agent_health),
        },
    }


@router.websocket("/ws")
async def websocket_monitoring(websocket: WebSocket):
    """WebSocket endpoint for real-time agent monitoring."""
    await websocket.accept()
    monitoring_service.active_connections.append(websocket)

    try:
        # Start monitoring if not already active
        if not monitoring_service.monitoring_active:
            await monitoring_service.start_monitoring()

        # Keep connection alive
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        monitoring_service.active_connections.remove(websocket)
        logger.info("WebSocket client disconnected from agent monitoring")
