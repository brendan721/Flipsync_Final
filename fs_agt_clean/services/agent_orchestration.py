"""
UnifiedAgent Orchestration Service for FlipSync.

This service provides multi-agent coordination capabilities including:
- UnifiedAgent workflow management with step-by-step execution
- Decision consensus mechanisms
- Task delegation and coordination
- UnifiedAgent handoff management
- Workflow state persistence and recovery
- Advanced error handling and retry strategies
- Workflow template system for reusable patterns
- Comprehensive workflow monitoring and metrics
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable, Union
from uuid import UUID, uuid4

from fs_agt_clean.agents.base_conversational_agent import (
    UnifiedAgentResponse,
    BaseConversationalUnifiedAgent,
)
from fs_agt_clean.agents.content.content_agent import ContentUnifiedAgent
from fs_agt_clean.agents.executive.executive_agent import ExecutiveUnifiedAgent
from fs_agt_clean.agents.logistics.logistics_agent import LogisticsUnifiedAgent
from fs_agt_clean.agents.market.market_agent import MarketUnifiedAgent
from fs_agt_clean.core.websocket.manager import websocket_manager
from fs_agt_clean.database.repositories.ai_analysis_repository import (
    UnifiedAgentCoordinationRepository,
)
from fs_agt_clean.core.state_management.persistence_manager import PersistenceManager

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Status of agent workflows."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    RETRYING = "retrying"


class WorkflowStepStatus(Enum):
    """Status of individual workflow steps."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class UnifiedAgentHandoffStatus(Enum):
    """Status of agent handoffs."""

    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class RetryStrategy(Enum):
    """Retry strategies for failed workflow steps."""

    NONE = "none"
    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow."""

    step_id: str
    name: str
    agent_type: str
    method_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    max_retries: int = 3
    timeout_seconds: int = 300
    status: WorkflowStepStatus = WorkflowStepStatus.PENDING
    result: Optional[Any] = None
    error_message: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    retry_count: int = 0


@dataclass
class WorkflowTemplate:
    """Template for creating reusable workflows."""

    template_id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    default_parameters: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    version: str = "1.0"


@dataclass
class WorkflowMetrics:
    """Metrics for workflow execution."""

    total_steps: int = 0
    completed_steps: int = 0
    failed_steps: int = 0
    skipped_steps: int = 0
    total_execution_time: float = 0.0
    average_step_time: float = 0.0
    retry_count: int = 0
    error_rate: float = 0.0


class UnifiedAgentWorkflow:
    """Enhanced multi-agent workflow with step-by-step execution."""

    def __init__(
        self,
        workflow_id: str,
        workflow_type: str,
        participating_agents: List[str],
        context: Dict[str, Any],
        steps: Optional[List[WorkflowStep]] = None,
        template_id: Optional[str] = None,
    ):
        self.workflow_id = workflow_id
        self.workflow_type = workflow_type
        self.participating_agents = participating_agents
        self.context = context
        self.steps = steps or []
        self.template_id = template_id
        self.status = WorkflowStatus.PENDING
        self.results = {}
        self.start_time = None
        self.end_time = None
        self.error_message = None
        self.current_step_index = 0
        self.metrics = WorkflowMetrics()
        self.checkpoint_data = {}
        self.last_checkpoint_time = None

    def get_current_step(self) -> Optional[WorkflowStep]:
        """Get the current step being executed."""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    def get_completed_steps(self) -> List[WorkflowStep]:
        """Get all completed steps."""
        return [
            step for step in self.steps if step.status == WorkflowStepStatus.COMPLETED
        ]

    def get_failed_steps(self) -> List[WorkflowStep]:
        """Get all failed steps."""
        return [step for step in self.steps if step.status == WorkflowStepStatus.FAILED]

    def get_progress(self) -> float:
        """Calculate workflow progress as a percentage."""
        if not self.steps:
            return 0.0
        completed = len(self.get_completed_steps())
        return (completed / len(self.steps)) * 100.0

    def create_checkpoint(self) -> Dict[str, Any]:
        """Create a checkpoint of the current workflow state."""
        self.checkpoint_data = {
            "workflow_id": self.workflow_id,
            "current_step_index": self.current_step_index,
            "context": self.context.copy(),
            "results": self.results.copy(),
            "metrics": {
                "total_steps": self.metrics.total_steps,
                "completed_steps": self.metrics.completed_steps,
                "failed_steps": self.metrics.failed_steps,
                "retry_count": self.metrics.retry_count,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.last_checkpoint_time = datetime.now(timezone.utc)
        return self.checkpoint_data

    def restore_from_checkpoint(self, checkpoint_data: Dict[str, Any]) -> bool:
        """Restore workflow state from a checkpoint."""
        try:
            self.current_step_index = checkpoint_data.get("current_step_index", 0)
            self.context.update(checkpoint_data.get("context", {}))
            self.results.update(checkpoint_data.get("results", {}))

            metrics_data = checkpoint_data.get("metrics", {})
            self.metrics.total_steps = metrics_data.get("total_steps", 0)
            self.metrics.completed_steps = metrics_data.get("completed_steps", 0)
            self.metrics.failed_steps = metrics_data.get("failed_steps", 0)
            self.metrics.retry_count = metrics_data.get("retry_count", 0)

            return True
        except Exception as e:
            logger.error(f"Error restoring workflow from checkpoint: {e}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "workflow_type": self.workflow_type,
            "participating_agents": self.participating_agents,
            "status": self.status.value,
            "context": self.context,
            "results": self.results,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "error_message": self.error_message,
            "current_step_index": self.current_step_index,
            "progress": self.get_progress(),
            "metrics": {
                "total_steps": self.metrics.total_steps,
                "completed_steps": self.metrics.completed_steps,
                "failed_steps": self.metrics.failed_steps,
                "skipped_steps": self.metrics.skipped_steps,
                "retry_count": self.metrics.retry_count,
                "error_rate": self.metrics.error_rate,
            },
            "steps": [
                {
                    "step_id": step.step_id,
                    "name": step.name,
                    "status": step.status.value,
                    "agent_type": step.agent_type,
                    "retry_count": step.retry_count,
                    "error_message": step.error_message,
                }
                for step in self.steps
            ],
        }


class UnifiedAgentHandoff:
    """Represents an agent handoff operation."""

    def __init__(
        self,
        handoff_id: str,
        from_agent: str,
        to_agent: str,
        context: Dict[str, Any],
        conversation_id: Optional[str] = None,
    ):
        self.handoff_id = handoff_id
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.context = context
        self.conversation_id = conversation_id
        self.status = UnifiedAgentHandoffStatus.INITIATED
        self.start_time = datetime.now(timezone.utc)
        self.completion_time = None
        self.error_message = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert handoff to dictionary."""
        return {
            "handoff_id": self.handoff_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "status": self.status.value,
            "context": self.context,
            "conversation_id": self.conversation_id,
            "start_time": self.start_time.isoformat(),
            "completion_time": (
                self.completion_time.isoformat() if self.completion_time else None
            ),
            "error_message": self.error_message,
        }


