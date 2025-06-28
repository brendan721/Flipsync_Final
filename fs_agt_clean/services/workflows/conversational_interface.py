"""
Conversational Interface Workflow for FlipSync.

This module implements the sophisticated multi-agent workflow for conversational interface
with intent recognition → agent routing → response aggregation coordination.

Workflow Steps:
1. Intent Recognition & Context Analysis (Communication UnifiedAgent)
2. Intelligent UnifiedAgent Routing & Selection (Executive UnifiedAgent)
3. Multi-UnifiedAgent Response Generation (Specialized UnifiedAgents)
4. Response Aggregation & Personalization (Content UnifiedAgent)
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fs_agt_clean.core.agents.real_agent_manager import RealUnifiedAgentManager
from fs_agt_clean.core.pipeline.controller import PipelineController
from fs_agt_clean.core.state_management.state_manager import StateManager
from fs_agt_clean.core.websocket.events import (
    EventType,
    WorkflowEvent,
    create_workflow_event,
)
from fs_agt_clean.services.agent_orchestration import (
    UnifiedAgentOrchestrationService,
    WorkflowStatus,
)

logger = logging.getLogger(__name__)


class ConversationMode(Enum):
    """Mode of conversation interaction."""

    SINGLE_QUERY = "single_query"
    MULTI_TURN = "multi_turn"
    WORKFLOW_GUIDED = "workflow_guided"
    CONTEXTUAL_ASSISTANCE = "contextual_assistance"


class ResponseStyle(Enum):
    """Style of response generation."""

    CONCISE = "concise"
    DETAILED = "detailed"
    TECHNICAL = "technical"
    BUSINESS_FOCUSED = "business_focused"


@dataclass
class ConversationalInterfaceRequest:
    """Request for conversational interface workflow."""

    user_message: str
    conversation_mode: ConversationMode = ConversationMode.SINGLE_QUERY
    response_style: ResponseStyle = ResponseStyle.BUSINESS_FOCUSED
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    user_context: Dict[str, Any] = field(default_factory=dict)
    personalization_preferences: Dict[str, Any] = field(default_factory=dict)
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None


@dataclass
class ConversationalInterfaceResult:
    """Result of conversational interface workflow."""

    workflow_id: str
    success: bool
    conversation_mode: ConversationMode
    intent_recognition_results: Dict[str, Any]
    agent_routing_results: Dict[str, Any]
    response_generation_results: Dict[str, Any]
    response_aggregation_results: Dict[str, Any]
    final_response: str
    confidence_score: float
    agents_consulted: List[str]
    personalization_applied: Dict[str, Any]
    follow_up_suggestions: List[str]
    error_message: Optional[str] = None
    execution_time_seconds: float = 0.0
    agents_involved: List[str] = field(default_factory=list)


class ConversationalInterfaceWorkflow:
    """
    Sophisticated Conversational Interface Workflow.

    Coordinates Communication UnifiedAgent → Executive UnifiedAgent → Specialized UnifiedAgents → Content UnifiedAgent
    for intent recognition, agent routing, response generation, and personalized aggregation.
    """

    def __init__(
        self,
        agent_manager: RealUnifiedAgentManager,
        pipeline_controller: PipelineController,
        state_manager: StateManager,
        orchestration_service: UnifiedAgentOrchestrationService,
    ):
        self.agent_manager = agent_manager
        self.pipeline_controller = pipeline_controller
        self.state_manager = state_manager
        self.orchestration_service = orchestration_service
        self.workflow_metrics = {
            "conversations_started": 0,
            "conversations_completed": 0,
            "conversations_failed": 0,
            "total_agents_consulted": 0,
            "average_confidence_score": 0.0,
            "average_execution_time": 0.0,
        }

    async def process_conversation(
        self, request: ConversationalInterfaceRequest
    ) -> ConversationalInterfaceResult:
        """
        Execute the complete conversational interface workflow.

        Args:
            request: Conversational interface request with user message and context

        Returns:
            ConversationalInterfaceResult with complete workflow results
        """
        workflow_id = str(uuid4())
        start_time = time.time()

        try:
            logger.info(f"Starting conversational interface workflow {workflow_id}")
            self.workflow_metrics["conversations_started"] += 1

            # Initialize workflow state
            workflow_state = {
                "workflow_id": workflow_id,
                "status": "started",
                "request": {
                    "user_message": request.user_message,
                    "conversation_mode": request.conversation_mode.value,
                    "response_style": request.response_style.value,
                    "conversation_history_length": len(request.conversation_history),
                },
                "steps_completed": [],
                "current_step": "intent_recognition",
                "agents_involved": [],
                "start_time": datetime.now(timezone.utc).isoformat(),
            }

            await self.state_manager.set_state(workflow_id, workflow_state)

            # Send workflow started event
            if request.conversation_id:
                workflow_event = create_workflow_event(
                    event_type=EventType.WORKFLOW_STARTED,
                    workflow_id=workflow_id,
                    workflow_type="conversational_interface",
                    participating_agents=[
                        "communication",
                        "executive",
                        "content",
                        "specialized",
                    ],
                    status="started",
                    conversation_id=request.conversation_id,
                )
                await self._notify_workflow_progress(workflow_event, request.user_id)

            # Step 1: Communication UnifiedAgent - Intent Recognition & Context Analysis
            intent_recognition_results = await self._execute_intent_recognition_step(
                workflow_id, request, workflow_state
            )

            # Step 2: Executive UnifiedAgent - Intelligent UnifiedAgent Routing & Selection
            agent_routing_results = await self._execute_agent_routing_step(
                workflow_id, request, intent_recognition_results, workflow_state
            )

            # Step 3: Specialized UnifiedAgents - Multi-UnifiedAgent Response Generation
            response_generation_results = await self._execute_response_generation_step(
                workflow_id,
                request,
                intent_recognition_results,
                agent_routing_results,
                workflow_state,
            )

            # Step 4: Content UnifiedAgent - Response Aggregation & Personalization
            response_aggregation_results = (
                await self._execute_response_aggregation_step(
                    workflow_id,
                    request,
                    intent_recognition_results,
                    agent_routing_results,
                    response_generation_results,
                    workflow_state,
                )
            )

            # Calculate final response and metrics
            final_response, confidence_score, follow_up_suggestions = (
                await self._finalize_conversation_response(
                    request,
                    intent_recognition_results,
                    agent_routing_results,
                    response_generation_results,
                    response_aggregation_results,
                )
            )

            # Finalize workflow
            execution_time = time.time() - start_time
            workflow_state["status"] = "completed"
            workflow_state["execution_time"] = execution_time
            await self.state_manager.set_state(workflow_id, workflow_state)

            # Send completion event
            if request.conversation_id:
                completion_event = create_workflow_event(
                    event_type=EventType.WORKFLOW_COMPLETED,
                    workflow_id=workflow_id,
                    workflow_type="conversational_interface",
                    participating_agents=workflow_state["agents_involved"],
                    status="completed",
                    conversation_id=request.conversation_id,
                )
                await self._notify_workflow_progress(completion_event, request.user_id)

            self.workflow_metrics["conversations_completed"] += 1
            self._update_average_execution_time(execution_time)
            self._update_conversation_metrics(
                confidence_score, len(workflow_state["agents_involved"])
            )

            return ConversationalInterfaceResult(
                workflow_id=workflow_id,
                success=True,
                conversation_mode=request.conversation_mode,
                intent_recognition_results=intent_recognition_results,
                agent_routing_results=agent_routing_results,
                response_generation_results=response_generation_results,
                response_aggregation_results=response_aggregation_results,
                final_response=final_response,
                confidence_score=confidence_score,
                agents_consulted=agent_routing_results.get("selected_agents", []),
                personalization_applied=response_aggregation_results.get(
                    "personalization_applied", {}
                ),
                follow_up_suggestions=follow_up_suggestions,
                execution_time_seconds=execution_time,
                agents_involved=workflow_state["agents_involved"],
            )

        except Exception as e:
            logger.error(f"Conversational interface workflow {workflow_id} failed: {e}")
            self.workflow_metrics["conversations_failed"] += 1

            # Update workflow state with error
            workflow_state["status"] = "failed"
            workflow_state["error"] = str(e)
            await self.state_manager.set_state(workflow_id, workflow_state)

            return ConversationalInterfaceResult(
                workflow_id=workflow_id,
                success=False,
                conversation_mode=request.conversation_mode,
                intent_recognition_results={},
                agent_routing_results={},
                response_generation_results={},
                response_aggregation_results={},
                final_response="I apologize, but I encountered an issue processing your request. Please try again.",
                confidence_score=0.0,
                agents_consulted=[],
                personalization_applied={},
                follow_up_suggestions=[],
                error_message=str(e),
                execution_time_seconds=time.time() - start_time,
                agents_involved=workflow_state.get("agents_involved", []),
            )

    async def _execute_intent_recognition_step(
        self,
        workflow_id: str,
        request: ConversationalInterfaceRequest,
        workflow_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute intent recognition and context analysis step using Communication UnifiedAgent."""
        try:
            logger.info(f"Executing intent recognition step for workflow {workflow_id}")

            # Get communication agent (fallback to executive agent)
            communication_agent = await self._get_agent_by_type("communication")
            if not communication_agent:
                communication_agent = await self._get_agent_by_type("executive")

            if not communication_agent:
                raise ValueError(
                    "No communication or executive agent available for intent recognition"
                )

            workflow_state["agents_involved"].append(communication_agent.agent_id)

            # Prepare intent recognition parameters
            intent_params = {
                "user_message": request.user_message,
                "conversation_history": request.conversation_history,
                "user_context": request.user_context,
                "conversation_mode": request.conversation_mode.value,
                "workflow_id": workflow_id,
            }

            # Execute intent recognition through agent coordination
            if hasattr(communication_agent, "recognize_intent_and_context"):
                intent_result = await communication_agent.recognize_intent_and_context(
                    **intent_params
                )
            else:
                # Fallback to generic agent task execution
                intent_result = await self.agent_manager.execute_agent_task(
                    communication_agent.agent_id,
                    {
                        "task": "intent_recognition_and_context_analysis",
                        "parameters": intent_params,
                        "workflow_context": {
                            "workflow_id": workflow_id,
                            "step": "intent_recognition",
                        },
                    },
                )

            # Process intent recognition results
            intent_recognition_results = {
                "agent_id": communication_agent.agent_id,
                "recognition_status": intent_result.get("status", "completed"),
                "primary_intent": intent_result.get(
                    "primary_intent", "general_inquiry"
                ),
                "intent_confidence": intent_result.get("intent_confidence", 0.8),
                "secondary_intents": intent_result.get("secondary_intents", []),
                "extracted_entities": intent_result.get("extracted_entities", []),
                "conversation_context": intent_result.get("conversation_context", {}),
                "user_sentiment": intent_result.get("user_sentiment", "neutral"),
                "complexity_level": intent_result.get("complexity_level", "medium"),
                "execution_time": intent_result.get("execution_time", 0),
            }

            # Update workflow state
            workflow_state["steps_completed"].append("intent_recognition")
            workflow_state["current_step"] = "agent_routing"
            await self.state_manager.set_state(workflow_id, workflow_state)

            logger.info(f"Intent recognition step completed for workflow {workflow_id}")
            return intent_recognition_results

        except Exception as e:
            logger.error(
                f"Intent recognition step failed for workflow {workflow_id}: {e}"
            )
            raise

    async def _execute_agent_routing_step(
        self,
        workflow_id: str,
        request: ConversationalInterfaceRequest,
        intent_recognition_results: Dict[str, Any],
        workflow_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute intelligent agent routing and selection step using Executive UnifiedAgent."""
        try:
            logger.info(f"Executing agent routing step for workflow {workflow_id}")

            # Get executive agent
            executive_agent = await self._get_agent_by_type("executive")
            if not executive_agent:
                raise ValueError("No executive agent available for agent routing")

            workflow_state["agents_involved"].append(executive_agent.agent_id)

            # Prepare agent routing parameters
            routing_params = {
                "primary_intent": intent_recognition_results.get("primary_intent"),
                "intent_confidence": intent_recognition_results.get(
                    "intent_confidence"
                ),
                "extracted_entities": intent_recognition_results.get(
                    "extracted_entities"
                ),
                "conversation_context": intent_recognition_results.get(
                    "conversation_context"
                ),
                "complexity_level": intent_recognition_results.get("complexity_level"),
                "user_context": request.user_context,
                "response_style": request.response_style.value,
                "workflow_id": workflow_id,
            }

            # Execute agent routing through agent coordination
            if hasattr(executive_agent, "route_and_select_agents"):
                routing_result = await executive_agent.route_and_select_agents(
                    **routing_params
                )
            else:
                # Fallback to generic agent task execution
                routing_result = await self.agent_manager.execute_agent_task(
                    executive_agent.agent_id,
                    {
                        "task": "intelligent_agent_routing_and_selection",
                        "parameters": routing_params,
                        "workflow_context": {
                            "workflow_id": workflow_id,
                            "step": "agent_routing",
                        },
                    },
                )

            # Process agent routing results
            agent_routing_results = {
                "agent_id": executive_agent.agent_id,
                "routing_status": routing_result.get("status", "completed"),
                "selected_agents": routing_result.get(
                    "selected_agents", ["market", "content"]
                ),
                "routing_confidence": routing_result.get("routing_confidence", 0.9),
                "routing_strategy": routing_result.get(
                    "routing_strategy", "intent_based"
                ),
                "agent_priorities": routing_result.get("agent_priorities", {}),
                "coordination_plan": routing_result.get("coordination_plan", {}),
                "fallback_agents": routing_result.get("fallback_agents", []),
                "execution_time": routing_result.get("execution_time", 0),
            }

            # Update workflow state
            workflow_state["steps_completed"].append("agent_routing")
            workflow_state["current_step"] = "response_generation"
            await self.state_manager.set_state(workflow_id, workflow_state)

            logger.info(f"UnifiedAgent routing step completed for workflow {workflow_id}")
            return agent_routing_results

        except Exception as e:
            logger.error(f"UnifiedAgent routing step failed for workflow {workflow_id}: {e}")
            raise

    async def _execute_response_generation_step(
        self,
        workflow_id: str,
        request: ConversationalInterfaceRequest,
        intent_recognition_results: Dict[str, Any],
        agent_routing_results: Dict[str, Any],
        workflow_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute multi-agent response generation step using Specialized UnifiedAgents."""
        try:
            logger.info(
                f"Executing response generation step for workflow {workflow_id}"
            )

            selected_agents = agent_routing_results.get(
                "selected_agents", ["market", "content"]
            )
            agent_responses = {}

            # Execute tasks with selected agents in parallel
            tasks = []
            for agent_type in selected_agents:
                agent = await self._get_agent_by_type(agent_type)
                if agent:
                    workflow_state["agents_involved"].append(agent.agent_id)
                    task = self._generate_agent_response(
                        agent,
                        agent_type,
                        workflow_id,
                        request,
                        intent_recognition_results,
                        agent_routing_results,
                    )
                    tasks.append((agent_type, task))

            # Wait for all agent responses
            for agent_type, task in tasks:
                try:
                    response = await task
                    agent_responses[agent_type] = response
                except Exception as e:
                    logger.warning(f"UnifiedAgent {agent_type} failed to respond: {e}")
                    agent_responses[agent_type] = {
                        "status": "failed",
                        "error": str(e),
                        "response": f"Unable to get response from {agent_type} agent",
                    }

            # Process response generation results
            response_generation_results = {
                "generation_status": "completed",
                "agents_consulted": list(agent_responses.keys()),
                "agent_responses": agent_responses,
                "response_quality_scores": {
                    agent_type: resp.get("quality_score", 0.8)
                    for agent_type, resp in agent_responses.items()
                },
                "coordination_success": len(agent_responses) > 0,
                "execution_time": sum(
                    resp.get("execution_time", 0) for resp in agent_responses.values()
                ),
            }

            # Update workflow state
            workflow_state["steps_completed"].append("response_generation")
            workflow_state["current_step"] = "response_aggregation"
            await self.state_manager.set_state(workflow_id, workflow_state)

            logger.info(
                f"Response generation step completed for workflow {workflow_id}"
            )
            return response_generation_results

        except Exception as e:
            logger.error(
                f"Response generation step failed for workflow {workflow_id}: {e}"
            )
            raise

    async def _execute_response_aggregation_step(
        self,
        workflow_id: str,
        request: ConversationalInterfaceRequest,
        intent_recognition_results: Dict[str, Any],
        agent_routing_results: Dict[str, Any],
        response_generation_results: Dict[str, Any],
        workflow_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute response aggregation and personalization step using Content UnifiedAgent."""
        try:
            logger.info(
                f"Executing response aggregation step for workflow {workflow_id}"
            )

            # Get content agent
            content_agent = await self._get_agent_by_type("content")
            if not content_agent:
                raise ValueError("No content agent available for response aggregation")

            workflow_state["agents_involved"].append(content_agent.agent_id)

            # Prepare aggregation parameters
            aggregation_params = {
                "agent_responses": response_generation_results.get(
                    "agent_responses", {}
                ),
                "primary_intent": intent_recognition_results.get("primary_intent"),
                "user_context": request.user_context,
                "personalization_preferences": request.personalization_preferences,
                "response_style": request.response_style.value,
                "conversation_mode": request.conversation_mode.value,
                "workflow_id": workflow_id,
            }

            # Execute response aggregation through agent coordination
            if hasattr(content_agent, "aggregate_and_personalize_response"):
                aggregation_result = (
                    await content_agent.aggregate_and_personalize_response(
                        **aggregation_params
                    )
                )
            else:
                # Fallback to generic agent task execution
                aggregation_result = await self.agent_manager.execute_agent_task(
                    content_agent.agent_id,
                    {
                        "task": "response_aggregation_and_personalization",
                        "parameters": aggregation_params,
                        "workflow_context": {
                            "workflow_id": workflow_id,
                            "step": "response_aggregation",
                        },
                    },
                )

            # Process aggregation results
            response_aggregation_results = {
                "agent_id": content_agent.agent_id,
                "aggregation_status": aggregation_result.get("status", "completed"),
                "aggregated_response": aggregation_result.get(
                    "aggregated_response", ""
                ),
                "personalization_applied": aggregation_result.get(
                    "personalization_applied", {}
                ),
                "response_coherence_score": aggregation_result.get(
                    "response_coherence_score", 0.9
                ),
                "personalization_score": aggregation_result.get(
                    "personalization_score", 0.8
                ),
                "follow_up_suggestions": aggregation_result.get(
                    "follow_up_suggestions", []
                ),
                "execution_time": aggregation_result.get("execution_time", 0),
            }

            # Update workflow state
            workflow_state["steps_completed"].append("response_aggregation")
            workflow_state["current_step"] = "completed"
            await self.state_manager.set_state(workflow_id, workflow_state)

            logger.info(
                f"Response aggregation step completed for workflow {workflow_id}"
            )
            return response_aggregation_results

        except Exception as e:
            logger.error(
                f"Response aggregation step failed for workflow {workflow_id}: {e}"
            )
            raise

    async def _generate_agent_response(
        self,
        agent,
        agent_type: str,
        workflow_id: str,
        request: ConversationalInterfaceRequest,
        intent_recognition_results: Dict[str, Any],
        agent_routing_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate response from a specific agent."""
        try:
            # Prepare agent-specific parameters
            agent_params = {
                "user_message": request.user_message,
                "primary_intent": intent_recognition_results.get("primary_intent"),
                "extracted_entities": intent_recognition_results.get(
                    "extracted_entities"
                ),
                "user_context": request.user_context,
                "response_style": request.response_style.value,
                "agent_priority": agent_routing_results.get("agent_priorities", {}).get(
                    agent_type, 1.0
                ),
                "workflow_id": workflow_id,
            }

            # Execute agent-specific response generation
            if hasattr(agent, "generate_conversational_response"):
                response = await agent.generate_conversational_response(**agent_params)
            else:
                # Fallback to generic agent task execution
                response = await self.agent_manager.execute_agent_task(
                    agent.agent_id,
                    {
                        "task": "conversational_response_generation",
                        "parameters": agent_params,
                        "workflow_context": {
                            "workflow_id": workflow_id,
                            "step": "response_generation",
                            "agent_type": agent_type,
                        },
                    },
                )

            return {
                "agent_id": agent.agent_id,
                "agent_type": agent_type,
                "status": response.get("status", "completed"),
                "response": response.get(
                    "response", f"Response from {agent_type} agent"
                ),
                "confidence": response.get("confidence", 0.8),
                "quality_score": response.get("quality_score", 0.8),
                "execution_time": response.get("execution_time", 0),
            }

        except Exception as e:
            logger.error(f"Error generating response from {agent_type} agent: {e}")
            return {
                "agent_id": getattr(agent, "agent_id", f"{agent_type}_agent"),
                "agent_type": agent_type,
                "status": "failed",
                "response": f"Unable to generate response from {agent_type} agent",
                "confidence": 0.0,
                "quality_score": 0.0,
                "execution_time": 0,
                "error": str(e),
            }

    async def _finalize_conversation_response(
        self,
        request: ConversationalInterfaceRequest,
        intent_recognition_results: Dict[str, Any],
        agent_routing_results: Dict[str, Any],
        response_generation_results: Dict[str, Any],
        response_aggregation_results: Dict[str, Any],
    ) -> tuple[str, float, List[str]]:
        """Finalize the conversation response with confidence score and follow-up suggestions."""
        try:
            # Get the aggregated response
            final_response = response_aggregation_results.get("aggregated_response", "")

            # If no aggregated response, create a fallback response
            if not final_response:
                agent_responses = response_generation_results.get("agent_responses", {})
                if agent_responses:
                    # Combine responses from all agents
                    responses = [
                        resp.get("response", "")
                        for resp in agent_responses.values()
                        if resp.get("response")
                    ]
                    final_response = (
                        " ".join(responses)
                        if responses
                        else "I'm here to help with your FlipSync needs."
                    )
                else:
                    final_response = "I'm here to help with your FlipSync needs. How can I assist you today?"

            # Calculate overall confidence score
            intent_confidence = intent_recognition_results.get("intent_confidence", 0.8)
            routing_confidence = agent_routing_results.get("routing_confidence", 0.9)
            response_coherence = response_aggregation_results.get(
                "response_coherence_score", 0.9
            )

            confidence_score = (
                intent_confidence + routing_confidence + response_coherence
            ) / 3

            # Get follow-up suggestions
            follow_up_suggestions = response_aggregation_results.get(
                "follow_up_suggestions", []
            )

            # Add default follow-up suggestions if none provided
            if not follow_up_suggestions:
                primary_intent = intent_recognition_results.get(
                    "primary_intent", "general_inquiry"
                )
                follow_up_suggestions = self._generate_default_follow_ups(
                    primary_intent
                )

            return final_response, confidence_score, follow_up_suggestions

        except Exception as e:
            logger.error(f"Error finalizing conversation response: {e}")
            return (
                "I apologize, but I encountered an issue processing your request. Please try again.",
                0.5,
                [
                    "How can I help you with FlipSync?",
                    "What would you like to know about our platform?",
                ],
            )

    def _generate_default_follow_ups(self, primary_intent: str) -> List[str]:
        """Generate default follow-up suggestions based on intent."""
        follow_up_map = {
            "product_creation": [
                "Would you like to create another product listing?",
                "Do you need help optimizing your product descriptions?",
                "Would you like to see sales analytics for your products?",
            ],
            "sales_optimization": [
                "Would you like to analyze competitor pricing?",
                "Do you need help with inventory management?",
                "Would you like to see performance metrics?",
            ],
            "market_research": [
                "Would you like to explore trending products?",
                "Do you need competitor analysis?",
                "Would you like market insights for a specific category?",
            ],
            "general_inquiry": [
                "How can I help you with FlipSync?",
                "Would you like to learn about our automation features?",
                "Do you need assistance with marketplace integration?",
            ],
        }

        return follow_up_map.get(primary_intent, follow_up_map["general_inquiry"])

    async def _get_agent_by_type(self, agent_type: str):
        """Get an agent instance by type from the agent manager."""
        try:
            # Use the orchestration service's agent registry
            if hasattr(self.orchestration_service, "agent_registry"):
                for (
                    agent_id,
                    agent,
                ) in self.orchestration_service.agent_registry.items():
                    if agent_type.lower() in agent_id.lower():
                        return agent

            # Fallback to agent manager
            available_agents = self.agent_manager.get_available_agents()
            for agent_id in available_agents:
                if agent_type.lower() in agent_id.lower():
                    return self.agent_manager.agents.get(agent_id)

            logger.warning(f"No agent found for type: {agent_type}")
            return None

        except Exception as e:
            logger.error(f"Error getting agent by type {agent_type}: {e}")
            return None

    async def _notify_workflow_progress(
        self, event: WorkflowEvent, user_id: Optional[str] = None
    ):
        """Send workflow progress notification via WebSocket."""
        try:
            from fs_agt_clean.core.websocket.manager import websocket_manager

            message = {
                "type": "workflow_progress",
                "data": {
                    "event_id": event.event_id,
                    "workflow_id": event.data.workflow_id,
                    "workflow_type": event.data.workflow_type,
                    "status": event.data.status,
                    "participating_agents": event.data.participating_agents,
                    "timestamp": event.timestamp.isoformat(),
                },
            }

            if user_id:
                await websocket_manager.send_to_user(user_id, message)
            else:
                await websocket_manager.broadcast(message)

        except Exception as e:
            logger.error(f"Error sending workflow progress notification: {e}")

    def _update_average_execution_time(self, execution_time: float):
        """Update the average execution time metric."""
        try:
            current_avg = self.workflow_metrics["average_execution_time"]
            completed_count = self.workflow_metrics["conversations_completed"]

            if completed_count <= 1:
                self.workflow_metrics["average_execution_time"] = execution_time
            else:
                # Calculate running average
                new_avg = (
                    (current_avg * (completed_count - 1)) + execution_time
                ) / completed_count
                self.workflow_metrics["average_execution_time"] = new_avg

        except Exception as e:
            logger.error(f"Error updating average execution time: {e}")

    def _update_conversation_metrics(
        self, confidence_score: float, agents_consulted: int
    ):
        """Update workflow metrics with conversation results."""
        try:
            # Update average confidence score
            current_avg = self.workflow_metrics["average_confidence_score"]
            completed_count = self.workflow_metrics["conversations_completed"]

            if completed_count <= 1:
                self.workflow_metrics["average_confidence_score"] = confidence_score
            else:
                new_avg = (
                    (current_avg * (completed_count - 1)) + confidence_score
                ) / completed_count
                self.workflow_metrics["average_confidence_score"] = new_avg

            # Update total agents consulted
            self.workflow_metrics["total_agents_consulted"] += agents_consulted

        except Exception as e:
            logger.error(f"Error updating conversation metrics: {e}")

    def get_workflow_metrics(self) -> Dict[str, Any]:
        """Get current workflow metrics."""
        return self.workflow_metrics.copy()
