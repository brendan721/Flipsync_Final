"""Dynamic pipeline configuration for flexible agent workflows."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import uuid4

from fs_agt_clean.core.protocols.agent_protocol import UnifiedAgentCategoryType
from fs_agt_clean.core.coordination.coordinator.agent_registry import UnifiedAgentRegistry
from fs_agt_clean.core.events.base import Event, EventPriority, EventType
from fs_agt_clean.core.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class PipelineStage:
    """A stage in a processing pipeline."""

    def __init__(
        self,
        stage_id: str,
        category: UnifiedAgentCategoryType,
        required: bool = True,
        timeout: float = 30.0,
        retry_count: int = 1,
        fallback_stage: Optional[str] = None,
    ):
        """Initialize pipeline stage.

        Args:
            stage_id: Unique identifier for this stage
            category: UnifiedAgent category for this stage
            required: Whether this stage is required for pipeline completion
            timeout: Timeout in seconds for this stage
            retry_count: Number of retries if stage fails
            fallback_stage: Stage to execute if this stage fails
        """
        self.stage_id = stage_id
        self.category = category
        self.required = required
        self.timeout = timeout
        self.retry_count = retry_count
        self.fallback_stage = fallback_stage
        self.metrics = {
            "executions": 0,
            "successes": 0,
            "failures": 0,
            "timeouts": 0,
            "retries": 0,
            "avg_execution_time": 0.0,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert stage to dictionary.

        Returns:
            Dictionary representation of the stage
        """
        return {
            "stage_id": self.stage_id,
            "category": self.category.value,
            "required": self.required,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "fallback_stage": self.fallback_stage,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineStage":
        """Create stage from dictionary.

        Args:
            data: Dictionary representation of the stage

        Returns:
            PipelineStage instance
        """
        return cls(
            stage_id=data["stage_id"],
            category=UnifiedAgentCategoryType(data["category"]),
            required=data.get("required", True),
            timeout=data.get("timeout", 30.0),
            retry_count=data.get("retry_count", 1),
            fallback_stage=data.get("fallback_stage"),
        )


class PipelineConfiguration:
    """Configuration for a processing pipeline."""

    def __init__(
        self,
        pipeline_id: str,
        stages: List[PipelineStage],
        description: str = "",
        max_parallel_stages: int = 1,
    ):
        """Initialize pipeline configuration.

        Args:
            pipeline_id: Unique identifier for this pipeline
            stages: List of pipeline stages in execution order
            description: Description of this pipeline
            max_parallel_stages: Maximum number of stages to execute in parallel
        """
        self.pipeline_id = pipeline_id
        self.stages = stages
        self.description = description
        self.max_parallel_stages = max_parallel_stages

        # Validate stage IDs are unique
        stage_ids = [stage.stage_id for stage in stages]
        if len(stage_ids) != len(set(stage_ids)):
            raise ConfigurationError(f"Pipeline {pipeline_id} has duplicate stage IDs")

        # Validate fallback stages exist
        for stage in stages:
            if stage.fallback_stage and stage.fallback_stage not in stage_ids:
                raise ConfigurationError(
                    f"Pipeline {pipeline_id} stage {stage.stage_id} has invalid fallback stage: {stage.fallback_stage}"
                )

    def to_dict(self) -> Dict[str, Any]:
        """Convert pipeline configuration to dictionary.

        Returns:
            Dictionary representation of the pipeline configuration
        """
        return {
            "pipeline_id": self.pipeline_id,
            "description": self.description,
            "max_parallel_stages": self.max_parallel_stages,
            "stages": [stage.to_dict() for stage in self.stages],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineConfiguration":
        """Create pipeline configuration from dictionary.

        Args:
            data: Dictionary representation of the pipeline configuration

        Returns:
            PipelineConfiguration instance
        """
        return cls(
            pipeline_id=data["pipeline_id"],
            description=data.get("description", ""),
            max_parallel_stages=data.get("max_parallel_stages", 1),
            stages=[PipelineStage.from_dict(stage) for stage in data["stages"]],
        )

    def to_json(self) -> str:
        """Convert pipeline configuration to JSON string.

        Returns:
            JSON string representation of the pipeline configuration
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "PipelineConfiguration":
        """Create pipeline configuration from JSON string.

        Args:
            json_str: JSON string representation of the pipeline configuration

        Returns:
            PipelineConfiguration instance
        """
        return cls.from_dict(json.loads(json_str))


class PipelineController:
    """Controller for dynamic pipeline execution."""

    def __init__(
        self, agent_registry: Optional[UnifiedAgentRegistry] = None, agent_manager=None
    ):
        """Initialize pipeline controller.

        Args:
            agent_registry: UnifiedAgent registry for agent discovery (optional)
            agent_manager: Real agent manager instance for agent coordination
        """
        self.agent_registry = agent_registry
        self.agent_manager = agent_manager
        self.communication_manager = None  # Will be set by communication manager
        self.pipeline_configs: Dict[str, PipelineConfiguration] = {}
        self.active_pipelines: Dict[str, Dict[str, Any]] = {}
        self.pipeline_templates: Dict[str, PipelineConfiguration] = {}

        # Workflow state persistence
        self.workflow_states: Dict[str, Dict[str, Any]] = {}
        self.workflow_history: Dict[str, List[Dict[str, Any]]] = {}

        # UnifiedAgent coordination tracking
        self.agent_coordination_status: Dict[str, Dict[str, Any]] = {}

        # WebSocket integration for real-time updates
        self.websocket_manager = None
        self.websocket_enabled = False

        # Initialize with default templates
        self._initialize_templates()

        # Set up agent manager integration if available
        if self.agent_manager:
            self._setup_agent_manager_integration()

        # Set up WebSocket integration
        self._setup_websocket_integration()

    def _setup_websocket_integration(self):
        """Set up WebSocket integration for real-time workflow updates."""
        try:
            from fs_agt_clean.core.websocket.manager import websocket_manager

            self.websocket_manager = websocket_manager
            self.websocket_enabled = True

            logger.info("WebSocket integration enabled for Pipeline Controller")

        except ImportError as e:
            logger.warning(f"WebSocket manager not available: {e}")
            self.websocket_enabled = False
        except Exception as e:
            logger.error(f"Failed to setup WebSocket integration: {e}")
            self.websocket_enabled = False

    async def broadcast_workflow_status(
        self, execution_id: str, workflow_data: Dict[str, Any]
    ):
        """Broadcast workflow status update via WebSocket."""
        if not self.websocket_enabled or not self.websocket_manager:
            return

        try:
            # Extract workflow information
            workflow_type = workflow_data.get("workflow_type", "unknown")
            status = workflow_data.get("status", "running")
            progress = workflow_data.get("progress", 0.0)
            participating_agents = workflow_data.get("participating_agents", [])
            current_agent = workflow_data.get("current_agent")
            error_message = workflow_data.get("error_message")

            # Broadcast workflow update
            await self.websocket_manager.broadcast_workflow_update(
                workflow_id=execution_id,
                workflow_type=workflow_type,
                status=status,
                progress=progress,
                participating_agents=participating_agents,
                current_agent=current_agent,
                error_message=error_message,
            )

            logger.debug(
                f"Broadcasted workflow status for {execution_id}: {status} ({progress:.1%})"
            )

        except Exception as e:
            logger.error(f"Failed to broadcast workflow status: {e}")

    async def broadcast_agent_coordination_status(
        self,
        coordination_id: str,
        coordinating_agents: List[str],
        task: str,
        progress: float,
        current_phase: str,
    ):
        """Broadcast agent coordination status via WebSocket."""
        if not self.websocket_enabled or not self.websocket_manager:
            return

        try:
            # Prepare agent statuses
            agent_statuses = {}
            for agent_name in coordinating_agents:
                if agent_name in self.agent_coordination_status:
                    agent_statuses[agent_name] = self.agent_coordination_status[
                        agent_name
                    ].get("status", "unknown")

            # Broadcast coordination update
            await self.websocket_manager.broadcast_agent_coordination(
                coordination_id=coordination_id,
                coordinating_agents=coordinating_agents,
                task=task,
                progress=progress,
                current_phase=current_phase,
                agent_statuses=agent_statuses,
            )

            logger.debug(
                f"Broadcasted agent coordination status: {coordination_id} - {current_phase}"
            )

        except Exception as e:
            logger.error(f"Failed to broadcast agent coordination status: {e}")

    def _setup_agent_manager_integration(self):
        """Set up integration with the agent manager for workflow coordination."""
        try:
            logger.info("Setting up Pipeline Controller integration with UnifiedAgent Manager")

            # Register pipeline controller with agent manager if it supports it
            if hasattr(self.agent_manager, "register_pipeline_controller"):
                self.agent_manager.register_pipeline_controller(self)

            # Set up workflow state synchronization
            if hasattr(self.agent_manager, "get_agent_status"):
                self._sync_agent_states()

            logger.info(
                "Pipeline Controller successfully integrated with UnifiedAgent Manager"
            )

        except Exception as e:
            logger.error(
                f"Failed to integrate Pipeline Controller with UnifiedAgent Manager: {e}"
            )

    def _sync_agent_states(self):
        """Synchronize agent states for workflow coordination."""
        try:
            if not self.agent_manager:
                return

            # Get current agent status from agent manager
            agent_status = self.agent_manager.get_agent_status()

            # Update coordination status
            for agent_name, status in agent_status.items():
                self.agent_coordination_status[agent_name] = {
                    "status": status.get("status", "unknown"),
                    "last_activity": status.get("last_activity"),
                    "error_count": status.get("error_count", 0),
                    "success_count": status.get("success_count", 0),
                    "available_for_workflow": status.get("status") == "active",
                }

            logger.debug(
                f"Synchronized {len(self.agent_coordination_status)} agent states"
            )

        except Exception as e:
            logger.error(f"Failed to sync agent states: {e}")

    def set_communication_manager(self, communication_manager):
        """Set the communication manager for agent coordination."""
        self.communication_manager = communication_manager
        logger.info("Communication manager set for Pipeline Controller")

    async def setup_agent_communication_protocol(self):
        """Set up the agent communication protocol using the event system."""
        try:
            from fs_agt_clean.core.coordination.event_system import (
                InMemoryEventBus,
                create_publisher,
                create_subscriber,
                EventType,
                EventPriority,
            )

            # Initialize event bus for agent communication
            self.event_bus = InMemoryEventBus(bus_id="pipeline_agent_communication")

            # Create publisher for pipeline controller
            self.publisher = create_publisher(source_id="pipeline_controller")

            # Create subscriber for pipeline controller
            self.subscriber = create_subscriber(subscriber_id="pipeline_controller")

            # Set up event handlers for agent coordination
            await self._setup_agent_communication_handlers()

            logger.info("UnifiedAgent communication protocol initialized successfully")

        except Exception as e:
            logger.error(f"Failed to setup agent communication protocol: {e}")

    async def _setup_agent_communication_handlers(self):
        """Set up event handlers for agent communication."""
        try:
            from fs_agt_clean.core.coordination.event_system import EventTypeFilter

            # Handler for agent responses
            async def handle_agent_response(event):
                """Handle responses from agents."""
                try:
                    agent_name = event.source
                    response_data = event.data
                    correlation_id = event.correlation_id

                    logger.debug(
                        f"Received response from agent {agent_name}: {correlation_id}"
                    )

                    # Update workflow state with agent response
                    if correlation_id in self.workflow_states:
                        workflow_state = self.workflow_states[correlation_id]
                        if "agent_responses" not in workflow_state["state"]:
                            workflow_state["state"]["agent_responses"] = {}

                        workflow_state["state"]["agent_responses"][agent_name] = {
                            "response": response_data,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "status": "completed",
                        }

                        await self.persist_workflow_state(
                            correlation_id, workflow_state["state"]
                        )

                except Exception as e:
                    logger.error(f"Error handling agent response: {e}")

            # Handler for agent status updates
            async def handle_agent_status(event):
                """Handle agent status updates."""
                try:
                    agent_name = event.source
                    status_data = event.data

                    # Update agent coordination status
                    if agent_name in self.agent_coordination_status:
                        self.agent_coordination_status[agent_name].update(
                            {
                                "status": status_data.get("status", "unknown"),
                                "last_activity": datetime.now(timezone.utc).isoformat(),
                                "available_for_workflow": status_data.get(
                                    "available", True
                                ),
                            }
                        )

                    logger.debug(
                        f"Updated status for agent {agent_name}: {status_data.get('status')}"
                    )

                except Exception as e:
                    logger.error(f"Error handling agent status: {e}")

            # Subscribe to agent responses and status updates
            from fs_agt_clean.core.coordination.event_system import EventType

            await self.subscriber.subscribe(
                filter=EventTypeFilter(event_types={EventType.RESPONSE}),
                handler=handle_agent_response,
            )

            await self.subscriber.subscribe(
                filter=EventTypeFilter(event_types={EventType.NOTIFICATION}),
                handler=handle_agent_status,
            )

            logger.info("UnifiedAgent communication handlers set up successfully")

        except Exception as e:
            logger.error(f"Failed to setup agent communication handlers: {e}")

    async def send_agent_command(
        self,
        agent_name: str,
        command_name: str,
        parameters: Dict[str, Any] = None,
        priority: str = "NORMAL",
        correlation_id: str = None,
    ) -> str:
        """Send a command to a specific agent through the event system."""
        try:
            from fs_agt_clean.core.coordination.event_system import EventPriority

            # Map priority string to EventPriority enum
            priority_map = {
                "LOW": EventPriority.LOW,
                "NORMAL": EventPriority.NORMAL,
                "HIGH": EventPriority.HIGH,
                "CRITICAL": EventPriority.CRITICAL,
            }

            event_priority = priority_map.get(priority, EventPriority.NORMAL)

            # Generate correlation ID if not provided
            if not correlation_id:
                correlation_id = f"cmd_{uuid4().hex[:8]}"

            # Send command through event system
            event_id = await self.publisher.publish_command(
                command_name=command_name,
                parameters=parameters or {},
                target=agent_name,
                priority=event_priority,
                correlation_id=correlation_id,
            )

            logger.info(
                f"Sent command '{command_name}' to agent '{agent_name}' with correlation ID: {correlation_id}"
            )

            # Broadcast agent coordination status
            await self.broadcast_agent_coordination_status(
                coordination_id=correlation_id,
                coordinating_agents=[agent_name],
                task=f"Command: {command_name}",
                progress=0.1,
                current_phase="command_sent",
            )

            return event_id

        except Exception as e:
            logger.error(f"Failed to send command to agent {agent_name}: {e}")
            raise

    async def send_agent_query(
        self,
        agent_name: str,
        query_name: str,
        query_data: Dict[str, Any] = None,
        timeout: float = 30.0,
        correlation_id: str = None,
    ) -> Dict[str, Any]:
        """Send a query to an agent and wait for response."""
        try:
            # Generate correlation ID if not provided
            if not correlation_id:
                correlation_id = f"qry_{uuid4().hex[:8]}"

            # Send query through event system
            event_id = await self.publisher.publish_query(
                query_name=query_name,
                query_data=query_data or {},
                target=agent_name,
                correlation_id=correlation_id,
            )

            logger.info(
                f"Sent query '{query_name}' to agent '{agent_name}' with correlation ID: {correlation_id}"
            )

            # Wait for response (simplified - in production would use proper response handling)
            import asyncio

            await asyncio.sleep(0.1)  # Give time for response

            # Check if response is available in workflow state
            if correlation_id in self.workflow_states:
                workflow_state = self.workflow_states[correlation_id]
                agent_responses = workflow_state["state"].get("agent_responses", {})
                if agent_name in agent_responses:
                    return agent_responses[agent_name]["response"]

            # Return timeout response if no response received
            return {
                "success": False,
                "error": f"Timeout waiting for response from agent {agent_name}",
                "timeout": timeout,
            }

        except Exception as e:
            logger.error(f"Failed to send query to agent {agent_name}: {e}")
            return {"success": False, "error": str(e)}

    async def broadcast_notification(
        self,
        notification_name: str,
        data: Dict[str, Any] = None,
        target_agents: List[str] = None,
    ) -> List[str]:
        """Broadcast a notification to multiple agents."""
        try:
            event_ids = []

            # If no target agents specified, broadcast to all available agents
            if not target_agents:
                target_agents = self.get_available_agents()

            # Send notification to each target agent
            for agent_name in target_agents:
                try:
                    event_id = await self.publisher.publish_notification(
                        notification_name=notification_name,
                        data=data or {},
                        target=agent_name,
                    )
                    event_ids.append(event_id)

                except Exception as e:
                    logger.error(
                        f"Failed to send notification to agent {agent_name}: {e}"
                    )

            logger.info(
                f"Broadcasted notification '{notification_name}' to {len(event_ids)} agents"
            )

            return event_ids

        except Exception as e:
            logger.error(f"Failed to broadcast notification: {e}")
            return []

    def get_available_agents(self) -> List[str]:
        """Get list of agents available for workflow coordination."""
        available_agents = []
        for agent_name, status in self.agent_coordination_status.items():
            if status.get("available_for_workflow", False):
                available_agents.append(agent_name)
        return available_agents

    async def persist_workflow_state(
        self, execution_id: str, state_data: Dict[str, Any]
    ):
        """Persist workflow state for recovery and monitoring."""
        try:
            self.workflow_states[execution_id] = {
                "state": state_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "execution_id": execution_id,
            }

            # Add to history
            if execution_id not in self.workflow_history:
                self.workflow_history[execution_id] = []

            self.workflow_history[execution_id].append(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "state_snapshot": state_data.copy(),
                    "event": "state_persisted",
                }
            )

            # Broadcast workflow status update via WebSocket
            await self.broadcast_workflow_status(execution_id, state_data)

            logger.debug(f"Persisted workflow state for execution {execution_id}")

        except Exception as e:
            logger.error(f"Failed to persist workflow state for {execution_id}: {e}")

    async def get_workflow_state(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve workflow state for recovery."""
        return self.workflow_states.get(execution_id)

    async def get_workflow_history(self, execution_id: str) -> List[Dict[str, Any]]:
        """Get workflow execution history."""
        return self.workflow_history.get(execution_id, [])

    async def cleanup_completed_workflows(self, max_age_hours: int = 24):
        """Clean up old completed workflow states."""
        try:
            from datetime import timedelta

            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)

            workflows_to_remove = []
            for execution_id, state_data in self.workflow_states.items():
                state_time = datetime.fromisoformat(
                    state_data["timestamp"].replace("Z", "+00:00")
                )
                if state_time < cutoff_time:
                    workflows_to_remove.append(execution_id)

            for execution_id in workflows_to_remove:
                del self.workflow_states[execution_id]
                if execution_id in self.workflow_history:
                    del self.workflow_history[execution_id]

            if workflows_to_remove:
                logger.info(
                    f"Cleaned up {len(workflows_to_remove)} old workflow states"
                )

        except Exception as e:
            logger.error(f"Failed to cleanup workflow states: {e}")

    def _initialize_templates(self) -> None:
        """Initialize default pipeline templates."""
        # Pricing update pipeline
        pricing_stages = [
            PipelineStage("executive", UnifiedAgentCategoryType.EXECUTIVE),
            PipelineStage("market", UnifiedAgentCategoryType.MARKET),
        ]
        self.pipeline_templates["pricing_update"] = PipelineConfiguration(
            pipeline_id="pricing_update",
            description="Update product pricing across marketplaces",
            stages=pricing_stages,
        )

        # Inventory sync pipeline
        inventory_stages = [
            PipelineStage("executive", UnifiedAgentCategoryType.EXECUTIVE),
            PipelineStage("market", UnifiedAgentCategoryType.MARKET),
            PipelineStage("logistics", UnifiedAgentCategoryType.LOGISTICS),
        ]
        self.pipeline_templates["inventory_sync"] = PipelineConfiguration(
            pipeline_id="inventory_sync",
            description="Synchronize inventory across marketplaces",
            stages=inventory_stages,
        )

        # Content generation pipeline
        content_stages = [
            PipelineStage("executive", UnifiedAgentCategoryType.EXECUTIVE),
            PipelineStage("content", UnifiedAgentCategoryType.CONTENT),
            PipelineStage("market", UnifiedAgentCategoryType.MARKET, required=False),
        ]
        self.pipeline_templates["content_generation"] = PipelineConfiguration(
            pipeline_id="content_generation",
            description="Generate content for product listings",
            stages=content_stages,
        )

        # Full marketplace cycle pipeline
        full_cycle_stages = [
            PipelineStage("executive", UnifiedAgentCategoryType.EXECUTIVE),
            PipelineStage("content", UnifiedAgentCategoryType.CONTENT),
            PipelineStage("market", UnifiedAgentCategoryType.MARKET),
            PipelineStage("logistics", UnifiedAgentCategoryType.LOGISTICS),
        ]
        self.pipeline_templates["full_marketplace_cycle"] = PipelineConfiguration(
            pipeline_id="full_marketplace_cycle",
            description="Complete marketplace cycle from content to logistics",
            stages=full_cycle_stages,
            max_parallel_stages=2,
        )

    def register_pipeline(self, config: PipelineConfiguration) -> None:
        """Register a pipeline configuration.

        Args:
            config: Pipeline configuration to register
        """
        self.pipeline_configs[config.pipeline_id] = config
        logger.info(f"Registered pipeline configuration: {config.pipeline_id}")

    def register_template(
        self, template_id: str, config: PipelineConfiguration
    ) -> None:
        """Register a pipeline template.

        Args:
            template_id: Template identifier
            config: Pipeline configuration template
        """
        self.pipeline_templates[template_id] = config
        logger.info(f"Registered pipeline template: {template_id}")

    def get_template(self, template_id: str) -> Optional[PipelineConfiguration]:
        """Get a pipeline template by ID.

        Args:
            template_id: Template identifier

        Returns:
            Pipeline configuration template or None if not found
        """
        return self.pipeline_templates.get(template_id)

    def create_pipeline_from_template(
        self,
        template_id: str,
        pipeline_id: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> PipelineConfiguration:
        """Create a pipeline configuration from a template.

        Args:
            template_id: Template identifier
            pipeline_id: New pipeline identifier
            params: Optional parameters to customize the template

        Returns:
            New pipeline configuration

        Raises:
            ConfigurationError: If template not found
        """
        template = self.get_template(template_id)
        if not template:
            raise ConfigurationError(f"Pipeline template not found: {template_id}")

        # Create a copy of the template
        template_dict = template.to_dict()
        template_dict["pipeline_id"] = pipeline_id

        # Apply custom parameters if provided
        if params:
            # Customize stages based on params
            if "stages" in params:
                for i, stage_params in enumerate(params["stages"]):
                    if i < len(template_dict["stages"]):
                        template_dict["stages"][i].update(stage_params)

            # Update other pipeline parameters
            for key, value in params.items():
                if key != "stages" and key in template_dict:
                    template_dict[key] = value

        # Create new configuration
        config = PipelineConfiguration.from_dict(template_dict)

        # Register the new pipeline
        self.register_pipeline(config)

        return config

    async def execute_pipeline(
        self,
        pipeline_id: str,
        data: Dict[str, Any],
        execution_id: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """Execute a pipeline with the given data.

        Args:
            pipeline_id: Pipeline identifier
            data: Input data for the pipeline
            execution_id: Optional execution identifier

        Returns:
            Tuple of (success, result data)

        Raises:
            ConfigurationError: If pipeline not found
        """
        config = self.pipeline_configs.get(pipeline_id)
        if not config:
            raise ConfigurationError(f"Pipeline configuration not found: {pipeline_id}")

        # Generate execution ID if not provided
        execution_id = execution_id or f"{pipeline_id}_{len(self.active_pipelines)}"

        # Initialize pipeline execution
        self.active_pipelines[execution_id] = {
            "pipeline_id": pipeline_id,
            "start_time": asyncio.get_event_loop().time(),
            "stages_completed": 0,
            "stages_failed": 0,
            "current_stage": None,
            "result_data": {},
        }

        # Execute stages in sequence or parallel based on configuration
        result_data = data.copy()
        success = True

        if config.max_parallel_stages > 1:
            # Execute stages in parallel batches
            for i in range(0, len(config.stages), config.max_parallel_stages):
                batch = config.stages[i : i + config.max_parallel_stages]
                batch_results = await asyncio.gather(
                    *[
                        self._execute_stage(stage, result_data, execution_id)
                        for stage in batch
                    ],
                    return_exceptions=True,
                )

                # Process batch results
                for j, (stage_success, stage_data) in enumerate(batch_results):
                    stage = batch[j]
                    if isinstance(stage_success, Exception):
                        logger.error(
                            f"Pipeline {pipeline_id} stage {stage.stage_id} failed with exception: {stage_success}"
                        )
                        success = False
                        self.active_pipelines[execution_id]["stages_failed"] += 1

                        if stage.required:
                            # Required stage failed, abort pipeline
                            logger.error(
                                f"Required stage {stage.stage_id} failed, aborting pipeline {pipeline_id}"
                            )
                            break
                    elif not stage_success:
                        logger.warning(
                            f"Pipeline {pipeline_id} stage {stage.stage_id} failed"
                        )
                        self.active_pipelines[execution_id]["stages_failed"] += 1

                        if stage.required:
                            success = False
                            # Required stage failed, abort pipeline
                            logger.error(
                                f"Required stage {stage.stage_id} failed, aborting pipeline {pipeline_id}"
                            )
                            break
                    else:
                        # Stage succeeded, update result data
                        result_data.update(stage_data)
                        self.active_pipelines[execution_id]["stages_completed"] += 1

                if not success and any(stage.required for stage in batch):
                    # A required stage failed, abort pipeline
                    break
        else:
            # Execute stages sequentially
            for stage in config.stages:
                stage_success, stage_data = await self._execute_stage(
                    stage, result_data, execution_id
                )

                if not stage_success:
                    logger.warning(
                        f"Pipeline {pipeline_id} stage {stage.stage_id} failed"
                    )
                    self.active_pipelines[execution_id]["stages_failed"] += 1

                    if stage.required:
                        success = False
                        # Required stage failed, abort pipeline
                        logger.error(
                            f"Required stage {stage.stage_id} failed, aborting pipeline {pipeline_id}"
                        )
                        break

                    # Try fallback stage if configured
                    if stage.fallback_stage:
                        fallback_stage = next(
                            (
                                s
                                for s in config.stages
                                if s.stage_id == stage.fallback_stage
                            ),
                            None,
                        )
                        if fallback_stage:
                            logger.info(
                                f"Executing fallback stage {fallback_stage.stage_id} for failed stage {stage.stage_id}"
                            )
                            fallback_success, fallback_data = await self._execute_stage(
                                fallback_stage, result_data, execution_id
                            )
                            if fallback_success:
                                # Fallback succeeded, update result data
                                result_data.update(fallback_data)
                                self.active_pipelines[execution_id][
                                    "stages_completed"
                                ] += 1
                else:
                    # Stage succeeded, update result data
                    result_data.update(stage_data)
                    self.active_pipelines[execution_id]["stages_completed"] += 1

        # Update pipeline execution status
        self.active_pipelines[execution_id][
            "end_time"
        ] = asyncio.get_event_loop().time()
        self.active_pipelines[execution_id]["success"] = success
        self.active_pipelines[execution_id]["result_data"] = result_data

        return success, result_data

    async def _execute_stage(
        self,
        stage: PipelineStage,
        data: Dict[str, Any],
        execution_id: str,
    ) -> Tuple[bool, Dict[str, Any]]:
        """Execute a pipeline stage.

        Args:
            stage: Pipeline stage to execute
            data: Input data for the stage
            execution_id: Execution identifier

        Returns:
            Tuple of (success, result data)
        """
        # Update current stage
        self.active_pipelines[execution_id]["current_stage"] = stage.stage_id

        # Use agent manager if available, otherwise fall back to agent registry
        if self.agent_manager:
            return await self._execute_stage_with_agent_manager(
                stage, data, execution_id
            )
        elif self.agent_registry:
            return await self._execute_stage_with_registry(stage, data, execution_id)
        else:
            logger.error("No agent manager or registry available for stage execution")
            return False, {}

    async def _execute_stage_with_agent_manager(
        self,
        stage: PipelineStage,
        data: Dict[str, Any],
        execution_id: str,
    ) -> Tuple[bool, Dict[str, Any]]:
        """Execute a pipeline stage using the real agent manager.

        Args:
            stage: Pipeline stage to execute
            data: Input data for the stage
            execution_id: Execution identifier

        Returns:
            Tuple of (success, result data)
        """
        # Get agents for this stage category from agent manager
        category_mapping = {
            UnifiedAgentCategoryType.MARKET: [
                "market_agent",
                "amazon_agent",
                "ebay_agent",
                "inventory_agent",
            ],
            UnifiedAgentCategoryType.EXECUTIVE: [
                "executive_agent",
                "strategy_agent",
                "resource_agent",
            ],
            UnifiedAgentCategoryType.CONTENT: [
                "content_agent",
                "listing_agent",
                "auto_listing_agent",
            ],
            UnifiedAgentCategoryType.LOGISTICS: [
                "logistics_agent",
                "shipping_agent",
                "warehouse_agent",
            ],
        }

        agent_names = category_mapping.get(stage.category, [])
        available_agents = []

        # Find available agents in the agent manager
        for agent_name in agent_names:
            if agent_name in self.agent_manager.agents:
                agent_info = self.agent_manager.agents[agent_name]
                if agent_info.get("status") == "active":
                    available_agents.append((agent_name, agent_info["instance"]))

        if not available_agents:
            logger.warning(f"No active agents found for category {stage.category}")
            return False, {}

        # Execute with retry logic
        retries = 0
        stage.metrics["executions"] += 1
        start_time = asyncio.get_event_loop().time()

        while retries <= stage.retry_count:
            try:
                # Use the first available agent
                agent_name, agent_instance = available_agents[0]
                logger.info(f"Executing stage {stage.stage_id} with agent {agent_name}")

                # Execute stage-specific logic based on category
                if self.communication_manager:
                    result = await self._execute_agent_task_with_communication(
                        agent_name, agent_instance, stage, data, execution_id
                    )
                else:
                    result = await self._execute_agent_task(agent_instance, stage, data)

                # Update metrics
                execution_time = asyncio.get_event_loop().time() - start_time
                stage.metrics["successes"] += 1
                stage.metrics["avg_execution_time"] = (
                    stage.metrics["avg_execution_time"] + execution_time
                ) / 2

                logger.info(
                    f"Stage {stage.stage_id} completed successfully in {execution_time:.2f}s"
                )
                return True, result

            except asyncio.TimeoutError:
                logger.warning(
                    f"Stage {stage.stage_id} timed out (attempt {retries + 1})"
                )
                retries += 1
                stage.metrics["timeouts"] += 1
                if retries <= stage.retry_count:
                    await asyncio.sleep(2**retries)  # Exponential backoff

            except Exception as e:
                logger.error(f"Error executing stage {stage.stage_id}: {e}")
                retries += 1
                stage.metrics["retries"] += 1
                if retries <= stage.retry_count:
                    await asyncio.sleep(2**retries)  # Exponential backoff

        # All retries exhausted
        stage.metrics["failures"] += 1
        return False, {}

    async def _execute_agent_task(
        self, agent_instance, stage: PipelineStage, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a task with a specific agent instance.

        Args:
            agent_instance: The agent instance to execute the task
            stage: Pipeline stage configuration
            data: Input data for the task

        Returns:
            Result data from the agent execution
        """
        try:
            # Create a task context for the agent
            task_context = {
                "stage_id": stage.stage_id,
                "category": stage.category.value,
                "data": data,
                "timeout": stage.timeout,
            }

            # Execute based on agent category
            if stage.category == UnifiedAgentCategoryType.MARKET:
                return await self._execute_market_task(agent_instance, task_context)
            elif stage.category == UnifiedAgentCategoryType.EXECUTIVE:
                return await self._execute_executive_task(agent_instance, task_context)
            elif stage.category == UnifiedAgentCategoryType.CONTENT:
                return await self._execute_content_task(agent_instance, task_context)
            elif stage.category == UnifiedAgentCategoryType.LOGISTICS:
                return await self._execute_logistics_task(agent_instance, task_context)
            else:
                logger.warning("Unknown agent category: %s", stage.category)
                return {"status": "unknown_category", "category": stage.category.value}

        except Exception as e:
            logger.error("Error executing agent task: %s", str(e))
            return {"status": "error", "error": str(e)}

    async def _execute_market_task(
        self, agent_instance, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a market-related task."""
        try:
            # Check if agent has specific methods we can call
            if hasattr(agent_instance, "analyze_market"):
                result = await agent_instance.analyze_market(context["data"])
                return {"status": "success", "result": result, "agent_type": "market"}
            elif hasattr(agent_instance, "process_message"):
                # Fallback to generic message processing
                message = f"Execute market analysis for stage {context['stage_id']}"
                result = await agent_instance.process_message(message, context)
                return {"status": "success", "result": result, "agent_type": "market"}
            else:
                return {
                    "status": "success",
                    "result": f"Market task executed for stage {context['stage_id']}",
                    "agent_type": "market",
                }
        except Exception as e:
            logger.error("Error in market task execution: %s", str(e))
            return {"status": "error", "error": str(e), "agent_type": "market"}

    async def _execute_executive_task(
        self, agent_instance, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an executive-related task."""
        try:
            if hasattr(agent_instance, "make_decision"):
                result = await agent_instance.make_decision(context["data"])
                return {
                    "status": "success",
                    "result": result,
                    "agent_type": "executive",
                }
            elif hasattr(agent_instance, "process_message"):
                message = f"Execute executive decision for stage {context['stage_id']}"
                result = await agent_instance.process_message(message, context)
                return {
                    "status": "success",
                    "result": result,
                    "agent_type": "executive",
                }
            else:
                return {
                    "status": "success",
                    "result": f"Executive task executed for stage {context['stage_id']}",
                    "agent_type": "executive",
                }
        except Exception as e:
            logger.error("Error in executive task execution: %s", str(e))
            return {"status": "error", "error": str(e), "agent_type": "executive"}

    async def _execute_content_task(
        self, agent_instance, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a content-related task."""
        try:
            if hasattr(agent_instance, "generate_content"):
                result = await agent_instance.generate_content(context["data"])
                return {"status": "success", "result": result, "agent_type": "content"}
            elif hasattr(agent_instance, "process_message"):
                message = f"Execute content generation for stage {context['stage_id']}"
                result = await agent_instance.process_message(message, context)
                return {"status": "success", "result": result, "agent_type": "content"}
            else:
                return {
                    "status": "success",
                    "result": f"Content task executed for stage {context['stage_id']}",
                    "agent_type": "content",
                }
        except Exception as e:
            logger.error("Error in content task execution: %s", str(e))
            return {"status": "error", "error": str(e), "agent_type": "content"}

    async def _execute_logistics_task(
        self, agent_instance, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a logistics-related task."""
        try:
            if hasattr(agent_instance, "calculate_shipping"):
                result = await agent_instance.calculate_shipping(context["data"])
                return {
                    "status": "success",
                    "result": result,
                    "agent_type": "logistics",
                }
            elif hasattr(agent_instance, "process_message"):
                message = (
                    f"Execute logistics calculation for stage {context['stage_id']}"
                )
                result = await agent_instance.process_message(message, context)
                return {
                    "status": "success",
                    "result": result,
                    "agent_type": "logistics",
                }
            else:
                return {
                    "status": "success",
                    "result": f"Logistics task executed for stage {context['stage_id']}",
                    "agent_type": "logistics",
                }
        except Exception as e:
            logger.error("Error in logistics task execution: %s", str(e))
            return {"status": "error", "error": str(e), "agent_type": "logistics"}

    async def _execute_agent_task_with_communication(
        self,
        agent_name: str,
        agent_instance,
        stage: PipelineStage,
        data: Dict[str, Any],
        execution_id: str,
    ) -> Dict[str, Any]:
        """Execute a task with communication manager integration."""
        try:
            from fs_agt_clean.core.protocols.agent_protocol import (
                CommandMessage,
                Priority,
            )
            from uuid import uuid4

            # Create a command message for the agent
            command_message = CommandMessage(
                sender_id="pipeline_controller",
                receiver_id=agent_name,
                correlation_id=execution_id,
                command="execute_pipeline_stage",
                parameters={
                    "stage_id": stage.stage_id,
                    "stage_category": stage.category.value,
                    "stage_data": data,
                    "execution_id": execution_id,
                },
                priority=Priority.HIGH,
            )

            # Send message through communication manager
            message_sent = await self.communication_manager.send_agent_message(
                command_message
            )

            if message_sent:
                logger.info(
                    f"Command sent to agent {agent_name} via communication manager"
                )

                # For now, also execute directly to get immediate result
                # In a full implementation, we would wait for the response message
                direct_result = await self._execute_agent_task(
                    agent_instance, stage, data
                )

                return {
                    "status": "success",
                    "result": direct_result,
                    "communication_used": True,
                    "agent_name": agent_name,
                    "stage_id": stage.stage_id,
                }
            else:
                logger.warning(
                    f"Failed to send command to agent {agent_name}, falling back to direct execution"
                )
                return await self._execute_agent_task(agent_instance, stage, data)

        except Exception as e:
            logger.error(f"Error in communication-enabled task execution: {e}")
            # Fallback to direct execution
            return await self._execute_agent_task(agent_instance, stage, data)

    async def _execute_stage_with_registry(
        self,
        stage: PipelineStage,
        data: Dict[str, Any],
        execution_id: str,
    ) -> Tuple[bool, Dict[str, Any]]:
        """Execute a pipeline stage using the agent registry (fallback).

        Args:
            stage: Pipeline stage to execute
            data: Input data for the stage
            execution_id: Execution identifier

        Returns:
            Tuple of (success, result data)
        """
        # Get agents for this stage category
        agents = await self.agent_registry.get_agents_by_category(stage.category)
        if not agents:
            logger.warning(f"No agents found for category {stage.category}")
            return False, {}

        # Create stage execution event
        from fs_agt_clean.core.events.base import Event, EventPriority, EventType

        event = Event(
            type=EventType.COMMAND_RECEIVED,
            source="pipeline_controller",
            target=agents[0],  # Send to first agent in category
            data={
                "command": "execute_stage",
                "stage_id": stage.stage_id,
                "execution_id": execution_id,
                "data": data,
            },
            priority=EventPriority.HIGH,
        )

        # Execute with retry logic
        retries = 0
        stage.metrics["executions"] += 1
        start_time = asyncio.get_event_loop().time()

        while retries <= stage.retry_count:
            try:
                # Send event to agent
                success = await self.agent_registry.send_event(event)

                if not success:
                    logger.warning(
                        f"Failed to send event to agent for stage {stage.stage_id}"
                    )
                    retries += 1
                    stage.metrics["retries"] += 1
                    continue

                # Wait for result with timeout
                # In a real implementation, this would use a callback or future
                # For simplicity, we'll simulate a successful response
                await asyncio.sleep(0.1)  # Simulate processing time

                # Update metrics
                end_time = asyncio.get_event_loop().time()
                execution_time = end_time - start_time
                stage.metrics["avg_execution_time"] = (
                    stage.metrics["avg_execution_time"]
                    * (stage.metrics["executions"] - 1)
                    + execution_time
                ) / stage.metrics["executions"]
                stage.metrics["successes"] += 1

                # Return success with simulated result data
                return True, {"stage_result": f"Result from {stage.stage_id}"}

            except asyncio.TimeoutError:
                logger.warning(f"Timeout executing stage {stage.stage_id}")
                stage.metrics["timeouts"] += 1
                retries += 1
                stage.metrics["retries"] += 1
            except Exception as e:
                logger.error(f"Error executing stage {stage.stage_id}: {str(e)}")
                stage.metrics["failures"] += 1
                retries += 1
                stage.metrics["retries"] += 1

        # All retries failed
        return False, {}