class UnifiedAgentOrchestrationService:
    """Enhanced service for orchestrating multi-agent workflows and coordination."""

    def __init__(self):
        """Initialize the orchestration service."""
        self.active_workflows: Dict[str, UnifiedAgentWorkflow] = {}
        self.active_handoffs: Dict[str, UnifiedAgentHandoff] = {}
        self.agent_registry: Dict[str, BaseConversationalUnifiedAgent] = {}
        self.workflow_templates: Dict[str, WorkflowTemplate] = {}
        self._coordination_repository = None
        self._persistence_manager = None

        # Initialize default agents
        self._initialize_agents()

        # Initialize workflow templates
        self._initialize_workflow_templates()

        logger.info("Enhanced UnifiedAgent Orchestration Service initialized")

    @property
    def coordination_repository(self):
        """Lazy initialization of coordination repository."""
        if self._coordination_repository is None:
            self._coordination_repository = UnifiedAgentCoordinationRepository()
        return self._coordination_repository

    @property
    def persistence_manager(self):
        """Lazy initialization of persistence manager."""
        if self._persistence_manager is None:
            self._persistence_manager = PersistenceManager()
        return self._persistence_manager

    def _initialize_agents(self):
        """Initialize default agent instances."""
        try:
            from fs_agt_clean.agents.logistics.logistics_agent import LogisticsUnifiedAgent
            from fs_agt_clean.agents.market.market_agent import MarketUnifiedAgent

            self.agent_registry = {
                "executive": ExecutiveUnifiedAgent(),
                "content": ContentUnifiedAgent(),
                "market": MarketUnifiedAgent(),  # ✅ FIXED: Market agent now properly registered
                "logistics": LogisticsUnifiedAgent(),  # ✅ FIXED: Logistics agent now properly registered
            }

            # Add specialized agents that are available
            try:
                from fs_agt_clean.agents.market.specialized.listing_agent import (
                    ListingUnifiedAgent,
                )

                self.agent_registry["listing"] = ListingUnifiedAgent()
                logger.info("Added ListingUnifiedAgent to registry")
            except Exception as e:
                logger.warning(f"Could not initialize ListingUnifiedAgent: {e}")

            try:
                from fs_agt_clean.agents.market.specialized.advertising_agent import (
                    AdvertisingUnifiedAgent,
                )

                self.agent_registry["advertising"] = AdvertisingUnifiedAgent()
                logger.info("Added AdvertisingUnifiedAgent to registry")
            except Exception as e:
                logger.warning(f"Could not initialize AdvertisingUnifiedAgent: {e}")

            # Add automation agents
            try:
                from fs_agt_clean.agents.automation.auto_pricing_agent import (
                    AutoPricingUnifiedAgent,
                )

                self.agent_registry["auto_pricing"] = AutoPricingUnifiedAgent()
                logger.info("Added AutoPricingUnifiedAgent to registry")
            except Exception as e:
                logger.warning(f"Could not initialize AutoPricingUnifiedAgent: {e}")

            try:
                from fs_agt_clean.agents.automation.auto_listing_agent import (
                    AutoListingUnifiedAgent,
                )

                self.agent_registry["auto_listing"] = AutoListingUnifiedAgent()
                logger.info("Added AutoListingUnifiedAgent to registry")
            except Exception as e:
                logger.warning(f"Could not initialize AutoListingUnifiedAgent: {e}")

            try:
                from fs_agt_clean.agents.automation.auto_inventory_agent import (
                    AutoInventoryUnifiedAgent,
                )

                self.agent_registry["auto_inventory"] = AutoInventoryUnifiedAgent()
                logger.info("Added AutoInventoryUnifiedAgent to registry")
            except Exception as e:
                logger.warning(f"Could not initialize AutoInventoryUnifiedAgent: {e}")

            # Add enhanced specialized analytics agents
            try:
                from fs_agt_clean.agents.market.specialized.enhanced_competitor_analyzer import (
                    EnhancedCompetitorAnalyzer,
                )

                self.agent_registry["competitor_analyzer"] = (
                    EnhancedCompetitorAnalyzer()
                )
                logger.info("Added EnhancedCompetitorAnalyzer to registry")
            except Exception as e:
                logger.warning(f"Could not initialize EnhancedCompetitorAnalyzer: {e}")

            try:
                from fs_agt_clean.agents.market.specialized.enhanced_trend_detector import (
                    EnhancedTrendDetector,
                )

                self.agent_registry["trend_detector"] = EnhancedTrendDetector()
                logger.info("Added EnhancedTrendDetector to registry")
            except Exception as e:
                logger.warning(f"Could not initialize EnhancedTrendDetector: {e}")

            try:
                from fs_agt_clean.agents.market.specialized.enhanced_market_analyzer import (
                    EnhancedMarketAnalyzer,
                )

                self.agent_registry["market_analyzer"] = EnhancedMarketAnalyzer()
                logger.info("Added EnhancedMarketAnalyzer to registry")
            except Exception as e:
                logger.warning(f"Could not initialize EnhancedMarketAnalyzer: {e}")

            logger.info(
                f"Initialized {len(self.agent_registry)} agents: {list(self.agent_registry.keys())}"
            )
        except Exception as e:
            logger.error(f"Error initializing agents: {e}")
            # Fallback to basic agents if specialized ones fail
            self.agent_registry = {
                "executive": ExecutiveUnifiedAgent(),
                "content": ContentUnifiedAgent(),
            }
            logger.warning(
                f"Fallback initialization with {len(self.agent_registry)} agents"
            )

    def _initialize_workflow_templates(self):
        """Initialize predefined workflow templates."""
        try:
            # Product Analysis Workflow Template
            product_analysis_steps = [
                WorkflowStep(
                    step_id="content_analysis",
                    name="Content Analysis",
                    agent_type="content",
                    method_name="analyze_product_content",
                    dependencies=[],
                    max_retries=2,
                    timeout_seconds=120,
                ),
                WorkflowStep(
                    step_id="shipping_calculation",
                    name="Shipping Calculation",
                    agent_type="logistics",
                    method_name="calculate_shipping_options",
                    dependencies=["content_analysis"],
                    max_retries=2,
                    timeout_seconds=60,
                ),
                WorkflowStep(
                    step_id="executive_recommendations",
                    name="Executive Recommendations",
                    agent_type="executive",
                    method_name="generate_recommendations",
                    dependencies=["content_analysis", "shipping_calculation"],
                    max_retries=1,
                    timeout_seconds=180,
                ),
            ]

            self.workflow_templates["product_analysis"] = WorkflowTemplate(
                template_id="product_analysis",
                name="Product Analysis Workflow",
                description="Comprehensive product analysis with content, logistics, and executive insights",
                steps=product_analysis_steps,
                tags=["analysis", "product", "multi-agent"],
            )

            # Listing Optimization Workflow Template
            listing_optimization_steps = [
                WorkflowStep(
                    step_id="content_optimization",
                    name="Content Optimization",
                    agent_type="content",
                    method_name="optimize_listing_content",
                    dependencies=[],
                    max_retries=2,
                    timeout_seconds=120,
                ),
                WorkflowStep(
                    step_id="market_analysis",
                    name="Market Analysis",
                    agent_type="market",
                    method_name="analyze_competition",
                    dependencies=[],
                    max_retries=2,
                    timeout_seconds=180,
                ),
                WorkflowStep(
                    step_id="optimization_plan",
                    name="Optimization Plan",
                    agent_type="executive",
                    method_name="generate_optimization_plan",
                    dependencies=["content_optimization", "market_analysis"],
                    max_retries=1,
                    timeout_seconds=120,
                ),
            ]

            self.workflow_templates["listing_optimization"] = WorkflowTemplate(
                template_id="listing_optimization",
                name="Listing Optimization Workflow",
                description="Multi-agent listing optimization with content and market analysis",
                steps=listing_optimization_steps,
                tags=["optimization", "listing", "market"],
            )

            # Market Research Workflow Template
            market_research_steps = [
                WorkflowStep(
                    step_id="market_trends",
                    name="Market Trends Analysis",
                    agent_type="market",
                    method_name="analyze_market_trends",
                    dependencies=[],
                    max_retries=2,
                    timeout_seconds=180,
                ),
                WorkflowStep(
                    step_id="content_trends",
                    name="Content Trends Analysis",
                    agent_type="content",
                    method_name="analyze_content_trends",
                    dependencies=[],
                    max_retries=2,
                    timeout_seconds=120,
                ),
                WorkflowStep(
                    step_id="research_synthesis",
                    name="Research Synthesis",
                    agent_type="executive",
                    method_name="synthesize_research_insights",
                    dependencies=["market_trends", "content_trends"],
                    max_retries=1,
                    timeout_seconds=120,
                ),
            ]

            self.workflow_templates["market_research"] = WorkflowTemplate(
                template_id="market_research",
                name="Market Research Workflow",
                description="Comprehensive market research with trend analysis and synthesis",
                steps=market_research_steps,
                tags=["research", "market", "trends"],
            )

            # AI-Powered Product Creation Workflow Template
            ai_product_creation_steps = [
                WorkflowStep(
                    step_id="image_analysis",
                    name="AI Image Analysis & Product Extraction",
                    agent_type="market",
                    method_name="analyze_image",
                    dependencies=[],
                    max_retries=2,
                    timeout_seconds=120,
                ),
                WorkflowStep(
                    step_id="strategic_decision",
                    name="Strategic Decision Making",
                    agent_type="executive",
                    method_name="generate_recommendations",
                    dependencies=["image_analysis"],
                    max_retries=2,
                    timeout_seconds=90,
                ),
                WorkflowStep(
                    step_id="content_generation",
                    name="AI Content Generation & Optimization",
                    agent_type="content",
                    method_name="generate_content",
                    dependencies=["image_analysis", "strategic_decision"],
                    max_retries=2,
                    timeout_seconds=150,
                ),
                WorkflowStep(
                    step_id="logistics_creation",
                    name="Logistics Planning & Listing Creation",
                    agent_type="logistics",
                    method_name="create_fulfillment_plan",
                    dependencies=[
                        "image_analysis",
                        "strategic_decision",
                        "content_generation",
                    ],
                    max_retries=2,
                    timeout_seconds=120,
                ),
            ]

            self.workflow_templates["ai_product_creation"] = WorkflowTemplate(
                template_id="ai_product_creation",
                name="AI-Powered Product Creation Workflow",
                description="Create complete product listings from images using sophisticated multi-agent AI coordination",
                steps=ai_product_creation_steps,
                tags=[
                    "ai",
                    "product_creation",
                    "image_analysis",
                    "marketplace",
                    "automation",
                ],
            )

            # Sales Optimization Workflow Template
            sales_optimization_steps = [
                WorkflowStep(
                    step_id="competitive_analysis",
                    name="Competitive Analysis & Market Monitoring",
                    agent_type="enhanced_competitor_analyzer",
                    method_name="analyze_competitive_landscape",
                    dependencies=[],
                    max_retries=2,
                    timeout_seconds=180,
                ),
                WorkflowStep(
                    step_id="pricing_strategy",
                    name="Pricing Strategy & ROI Optimization",
                    agent_type="executive",
                    method_name="develop_pricing_strategy",
                    dependencies=["competitive_analysis"],
                    max_retries=2,
                    timeout_seconds=120,
                ),
                WorkflowStep(
                    step_id="listing_updates",
                    name="Listing Updates & Content Optimization",
                    agent_type="content",
                    method_name="optimize_listing_content",
                    dependencies=["competitive_analysis", "pricing_strategy"],
                    max_retries=2,
                    timeout_seconds=150,
                ),
                WorkflowStep(
                    step_id="performance_analytics",
                    name="Performance Tracking & Analytics",
                    agent_type="logistics",
                    method_name="track_performance_metrics",
                    dependencies=[
                        "competitive_analysis",
                        "pricing_strategy",
                        "listing_updates",
                    ],
                    max_retries=2,
                    timeout_seconds=120,
                ),
            ]

            self.workflow_templates["sales_optimization"] = WorkflowTemplate(
                template_id="sales_optimization",
                name="Sales Optimization Workflow",
                description="Comprehensive sales optimization with competitive analysis, pricing strategy, listing updates, and ROI optimization",
                steps=sales_optimization_steps,
                tags=[
                    "sales",
                    "optimization",
                    "competitive_analysis",
                    "pricing",
                    "roi",
                    "marketplace",
                ],
            )

            # Market Synchronization Workflow Template
            market_synchronization_steps = [
                WorkflowStep(
                    step_id="inventory_sync",
                    name="Cross-Platform Inventory Sync",
                    agent_type="logistics",
                    method_name="synchronize_inventory",
                    parameters={
                        "sync_scope": "full_sync",
                        "marketplaces": ["ebay", "amazon"],
                    },
                    dependencies=[],
                    max_retries=2,
                    timeout_seconds=180,
                ),
                WorkflowStep(
                    step_id="listing_consistency",
                    name="Listing Consistency Management",
                    agent_type="market",
                    method_name="ensure_listing_consistency",
                    parameters={
                        "consistency_checks": [
                            "title",
                            "description",
                            "pricing",
                            "images",
                        ],
                    },
                    dependencies=["inventory_sync"],
                    max_retries=2,
                    timeout_seconds=120,
                ),
                WorkflowStep(
                    step_id="conflict_resolution",
                    name="Conflict Resolution & Data Validation",
                    agent_type="executive",
                    method_name="resolve_marketplace_conflicts",
                    parameters={
                        "resolution_strategy": "marketplace_priority",
                        "validation_level": "comprehensive",
                    },
                    dependencies=["inventory_sync", "listing_consistency"],
                    max_retries=1,
                    timeout_seconds=120,
                ),
                WorkflowStep(
                    step_id="sync_monitoring",
                    name="Sync Monitoring & Performance Analytics",
                    agent_type="logistics",
                    method_name="monitor_sync_performance",
                    parameters={
                        "monitoring_scope": "comprehensive",
                        "analytics_level": "detailed",
                    },
                    dependencies=["conflict_resolution"],
                    max_retries=1,
                    timeout_seconds=60,
                ),
            ]

            self.workflow_templates["market_synchronization"] = WorkflowTemplate(
                template_id="market_synchronization",
                name="Market Synchronization Workflow",
                description="Cross-platform inventory sync, listing consistency, conflict resolution, and sync monitoring",
                steps=market_synchronization_steps,
                tags=[
                    "synchronization",
                    "marketplace",
                    "inventory",
                    "conflict_resolution",
                    "cross_platform",
                    "automation",
                ],
            )

            # Conversational Interface Workflow Template
            conversational_interface_steps = [
                WorkflowStep(
                    step_id="intent_recognition",
                    name="Intent Recognition & Context Analysis",
                    agent_type="executive",
                    method_name="recognize_intent_and_context",
                    parameters={
                        "analysis_depth": "comprehensive",
                        "context_extraction": "detailed",
                    },
                    dependencies=[],
                    max_retries=2,
                    timeout_seconds=60,
                ),
                WorkflowStep(
                    step_id="agent_routing",
                    name="Intelligent UnifiedAgent Routing & Selection",
                    agent_type="executive",
                    method_name="route_and_select_agents",
                    parameters={
                        "routing_strategy": "intent_based",
                        "selection_criteria": "expertise_match",
                    },
                    dependencies=["intent_recognition"],
                    max_retries=1,
                    timeout_seconds=30,
                ),
                WorkflowStep(
                    step_id="response_generation",
                    name="Multi-UnifiedAgent Response Generation",
                    agent_type="multi",
                    method_name="generate_conversational_response",
                    parameters={
                        "coordination_mode": "parallel",
                        "response_quality": "high",
                    },
                    dependencies=["agent_routing"],
                    max_retries=2,
                    timeout_seconds=120,
                ),
                WorkflowStep(
                    step_id="response_aggregation",
                    name="Response Aggregation & Personalization",
                    agent_type="content",
                    method_name="aggregate_and_personalize_response",
                    parameters={
                        "personalization_level": "adaptive",
                        "coherence_optimization": "enabled",
                    },
                    dependencies=["response_generation"],
                    max_retries=1,
                    timeout_seconds=60,
                ),
            ]

            self.workflow_templates["conversational_interface"] = WorkflowTemplate(
                template_id="conversational_interface",
                name="Conversational Interface Workflow",
                description="Intent recognition, agent routing, response generation, and personalized aggregation",
                steps=conversational_interface_steps,
                tags=[
                    "conversational",
                    "interface",
                    "intent_recognition",
                    "agent_routing",
                    "personalization",
                    "automation",
                ],
            )

            logger.info(
                f"Initialized {len(self.workflow_templates)} workflow templates"
            )

        except Exception as e:
            logger.error(f"Error initializing workflow templates: {e}")
            self.workflow_templates = {}

    async def coordinate_agents(
        self,
        workflow_type: str,
        participating_agents: List[str],
        context: Dict[str, Any],
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Coordinate multiple agents in a workflow."""
        workflow_id = str(uuid4())
        start_time = time.time()

        try:
            # Create workflow
            workflow = UnifiedAgentWorkflow(
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                participating_agents=participating_agents,
                context=context,
            )
            workflow.start_time = datetime.now(timezone.utc)
            workflow.status = WorkflowStatus.IN_PROGRESS

            self.active_workflows[workflow_id] = workflow

            # Notify via WebSocket
            await self._notify_workflow_status(workflow, user_id, conversation_id)

            # Execute workflow based on type
            if workflow_type == "product_analysis":
                results = await self._execute_product_analysis_workflow(workflow)
            elif workflow_type == "listing_optimization":
                results = await self._execute_listing_optimization_workflow(workflow)
            elif workflow_type == "decision_consensus":
                results = await self._execute_decision_consensus_workflow(workflow)
            elif workflow_type == "pricing_strategy":
                results = await self._execute_pricing_strategy_workflow(workflow)
            elif workflow_type == "market_research":
                results = await self._execute_market_research_workflow(workflow)
            else:
                raise ValueError(f"Unknown workflow type: {workflow_type}")

            # Complete workflow
            workflow.status = WorkflowStatus.COMPLETED
            workflow.results = results
            workflow.end_time = datetime.now(timezone.utc)

            processing_time = int((time.time() - start_time) * 1000)

            # Log coordination activity
            await self.coordination_repository.log_coordination_activity(
                participating_agents=participating_agents,
                coordination_type=workflow_type,
                status="completed",
                result_data=results,
                processing_time_ms=processing_time,
                workflow_id=UUID(workflow_id),
            )

            # Final notification
            await self._notify_workflow_status(workflow, user_id, conversation_id)

            # Send final response to WebSocket client
            await self._send_workflow_final_response(
                workflow, results, conversation_id, user_id
            )

            return {
                "workflow_id": workflow_id,
                "status": "completed",
                "results": results,
                "processing_time_ms": processing_time,
            }

        except Exception as e:
            logger.error(f"Error in agent coordination: {e}")

            # Check if we have partial results from successful agents
            partial_results = {}
            for agent_name, result in agent_results.items():
                if result and not isinstance(result, Exception):
                    partial_results[agent_name] = result

            # If we have some successful results, provide partial response
            if partial_results:
                logger.info(
                    f"Providing partial results from {len(partial_results)} successful agents"
                )

                # Mark workflow as partially completed
                if workflow_id in self.active_workflows:
                    workflow = self.active_workflows[workflow_id]
                    workflow.status = WorkflowStatus.COMPLETED
                    workflow.result = {
                        "status": "partial_success",
                        "successful_agents": list(partial_results.keys()),
                        "failed_agents": [
                            agent
                            for agent in participating_agents
                            if agent not in partial_results
                        ],
                        "results": partial_results,
                        "error_message": f"Some agents failed: {str(e)}",
                    }
                    workflow.end_time = datetime.now(timezone.utc)

                    await self._notify_workflow_status(
                        workflow, user_id, conversation_id
                    )

                    # Send final response even for partial success
                    await self._send_workflow_final_response(
                        workflow,
                        {
                            "agent_results": partial_results,
                            "successful_agents": list(partial_results.keys()),
                        },
                        conversation_id,
                        user_id,
                    )

                processing_time = int((time.time() - start_time) * 1000)

                # Log partial coordination success
                await self.coordination_repository.log_coordination_activity(
                    participating_agents=participating_agents,
                    coordination_type=workflow_type,
                    status="partial_success",
                    result_data={
                        "successful_agents": list(partial_results.keys()),
                        "partial_results": partial_results,
                        "error": str(e),
                    },
                    processing_time_ms=processing_time,
                    workflow_id=UUID(workflow_id) if workflow_id else None,
                )

                return {
                    "status": "partial_success",
                    "workflow_id": workflow_id,
                    "results": partial_results,
                    "successful_agents": list(partial_results.keys()),
                    "failed_agents": [
                        agent
                        for agent in participating_agents
                        if agent not in partial_results
                    ],
                    "error_message": f"Some agents failed: {str(e)}",
                }
            else:
                # Complete failure - no successful results
                if workflow_id in self.active_workflows:
                    workflow = self.active_workflows[workflow_id]
                    workflow.status = WorkflowStatus.FAILED
                    workflow.error_message = str(e)
                    workflow.end_time = datetime.now(timezone.utc)

                    await self._notify_workflow_status(
                        workflow, user_id, conversation_id
                    )

                processing_time = int((time.time() - start_time) * 1000)

                # Log failed coordination
                await self.coordination_repository.log_coordination_activity(
                    participating_agents=participating_agents,
                    coordination_type=workflow_type,
                    status="failed",
                    result_data={"error": str(e)},
                    processing_time_ms=processing_time,
                    workflow_id=UUID(workflow_id) if workflow_id else None,
                )

            return {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": str(e),
                "processing_time_ms": processing_time,
            }

    async def manage_workflow(self, workflow_id: str, action: str) -> Dict[str, Any]:
        """Manage an active workflow (pause, resume, cancel)."""
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow = self.active_workflows[workflow_id]

        if action == "cancel":
            workflow.status = WorkflowStatus.CANCELLED
            workflow.end_time = datetime.now(timezone.utc)
            await self._notify_workflow_status(workflow, None, None)
            return {"status": "cancelled"}

        # TODO: Implement pause/resume functionality
        return {"status": "action_not_implemented", "action": action}

    async def handle_consensus(
        self,
        decision_context: Dict[str, Any],
        participating_agents: List[str],
        consensus_threshold: float = 0.7,
    ) -> Dict[str, Any]:
        """Handle consensus decision-making among agents."""
        try:
            agent_decisions = {}

            # Collect decisions from each agent
            for agent_name in participating_agents:
                if agent_name in self.agent_registry:
                    agent = self.agent_registry[agent_name]

                    # Get agent's decision
                    decision = await self._get_agent_decision(agent, decision_context)
                    agent_decisions[agent_name] = decision

            # Calculate consensus
            consensus_result = self._calculate_consensus(
                agent_decisions, consensus_threshold
            )

            return {
                "consensus_reached": consensus_result["consensus_reached"],
                "final_decision": consensus_result["final_decision"],
                "agent_decisions": agent_decisions,
                "consensus_score": consensus_result["consensus_score"],
            }

        except Exception as e:
            logger.error(f"Error in consensus handling: {e}")
            return {"consensus_reached": False, "error": str(e)}

    async def initiate_agent_handoff(
        self,
        from_agent_type: str,
        to_agent_type: str,
        context: Dict[str, Any],
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Initiate a handoff between agents."""
        handoff_id = str(uuid4())

        try:
            # Create handoff
            handoff = UnifiedAgentHandoff(
                handoff_id=handoff_id,
                from_agent=from_agent_type,
                to_agent=to_agent_type,
                context=context,
                conversation_id=conversation_id,
            )

            self.active_handoffs[handoff_id] = handoff
            handoff.status = UnifiedAgentHandoffStatus.IN_PROGRESS

            # Notify via WebSocket
            await self._notify_handoff_status(handoff, user_id)

            # Perform handoff
            if to_agent_type in self.agent_registry:
                to_agent = self.agent_registry[to_agent_type]

                # Prepare context for new agent
                handoff_context = {
                    "previous_agent": from_agent_type,
                    "handoff_reason": context.get("reason", "user_request"),
                    "conversation_history": context.get("conversation_history", []),
                    "current_query": context.get("current_query", ""),
                    **context,
                }

                # Get response from new agent
                response = await to_agent.process_message(
                    message=handoff_context.get("current_query", ""),
                    context=handoff_context,
                )

                # Complete handoff
                handoff.status = UnifiedAgentHandoffStatus.COMPLETED
                handoff.completion_time = datetime.now(timezone.utc)

                await self._notify_handoff_status(handoff, user_id)

                return {
                    "handoff_id": handoff_id,
                    "status": "completed",
                    "new_agent_response": (
                        response.to_dict()
                        if hasattr(response, "to_dict")
                        else str(response)
                    ),
                    "completion_time": handoff.completion_time.isoformat(),
                }
            else:
                raise ValueError(f"Target agent {to_agent_type} not available")

        except Exception as e:
            logger.error(f"Error in agent handoff: {e}")

            if handoff_id in self.active_handoffs:
                handoff = self.active_handoffs[handoff_id]
                handoff.status = UnifiedAgentHandoffStatus.FAILED
                handoff.error_message = str(e)
                handoff.completion_time = datetime.now(timezone.utc)

                await self._notify_handoff_status(handoff, user_id)

            return {"handoff_id": handoff_id, "status": "failed", "error": str(e)}

    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get status of a workflow."""
        if workflow_id not in self.active_workflows:
            return {"error": "Workflow not found"}

        workflow = self.active_workflows[workflow_id]
        return workflow.to_dict()

    async def get_handoff_status(self, handoff_id: str) -> Dict[str, Any]:
        """Get status of an agent handoff."""
        if handoff_id not in self.active_handoffs:
            return {"error": "Handoff not found"}

        handoff = self.active_handoffs[handoff_id]
        return handoff.to_dict()

    # ===== WORKFLOW EXECUTION ENGINE FOUNDATION =====

    async def create_workflow(
        self,
        workflow_type: str,
        context: Dict[str, Any],
        priority: str = "medium",
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> UnifiedAgentWorkflow:
        """Create a new workflow instance.

        Args:
            workflow_type: Type of workflow to create
            context: Context data for the workflow
            priority: Priority level (low, medium, high)
            user_id: Optional user ID
            conversation_id: Optional conversation ID

        Returns:
            UnifiedAgentWorkflow: Created workflow instance

        Raises:
            ValueError: If workflow_type is not supported
        """
        try:
            # Generate unique workflow ID
            workflow_id = str(uuid4())

            # Determine participating agents based on workflow type
            participating_agents = self._get_agents_for_workflow_type(workflow_type)

            # Create workflow instance
            workflow = UnifiedAgentWorkflow(
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                participating_agents=participating_agents,
                context=context,
            )

            # Set workflow properties
            workflow.start_time = datetime.now(timezone.utc)
            workflow.status = WorkflowStatus.PENDING
            workflow.priority = priority
            workflow.user_id = user_id
            workflow.conversation_id = conversation_id

            # Add to active workflows
            self.active_workflows[workflow_id] = workflow

            logger.info(f"Created workflow {workflow_id} of type {workflow_type}")

            return workflow

        except Exception as e:
            logger.error(f"Error creating workflow: {e}")
            raise

    def _get_agents_for_workflow_type(self, workflow_type: str) -> List[str]:
        """Get the list of agents required for a specific workflow type."""
        workflow_agent_mapping = {
            "product_analysis": ["content", "logistics", "executive"],
            "listing_optimization": ["content", "market", "executive"],
            "market_research": ["market", "content", "executive"],
            "pricing_strategy": ["market", "executive"],
            "decision_consensus": ["executive", "market", "content"],
            "inventory_management": ["logistics", "executive"],
            "competitive_analysis": ["market", "competitor_analyzer", "executive"],
            "content_optimization": ["content", "market", "executive"],
            "cross_platform_sync": ["market", "logistics", "executive"],
        }

        agents = workflow_agent_mapping.get(workflow_type, ["executive"])

        # Filter to only include agents that are actually available
        available_agents = []
        for agent_name in agents:
            if agent_name in self.agent_registry:
                available_agents.append(agent_name)
            else:
                logger.warning(
                    f"UnifiedAgent {agent_name} not available for workflow {workflow_type}"
                )

        # Ensure we have at least one agent
        if not available_agents and "executive" in self.agent_registry:
            available_agents = ["executive"]

        return available_agents

    async def create_workflow_from_template(
        self,
        template_id: str,
        context: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> str:
        """Create a new workflow from a template."""
        try:
            if template_id not in self.workflow_templates:
                raise ValueError(f"Workflow template {template_id} not found")

            template = self.workflow_templates[template_id]
            workflow_id = str(uuid4())

            # Create workflow steps from template
            workflow_steps = []
            for step_template in template.steps:
                step = WorkflowStep(
                    step_id=step_template.step_id,
                    name=step_template.name,
                    agent_type=step_template.agent_type,
                    method_name=step_template.method_name,
                    parameters=step_template.parameters.copy(),
                    dependencies=step_template.dependencies.copy(),
                    retry_strategy=step_template.retry_strategy,
                    max_retries=step_template.max_retries,
                    timeout_seconds=step_template.timeout_seconds,
                )
                workflow_steps.append(step)

            # Merge template parameters with provided parameters
            merged_context = template.default_parameters.copy()
            merged_context.update(context)
            if parameters:
                merged_context.update(parameters)

            # Extract participating agents from steps
            participating_agents = list(set(step.agent_type for step in workflow_steps))

            # Create workflow
            workflow = UnifiedAgentWorkflow(
                workflow_id=workflow_id,
                workflow_type=template_id,
                participating_agents=participating_agents,
                context=merged_context,
                steps=workflow_steps,
                template_id=template_id,
            )

            # Initialize metrics
            workflow.metrics.total_steps = len(workflow_steps)

            # Store workflow
            self.active_workflows[workflow_id] = workflow

            # Save initial state
            await self._save_workflow_state(workflow)

            logger.info(f"Created workflow {workflow_id} from template {template_id}")
            return workflow_id

        except Exception as e:
            logger.error(f"Error creating workflow from template: {e}")
            raise

    async def execute_workflow_step_by_step(
        self,
        workflow_id: str,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a workflow step by step with full error handling and persistence."""
        try:
            if workflow_id not in self.active_workflows:
                raise ValueError(f"Workflow {workflow_id} not found")

            workflow = self.active_workflows[workflow_id]
            workflow.status = WorkflowStatus.IN_PROGRESS
            workflow.start_time = datetime.now(timezone.utc)

            # Notify workflow started
            await self._notify_workflow_status(workflow, user_id, conversation_id)

            # Execute steps
            while workflow.current_step_index < len(workflow.steps):
                current_step = workflow.get_current_step()
                if not current_step:
                    break

                # Check dependencies
                if not await self._check_step_dependencies(workflow, current_step):
                    logger.warning(
                        f"Dependencies not met for step {current_step.step_id}"
                    )
                    current_step.status = WorkflowStepStatus.SKIPPED
                    workflow.metrics.skipped_steps += 1
                    workflow.current_step_index += 1
                    continue

                # Execute step with retry logic
                step_result = await self._execute_workflow_step_with_retry(
                    workflow, current_step
                )

                # Update workflow state
                if step_result["success"]:
                    current_step.status = WorkflowStepStatus.COMPLETED
                    current_step.result = step_result["result"]
                    workflow.metrics.completed_steps += 1

                    # Store result in workflow context
                    workflow.context[f"step_{current_step.step_id}_result"] = (
                        step_result["result"]
                    )
                else:
                    current_step.status = WorkflowStepStatus.FAILED
                    current_step.error_message = step_result["error"]
                    workflow.metrics.failed_steps += 1

                    # Check if this is a critical failure
                    if not step_result.get("can_continue", False):
                        workflow.status = WorkflowStatus.FAILED
                        workflow.error_message = f"Critical failure in step {current_step.step_id}: {step_result['error']}"
                        break

                # Create checkpoint after each step
                workflow.create_checkpoint()
                await self._save_workflow_state(workflow)

                # Move to next step
                workflow.current_step_index += 1

                # Notify step completion
                await self._notify_workflow_step_completion(
                    workflow, current_step, user_id, conversation_id
                )

            # Finalize workflow
            if workflow.status != WorkflowStatus.FAILED:
                workflow.status = WorkflowStatus.COMPLETED

            workflow.end_time = datetime.now(timezone.utc)
            workflow.metrics.total_execution_time = (
                workflow.end_time - workflow.start_time
            ).total_seconds()

            if workflow.metrics.completed_steps > 0:
                workflow.metrics.average_step_time = (
                    workflow.metrics.total_execution_time
                    / workflow.metrics.completed_steps
                )

            workflow.metrics.error_rate = (
                workflow.metrics.failed_steps / workflow.metrics.total_steps
                if workflow.metrics.total_steps > 0
                else 0.0
            )

            # Final save
            await self._save_workflow_state(workflow)

            # Final notification
            await self._notify_workflow_status(workflow, user_id, conversation_id)

            return {
                "workflow_id": workflow_id,
                "status": workflow.status.value,
                "results": workflow.results,
                "metrics": workflow.metrics.__dict__,
                "completed_steps": len(workflow.get_completed_steps()),
                "failed_steps": len(workflow.get_failed_steps()),
                "progress": workflow.get_progress(),
            }

        except Exception as e:
            logger.error(f"Error executing workflow {workflow_id}: {e}")

            # Update workflow status on error
            if workflow_id in self.active_workflows:
                workflow = self.active_workflows[workflow_id]
                workflow.status = WorkflowStatus.FAILED
                workflow.error_message = str(e)
                workflow.end_time = datetime.now(timezone.utc)
                await self._save_workflow_state(workflow)

            return {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": str(e),
            }

    async def _check_step_dependencies(
        self, workflow: UnifiedAgentWorkflow, step: WorkflowStep
    ) -> bool:
        """Check if all dependencies for a step are satisfied."""
        try:
            if not step.dependencies:
                return True

            for dependency_id in step.dependencies:
                # Find the dependency step
                dependency_step = None
                for workflow_step in workflow.steps:
                    if workflow_step.step_id == dependency_id:
                        dependency_step = workflow_step
                        break

                if not dependency_step:
                    logger.warning(f"Dependency step {dependency_id} not found")
                    return False

                if dependency_step.status != WorkflowStepStatus.COMPLETED:
                    logger.debug(
                        f"Dependency {dependency_id} not completed (status: {dependency_step.status})"
                    )
                    return False

            return True

        except Exception as e:
            logger.error(f"Error checking step dependencies: {e}")
            return False

    async def _execute_workflow_step_with_retry(
        self, workflow: UnifiedAgentWorkflow, step: WorkflowStep
    ) -> Dict[str, Any]:
        """Execute a workflow step with retry logic."""
        step.start_time = datetime.now(timezone.utc)
        step.status = WorkflowStepStatus.IN_PROGRESS

        for attempt in range(step.max_retries + 1):
            try:
                # Get the agent for this step
                agent = await self._get_agent_by_type(step.agent_type)
                if not agent:
                    return {
                        "success": False,
                        "error": f"UnifiedAgent {step.agent_type} not available",
                        "can_continue": False,
                    }

                # Prepare step parameters
                step_params = step.parameters.copy()
                step_params.update(workflow.context)

                # Execute the step method with timeout
                result = await asyncio.wait_for(
                    self._execute_agent_method(agent, step.method_name, step_params),
                    timeout=step.timeout_seconds,
                )

                step.end_time = datetime.now(timezone.utc)
                step.retry_count = attempt

                return {
                    "success": True,
                    "result": result,
                    "attempt": attempt + 1,
                }

            except asyncio.TimeoutError:
                error_msg = f"Step {step.step_id} timed out after {step.timeout_seconds} seconds"
                logger.warning(f"{error_msg} (attempt {attempt + 1})")
                step.error_message = error_msg

            except Exception as e:
                error_msg = f"Step {step.step_id} failed: {str(e)}"
                logger.warning(f"{error_msg} (attempt {attempt + 1})")
                step.error_message = error_msg

            # Apply retry delay if not the last attempt
            if attempt < step.max_retries:
                delay = self._calculate_retry_delay(step.retry_strategy, attempt)
                if delay > 0:
                    logger.info(f"Retrying step {step.step_id} in {delay} seconds")
                    await asyncio.sleep(delay)

                step.status = WorkflowStepStatus.RETRYING
                workflow.metrics.retry_count += 1

        # All retries exhausted
        step.end_time = datetime.now(timezone.utc)
        step.retry_count = step.max_retries
        step.status = WorkflowStepStatus.FAILED

        return {
            "success": False,
            "error": step.error_message or "Step failed after all retries",
            "can_continue": True,  # Most failures can continue to next step
            "attempts": step.max_retries + 1,
        }

    def _calculate_retry_delay(self, strategy: RetryStrategy, attempt: int) -> float:
        """Calculate retry delay based on strategy."""
        if strategy == RetryStrategy.NONE:
            return 0.0
        elif strategy == RetryStrategy.FIXED_DELAY:
            return 2.0  # 2 seconds fixed delay
        elif strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            return min(2.0**attempt, 30.0)  # Exponential backoff, max 30 seconds
        elif strategy == RetryStrategy.LINEAR_BACKOFF:
            return min(2.0 * (attempt + 1), 20.0)  # Linear backoff, max 20 seconds
        else:
            return 1.0  # Default 1 second

    async def _execute_agent_method(
        self,
        agent: BaseConversationalUnifiedAgent,
        method_name: str,
        parameters: Dict[str, Any],
    ) -> Any:
        """Execute a specific method on an agent."""
        try:
            # Check if the agent has the requested method
            if not hasattr(agent, method_name):
                raise AttributeError(
                    f"UnifiedAgent {agent.agent_type} does not have method {method_name}"
                )

            method = getattr(agent, method_name)

            # Call the method with parameters
            if asyncio.iscoroutinefunction(method):
                result = await method(**parameters)
            else:
                result = method(**parameters)

            return result

        except Exception as e:
            logger.error(f"Error executing agent method {method_name}: {e}")
            raise

    async def _save_workflow_state(self, workflow: UnifiedAgentWorkflow) -> bool:
        """Save workflow state to persistent storage."""
        try:
            workflow_data = {
                "workflow": workflow.to_dict(),
                "checkpoint": workflow.checkpoint_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Save to persistence manager
            success = await self.persistence_manager.save_state(
                agent_id=f"workflow_{workflow.workflow_id}",
                state=workflow_data,
            )

            if success:
                logger.debug(f"Saved state for workflow {workflow.workflow_id}")
            else:
                logger.warning(
                    f"Failed to save state for workflow {workflow.workflow_id}"
                )

            return success

        except Exception as e:
            logger.error(f"Error saving workflow state: {e}")
            return False

    async def _load_workflow_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Load workflow state from persistent storage."""
        try:
            state = await self.persistence_manager.load_state(
                agent_id=f"workflow_{workflow_id}"
            )

            if state:
                logger.debug(f"Loaded state for workflow {workflow_id}")
                return state
            else:
                logger.debug(f"No saved state found for workflow {workflow_id}")
                return None

        except Exception as e:
            logger.error(f"Error loading workflow state: {e}")
            return None

    async def _notify_workflow_step_completion(
        self,
        workflow: UnifiedAgentWorkflow,
        step: WorkflowStep,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ):
        """Notify about workflow step completion via WebSocket."""
        try:
            step_data = {
                "workflow_id": workflow.workflow_id,
                "step_id": step.step_id,
                "step_name": step.name,
                "status": step.status.value,
                "agent_type": step.agent_type,
                "retry_count": step.retry_count,
                "error_message": step.error_message,
                "progress": workflow.get_progress(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await websocket_manager.broadcast_to_user(
                user_id=user_id or "system",
                message_type="workflow_step_update",
                data=step_data,
            )

        except Exception as e:
            logger.error(f"Error notifying workflow step completion: {e}")

    async def resume_workflow_from_checkpoint(
        self,
        workflow_id: str,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Resume a workflow from its last checkpoint."""
        try:
            # Load workflow state
            workflow_state = await self._load_workflow_state(workflow_id)
            if not workflow_state:
                raise ValueError(f"No saved state found for workflow {workflow_id}")

            # Recreate workflow from saved state
            workflow_data = workflow_state["workflow"]
            checkpoint_data = workflow_state.get("checkpoint", {})

            # Create workflow steps
            steps = []
            for step_data in workflow_data.get("steps", []):
                step = WorkflowStep(
                    step_id=step_data["step_id"],
                    name=step_data["name"],
                    agent_type=step_data["agent_type"],
                    method_name="",  # Will be restored from template
                    status=WorkflowStepStatus(step_data["status"]),
                    retry_count=step_data.get("retry_count", 0),
                    error_message=step_data.get("error_message"),
                )
                steps.append(step)

            # Recreate workflow
            workflow = UnifiedAgentWorkflow(
                workflow_id=workflow_id,
                workflow_type=workflow_data["workflow_type"],
                participating_agents=workflow_data["participating_agents"],
                context=workflow_data["context"],
                steps=steps,
                template_id=workflow_data.get("template_id"),
            )

            # Restore from checkpoint
            if checkpoint_data:
                workflow.restore_from_checkpoint(checkpoint_data)

            # Store in active workflows
            self.active_workflows[workflow_id] = workflow

            logger.info(f"Resumed workflow {workflow_id} from checkpoint")

            # Continue execution from current step
            return await self.execute_workflow_step_by_step(
                workflow_id, user_id, conversation_id
            )

        except Exception as e:
            logger.error(f"Error resuming workflow from checkpoint: {e}")
            return {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": f"Failed to resume from checkpoint: {str(e)}",
            }

    async def get_workflow_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get all available workflow templates."""
        return {
            template_id: {
                "template_id": template.template_id,
                "name": template.name,
                "description": template.description,
                "steps": len(template.steps),
                "tags": template.tags,
                "version": template.version,
            }
            for template_id, template in self.workflow_templates.items()
        }

    async def get_workflow_metrics(self, workflow_id: str) -> Dict[str, Any]:
        """Get comprehensive metrics for a workflow."""
        try:
            if workflow_id not in self.active_workflows:
                # Try to load from persistent storage
                workflow_state = await self._load_workflow_state(workflow_id)
                if not workflow_state:
                    return {"error": "Workflow not found"}

                workflow_data = workflow_state["workflow"]
                metrics = workflow_data.get("metrics", {})
            else:
                workflow = self.active_workflows[workflow_id]
                metrics = workflow.metrics.__dict__

            return {
                "workflow_id": workflow_id,
                "metrics": metrics,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting workflow metrics: {e}")
            return {"error": str(e)}

    # ===== END WORKFLOW EXECUTION ENGINE FOUNDATION =====

    async def _execute_product_analysis_workflow(
        self, workflow: UnifiedAgentWorkflow
    ) -> Dict[str, Any]:
        """Execute a product analysis workflow."""
        try:
            # Get product data from workflow context
            product_data = workflow.context.get("product_data", {})
            image_url = workflow.context.get("image_url")

            # Step 1: Content UnifiedAgent analyzes product
            content_agent = await self._get_agent_by_type("content")
            if content_agent:
                analysis_result = await content_agent.analyze_product(
                    product_data, image_url
                )
                workflow.context["content_analysis"] = analysis_result

            # Step 2: Logistics UnifiedAgent calculates shipping
            logistics_agent = await self._get_agent_by_type("logistics")
            if logistics_agent:
                shipping_result = await logistics_agent.calculate_shipping_options(
                    product_data
                )
                workflow.context["shipping_analysis"] = shipping_result

            # Step 3: Executive UnifiedAgent makes final recommendations
            executive_agent = await self._get_agent_by_type("executive")
            if executive_agent:
                final_recommendations = await executive_agent.generate_recommendations(
                    workflow.context
                )
                workflow.context["final_recommendations"] = final_recommendations

            return {
                "workflow_type": "product_analysis",
                "status": "completed",
                "results": workflow.context,
                "agents_involved": len(
                    [a for a in [content_agent, logistics_agent, executive_agent] if a]
                ),
            }

        except Exception as e:
            logger.error(f"Error in product analysis workflow: {e}")
            return {
                "workflow_type": "product_analysis",
                "status": "failed",
                "error": str(e),
            }

    async def _execute_listing_optimization_workflow(
        self, workflow: UnifiedAgentWorkflow
    ) -> Dict[str, Any]:
        """Execute a listing optimization workflow."""
        try:
            # Get listing data from workflow context
            listing_data = workflow.context.get("listing_data", {})
            marketplace = workflow.context.get("marketplace", "amazon")

            # Step 1: Content UnifiedAgent optimizes title and description
            content_agent = await self._get_agent_by_type("content")
            if content_agent:
                content_optimization = await content_agent.optimize_listing_content(
                    listing_data, marketplace
                )
                workflow.context["content_optimization"] = content_optimization

            # Step 2: Market UnifiedAgent analyzes competition and pricing
            market_agent = await self._get_agent_by_type("market")
            if market_agent:
                market_analysis = await market_agent.analyze_competition(
                    listing_data, marketplace
                )
                workflow.context["market_analysis"] = market_analysis

            # Step 3: Executive UnifiedAgent provides final optimization recommendations
            executive_agent = await self._get_agent_by_type("executive")
            if executive_agent:
                optimization_recommendations = (
                    await executive_agent.generate_optimization_plan(workflow.context)
                )
                workflow.context["optimization_recommendations"] = (
                    optimization_recommendations
                )

            return {
                "workflow_type": "listing_optimization",
                "status": "completed",
                "results": workflow.context,
                "marketplace": marketplace,
                "agents_involved": len(
                    [a for a in [content_agent, market_agent, executive_agent] if a]
                ),
            }

        except Exception as e:
            logger.error(f"Error in listing optimization workflow: {e}")
            return {
                "workflow_type": "listing_optimization",
                "status": "failed",
                "error": str(e),
            }

    async def _execute_decision_consensus_workflow(
        self, workflow: UnifiedAgentWorkflow
    ) -> Dict[str, Any]:
        """Execute a decision consensus workflow."""
        try:
            # Get decision context and threshold
            decision_context = workflow.context.get("decision_context", {})
            consensus_threshold = workflow.context.get("consensus_threshold", 0.7)

            # Get decisions from all relevant agents
            agent_decisions = {}

            # Content UnifiedAgent decision
            content_agent = await self._get_agent_by_type("content")
            if content_agent:
                content_decision = await self._get_agent_decision(
                    content_agent, decision_context
                )
                agent_decisions["content"] = content_decision

            # Logistics UnifiedAgent decision
            logistics_agent = await self._get_agent_by_type("logistics")
            if logistics_agent:
                logistics_decision = await self._get_agent_decision(
                    logistics_agent, decision_context
                )
                agent_decisions["logistics"] = logistics_decision

            # Executive UnifiedAgent decision
            executive_agent = await self._get_agent_by_type("executive")
            if executive_agent:
                executive_decision = await self._get_agent_decision(
                    executive_agent, decision_context
                )
                agent_decisions["executive"] = executive_decision

            # Calculate consensus
            consensus_result = self._calculate_consensus(
                agent_decisions, consensus_threshold
            )
            workflow.context["agent_decisions"] = agent_decisions
            workflow.context["consensus_result"] = consensus_result

            return {
                "workflow_type": "decision_consensus",
                "status": "completed",
                "results": workflow.context,
                "consensus_reached": consensus_result["consensus_reached"],
                "final_decision": consensus_result["final_decision"],
                "agents_involved": len(agent_decisions),
            }

        except Exception as e:
            logger.error(f"Error in decision consensus workflow: {e}")
            return {
                "workflow_type": "decision_consensus",
                "status": "failed",
                "error": str(e),
            }

    async def _get_agent_decision(
        self, agent: BaseConversationalUnifiedAgent, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get a decision from an agent."""
        try:
            # Prepare decision prompt based on context
            decision_prompt = self._prepare_decision_prompt(context)

            # Get agent response
            response = await agent.process_message(decision_prompt, context)

            # Extract decision information from response
            decision_data = {
                "decision": self._extract_decision(response.content),
                "confidence": response.confidence_score,
                "reasoning": response.content,
                "agent_type": agent.agent_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            return decision_data

        except Exception as e:
            logger.error(f"Error getting agent decision: {e}")
            return {
                "decision": "abstain",
                "confidence": 0.0,
                "reasoning": f"Error getting decision: {str(e)}",
                "agent_type": getattr(agent, "agent_type", "unknown"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def _calculate_consensus(
        self, agent_decisions: Dict[str, Any], threshold: float
    ) -> Dict[str, Any]:
        """Calculate consensus from agent decisions."""
        try:
            if not agent_decisions:
                return {
                    "consensus_reached": False,
                    "final_decision": "no_consensus",
                    "consensus_score": 0.0,
                    "reasoning": "No agent decisions available",
                }

            # Count decisions and calculate weighted scores
            decision_counts = {}
            total_confidence = 0
            weighted_decisions = {}

            for agent_type, decision_data in agent_decisions.items():
                decision = decision_data.get("decision", "abstain")
                confidence = decision_data.get("confidence", 0.0)

                if decision not in decision_counts:
                    decision_counts[decision] = 0
                    weighted_decisions[decision] = 0

                decision_counts[decision] += 1
                weighted_decisions[decision] += confidence
                total_confidence += confidence

            # Find the decision with highest weighted score
            if total_confidence > 0:
                best_decision = max(
                    weighted_decisions.keys(), key=lambda k: weighted_decisions[k]
                )
                consensus_score = weighted_decisions[best_decision] / total_confidence
            else:
                best_decision = "no_consensus"
                consensus_score = 0.0

            # Check if consensus threshold is met
            consensus_reached = consensus_score >= threshold

            return {
                "consensus_reached": consensus_reached,
                "final_decision": (
                    best_decision if consensus_reached else "no_consensus"
                ),
                "consensus_score": consensus_score,
                "decision_breakdown": decision_counts,
                "weighted_scores": weighted_decisions,
                "threshold_used": threshold,
                "reasoning": f"Consensus {'reached' if consensus_reached else 'not reached'} with score {consensus_score:.2f}",
            }

        except Exception as e:
            logger.error(f"Error calculating consensus: {e}")
            return {
                "consensus_reached": False,
                "final_decision": "error",
                "consensus_score": 0.0,
                "reasoning": f"Error calculating consensus: {str(e)}",
            }

    def _prepare_decision_prompt(self, context: Dict[str, Any]) -> str:
        """Prepare a decision prompt for agents based on context."""
        decision_type = context.get("decision_type", "general")

        prompts = {
            "product_approval": f"""
Please analyze the following product data and provide your decision on whether to approve this product for listing:

Product Data: {context.get('product_data', {})}
Market Analysis: {context.get('market_analysis', {})}
Risk Factors: {context.get('risk_factors', [])}

Please respond with one of: approve, reject, needs_review
Provide your reasoning and confidence level.
""",
            "pricing_decision": f"""
Please analyze the pricing strategy for this product and provide your decision:

Product: {context.get('product_name', 'Unknown')}
Current Price: {context.get('current_price', 'N/A')}
Competitor Prices: {context.get('competitor_prices', [])}
Market Conditions: {context.get('market_conditions', {})}

Please respond with one of: approve_price, adjust_higher, adjust_lower, needs_analysis
Provide your reasoning and confidence level.
""",
            "general": f"""
Please analyze the following situation and provide your decision:

Context: {context}

Please provide your decision, reasoning, and confidence level.
""",
        }

        return prompts.get(decision_type, prompts["general"])

    def _extract_decision(self, response_content: str) -> str:
        """Extract decision from agent response content."""
        content_lower = response_content.lower()

        # Common decision patterns
        if any(
            word in content_lower for word in ["approve", "accept", "yes", "proceed"]
        ):
            return "approve"
        elif any(word in content_lower for word in ["reject", "deny", "no", "decline"]):
            return "reject"
        elif any(
            word in content_lower for word in ["review", "investigate", "analyze"]
        ):
            return "needs_review"
        elif any(word in content_lower for word in ["higher", "increase", "raise"]):
            return "adjust_higher"
        elif any(word in content_lower for word in ["lower", "decrease", "reduce"]):
            return "adjust_lower"
        else:
            return "unclear"

    async def _get_agent_by_type(
        self, agent_type: str
    ) -> Optional[BaseConversationalUnifiedAgent]:
        """Get an agent instance by type."""
        try:
            # Use the agent registry for proper agent instances
            if agent_type in self.agent_registry:
                return self.agent_registry[agent_type]

            # If not in registry, try to create dynamically
            from fs_agt_clean.agents.content.content_agent import ContentUnifiedAgent
            from fs_agt_clean.agents.executive.executive_agent import ExecutiveUnifiedAgent
            from fs_agt_clean.agents.logistics.logistics_agent import LogisticsUnifiedAgent
            from fs_agt_clean.agents.market.market_agent import MarketUnifiedAgent

            agent_classes = {
                "content": ContentUnifiedAgent,
                "logistics": LogisticsUnifiedAgent,
                "executive": ExecutiveUnifiedAgent,
                "market": MarketUnifiedAgent,  # ✅ FIXED: Now uses actual MarketUnifiedAgent instead of ContentUnifiedAgent fallback
            }

            agent_class = agent_classes.get(agent_type)
            if agent_class:
                # Initialize agent with basic configuration
                agent = agent_class(agent_id=f"{agent_type}_agent")
                await agent.initialize()
                return agent

            return None

        except Exception as e:
            logger.error(f"Error getting agent by type {agent_type}: {e}")
            return None

    async def _notify_workflow_status(
        self,
        workflow: UnifiedAgentWorkflow,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ):
        """Notify about workflow status via WebSocket."""
        try:
            # Calculate progress based on workflow status
            progress = 0.0
            if workflow.status == WorkflowStatus.IN_PROGRESS:
                progress = 0.5  # 50% when in progress
            elif workflow.status == WorkflowStatus.COMPLETED:
                progress = 1.0  # 100% when completed
            elif workflow.status == WorkflowStatus.FAILED:
                progress = 0.0  # 0% when failed

            # Use the enhanced workflow broadcast method
            await websocket_manager.broadcast_workflow_update(
                workflow_id=workflow.workflow_id,
                workflow_type=workflow.workflow_type,
                status=workflow.status.value,
                progress=progress,
                participating_agents=workflow.participating_agents,
                current_agent=None,  # TODO: Track current agent in workflow
                error_message=workflow.error_message,
                conversation_id=conversation_id,
            )

        except Exception as e:
            logger.error(f"Error notifying workflow status: {e}")

    async def _send_workflow_final_response(
        self,
        workflow: UnifiedAgentWorkflow,
        results: Dict[str, Any],
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        """Send the final workflow response to WebSocket clients."""
        try:
            # Extract the final response content based on workflow type
            final_content = self._extract_final_response_content(workflow, results)

            if final_content and conversation_id:
                # Import here to avoid circular imports
                from fs_agt_clean.core.websocket.events import (
                    UnifiedAgentType,
                    SenderType,
                    create_message_event,
                )
                from fs_agt_clean.core.websocket.manager import websocket_manager

                # Create message event for the final response
                message_event = create_message_event(
                    conversation_id=conversation_id,
                    message_id=f"workflow_final_{int(time.time() * 1000)}",
                    content=final_content,
                    sender=SenderType.AGENT,
                    agent_type=UnifiedAgentType.EXECUTIVE,
                    metadata={
                        "workflow_id": workflow.workflow_id,
                        "workflow_type": workflow.workflow_type,
                        "participating_agents": workflow.participating_agents,
                        "is_final_response": True,
                    },
                )

                # Send to conversation (UUID conversation ID)
                sent_count = await websocket_manager.send_to_conversation(
                    conversation_id, message_event.dict()
                )

                # CRITICAL FIX: Also try to send to original conversation ID if available
                # This handles the conversation ID mapping issue where frontend expects original ID
                # but backend has mapped it to a UUID
                additional_sent = 0
                original_conversation_id = workflow.context.get(
                    "original_conversation_id"
                )

                if (
                    original_conversation_id
                    and original_conversation_id != conversation_id
                ):
                    try:
                        logger.info(
                            f"🔄 Also sending to original conversation ID: {original_conversation_id}"
                        )
                        additional_sent = await websocket_manager.send_to_conversation(
                            original_conversation_id, message_event.dict()
                        )
                        if additional_sent > 0:
                            logger.info(
                                f"✅ Also sent final workflow response to {additional_sent} clients in conversation '{original_conversation_id}'"
                            )
                    except Exception as e:
                        logger.warning(
                            f"Failed to send to original conversation '{original_conversation_id}': {e}"
                        )
                else:
                    # Fallback: try sending to "main" if this is a UUID and no original_conversation_id
                    try:
                        import uuid

                        # Check if current conversation_id is a UUID
                        uuid.UUID(conversation_id)
                        # It's a UUID, also try sending to "main" for frontend compatibility
                        additional_sent = await websocket_manager.send_to_conversation(
                            "main", message_event.dict()
                        )
                        if additional_sent > 0:
                            logger.info(
                                f"✅ Also sent final workflow response to {additional_sent} clients in conversation 'main'"
                            )
                    except ValueError:
                        # Not a UUID, no additional sending needed
                        pass
                    except Exception as e:
                        logger.warning(f"Failed to send to 'main' conversation: {e}")

                total_sent = sent_count + additional_sent
                logger.info(
                    f"✅ Sent final workflow response to {total_sent} total clients (UUID: {sent_count}, original/main: {additional_sent})"
                )

        except Exception as e:
            logger.error(f"Error sending workflow final response: {e}")

    def _extract_final_response_content(
        self, workflow: UnifiedAgentWorkflow, results: Dict[str, Any]
    ) -> Optional[str]:
        """Extract the final response content from workflow results."""
        try:
            # For pricing strategy workflow, get the executive agent's final response
            if workflow.workflow_type == "pricing_strategy":
                # Check if we have the final pricing strategy from executive agent
                if "final_pricing_strategy" in workflow.context:
                    executive_response = workflow.context["final_pricing_strategy"]
                    if hasattr(executive_response, "content"):
                        return executive_response.content
                    elif isinstance(executive_response, str):
                        return executive_response
                    elif isinstance(executive_response, dict):
                        # Check for executive_strategy key (from formulate_pricing_strategy)
                        if "executive_strategy" in executive_response:
                            return executive_response["executive_strategy"]
                        elif "content" in executive_response:
                            return executive_response["content"]

                # Fallback: construct response from agent results
                agent_results = results.get("agent_results", {})
                if "executive" in agent_results:
                    executive_result = agent_results["executive"]
                    if hasattr(executive_result, "content"):
                        return executive_result.content
                    elif isinstance(executive_result, str):
                        return executive_result
                    elif isinstance(executive_result, dict):
                        # Check for executive_strategy key (from formulate_pricing_strategy)
                        if "executive_strategy" in executive_result:
                            return executive_result["executive_strategy"]
                        elif "content" in executive_result:
                            return executive_result["content"]

                # Final fallback: create a summary response
                successful_agents = results.get("successful_agents", [])
                if successful_agents:
                    return f"""## Pricing Strategy Analysis Complete ✅

**Analysis Summary:**
Our team of {len(successful_agents)} agents has completed a comprehensive pricing strategy analysis.

**Participating UnifiedAgents:** {', '.join(successful_agents)}

**Key Findings:**
- Market analysis completed by our Market UnifiedAgent
- Content positioning reviewed by our Content UnifiedAgent
- Strategic recommendations formulated by our Executive UnifiedAgent

The detailed analysis has been processed and our recommendations are ready for implementation.

*For specific details, please refer to the individual agent analyses in your dashboard.*"""

            # Handle other workflow types
            elif workflow.workflow_type == "market_research":
                if "research_insights" in workflow.context:
                    return workflow.context["research_insights"]

            elif workflow.workflow_type == "listing_optimization":
                if "optimization_recommendations" in workflow.context:
                    return workflow.context["optimization_recommendations"]

            # Generic fallback
            return f"Workflow '{workflow.workflow_type}' completed successfully with {len(workflow.participating_agents)} agents."

        except Exception as e:
            logger.error(f"Error extracting final response content: {e}")
            return f"Workflow '{workflow.workflow_type}' completed successfully."

    async def _notify_handoff_status(
        self, handoff: UnifiedAgentHandoff, user_id: Optional[str] = None
    ):
        """Notify about handoff status via WebSocket."""
        try:
            message = {"type": "agent_handoff_complete", "data": handoff.to_dict()}

            if user_id:
                await websocket_manager.send_to_user(user_id, message)
            else:
                await websocket_manager.broadcast(message)

        except Exception as e:
            logger.error(f"Error notifying handoff status: {e}")

    async def _execute_pricing_strategy_workflow(
        self, workflow: UnifiedAgentWorkflow
    ) -> Dict[str, Any]:
        """Execute a pricing strategy workflow with retry mechanisms and graceful degradation."""
        # Get product data from workflow context
        product_data = workflow.context.get("product_data", {})
        user_message = workflow.context.get("user_message", "")

        # Track successful agent results for partial response capability
        agent_results = {}
        successful_agents = []
        failed_agents = []

        # Step 1: Market UnifiedAgent analyzes pricing landscape (with retry)
        try:
            market_agent = await self._get_agent_by_type("market")
            if market_agent:
                logger.info("Starting Market UnifiedAgent pricing analysis...")
                pricing_analysis = await self._execute_agent_request_with_retry(
                    market_agent.analyze_pricing_strategy,
                    product_data,
                    user_message,
                    max_retries=1,  # Reduced retries due to long timeouts
                    base_delay=2.0,
                )
                workflow.context["pricing_analysis"] = pricing_analysis
                agent_results["market"] = pricing_analysis
                successful_agents.append("market")
                logger.info("Market UnifiedAgent pricing analysis completed successfully")
        except Exception as e:
            logger.error(f"Market UnifiedAgent failed: {e}")
            failed_agents.append("market")
            agent_results["market"] = f"Failed: {str(e)}"

        # Step 2: Content UnifiedAgent analyzes product positioning (with retry)
        try:
            content_agent = await self._get_agent_by_type("content")
            if content_agent:
                logger.info("Starting Content UnifiedAgent positioning analysis...")
                positioning_analysis = await self._execute_agent_request_with_retry(
                    content_agent.analyze_product_positioning,
                    product_data,
                    max_retries=1,  # Reduced retries due to long timeouts
                    base_delay=2.0,
                )
                workflow.context["positioning_analysis"] = positioning_analysis
                agent_results["content"] = positioning_analysis
                successful_agents.append("content")
                logger.info("Content UnifiedAgent positioning analysis completed successfully")
        except Exception as e:
            logger.error(f"Content UnifiedAgent failed: {e}")
            failed_agents.append("content")
            agent_results["content"] = f"Failed: {str(e)}"

        # Step 3: Executive UnifiedAgent formulates final pricing strategy (with retry)
        try:
            executive_agent = await self._get_agent_by_type("executive")
            if executive_agent:
                logger.info("Starting Executive UnifiedAgent strategy formulation...")
                pricing_strategy = await self._execute_agent_request_with_retry(
                    executive_agent.formulate_pricing_strategy,
                    workflow.context,
                    max_retries=1,  # Reduced retries due to long timeouts
                    base_delay=2.0,
                )
                workflow.context["final_pricing_strategy"] = pricing_strategy
                agent_results["executive"] = pricing_strategy
                successful_agents.append("executive")
                logger.info(
                    "Executive UnifiedAgent strategy formulation completed successfully"
                )
        except Exception as e:
            logger.error(f"Executive UnifiedAgent failed: {e}")
            failed_agents.append("executive")
            agent_results["executive"] = f"Failed: {str(e)}"

        # Determine workflow status based on results
        if successful_agents:
            status = "completed" if not failed_agents else "partial_success"
            logger.info(
                f"Pricing strategy workflow {status}: {len(successful_agents)} successful, {len(failed_agents)} failed"
            )

            return {
                "workflow_type": "pricing_strategy",
                "status": status,
                "results": workflow.context,
                "agent_results": agent_results,
                "successful_agents": successful_agents,
                "failed_agents": failed_agents,
                "agents_involved": len(successful_agents),
            }
        else:
            # Complete failure
            logger.error("All agents failed in pricing strategy workflow")
            return {
                "workflow_type": "pricing_strategy",
                "status": "failed",
                "error": "All agents failed to complete their tasks",
                "agent_results": agent_results,
                "failed_agents": failed_agents,
            }

    async def _execute_market_research_workflow(
        self, workflow: UnifiedAgentWorkflow
    ) -> Dict[str, Any]:
        """Execute a market research workflow."""
        try:
            # Get research parameters from workflow context
            research_topic = workflow.context.get("user_message", "")
            research_scope = workflow.context.get("research_scope", "general")

            # Step 1: Market UnifiedAgent conducts primary research
            market_agent = await self._get_agent_by_type("market")
            if market_agent:
                market_research = await market_agent.conduct_market_research(
                    research_topic, research_scope
                )
                workflow.context["market_research"] = market_research

            # Step 2: Content UnifiedAgent analyzes content trends
            content_agent = await self._get_agent_by_type("content")
            if content_agent:
                content_trends = await content_agent.analyze_content_trends(
                    research_topic
                )
                workflow.context["content_trends"] = content_trends

            # Step 3: Executive UnifiedAgent synthesizes insights
            executive_agent = await self._get_agent_by_type("executive")
            if executive_agent:
                research_insights = await executive_agent.synthesize_research_insights(
                    workflow.context
                )
                workflow.context["research_insights"] = research_insights

            return {
                "workflow_type": "market_research",
                "status": "completed",
                "results": workflow.context,
                "agents_involved": len(
                    [a for a in [market_agent, content_agent, executive_agent] if a]
                ),
            }

        except Exception as e:
            logger.error(f"Error in market research workflow: {e}")
            return {
                "workflow_type": "market_research",
                "status": "failed",
                "error": str(e),
            }

    async def _execute_agent_request_with_retry(
        self,
        agent_method,
        *args,
        max_retries: int = 2,
        base_delay: float = 1.0,
        **kwargs,
    ) -> Any:
        """Execute an agent request with exponential backoff retry mechanism."""
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                result = await agent_method(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"UnifiedAgent request succeeded on attempt {attempt + 1}")
                return result

            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    delay = base_delay * (2**attempt)  # Exponential backoff
                    logger.warning(
                        f"UnifiedAgent request failed on attempt {attempt + 1}, retrying in {delay}s: {str(e)}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"UnifiedAgent request failed after {max_retries + 1} attempts: {str(e)}"
                    )

        # If all retries failed, raise the last exception
        raise last_exception


# Global orchestration service instance
orchestration_service = UnifiedAgentOrchestrationService()
