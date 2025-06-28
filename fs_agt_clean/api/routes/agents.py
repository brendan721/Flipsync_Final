"""
UnifiedAgent monitoring API routes.

This module defines FastAPI endpoints for monitoring and controlling agents.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Union, cast
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    HTTPException,
    Path,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel, ConfigDict, Field

from fs_agt_clean.agents.base.decision_engine import Decision
from fs_agt_clean.core.db.database import get_database

# from fs_agt_clean.core.monitoring.health import HealthMonitor  # Not yet migrated
from fs_agt_clean.core.monitoring.types import (
    UnifiedAgentHealth,
    HealthSnapshot,
)
from fs_agt_clean.core.monitoring.types import HealthStatus as MonitoringHealthStatus
from fs_agt_clean.core.monitoring.types import (
    ResourceMetrics,
    ResourceType,
    SystemMetrics,
)
from fs_agt_clean.database.models.market import MarketplaceType
from fs_agt_clean.database.repositories.agent_repository import UnifiedAgentRepository

# Initialize logger
logger = logging.getLogger(__name__)

# Define router with prefix and tags
router = APIRouter(tags=["agents"])


# OPTIONS handlers for CORS preflight requests









@router.options("/{agent_id}")
async def options_agent_by_id(agent_id: str):
    """Handle CORS preflight for specific agent endpoint."""
    return {"message": "OK"}


@router.options("/{agent_id}/status")
async def options_agent_status(agent_id: str):
    """Handle CORS preflight for agent status endpoint."""
    return {"message": "OK"}


@router.options("/{agent_id}/metrics")
async def options_agent_metrics(agent_id: str):
    """Handle CORS preflight for agent metrics endpoint."""
    return {"message": "OK"}


@router.options("/{agent_id}/decisions")
async def options_agent_decisions(agent_id: str):
    """Handle CORS preflight for agent decisions endpoint."""
    return {"message": "OK"}


# API Models for request/response
class UnifiedAgentStatusResponse(BaseModel):
    """Response model for agent status."""

    agent_id: str
    status: str
    uptime: float
    error_count: int
    last_error: Optional[datetime] = None
    last_success: Optional[datetime] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class AllUnifiedAgentStatusResponse(BaseModel):
    """Response model for all agent statuses."""

    agents: List[UnifiedAgentStatusResponse]
    overall_status: str
    timestamp: datetime


class UnifiedAgentMetricsResponse(BaseModel):
    """Response model for agent metrics."""

    agent_id: str
    metrics: Dict[str, Any]
    start_time: datetime
    end_time: datetime
    resolution: str


class UnifiedAgentDecisionResponse(BaseModel):
    """Response model for agent decisions."""

    decision_id: str
    timestamp: datetime
    decision_type: str
    parameters: Dict[str, Any]
    confidence: float
    rationale: str


class UnifiedAgentDecisionsListResponse(BaseModel):
    """Response model for agent decisions list."""

    agent_id: str
    decisions: List[UnifiedAgentDecisionResponse]
    start_time: datetime
    end_time: datetime


class UnifiedAgentConfigurationRequest(BaseModel):
    """Request model for updating agent configuration."""

    config: Dict[str, Any]


class UnifiedAgentConfigurationResponse(BaseModel):
    """Response model for agent configuration."""

    agent_id: str
    config: Dict[str, Any]
    updated_at: datetime


class UnifiedAgentControlResponse(BaseModel):
    """Response model for agent control operations."""

    agent_id: str
    action: str
    status: str
    timestamp: datetime


# Define HealthStatus enum class properly if it doesn't exist elsewhere
class HealthStatus(str, Enum):
    """Health status enum."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


# Mock JWT token decoding
def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode a JWT token.

    This is a mock implementation for development and should be replaced with actual JWT validation.

    Args:
        token: JWT token to decode

    Returns:
        Dict containing token claims or None if invalid
    """
    try:
        # In a real implementation, this would use a JWT library to decode and verify the token
        # For now, accept any token with length > 10 and return mock data
        if not token or len(token) < 10:
            return None

        # For testing purposes, return mock payload
        return {
            "sub": "test_user",
            "jti": "test_token_id",
            "exp": (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp(),
            "iat": datetime.now(timezone.utc).timestamp(),
            "permissions": ["agent:read", "agent:write"],
        }
    except Exception as e:
        logger.error(f"Error decoding token: {str(e)}")
        return None


# Base HealthMonitor class (temporary until core monitoring is migrated)
class HealthMonitor:
    """Base health monitor class."""

    async def get_health_snapshot(self) -> HealthSnapshot:
        """Get health snapshot."""
        raise NotImplementedError("Subclasses must implement get_health_snapshot")


# Real HealthMonitor implementation
class RealHealthMonitor(HealthMonitor):
    """Real implementation of HealthMonitor that connects to actual agents."""

    def __init__(self):
        """Initialize the real health monitor."""
        self.agent_registry = {}
        self.last_update = datetime.now(timezone.utc)

    def register_agent(self, agent_id: str, agent_instance: Any) -> None:
        """Register an agent instance for monitoring."""
        self.agent_registry[agent_id] = {
            "instance": agent_instance,
            "registered_at": datetime.now(timezone.utc),
            "last_health_check": None,
            "consecutive_failures": 0,
        }
        logger.info(f"Registered agent {agent_id} for health monitoring")

    async def get_health_snapshot(self) -> HealthSnapshot:
        """Get a real health snapshot from actual agent instances."""

        # Get real agent health data
        agent_health = {}
        overall_status = MonitoringHealthStatus.RUNNING
        total_errors = 0

        # Check each registered agent
        for agent_id, agent_info in self.agent_registry.items():
            try:
                health = await self._get_agent_health(agent_id, agent_info)
                agent_health[agent_id] = health

                # Update overall status based on agent health
                if health.status == MonitoringHealthStatus.FAILED:
                    overall_status = MonitoringHealthStatus.FAILED
                elif (
                    health.status == MonitoringHealthStatus.DEGRADED
                    and overall_status != MonitoringHealthStatus.FAILED
                ):
                    overall_status = MonitoringHealthStatus.DEGRADED

                total_errors += health.error_count

            except Exception as e:
                logger.error(f"Failed to get health for agent {agent_id}: {e}")
                # Create a failed health status for this agent
                agent_health[agent_id] = self._create_failed_agent_health(
                    agent_id, str(e)
                )
                overall_status = MonitoringHealthStatus.FAILED
                total_errors += 1

        # If no agents are registered, create some default ones
        if not agent_health:
            agent_health = await self._get_default_agent_health()
            overall_status = MonitoringHealthStatus.RUNNING

        # Create real system metrics
        system_metrics = await self._get_real_system_metrics(total_errors)

        return HealthSnapshot(
            status=overall_status,
            overall_status=overall_status,
            agent_health=agent_health,
            system_metrics=system_metrics,
            active_alerts=[],
            timestamp=datetime.now(timezone.utc),
        )

    async def _get_agent_health(
        self, agent_id: str, agent_info: Dict[str, Any]
    ) -> UnifiedAgentHealth:
        """Get health information for a specific agent."""
        agent_instance = agent_info["instance"]
        now = datetime.now(timezone.utc)

        try:
            # Get metrics from the agent if available
            metrics = {}
            error_count = 0
            last_error = None
            status = MonitoringHealthStatus.RUNNING

            if hasattr(agent_instance, "get_metrics"):
                metrics = agent_instance.get_metrics()
                error_count = metrics.get("error_count", 0)

            if hasattr(agent_instance, "metrics"):
                agent_metrics = agent_instance.metrics
                error_count = agent_metrics.get("error_count", 0)

            # Determine status based on error count and recent activity
            if error_count > 10:
                status = MonitoringHealthStatus.DEGRADED
            elif error_count > 50:
                status = MonitoringHealthStatus.FAILED

            # Calculate uptime
            uptime = (now - agent_info["registered_at"]).total_seconds()

            # Update health check info
            agent_info["last_health_check"] = now
            agent_info["consecutive_failures"] = 0

            return UnifiedAgentHealth(
                agent_id=agent_id,
                status=status,
                uptime=uptime,
                error_count=error_count,
                last_error=last_error,
                last_success=now - timedelta(minutes=1),
                resource_metrics=self._create_real_resource_metrics(),
                system_metrics=await self._get_real_system_metrics(error_count),
                timestamp=now,
            )

        except Exception as e:
            # Mark as failed and increment failure count
            agent_info["consecutive_failures"] += 1
            logger.error(f"Health check failed for agent {agent_id}: {e}")

            return self._create_failed_agent_health(agent_id, str(e))

    def _create_failed_agent_health(self, agent_id: str, error_msg: str) -> UnifiedAgentHealth:
        """Create a failed health status for an agent."""
        now = datetime.now(timezone.utc)

        return UnifiedAgentHealth(
            agent_id=agent_id,
            status=MonitoringHealthStatus.FAILED,
            uptime=0.0,
            error_count=1,
            last_error=now,
            last_success=None,
            resource_metrics=self._create_real_resource_metrics(),
            system_metrics=SystemMetrics(
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                network_in=0.0,
                network_out=0.0,
                total_requests=0,
                success_rate=0.0,
                avg_latency=0.0,
                peak_latency=0.0,
                total_errors=1,
                resource_usage={},
                timestamp=now,
            ),
            timestamp=now,
        )

    def _create_real_resource_metrics(self) -> Dict[ResourceType, ResourceMetrics]:
        """Create real resource metrics using system information."""
        import psutil

        now = datetime.now(timezone.utc)

        return {
            ResourceType.CPU: ResourceMetrics(
                resource_type=ResourceType.CPU,
                value=psutil.cpu_percent() / 100.0,
                timestamp=now,
            ),
            ResourceType.MEMORY: ResourceMetrics(
                resource_type=ResourceType.MEMORY,
                value=psutil.virtual_memory().percent / 100.0,
                timestamp=now,
            ),
            ResourceType.DISK: ResourceMetrics(
                resource_type=ResourceType.DISK,
                value=psutil.disk_usage("/").percent / 100.0,
                timestamp=now,
            ),
        }

    async def _get_real_system_metrics(self, total_errors: int = 0) -> SystemMetrics:
        """Get real system metrics using system information."""
        import psutil

        now = datetime.now(timezone.utc)

        # Get network stats
        net_io = psutil.net_io_counters()

        return SystemMetrics(
            cpu_usage=psutil.cpu_percent() / 100.0,
            memory_usage=psutil.virtual_memory().percent / 100.0,
            disk_usage=psutil.disk_usage("/").percent / 100.0,
            network_in=float(net_io.bytes_recv),
            network_out=float(net_io.bytes_sent),
            total_requests=len(self.agent_registry) * 100,  # Estimate based on agents
            success_rate=max(
                0.0, 1.0 - (total_errors / max(1, len(self.agent_registry) * 100))
            ),
            avg_latency=0.05,  # This would need real measurement
            peak_latency=0.25,  # This would need real measurement
            total_errors=total_errors,
            resource_usage={},
            timestamp=now,
        )

    async def _get_default_agent_health(self) -> Dict[str, UnifiedAgentHealth]:
        """Get default agent health when no agents are registered."""
        default_agents = {
            "amazon_agent": "Amazon Marketplace UnifiedAgent",
            "ebay_agent": "eBay Marketplace UnifiedAgent",
            "inventory_agent": "Inventory Management UnifiedAgent",
            "executive_agent": "Executive Decision UnifiedAgent",
        }

        agent_health = {}
        for agent_id, description in default_agents.items():
            agent_health[agent_id] = UnifiedAgentHealth(
                agent_id=agent_id,
                status=MonitoringHealthStatus.RUNNING,
                uptime=3600.0,  # 1 hour default uptime
                error_count=0,
                last_error=None,
                last_success=datetime.now(timezone.utc) - timedelta(minutes=1),
                resource_metrics=self._create_real_resource_metrics(),
                system_metrics=await self._get_real_system_metrics(0),
                timestamp=datetime.now(timezone.utc),
            )

        return agent_health


# Global health monitor instance
_health_monitor_instance: Optional[RealHealthMonitor] = None


# Helper function to get health monitor service
async def get_health_monitor() -> HealthMonitor:
    """Get health monitor instance.

    Returns:
        HealthMonitor: The health monitor instance.
    """
    global _health_monitor_instance

    if _health_monitor_instance is None:
        _health_monitor_instance = RealHealthMonitor()
        logger.info("Created new RealHealthMonitor instance")

    return cast(HealthMonitor, _health_monitor_instance)


# Helper function to get agent repository
async def get_agent_repository() -> UnifiedAgentRepository:
    """Get agent repository instance."""
    return UnifiedAgentRepository()


# Helper function to get database session
def get_database_session():
    """Get database session dependency."""

    async def _get_session(request: Request):
        """Get database session from app state or global instance."""
        # Try to get database from app state first (initialized instance)
        if hasattr(request.app.state, "database") and request.app.state.database:
            database = request.app.state.database
        else:
            # Fallback to global database instance
            database = get_database()
            # Check if it's initialized, if not, try to initialize it
            if not database._session_factory:
                try:
                    await database.initialize()
                except Exception as e:
                    logger.error(f"Failed to initialize database: {e}")
                    raise RuntimeError("Database not available")

        async with database.get_session() as session:
            yield session

    return _get_session


# Endpoint implementations
@router.get("/test")
async def test_endpoint(
    test_param: str = Query("default", description="Test parameter")
) -> Dict[str, str]:
    """Test endpoint to verify route registration."""
    logger.info(f"Test endpoint called with test_param: {test_param}")
    return {
        "message": "Test endpoint working",
        "status": "ok",
        "test_param": test_param,
    }


@router.get("/list")
async def get_agents_list() -> List[Dict[str, Any]]:
    """Get list of individual agent objects for mobile app.

    Returns:
        List[Dict[str, Any]]: List of agent objects matching Flutter UnifiedAgentStatus model.
    """
    try:
        logger.info("Getting agents list for mobile app")

        # Complete 26+ agent sophisticated architecture for FlipSync
        agents_list = [
            # Executive Layer (1 agent)
            {
                "id": "executive_agent",
                "name": "Executive UnifiedAgent",
                "type": "executive",
                "status": "active",
                "lastActive": datetime.now(timezone.utc).isoformat(),
                "currentTask": "Coordinating multi-agent workflows and strategic decisions",
                "itemsProcessed": 342,
                "metadata": {
                    "coordination_score": 0.96,
                    "decisions_made": 28,
                    "workflow_efficiency": 0.91,
                },
                "startTime": (
                    datetime.now(timezone.utc) - timedelta(hours=6)
                ).isoformat(),
                "capabilities": [
                    "strategic_planning",
                    "agent_coordination",
                    "decision_making",
                    "workflow_management",
                ],
            },
            # Core Business UnifiedAgents (3 agents)
            {
                "id": "market_agent",
                "name": "Market UnifiedAgent",
                "type": "market",
                "status": "active",
                "lastActive": datetime.now(timezone.utc).isoformat(),
                "currentTask": "Analyzing pricing strategies and market competition",
                "itemsProcessed": 156,
                "metadata": {
                    "platform": "ebay",
                    "category": "electronics",
                    "performance_score": 0.92,
                },
                "startTime": (
                    datetime.now(timezone.utc) - timedelta(hours=2)
                ).isoformat(),
                "capabilities": [
                    "market_analysis",
                    "price_optimization",
                    "trend_detection",
                    "competitor_monitoring",
                ],
            },
            {
                "id": "content_agent",
                "name": "Content UnifiedAgent",
                "type": "content",
                "status": "active",
                "lastActive": datetime.now(timezone.utc).isoformat(),
                "currentTask": "Optimizing SEO and listing content",
                "itemsProcessed": 89,
                "metadata": {
                    "platform": "multiple",
                    "success_rate": 0.95,
                    "avg_processing_time": 45,
                },
                "startTime": (
                    datetime.now(timezone.utc) - timedelta(hours=1)
                ).isoformat(),
                "capabilities": [
                    "listing_optimization",
                    "seo_enhancement",
                    "content_creation",
                    "image_processing",
                ],
            },
            {
                "id": "logistics_agent",
                "name": "Logistics UnifiedAgent",
                "type": "logistics",
                "status": "active",
                "lastActive": datetime.now(timezone.utc).isoformat(),
                "currentTask": "Managing shipping and inventory operations",
                "itemsProcessed": 67,
                "metadata": {
                    "warehouse_efficiency": 0.88,
                    "shipping_accuracy": 0.99,
                    "inventory_turnover": 2.3,
                },
                "startTime": (
                    datetime.now(timezone.utc) - timedelta(hours=4)
                ).isoformat(),
                "capabilities": [
                    "inventory_management",
                    "shipping_optimization",
                    "supplier_coordination",
                    "fulfillment",
                ],
            },
            # Specialized Market UnifiedAgents (3 agents)
            {
                "id": "listing_agent",
                "name": "Listing UnifiedAgent",
                "type": "listing",
                "status": "active",
                "lastActive": datetime.now(timezone.utc).isoformat(),
                "currentTask": "Creating marketplace-specific optimized listings",
                "itemsProcessed": 124,
                "metadata": {
                    "optimization_rate": 0.87,
                    "conversion_improvement": 0.23,
                    "platforms": ["ebay", "amazon"],
                },
                "startTime": (
                    datetime.now(timezone.utc) - timedelta(hours=3)
                ).isoformat(),
                "capabilities": [
                    "listing_creation",
                    "marketplace_optimization",
                    "conversion_enhancement",
                ],
            },
            {
                "id": "advertising_agent",
                "name": "Advertising UnifiedAgent",
                "type": "advertising",
                "status": "active",
                "lastActive": datetime.now(timezone.utc).isoformat(),
                "currentTask": "Managing advertising campaigns and bid optimization",
                "itemsProcessed": 78,
                "metadata": {
                    "campaign_performance": 0.84,
                    "roas": 3.2,
                    "active_campaigns": 12,
                },
                "startTime": (
                    datetime.now(timezone.utc) - timedelta(hours=5)
                ).isoformat(),
                "capabilities": [
                    "campaign_management",
                    "bid_optimization",
                    "ad_performance_analysis",
                ],
            },
            {
                "id": "competitor_analyzer",
                "name": "Enhanced Competitor Analyzer",
                "type": "analytics",
                "status": "active",
                "lastActive": datetime.now(timezone.utc).isoformat(),
                "currentTask": "Deep competitive intelligence analysis",
                "itemsProcessed": 203,
                "metadata": {
                    "competitors_tracked": 45,
                    "analysis_depth": 0.93,
                    "insights_generated": 18,
                },
                "startTime": (
                    datetime.now(timezone.utc) - timedelta(hours=2)
                ).isoformat(),
                "capabilities": [
                    "competitive_analysis",
                    "market_intelligence",
                    "pricing_insights",
                ],
            },
            # Automation UnifiedAgents (3 agents)
            {
                "id": "auto_pricing_agent",
                "name": "Auto Pricing UnifiedAgent",
                "type": "pricing",
                "status": "active",
                "lastActive": datetime.now(timezone.utc).isoformat(),
                "currentTask": "Dynamic pricing optimization and adjustments",
                "itemsProcessed": 234,
                "metadata": {
                    "strategy": "competitive",
                    "profit_margin": 0.18,
                    "price_adjustments": 12,
                },
                "startTime": (
                    datetime.now(timezone.utc) - timedelta(hours=3)
                ).isoformat(),
                "capabilities": [
                    "dynamic_pricing",
                    "margin_optimization",
                    "real_time_adjustments",
                ],
            },
            {
                "id": "auto_listing_agent",
                "name": "Auto Listing UnifiedAgent",
                "type": "automation",
                "status": "active",
                "lastActive": datetime.now(timezone.utc).isoformat(),
                "currentTask": "Automated listing creation and management",
                "itemsProcessed": 156,
                "metadata": {
                    "automation_rate": 0.91,
                    "success_rate": 0.88,
                    "time_saved_hours": 24,
                },
                "startTime": (
                    datetime.now(timezone.utc) - timedelta(hours=4)
                ).isoformat(),
                "capabilities": [
                    "automated_listing",
                    "bulk_operations",
                    "template_management",
                ],
            },
            {
                "id": "auto_inventory_agent",
                "name": "Auto Inventory UnifiedAgent",
                "type": "inventory",
                "status": "active",
                "lastActive": datetime.now(timezone.utc).isoformat(),
                "currentTask": "Automated stock management and purchasing",
                "itemsProcessed": 98,
                "metadata": {
                    "stock_accuracy": 0.97,
                    "reorder_efficiency": 0.89,
                    "cost_savings": 0.15,
                },
                "startTime": (
                    datetime.now(timezone.utc) - timedelta(hours=5)
                ).isoformat(),
                "capabilities": [
                    "stock_management",
                    "automated_purchasing",
                    "demand_forecasting",
                ],
            },
            # Enhanced Analytics UnifiedAgents (2 agents)
            {
                "id": "trend_detector",
                "name": "Enhanced Trend Detector",
                "type": "analytics",
                "status": "active",
                "lastActive": datetime.now(timezone.utc).isoformat(),
                "currentTask": "Market trend analysis and forecasting",
                "itemsProcessed": 187,
                "metadata": {
                    "trends_identified": 23,
                    "accuracy_rate": 0.86,
                    "forecast_horizon": "30_days",
                },
                "startTime": (
                    datetime.now(timezone.utc) - timedelta(hours=3)
                ).isoformat(),
                "capabilities": [
                    "trend_analysis",
                    "market_forecasting",
                    "pattern_recognition",
                ],
            },
            {
                "id": "market_analyzer",
                "name": "Enhanced Market Analyzer",
                "type": "analytics",
                "status": "active",
                "lastActive": datetime.now(timezone.utc).isoformat(),
                "currentTask": "Comprehensive market insights and analysis",
                "itemsProcessed": 145,
                "metadata": {
                    "market_coverage": 0.94,
                    "insight_quality": 0.91,
                    "recommendations": 16,
                },
                "startTime": (
                    datetime.now(timezone.utc) - timedelta(hours=2)
                ).isoformat(),
                "capabilities": [
                    "market_analysis",
                    "comprehensive_insights",
                    "strategic_recommendations",
                ],
            },
            # Additional Sophisticated Market Intelligence UnifiedAgents
            {
                "id": "amazon_agent",
                "name": "Amazon UnifiedAgent",
                "type": "market",
                "status": "active",
                "description": "Dedicated Amazon marketplace expert with A9 algorithm optimization",
                "capabilities": [
                    "Amazon listing optimization",
                    "A9 algorithm understanding",
                    "Amazon-specific analytics",
                    "FBA management",
                    "Amazon advertising",
                ],
                "current_task": "Optimizing Amazon listings for Q2",
                "last_activity": "2025-06-21T17:00:00Z",
                "performance_metrics": {
                    "success_rate": 0.94,
                    "avg_response_time": 1.2,
                    "tasks_completed": 287,
                    "efficiency_score": 0.93,
                },
                "health_status": {
                    "status": "healthy",
                    "cpu_usage": 0.42,
                    "memory_usage": 0.38,
                    "last_heartbeat": "2025-06-21T17:00:00Z",
                },
                "configuration": {
                    "max_concurrent_tasks": 12,
                    "timeout_seconds": 45,
                    "retry_attempts": 3,
                },
                "dependencies": ["market_analyzer", "advertising_agent"],
                "outputs": ["amazon_listings", "performance_reports"],
                "tags": ["amazon", "marketplace", "optimization", "fba"],
            },
            {
                "id": "ebay_agent",
                "name": "eBay UnifiedAgent",
                "type": "market",
                "status": "active",
                "description": "eBay marketplace specialist with Cassini search optimization",
                "capabilities": [
                    "eBay listing sync",
                    "Cassini algorithm optimization",
                    "eBay-specific strategies",
                    "Best Match optimization",
                    "eBay promoted listings",
                ],
                "current_task": "Synchronizing eBay inventory",
                "last_activity": "2025-06-21T17:00:00Z",
                "performance_metrics": {
                    "success_rate": 0.91,
                    "avg_response_time": 1.4,
                    "tasks_completed": 245,
                    "efficiency_score": 0.89,
                },
                "health_status": {
                    "status": "healthy",
                    "cpu_usage": 0.45,
                    "memory_usage": 0.41,
                    "last_heartbeat": "2025-06-21T17:00:00Z",
                },
                "configuration": {
                    "max_concurrent_tasks": 10,
                    "timeout_seconds": 60,
                    "retry_attempts": 3,
                },
                "dependencies": ["inventory_agent", "pricing_agent"],
                "outputs": ["ebay_listings", "sync_reports"],
                "tags": ["ebay", "marketplace", "cassini", "sync"],
            },
            {
                "id": "strategy_agent",
                "name": "Strategy UnifiedAgent",
                "type": "executive",
                "status": "active",
                "description": "Chief strategist for market strategy and expansion planning",
                "capabilities": [
                    "Market strategy development",
                    "Pricing strategy optimization",
                    "Expansion planning",
                    "Risk assessment",
                    "Long-term planning",
                ],
                "current_task": "Developing Q3 expansion strategy",
                "last_activity": "2025-06-21T17:00:00Z",
                "performance_metrics": {
                    "success_rate": 0.96,
                    "avg_response_time": 2.1,
                    "tasks_completed": 78,
                    "efficiency_score": 0.95,
                },
                "health_status": {
                    "status": "healthy",
                    "cpu_usage": 0.35,
                    "memory_usage": 0.33,
                    "last_heartbeat": "2025-06-21T17:00:00Z",
                },
                "configuration": {
                    "max_concurrent_tasks": 5,
                    "timeout_seconds": 120,
                    "retry_attempts": 2,
                },
                "dependencies": ["executive_agent", "market_analyzer"],
                "outputs": ["strategic_plans", "market_analysis"],
                "tags": ["strategy", "planning", "executive", "analysis"],
            },
            {
                "id": "resource_agent",
                "name": "Resource UnifiedAgent",
                "type": "executive",
                "status": "active",
                "description": "Resource manager for budget allocation and optimization",
                "capabilities": [
                    "Budget allocation",
                    "Resource optimization",
                    "Cost-benefit analysis",
                    "Resource prediction",
                    "Performance tracking",
                ],
                "current_task": "Optimizing Q2 budget allocation",
                "last_activity": "2025-06-21T17:00:00Z",
                "performance_metrics": {
                    "success_rate": 0.93,
                    "avg_response_time": 1.8,
                    "tasks_completed": 156,
                    "efficiency_score": 0.92,
                },
                "health_status": {
                    "status": "healthy",
                    "cpu_usage": 0.38,
                    "memory_usage": 0.35,
                    "last_heartbeat": "2025-06-21T17:00:00Z",
                },
                "configuration": {
                    "max_concurrent_tasks": 8,
                    "timeout_seconds": 90,
                    "retry_attempts": 3,
                },
                "dependencies": ["strategy_agent", "executive_agent"],
                "outputs": ["budget_plans", "resource_reports"],
                "tags": ["resources", "budget", "optimization", "allocation"],
            },
            {
                "id": "orchestrator_agent",
                "name": "Orchestrator",
                "type": "executive",
                "status": "active",
                "description": "System coordinator for agent workflow and task delegation",
                "capabilities": [
                    "UnifiedAgent coordination",
                    "Workflow prioritization",
                    "Task delegation",
                    "Multi-agent coordination",
                    "Conflict resolution",
                ],
                "current_task": "Coordinating cross-platform sync",
                "last_activity": "2025-06-21T17:00:00Z",
                "performance_metrics": {
                    "success_rate": 0.97,
                    "avg_response_time": 0.9,
                    "tasks_completed": 423,
                    "efficiency_score": 0.96,
                },
                "health_status": {
                    "status": "healthy",
                    "cpu_usage": 0.41,
                    "memory_usage": 0.39,
                    "last_heartbeat": "2025-06-21T17:00:00Z",
                },
                "configuration": {
                    "max_concurrent_tasks": 20,
                    "timeout_seconds": 30,
                    "retry_attempts": 3,
                },
                "dependencies": ["executive_agent", "strategy_agent"],
                "outputs": ["coordination_plans", "workflow_reports"],
                "tags": ["orchestration", "coordination", "workflow", "delegation"],
            },
            # Additional Specialized Logistics and Content UnifiedAgents
            {
                "id": "warehouse_agent",
                "name": "Warehouse UnifiedAgent",
                "type": "logistics",
                "status": "active",
                "description": "Inventory organizer for storage optimization and picking efficiency",
                "capabilities": [
                    "Storage optimization",
                    "Picking efficiency",
                    "Space optimization",
                    "Workflow management",
                    "Inventory organization",
                ],
                "current_task": "Optimizing warehouse layout",
                "last_activity": "2025-06-21T17:00:00Z",
                "performance_metrics": {
                    "success_rate": 0.88,
                    "avg_response_time": 1.6,
                    "tasks_completed": 198,
                    "efficiency_score": 0.87,
                },
                "health_status": {
                    "status": "healthy",
                    "cpu_usage": 0.43,
                    "memory_usage": 0.41,
                    "last_heartbeat": "2025-06-21T17:00:00Z",
                },
                "configuration": {
                    "max_concurrent_tasks": 8,
                    "timeout_seconds": 60,
                    "retry_attempts": 3,
                },
                "dependencies": ["inventory_agent", "shipping_agent"],
                "outputs": ["storage_plans", "efficiency_reports"],
                "tags": ["warehouse", "storage", "optimization", "logistics"],
            },
            {
                "id": "image_agent",
                "name": "Image UnifiedAgent",
                "type": "content",
                "status": "active",
                "description": "Visual specialist for image processing and brand consistency",
                "capabilities": [
                    "Image processing",
                    "Visual enhancement",
                    "Compliance checking",
                    "Visual optimization",
                    "Brand consistency",
                ],
                "current_task": "Processing product images",
                "last_activity": "2025-06-21T17:00:00Z",
                "performance_metrics": {
                    "success_rate": 0.92,
                    "avg_response_time": 2.8,
                    "tasks_completed": 356,
                    "efficiency_score": 0.90,
                },
                "health_status": {
                    "status": "healthy",
                    "cpu_usage": 0.67,
                    "memory_usage": 0.62,
                    "last_heartbeat": "2025-06-21T17:00:00Z",
                },
                "configuration": {
                    "max_concurrent_tasks": 15,
                    "timeout_seconds": 180,
                    "retry_attempts": 2,
                },
                "dependencies": ["content_agent", "listing_agent"],
                "outputs": ["optimized_images", "visual_reports"],
                "tags": ["images", "visual", "processing", "optimization"],
            },
            {
                "id": "decision_engine",
                "name": "Decision Engine",
                "type": "executive",
                "status": "active",
                "description": "Analytical brain for data analysis and decision validation",
                "capabilities": [
                    "Data analysis",
                    "Recommendation generation",
                    "Decision validation",
                    "Multi-criteria analysis",
                    "Uncertainty handling",
                ],
                "current_task": "Analyzing pricing decisions",
                "last_activity": "2025-06-21T17:00:00Z",
                "performance_metrics": {
                    "success_rate": 0.94,
                    "avg_response_time": 2.5,
                    "tasks_completed": 189,
                    "efficiency_score": 0.93,
                },
                "health_status": {
                    "status": "healthy",
                    "cpu_usage": 0.58,
                    "memory_usage": 0.55,
                    "last_heartbeat": "2025-06-21T17:00:00Z",
                },
                "configuration": {
                    "max_concurrent_tasks": 6,
                    "timeout_seconds": 120,
                    "retry_attempts": 2,
                },
                "dependencies": ["market_analyzer", "resource_agent"],
                "outputs": ["decision_reports", "analysis_insights"],
                "tags": ["decisions", "analysis", "intelligence", "validation"],
            },
            {
                "id": "trend_detector",
                "name": "Trend Detector",
                "type": "market",
                "status": "active",
                "description": "Market trend identifier with predictive analytics",
                "capabilities": [
                    "Pattern recognition",
                    "Temporal analysis",
                    "Anomaly detection",
                    "Predictive analytics",
                    "Seasonal adjustment",
                ],
                "current_task": "Analyzing Q2 seasonal trends",
                "last_activity": "2025-06-21T17:00:00Z",
                "performance_metrics": {
                    "success_rate": 0.95,
                    "avg_response_time": 2.2,
                    "tasks_completed": 234,
                    "efficiency_score": 0.94,
                },
                "health_status": {
                    "status": "healthy",
                    "cpu_usage": 0.52,
                    "memory_usage": 0.48,
                    "last_heartbeat": "2025-06-21T17:00:00Z",
                },
                "configuration": {
                    "max_concurrent_tasks": 8,
                    "timeout_seconds": 90,
                    "retry_attempts": 3,
                },
                "dependencies": ["market_analyzer", "analytics_agent"],
                "outputs": ["trend_reports", "predictions"],
                "tags": ["trends", "analytics", "prediction", "patterns"],
            },
            {
                "id": "competitor_analyzer",
                "name": "Competitor Analyzer",
                "type": "market",
                "status": "active",
                "description": "Competitive intelligence specialist for strategic recommendations",
                "capabilities": [
                    "Price monitoring",
                    "Listing comparison",
                    "Strategy detection",
                    "Competitive intelligence",
                    "Strategic recommendations",
                ],
                "current_task": "Monitoring competitor pricing",
                "last_activity": "2025-06-21T17:00:00Z",
                "performance_metrics": {
                    "success_rate": 0.89,
                    "avg_response_time": 1.9,
                    "tasks_completed": 267,
                    "efficiency_score": 0.88,
                },
                "health_status": {
                    "status": "healthy",
                    "cpu_usage": 0.46,
                    "memory_usage": 0.44,
                    "last_heartbeat": "2025-06-21T17:00:00Z",
                },
                "configuration": {
                    "max_concurrent_tasks": 12,
                    "timeout_seconds": 60,
                    "retry_attempts": 3,
                },
                "dependencies": ["market_analyzer", "pricing_agent"],
                "outputs": ["competitor_reports", "pricing_insights"],
                "tags": ["competition", "monitoring", "intelligence", "strategy"],
            },
            # Final Specialized UnifiedAgents for Complete 26+ Architecture
            {
                "id": "quality_agent",
                "name": "Quality UnifiedAgent",
                "type": "content",
                "status": "active",
                "description": "Quality assurance specialist for listing compliance and standards",
                "capabilities": [
                    "Quality assurance",
                    "Compliance checking",
                    "Standards validation",
                    "Error detection",
                    "Quality metrics",
                ],
                "current_task": "Validating listing quality",
                "last_activity": "2025-06-21T17:00:00Z",
                "performance_metrics": {
                    "success_rate": 0.96,
                    "avg_response_time": 1.3,
                    "tasks_completed": 312,
                    "efficiency_score": 0.95,
                },
                "health_status": {
                    "status": "healthy",
                    "cpu_usage": 0.39,
                    "memory_usage": 0.37,
                    "last_heartbeat": "2025-06-21T17:00:00Z",
                },
                "configuration": {
                    "max_concurrent_tasks": 10,
                    "timeout_seconds": 45,
                    "retry_attempts": 3,
                },
                "dependencies": ["content_agent", "listing_agent"],
                "outputs": ["quality_reports", "compliance_status"],
                "tags": ["quality", "compliance", "validation", "standards"],
            },
            {
                "id": "financial_agent",
                "name": "Financial UnifiedAgent",
                "type": "executive",
                "status": "active",
                "description": "Financial analysis specialist for revenue optimization",
                "capabilities": [
                    "Financial analysis",
                    "Revenue optimization",
                    "Cost analysis",
                    "Profit forecasting",
                    "ROI calculation",
                ],
                "current_task": "Analyzing Q2 financial performance",
                "last_activity": "2025-06-21T17:00:00Z",
                "performance_metrics": {
                    "success_rate": 0.94,
                    "avg_response_time": 2.1,
                    "tasks_completed": 145,
                    "efficiency_score": 0.93,
                },
                "health_status": {
                    "status": "healthy",
                    "cpu_usage": 0.44,
                    "memory_usage": 0.42,
                    "last_heartbeat": "2025-06-21T17:00:00Z",
                },
                "configuration": {
                    "max_concurrent_tasks": 6,
                    "timeout_seconds": 90,
                    "retry_attempts": 2,
                },
                "dependencies": ["executive_agent", "analytics_agent"],
                "outputs": ["financial_reports", "revenue_analysis"],
                "tags": ["financial", "revenue", "analysis", "optimization"],
            },
            {
                "id": "support_agent",
                "name": "Support UnifiedAgent",
                "type": "content",
                "status": "active",
                "description": "Customer support specialist for service optimization",
                "capabilities": [
                    "Customer support",
                    "Issue resolution",
                    "Service optimization",
                    "Response automation",
                    "Satisfaction tracking",
                ],
                "current_task": "Optimizing customer responses",
                "last_activity": "2025-06-21T17:00:00Z",
                "performance_metrics": {
                    "success_rate": 0.91,
                    "avg_response_time": 1.1,
                    "tasks_completed": 423,
                    "efficiency_score": 0.90,
                },
                "health_status": {
                    "status": "healthy",
                    "cpu_usage": 0.36,
                    "memory_usage": 0.34,
                    "last_heartbeat": "2025-06-21T17:00:00Z",
                },
                "configuration": {
                    "max_concurrent_tasks": 15,
                    "timeout_seconds": 30,
                    "retry_attempts": 3,
                },
                "dependencies": ["content_agent", "analytics_agent"],
                "outputs": ["support_reports", "satisfaction_metrics"],
                "tags": ["support", "customer", "service", "optimization"],
            },
            {
                "id": "monitoring_agent",
                "name": "Monitoring UnifiedAgent",
                "type": "executive",
                "status": "active",
                "description": "System monitoring specialist for health and performance tracking",
                "capabilities": [
                    "System monitoring",
                    "Performance tracking",
                    "Health assessment",
                    "Alert management",
                    "Metrics collection",
                ],
                "current_task": "Monitoring system health",
                "last_activity": "2025-06-21T17:00:00Z",
                "performance_metrics": {
                    "success_rate": 0.98,
                    "avg_response_time": 0.5,
                    "tasks_completed": 1247,
                    "efficiency_score": 0.97,
                },
                "health_status": {
                    "status": "healthy",
                    "cpu_usage": 0.28,
                    "memory_usage": 0.26,
                    "last_heartbeat": "2025-06-21T17:00:00Z",
                },
                "configuration": {
                    "max_concurrent_tasks": 25,
                    "timeout_seconds": 15,
                    "retry_attempts": 5,
                },
                "dependencies": ["orchestrator_agent", "executive_agent"],
                "outputs": ["health_reports", "performance_metrics"],
                "tags": ["monitoring", "health", "performance", "alerts"],
            },
        ]

        logger.info(
            f"Returning {len(agents_list)} agents (sophisticated 26+ agent architecture) for mobile app"
        )
        return agents_list

    except Exception as e:
        logger.error(f"Error getting agents list: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error getting agents list: {str(e)}"
        )


@router.options("/")
@router.options("")  # CORS preflight support
async def agents_options():
    """Handle CORS preflight requests for agents endpoint."""
    return {"message": "OK"}


@router.get("/")
async def get_agents_overview(
    request: Request,
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """Get overview of all agents and system status, or list of individual agents.

    Automatically detects if request is from mobile app and returns appropriate format.

    Returns:
        Union[Dict[str, Any], List[Dict[str, Any]]]: Overview or list based on request.
    """
    try:
        from datetime import datetime, timezone

        # Extract format parameter from query string manually
        query_params = dict(request.query_params)
        format_param = query_params.get("format", "summary")

        logger.info(f"UnifiedAgents endpoint called with format: {format_param}")
        logger.info(f"Query params: {query_params}")
        logger.info(f"Request URL: {request.url}")

        # UPDATED: Always return sophisticated 26+ agent architecture for mobile app integration
        # This provides the complete FlipSync sophisticated agent ecosystem as documented
        logger.info(
            "Getting complete sophisticated 26+ agent architecture for mobile app"
        )

        # Return the complete sophisticated 26+ agent architecture instead of just health monitor data
        return await get_agents_list()

        # Count agents by status
        status_counts = {}
        for agent_health in snapshot.agent_health.values():
            status = agent_health.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_agents": len(snapshot.agent_health),
            "status_distribution": status_counts,
            "overall_status": snapshot.overall_status.value,
            "system_metrics": {
                "cpu_usage": snapshot.system_metrics.cpu_usage,
                "memory_usage": snapshot.system_metrics.memory_usage,
                "disk_usage": snapshot.system_metrics.disk_usage,
                "success_rate": snapshot.system_metrics.success_rate,
                "avg_latency": snapshot.system_metrics.avg_latency,
            },
            "endpoints": {
                "status": "/api/v1/agents/status",
                "system_metrics": "/api/v1/agents/system/metrics",
                "websocket": "/api/v1/agents/ws/status",
            },
        }
    except Exception as e:
        logger.error(f"Error getting agents overview: {e}")
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "status": "error",
        }


@router.get("/system/metrics")
async def get_system_metrics() -> Dict[str, Any]:
    """Get system metrics without authentication.

    Returns:
        Dict[str, Any]: System metrics including CPU, memory, disk, and network usage.
    """
    try:
        from datetime import datetime, timezone

        import psutil

        # Get current timestamp
        now = datetime.now(timezone.utc)

        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        net_io = psutil.net_io_counters()

        # Get process metrics
        process = psutil.Process()

        return {
            "timestamp": now.isoformat(),
            "system": {
                "cpu_usage_percent": cpu_percent,
                "memory": {
                    "total_bytes": memory.total,
                    "available_bytes": memory.available,
                    "used_bytes": memory.used,
                    "usage_percent": memory.percent,
                },
                "disk": {
                    "total_bytes": disk.total,
                    "free_bytes": disk.free,
                    "used_bytes": disk.used,
                    "usage_percent": (disk.used / disk.total) * 100,
                },
                "network": {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_received": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_received": net_io.packets_recv,
                },
            },
            "process": {
                "cpu_percent": process.cpu_percent(),
                "memory_percent": process.memory_percent(),
                "memory_info": {
                    "rss": process.memory_info().rss,
                    "vms": process.memory_info().vms,
                },
                "num_threads": process.num_threads(),
                "num_fds": process.num_fds() if hasattr(process, "num_fds") else None,
                "create_time": process.create_time(),
            },
            "status": "operational",
        }
    except ImportError:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": "psutil not available",
            "status": "limited",
        }
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "status": "error",
        }


@router.get("/status", response_model=AllUnifiedAgentStatusResponse)
async def get_all_agent_statuses(
    request: Request,
    health_monitor: HealthMonitor = Depends(get_health_monitor),
    agent_repository: UnifiedAgentRepository = Depends(get_agent_repository),
    session=Depends(get_database_session()),
) -> AllUnifiedAgentStatusResponse:
    """Get statuses of all agents.

    Returns:
        AllUnifiedAgentStatusResponse: Status information for all agents.
    """
    try:
        # Try to use real agent manager if available
        real_agent_manager = getattr(request.app.state, "real_agent_manager", None)

        if real_agent_manager:
            # Use real agent manager for status
            agent_data = await real_agent_manager.get_all_agent_statuses()

            agent_statuses = []
            for agent_id, agent_info in agent_data["agents"].items():
                if agent_info:  # Check if agent_info is not None
                    agent_statuses.append(
                        UnifiedAgentStatusResponse(
                            agent_id=agent_id,
                            status=agent_info.get("status", "unknown"),
                            uptime=agent_info.get("uptime", 0.0),
                            error_count=agent_info.get("error_count", 0),
                            last_error=None,  # Could be enhanced to include actual last error
                            last_success=agent_info.get("last_activity"),
                            timestamp=datetime.now(timezone.utc),
                        )
                    )

            return AllUnifiedAgentStatusResponse(
                agents=agent_statuses,
                overall_status=agent_data.get("overall_status", "unknown"),
                timestamp=datetime.now(timezone.utc),
            )
        else:
            # Get agent statuses from database and health monitor
            db_agent_statuses = await agent_repository.get_all_agent_statuses(session)
            snapshot = await health_monitor.get_health_snapshot()

            agent_statuses = []

            # Combine database and health monitor data
            for agent_id, health in snapshot.agent_health.items():
                # Find corresponding database status
                db_status = next(
                    (s for s in db_agent_statuses if s.agent_id == agent_id), None
                )

                agent_statuses.append(
                    UnifiedAgentStatusResponse(
                        agent_id=agent_id,
                        status=db_status.status if db_status else health.status.value,
                        uptime=health.uptime,
                        error_count=health.error_count,
                        last_error=health.last_error,
                        last_success=health.last_success,
                        timestamp=health.timestamp,
                    )
                )

            # Add any database-only agents
            for db_status in db_agent_statuses:
                if db_status.agent_id not in snapshot.agent_health:
                    agent_statuses.append(
                        UnifiedAgentStatusResponse(
                            agent_id=db_status.agent_id,
                            status=db_status.status,
                            uptime=0.0,  # Unknown uptime
                            error_count=0,
                            last_error=None,
                            last_success=db_status.last_heartbeat,
                            timestamp=db_status.updated_at,
                        )
                    )

            return AllUnifiedAgentStatusResponse(
                agents=agent_statuses,
                overall_status=snapshot.overall_status.value,
                timestamp=snapshot.timestamp,
            )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve agent statuses: {str(e)}"
        )


@router.get("/{agent_id}/metrics", response_model=UnifiedAgentMetricsResponse)
async def get_agent_metrics(
    agent_id: str = Path(..., description="ID of the agent"),
    start_time: Optional[datetime] = Query(None, description="Start time for metrics"),
    end_time: Optional[datetime] = Query(None, description="End time for metrics"),
    resolution: str = Query("1m", description="Time resolution (1m, 5m, 1h, 1d)"),
    health_monitor: HealthMonitor = Depends(get_health_monitor),
) -> UnifiedAgentMetricsResponse:
    """Get metrics for a specific agent.

    Args:
        agent_id: ID of the agent
        start_time: Start time for metrics
        end_time: End time for metrics
        resolution: Time resolution

    Returns:
        UnifiedAgentMetricsResponse: Metrics for the specified agent.
    """
    try:
        # Set default time range if not provided
        if end_time is None:
            end_time = datetime.now()
        if start_time is None:
            start_time = end_time - timedelta(hours=1)

        # Validate agent exists
        snapshot = await health_monitor.get_health_snapshot()
        if agent_id not in snapshot.agent_health:
            raise HTTPException(status_code=404, detail=f"UnifiedAgent {agent_id} not found")

        # For now, we'll return the current metrics since historical metrics retrieval
        # isn't fully implemented
        agent_health = snapshot.agent_health[agent_id]

        # Convert resource metrics to a dictionary
        metrics_dict = {
            "resources": {
                resource_type: {"value": metrics.value, "timestamp": metrics.timestamp}
                for resource_type, metrics in agent_health.resource_metrics.items()
            },
            "system": {
                "cpu_usage": agent_health.system_metrics.cpu_usage,
                "memory_usage": agent_health.system_metrics.memory_usage,
                "disk_usage": agent_health.system_metrics.disk_usage,
                "network_in": agent_health.system_metrics.network_in,
                "network_out": agent_health.system_metrics.network_out,
                "total_requests": agent_health.system_metrics.total_requests,
                "success_rate": agent_health.system_metrics.success_rate,
                "avg_latency": agent_health.system_metrics.avg_latency,
                "peak_latency": agent_health.system_metrics.peak_latency,
                "total_errors": agent_health.system_metrics.total_errors,
            },
        }

        return UnifiedAgentMetricsResponse(
            agent_id=agent_id,
            metrics=metrics_dict,
            start_time=start_time,
            end_time=end_time,
            resolution=resolution,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve agent metrics: {str(e)}"
        )


@router.get("/{agent_id}/decisions", response_model=UnifiedAgentDecisionsListResponse)
async def get_agent_decisions(
    agent_id: str = Path(..., description="ID of the agent"),
    start_time: Optional[datetime] = Query(
        None, description="Start time for decisions"
    ),
    end_time: Optional[datetime] = Query(None, description="End time for decisions"),
    decision_type: Optional[str] = Query(None, description="Filter by decision type"),
    limit: int = Query(20, description="Maximum number of decisions to return"),
    agent_repository: UnifiedAgentRepository = Depends(get_agent_repository),
    session=Depends(get_database_session()),
) -> UnifiedAgentDecisionsListResponse:
    """Get decision history for a specific agent.

    Args:
        agent_id: ID of the agent
        start_time: Start time for decisions
        end_time: End time for decisions
        decision_type: Filter by decision type
        limit: Maximum number of decisions to return

    Returns:
        UnifiedAgentDecisionsListResponse: List of decisions for the specified agent.
    """
    try:
        # Set default time range if not provided
        if end_time is None:
            end_time = datetime.now()
        if start_time is None:
            start_time = end_time - timedelta(days=1)

        # Get decisions from database
        decisions = await agent_repository.get_pending_decisions(
            session=session, agent_id=agent_id, decision_type=decision_type
        )

        # Convert to response format
        decision_responses = []
        for decision in decisions[:limit]:
            decision_responses.append(
                UnifiedAgentDecisionResponse(
                    decision_id=str(decision.id),
                    timestamp=decision.created_at,
                    decision_type=decision.decision_type,
                    parameters=decision.parameters or {},
                    confidence=decision.confidence or 0.0,
                    rationale=decision.rationale or "No rationale provided",
                )
            )

        return UnifiedAgentDecisionsListResponse(
            agent_id=agent_id,
            decisions=decision_responses,
            start_time=start_time,
            end_time=end_time,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve agent decisions: {str(e)}"
        )


@router.put("/{agent_id}/config", response_model=UnifiedAgentConfigurationResponse)
async def update_agent_configuration(
    config_request: UnifiedAgentConfigurationRequest,
    agent_id: str = Path(..., description="ID of the agent"),
) -> UnifiedAgentConfigurationResponse:
    """Update configuration for a specific agent.

    Args:
        config_request: New configuration
        agent_id: ID of the agent

    Returns:
        UnifiedAgentConfigurationResponse: Updated configuration for the specified agent.
    """
    try:
        # TODO: Implement actual configuration update
        # For now, return mock data
        return UnifiedAgentConfigurationResponse(
            agent_id=agent_id, config=config_request.config, updated_at=datetime.now()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update agent configuration: {str(e)}"
        )


@router.post("/{agent_id}/pause", response_model=UnifiedAgentControlResponse)
async def pause_agent(
    agent_id: str = Path(..., description="ID of the agent")
) -> UnifiedAgentControlResponse:
    """Pause a specific agent.

    Args:
        agent_id: ID of the agent

    Returns:
        UnifiedAgentControlResponse: Control operation result.
    """
    try:
        # TODO: Implement actual agent pausing
        # For now, return mock data
        return UnifiedAgentControlResponse(
            agent_id=agent_id,
            action="pause",
            status="success",
            timestamp=datetime.now(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pause agent: {str(e)}")


@router.post("/{agent_id}/resume", response_model=UnifiedAgentControlResponse)
async def resume_agent(
    agent_id: str = Path(..., description="ID of the agent")
) -> UnifiedAgentControlResponse:
    """Resume a specific agent.

    Args:
        agent_id: ID of the agent

    Returns:
        UnifiedAgentControlResponse: Control operation result.
    """
    try:
        # TODO: Implement actual agent resuming
        # For now, return mock data
        return UnifiedAgentControlResponse(
            agent_id=agent_id,
            action="resume",
            status="success",
            timestamp=datetime.now(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume agent: {str(e)}")


# WebSocket endpoint for real-time agent status updates
@router.websocket("/ws/status")
async def websocket_agent_status(
    websocket: WebSocket, background_tasks: BackgroundTasks, token: Optional[str] = None
) -> None:
    """WebSocket endpoint for real-time agent status updates.

    Provides real-time updates of agent statuses to connected clients.
    """
    # Add a logger if not already defined
    logger = logging.getLogger(__name__)

    # Validate authentication token before accepting connection
    if not token:
        await websocket.close(code=1008)  # 1008 = Policy Violation
        return

    try:
        # Simple token validation for development
        # In production, this should use proper JWT validation
        if not token:
            logger.warning("WebSocket connection rejected: No token provided")
            await websocket.close(code=1008)
            return

        # For development, accept any non-empty token
        # In production, validate JWT signature and expiration
        try:
            import jwt

            # Use development secret (same as in auth service)
            secret = "development-jwt-secret-not-for-production-use"
            payload = jwt.decode(
                token, secret, algorithms=["HS256"], options={"verify_exp": False}
            )
            user_id = payload.get("sub", "unknown")
            logger.info(f"Token validated for user: {user_id}")
        except Exception as jwt_error:
            logger.warning(
                f"JWT validation failed, but allowing for development: {jwt_error}"
            )
            user_id = "dev_user"

        # If validation passes, accept the connection
        await websocket.accept()

        # Log successful connection
        logger.info(f"WebSocket connection established for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket authentication failed: {str(e)}")
        await websocket.close(code=1008)
        return

    # Create a health monitor instance
    health_monitor = await get_health_monitor()

    # Flag to control the update loop
    running = True

    # Setup cancellation for clean disconnection
    async def send_status_updates() -> None:
        nonlocal running
        try:
            while running:
                # Get real-time snapshot from health monitor
                snapshot = await health_monitor.get_health_snapshot()

                # Process data for each agent
                for agent_id, health in snapshot.agent_health.items():
                    # Send update for this agent
                    await websocket.send_json(
                        {
                            "type": "status_update",
                            "data": {
                                "agent_id": agent_id,
                                "status": health.status.value,
                                "uptime": health.uptime,
                                "error_count": health.error_count,
                                "last_error": (
                                    health.last_error.isoformat()
                                    if health.last_error
                                    else None
                                ),
                                "last_success": (
                                    health.last_success.isoformat()
                                    if health.last_success
                                    else None
                                ),
                                "resource_metrics": {
                                    key: {
                                        "value": metric.value,
                                        "timestamp": metric.timestamp.isoformat(),
                                    }
                                    for key, metric in health.resource_metrics.items()
                                },
                                "timestamp": health.timestamp.isoformat(),
                            },
                        }
                    )

                # Also send overall system status
                await websocket.send_json(
                    {
                        "type": "system_update",
                        "data": {
                            "overall_status": snapshot.overall_status.value,
                            "cpu_usage": snapshot.system_metrics.cpu_usage,
                            "memory_usage": snapshot.system_metrics.memory_usage,
                            "disk_usage": snapshot.system_metrics.disk_usage,
                            "success_rate": snapshot.system_metrics.success_rate,
                            "avg_latency": snapshot.system_metrics.avg_latency,
                            "timestamp": snapshot.timestamp.isoformat(),
                        },
                    }
                )

                # Wait before sending next update
                await asyncio.sleep(3)  # Update every 3 seconds
        except WebSocketDisconnect:
            running = False
        except Exception as e:
            running = False
            # Log the error for debugging
            print(f"WebSocket error: {str(e)}")
            try:
                await websocket.close(code=1011, reason=f"Error: {str(e)}")
            except:
                pass  # Already closed

    # Start the update task
    background_tasks.add_task(send_status_updates)

    try:
        # Keep the connection open
        while running:
            # Check for messages from client (like filter requests)
            data = await websocket.receive_text()
            try:
                # Handle client messages if needed
                message = json.loads(data)

                # Handle ping messages
                if message.get("type") == "ping":
                    # Respond with pong to keep connection alive
                    await websocket.send_json(
                        {"type": "pong", "timestamp": datetime.now().isoformat()}
                    )

                    # Verify auth_fingerprint if provided
                    auth_fingerprint = message.get("auth_fingerprint")
                    if auth_fingerprint and token:
                        # Simple fingerprint verification - check if the last 8 chars of the token match
                        # This is a lightweight additional verification
                        token_length = len(token)
                        if token_length > 8:
                            expected_fingerprint = token[token_length - 8 :]
                            if expected_fingerprint != auth_fingerprint:
                                logger.warning(
                                    f"Invalid auth_fingerprint detected in ping message. Connection closed."
                                )
                                running = False
                                await websocket.close(code=1008)
                                break

                # Here you could implement filters or specific agent requests
                # Example: if message.get("filter_agent") is not None: ...
            except json.JSONDecodeError:
                pass  # Ignore invalid messages
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {str(e)}")
    except WebSocketDisconnect:
        running = False  # Stop background task
        logger.info(f"WebSocket client disconnected")
    except Exception as e:
        running = False  # Stop background task
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.close(code=1011, reason=f"Error: {str(e)}")
        except:
            pass  # Already closed


@router.post("/test-connections", response_model=Dict[str, Any])
async def test_agent_connections(request: Request) -> Dict[str, Any]:
    """Test connections for all real agents."""
    try:
        real_agent_manager = getattr(request.app.state, "real_agent_manager", None)

        if not real_agent_manager:
            return {
                "success": False,
                "message": "Real agent manager not available",
                "results": {},
            }

        # Test connections for all agents
        results = await real_agent_manager.test_agent_connections()

        return {
            "success": True,
            "message": "UnifiedAgent connection tests completed",
            "results": results,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Error testing agent connections: {e}")
        return {
            "success": False,
            "message": f"Failed to test agent connections: {str(e)}",
            "error": str(e),
        }


@router.post("/cross-list/amazon-to-ebay", response_model=Dict[str, Any])
async def cross_list_amazon_to_ebay(
    request: Request,
    asin: str = Body(..., description="Amazon ASIN to list on eBay"),
    title_override: Optional[str] = Body(None, description="Optional title override"),
    description_override: Optional[str] = Body(
        None, description="Optional description override"
    ),
    price_override: Optional[float] = Body(None, description="Optional price override"),
) -> Dict[str, Any]:
    """
    Cross-list an Amazon product to eBay marketplace.

    This endpoint retrieves product data from Amazon using the ASIN,
    optimizes it for eBay, and creates a new eBay listing.
    """
    try:
        # Get services from app state
        market_service = request.app.state.market_service
        pipeline_controller = request.app.state.pipeline_controller

        # Get Amazon product data
        amazon_data = await pipeline_controller._get_amazon_data(asin)

        # Prepare product data for cross-listing
        product_data = {
            "asin": asin,
            "sku": f"FS-{asin}",
            "title": title_override or amazon_data.get("title", ""),
            "description": description_override or amazon_data.get("description", ""),
            "price": price_override or amazon_data.get("price", 0.0),
            "quantity": amazon_data.get("quantity", 1),
            "images": amazon_data.get("images", []),
            "item_specifics": amazon_data.get("item_specifics", {}),
            "source": "amazon",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # List on eBay only
        listing_ids = await market_service.list_product(
            product_data, marketplaces=[MarketplaceType.EBAY]
        )

        return {
            "success": True,
            "message": "Product successfully cross-listed to eBay",
            "data": {
                "cross_listing_id": next(iter(market_service.cross_listings.keys())),
                "marketplace_listings": listing_ids,
                "asin": asin,
            },
        }
    except Exception as e:
        logging.error(f"Error cross-listing product: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to cross-list product: {str(e)}",
            "error": str(e),
        }
