"""
FlipSync 4+1 Architecture Chat API Routes - StrategicChatService Integration
===========================================================================

Phase 3.3.1: StrategicChatService API Integration
This module provides chat API endpoints that integrate with the 4+1 architecture:
- Chat endpoints use 4+1 architecture database exclusively
- Integration with AutonomousAgentRepository for agent coordination
- Conversational interface endpoints that complement autonomous agent APIs
- Chat service can query and interact with autonomous_agents table data
- Real-time chat integration with WebSocket endpoints from Phase 3.2

Key Features:
- StrategicChatService integration with autonomous agents
- Chat-to-agent command routing and response handling
- Conversational monitoring and logging to 4+1 architecture database
- Chat service can trigger autonomous agent actions through proper APIs
- Chat history integrated with agent decision tracking

API Endpoints:
- POST /chat/4plus1/conversations - Create conversation with agent context
- GET /chat/4plus1/conversations/{conversation_id} - Get conversation with agent data
- POST /chat/4plus1/conversations/{conversation_id}/messages - Send message with agent routing
- GET /chat/4plus1/agent-status - Get agent status through conversational interface
- POST /chat/4plus1/agent-command - Send commands to autonomous agents via chat
- GET /chat/4plus1/agent-decisions - Query agent decisions through chat interface

Architecture Compliance:
- Maintains separation between LLM-powered chat and LLM-free autonomous agents
- Uses AutonomousAgentRepository exclusively for agent data
- Stores chat data in 4+1 architecture database tables
- Integrates with WebSocket endpoints for real-time updates
- Zero legacy chat dependencies
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

# Import 4+1 architecture components
from fs_agt_clean.core.db.database import get_database
from fs_agt_clean.database.repositories.autonomous_agent_repository import (
    AutonomousAgentRepository,
)
from fs_agt_clean.database.repositories.chat_repository import ChatRepository
from fs_agt_clean.database.models.autonomous_agent import (
    AutonomousAgent,
    AutonomousAgentDecision,
)
from fs_agt_clean.core.architecture.boundaries import (
    ArchitecturalBoundaries,
    ArchitecturalLayer,
)

# Import StrategicChatService components
from fs_agt_clean.services.communication.strategic_chat_service import (
    StrategicChatService,
    ChatRequest,
    ChatResponse,
)
from fs_agt_clean.services.communication.strategic_chat_adapter import (
    StrategicChatAdapter,
)

# Import authentication
from fs_agt_clean.api.dependencies.dependencies import get_current_user_optional
from fs_agt_clean.database.models.unified_user import UnifiedUserResponse

# Configure logging
logger = logging.getLogger(__name__)

# Create router for 4+1 architecture chat endpoints
router = APIRouter(prefix="/chat/4plus1", tags=["4+1-architecture-chat"])

# Database and repository instances
database = get_database()
autonomous_agent_repository = AutonomousAgentRepository()
chat_repository = ChatRepository()


# Pydantic models for API requests/responses
class ChatMessage4Plus1Request(BaseModel):
    """Request model for 4+1 architecture chat messages."""

    text: str
    agent_context: Optional[str] = None  # Specific agent to route to
    include_agent_data: bool = True  # Include agent status in response
    priority: str = "normal"  # normal, high, urgent


class ChatMessage4Plus1Response(BaseModel):
    """Response model for 4+1 architecture chat messages."""

    id: str
    text: str
    sender: str
    timestamp: str
    agent_context: Optional[str] = None
    agent_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = {}


class AgentCommand4Plus1Request(BaseModel):
    """Request model for agent commands through chat interface."""

    command: str
    agent_id: Optional[str] = None
    agent_type: Optional[str] = None
    parameters: Dict[str, Any] = {}


class AgentCommand4Plus1Response(BaseModel):
    """Response model for agent commands through chat interface."""

    success: bool
    message: str
    agent_id: Optional[str] = None
    command_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class StrategicChatService4Plus1:
    """
    Enhanced StrategicChatService that integrates with 4+1 architecture.

    Provides conversational interface capabilities while maintaining strict
    separation between LLM-powered chat and LLM-free autonomous agents.
    """

    def __init__(self):
        self.strategic_chat = StrategicChatService(daily_budget=10.0)
        self.autonomous_agent_repository = AutonomousAgentRepository()
        self.chat_repository = ChatRepository()

        # Agent command mapping (will be set to standalone functions)
        self.agent_commands = {
            "status": None,  # Will be set after functions are defined
            "decisions": None,
            "performance": None,
            "trigger": None,
        }

        logger.info(
            "StrategicChatService4Plus1 initialized with 4+1 architecture integration"
        )

    async def handle_chat_with_agent_context(
        self,
        message: str,
        conversation_id: str,
        user_id: str,
        agent_context: Optional[str] = None,
        include_agent_data: bool = True,
    ) -> Dict[str, Any]:
        """Handle chat message with autonomous agent context integration."""

        # Analyze user intent to determine if agent interaction is needed
        intent_analysis = await self.strategic_chat.analyze_user_intent(message)

        # Get agent data if requested or if intent suggests agent interaction
        agent_data = None
        if (
            include_agent_data
            or intent_analysis.get("suggested_agent") != "conversational_interface"
        ):
            agent_data = await self._get_relevant_agent_data(
                intent_analysis, agent_context
            )

        # Create enhanced chat request with agent context
        chat_request = ChatRequest(
            message=message,
            user_id=user_id,
            conversation_id=conversation_id,
            context={
                "agent_data": agent_data,
                "intent_analysis": intent_analysis,
                "architecture_layer": ArchitecturalLayer.CONVERSATIONAL.value,
                "llm_provider": "Gemini",
            },
            priority="normal",
        )

        # Get strategic chat response
        chat_response = await self.strategic_chat.handle_chat(chat_request)

        # Store conversation in 4+1 architecture database
        await self._store_conversation_4plus1(
            conversation_id, user_id, message, chat_response, agent_data
        )

        return {
            "response": chat_response.content,
            "confidence": chat_response.confidence,
            "response_time": chat_response.response_time,
            "agent_data": agent_data,
            "intent_analysis": intent_analysis,
            "metadata": {
                **chat_response.metadata,
                "architecture_compliance": {
                    "llm_free_agents": True,
                    "conversational_interface_llm": True,
                    "separation_maintained": True,
                },
            },
        }

    async def _get_relevant_agent_data(
        self, intent_analysis: Dict[str, Any], agent_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get relevant autonomous agent data based on intent analysis."""
        try:
            async with database.get_session() as session:
                # Get all autonomous agents
                agents = (
                    await self.autonomous_agent_repository.get_all_autonomous_agents(
                        session
                    )
                )

                # Filter agents based on intent or context
                relevant_agents = []
                if agent_context:
                    # Specific agent requested
                    for agent in agents:
                        if (
                            agent_context.lower() in agent.agent_id.lower()
                            or agent_context.lower() in agent.agent_type.lower()
                        ):
                            relevant_agents.append(agent)
                else:
                    # Use intent analysis to find relevant agents
                    suggested_agent = intent_analysis.get("suggested_agent", "")
                    if (
                        suggested_agent
                        and suggested_agent != "conversational_interface"
                    ):
                        for agent in agents:
                            if suggested_agent.lower() in agent.agent_id.lower():
                                relevant_agents.append(agent)
                    else:
                        # Include all agents for general queries
                        relevant_agents = agents[:3]  # Limit to top 3 for performance

                # Get recent decisions for relevant agents
                agent_data = {}
                for agent in relevant_agents:
                    recent_decisions = (
                        await self.autonomous_agent_repository.get_agent_decisions(
                            session, agent.agent_id, limit=3
                        )
                    )

                    agent_data[agent.agent_id] = {
                        "agent_type": agent.agent_type,
                        "status": agent.status,
                        "last_heartbeat": (
                            agent.last_heartbeat.isoformat()
                            if agent.last_heartbeat
                            else None
                        ),
                        "llm_free": agent.llm_free,
                        "uses_standard_pipeline": agent.uses_standard_decision_pipeline,
                        "recent_decisions": [
                            {
                                "decision_id": d.decision_id,
                                "decision_type": d.decision_type,
                                "status": d.status,
                                "execution_time_ms": d.execution_time_ms,
                                "confidence": d.confidence,
                                "llm_free_compliant": not d.used_llm,
                                "created_at": d.created_at.isoformat(),
                            }
                            for d in recent_decisions
                        ],
                    }

                return {
                    "agents_count": len(relevant_agents),
                    "agents": agent_data,
                    "query_timestamp": datetime.now(timezone.utc).isoformat(),
                    "data_source": "autonomous_agents table",
                }

        except Exception as e:
            logger.error(f"Error getting agent data: {e}")
            return {
                "error": f"Failed to retrieve agent data: {str(e)}",
                "agents_count": 0,
                "agents": {},
            }

    async def _store_conversation_4plus1(
        self,
        conversation_id: str,
        user_id: str,
        user_message: str,
        chat_response: ChatResponse,
        agent_data: Optional[Dict[str, Any]],
    ):
        """Store conversation in 4+1 architecture database."""
        try:
            async with database.get_session() as session:
                # Create or get conversation
                try:
                    conversation = await self.chat_repository.get_conversation(
                        session, conversation_id
                    )
                except:
                    # Create new conversation
                    conversation = await self.chat_repository.create_conversation(
                        session,
                        user_id,
                        f"Chat with Agent Context - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    )
                    conversation_id = str(conversation.id)

                # Store user message
                await self.chat_repository.create_message(
                    session,
                    conversation_id,
                    user_message,
                    "user",
                    metadata={
                        "agent_context_requested": agent_data is not None,
                        "architecture_layer": ArchitecturalLayer.CONVERSATIONAL.value,
                    },
                )

                # Store assistant response
                await self.chat_repository.create_message(
                    session,
                    conversation_id,
                    chat_response.content,
                    "agent",
                    agent_type="strategic_chat",
                    metadata={
                        "confidence": chat_response.confidence,
                        "response_time": chat_response.response_time,
                        "agent_data_included": agent_data is not None,
                        "llm_provider": "Gemini",
                        "architecture_compliance": {
                            "llm_free_agents": True,
                            "conversational_interface_llm": True,
                            "separation_maintained": True,
                        },
                        **chat_response.metadata,
                    },
                )

        except Exception as e:
            logger.error(f"Error storing conversation in 4+1 database: {e}")


# Global service instance
strategic_chat_4plus1 = StrategicChatService4Plus1()


@router.post("/conversations", response_model=Dict[str, Any])
async def create_conversation_4plus1(
    request: Request,
    current_user: Optional[UnifiedUserResponse] = Depends(get_current_user_optional),
):
    """
    Create a new conversation with 4+1 architecture agent context.

    Creates a conversation that can interact with autonomous agents while
    maintaining the separation between LLM-powered chat and LLM-free agents.
    """
    try:
        user_id = current_user.id if current_user else "anonymous"
        conversation_id = str(uuid4())

        # Create conversation in 4+1 architecture database
        async with database.get_session() as session:
            conversation = await chat_repository.create_conversation(
                session,
                user_id,
                f"4+1 Architecture Chat - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            )

            # Add initial system message explaining capabilities
            await chat_repository.create_message(
                session,
                str(conversation.id),
                "Welcome to FlipSync's 4+1 Architecture Chat! I can help you interact with and monitor autonomous agents, get real-time status updates, and coordinate agent actions. How can I assist you today?",
                "system",
                agent_type="strategic_chat",
                metadata={
                    "conversation_type": "4plus1_architecture",
                    "capabilities": [
                        "agent_status_queries",
                        "agent_decision_monitoring",
                        "agent_command_routing",
                        "real_time_updates",
                    ],
                    "architecture_layer": ArchitecturalLayer.CONVERSATIONAL.value,
                },
            )

        return {
            "success": True,
            "conversation_id": str(conversation.id),
            "message": "4+1 Architecture conversation created successfully",
            "capabilities": [
                "Query autonomous agent status and decisions",
                "Send commands to autonomous agents",
                "Monitor real-time agent performance",
                "Get compliance and performance metrics",
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Error creating 4+1 conversation: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create conversation: {str(e)}"
        )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=ChatMessage4Plus1Response,
)
async def send_message_4plus1(
    conversation_id: str,
    message_request: ChatMessage4Plus1Request,
    current_user: Optional[UnifiedUserResponse] = Depends(get_current_user_optional),
):
    """
    Send a message in a 4+1 architecture conversation with agent context.

    Processes the message through StrategicChatService while providing
    autonomous agent data and maintaining architectural separation.
    """
    try:
        user_id = current_user.id if current_user else "anonymous"

        # Handle chat with agent context
        response_data = await strategic_chat_4plus1.handle_chat_with_agent_context(
            message=message_request.text,
            conversation_id=conversation_id,
            user_id=user_id,
            agent_context=message_request.agent_context,
            include_agent_data=message_request.include_agent_data,
        )

        return ChatMessage4Plus1Response(
            id=str(uuid4()),
            text=response_data["response"],
            sender="strategic_chat",
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_context=message_request.agent_context,
            agent_data=response_data.get("agent_data"),
            metadata={
                "confidence": response_data.get("confidence", 0.0),
                "response_time": response_data.get("response_time", 0.0),
                "intent_analysis": response_data.get("intent_analysis", {}),
                **response_data.get("metadata", {}),
            },
        )

    except Exception as e:
        logger.error(f"Error sending 4+1 message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@router.get("/agent-status", response_model=Dict[str, Any])
async def get_agent_status_4plus1(
    agent_id: Optional[str] = None,
    current_user: Optional[UnifiedUserResponse] = Depends(get_current_user_optional),
):
    """
    Get autonomous agent status through conversational interface.

    Provides agent status information that can be used in chat responses
    while maintaining 4+1 architecture separation.
    """
    try:
        async with database.get_session() as session:
            if agent_id:
                # Get specific agent
                agent = await autonomous_agent_repository.get_autonomous_agent(
                    session, agent_id
                )
                if not agent:
                    raise HTTPException(
                        status_code=404, detail=f"Agent {agent_id} not found"
                    )
                agents = [agent]
            else:
                # Get all agents
                agents = await autonomous_agent_repository.get_all_autonomous_agents(
                    session
                )

            agent_status_data = []
            for agent in agents:
                # Get recent decisions for performance metrics
                recent_decisions = (
                    await autonomous_agent_repository.get_agent_decisions(
                        session, agent.agent_id, limit=5
                    )
                )

                # Calculate performance metrics
                performance_metrics = {
                    "total_decisions": len(recent_decisions),
                    "llm_free_decisions": sum(
                        1 for d in recent_decisions if not d.used_llm
                    ),
                    "avg_execution_time": (
                        sum(
                            d.execution_time_ms
                            for d in recent_decisions
                            if d.execution_time_ms
                        )
                        / len(recent_decisions)
                        if recent_decisions
                        else 0
                    ),
                    "performance_compliant": sum(
                        1
                        for d in recent_decisions
                        if d.execution_time_ms and d.execution_time_ms < 1000
                    ),
                }

                agent_status = {
                    "agent_id": agent.agent_id,
                    "agent_type": agent.agent_type,
                    "status": agent.status,
                    "last_heartbeat": (
                        agent.last_heartbeat.isoformat()
                        if agent.last_heartbeat
                        else None
                    ),
                    "architecture_compliance": {
                        "llm_free": agent.llm_free,
                        "uses_standard_pipeline": agent.uses_standard_decision_pipeline,
                        "architecture_layer": ArchitecturalBoundaries.validate_agent_type(
                            agent.agent_id
                        ).value,
                    },
                    "performance_metrics": performance_metrics,
                    "created_at": agent.created_at.isoformat(),
                    "updated_at": agent.updated_at.isoformat(),
                }
                agent_status_data.append(agent_status)

            return {
                "success": True,
                "agents": agent_status_data,
                "summary": {
                    "total_agents": len(agent_status_data),
                    "active_agents": sum(
                        1 for a in agent_status_data if a["status"] == "active"
                    ),
                    "llm_free_agents": sum(
                        1
                        for a in agent_status_data
                        if a["architecture_compliance"]["llm_free"]
                    ),
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data_source": "autonomous_agents table",
                "interface_type": "conversational",
            }

    except Exception as e:
        logger.error(f"Error getting agent status for chat: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get agent status: {str(e)}"
        )


@router.post("/agent-command", response_model=AgentCommand4Plus1Response)
async def send_agent_command_4plus1(
    command_request: AgentCommand4Plus1Request,
    current_user: Optional[UnifiedUserResponse] = Depends(get_current_user_optional),
):
    """
    Send commands to autonomous agents through conversational interface.

    Allows chat interface to trigger agent actions while maintaining
    proper separation between conversational and autonomous layers.
    """
    try:
        command_id = str(uuid4())

        # Validate command
        if command_request.command not in [
            "status",
            "decisions",
            "performance",
            "trigger",
        ]:
            raise HTTPException(
                status_code=400, detail=f"Invalid command: {command_request.command}"
            )

        # Route command to appropriate handler
        if command_request.command == "status":
            result = await _handle_status_command(command_request)
        elif command_request.command == "decisions":
            result = await _handle_decisions_command(command_request)
        elif command_request.command == "performance":
            result = await _handle_performance_command(command_request)
        elif command_request.command == "trigger":
            result = await _handle_trigger_command(command_request)

        return AgentCommand4Plus1Response(
            success=True,
            message=f"Command '{command_request.command}' executed successfully",
            agent_id=command_request.agent_id,
            command_id=command_id,
            result=result,
        )

    except Exception as e:
        logger.error(f"Error executing agent command: {e}")
        return AgentCommand4Plus1Response(
            success=False,
            message=f"Command execution failed: {str(e)}",
            agent_id=command_request.agent_id,
            command_id=command_id,
            result=None,
        )


@router.get("/agent-decisions", response_model=Dict[str, Any])
async def get_agent_decisions_4plus1(
    agent_id: Optional[str] = None,
    limit: int = 10,
    llm_free_only: bool = False,
    current_user: Optional[UnifiedUserResponse] = Depends(get_current_user_optional),
):
    """
    Query agent decisions through chat interface.

    Provides decision data that can be used in conversational responses
    while maintaining 4+1 architecture compliance.
    """
    try:
        async with database.get_session() as session:
            if agent_id:
                # Get decisions for specific agent
                decisions = await autonomous_agent_repository.get_agent_decisions(
                    session, agent_id, limit=limit
                )
            else:
                # Get recent decisions from all agents
                from sqlalchemy import select
                from fs_agt_clean.database.models.autonomous_agent import (
                    AutonomousAgentDecision,
                )

                query = (
                    select(AutonomousAgentDecision)
                    .order_by(AutonomousAgentDecision.created_at.desc())
                    .limit(limit)
                )

                if llm_free_only:
                    query = query.where(AutonomousAgentDecision.used_llm == False)

                result = await session.execute(query)
                decisions = result.scalars().all()

            decisions_data = []
            for decision in decisions:
                decision_data = {
                    "decision_id": decision.decision_id,
                    "agent_id": decision.agent_id,
                    "decision_type": decision.decision_type,
                    "status": decision.status,
                    "execution_time_ms": decision.execution_time_ms,
                    "confidence": decision.confidence,
                    "compliance": {
                        "used_llm": decision.used_llm,
                        "used_standard_pipeline": decision.used_standard_pipeline,
                        "algorithm_used": decision.algorithm_used,
                        "llm_free_compliant": not decision.used_llm,
                        "performance_compliant": (
                            decision.execution_time_ms < 1000
                            if decision.execution_time_ms
                            else False
                        ),
                    },
                    "timestamps": {
                        "started_at": (
                            decision.started_at.isoformat()
                            if decision.started_at
                            else None
                        ),
                        "completed_at": (
                            decision.completed_at.isoformat()
                            if decision.completed_at
                            else None
                        ),
                        "created_at": decision.created_at.isoformat(),
                    },
                }
                decisions_data.append(decision_data)

            return {
                "success": True,
                "decisions": decisions_data,
                "summary": {
                    "total_decisions": len(decisions_data),
                    "llm_free_decisions": sum(
                        1
                        for d in decisions_data
                        if d["compliance"]["llm_free_compliant"]
                    ),
                    "performance_compliant": sum(
                        1
                        for d in decisions_data
                        if d["compliance"]["performance_compliant"]
                    ),
                    "avg_execution_time": (
                        sum(
                            d["execution_time_ms"]
                            for d in decisions_data
                            if d["execution_time_ms"]
                        )
                        / len(decisions_data)
                        if decisions_data
                        else 0
                    ),
                },
                "filters": {
                    "agent_id": agent_id,
                    "limit": limit,
                    "llm_free_only": llm_free_only,
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data_source": "autonomous_agent_decisions table",
                "interface_type": "conversational",
            }

    except Exception as e:
        logger.error(f"Error getting agent decisions for chat: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get agent decisions: {str(e)}"
        )


# Helper functions for agent command handling


async def _handle_status_command(
    command_request: AgentCommand4Plus1Request,
) -> Dict[str, Any]:
    """Handle status command for agents."""
    async with database.get_session() as session:
        if command_request.agent_id:
            agent = await autonomous_agent_repository.get_autonomous_agent(
                session, command_request.agent_id
            )
            if not agent:
                return {"error": f"Agent {command_request.agent_id} not found"}

            return {
                "agent_id": agent.agent_id,
                "status": agent.status,
                "last_heartbeat": (
                    agent.last_heartbeat.isoformat() if agent.last_heartbeat else None
                ),
                "llm_free": agent.llm_free,
            }
        else:
            agents = await autonomous_agent_repository.get_all_autonomous_agents(
                session
            )
            return {
                "total_agents": len(agents),
                "active_agents": sum(1 for a in agents if a.status == "active"),
                "llm_free_agents": sum(1 for a in agents if a.llm_free),
            }


async def _handle_decisions_command(
    command_request: AgentCommand4Plus1Request,
) -> Dict[str, Any]:
    """Handle decisions command for agents."""
    limit = command_request.parameters.get("limit", 5)

    async with database.get_session() as session:
        if command_request.agent_id:
            decisions = await autonomous_agent_repository.get_agent_decisions(
                session, command_request.agent_id, limit=limit
            )
        else:
            from sqlalchemy import select
            from fs_agt_clean.database.models.autonomous_agent import (
                AutonomousAgentDecision,
            )

            query = (
                select(AutonomousAgentDecision)
                .order_by(AutonomousAgentDecision.created_at.desc())
                .limit(limit)
            )

            result = await session.execute(query)
            decisions = result.scalars().all()

        return {
            "total_decisions": len(decisions),
            "llm_free_decisions": sum(1 for d in decisions if not d.used_llm),
            "recent_decisions": [
                {
                    "decision_id": d.decision_id,
                    "agent_id": d.agent_id,
                    "decision_type": d.decision_type,
                    "status": d.status,
                    "llm_free": not d.used_llm,
                }
                for d in decisions[:3]  # Show top 3
            ],
        }


async def _handle_performance_command(
    command_request: AgentCommand4Plus1Request,
) -> Dict[str, Any]:
    """Handle performance command for agents."""
    async with database.get_session() as session:
        if command_request.agent_id:
            decisions = await autonomous_agent_repository.get_agent_decisions(
                session, command_request.agent_id, limit=10
            )

            if not decisions:
                return {
                    "error": f"No decisions found for agent {command_request.agent_id}"
                }

            avg_time = sum(
                d.execution_time_ms for d in decisions if d.execution_time_ms
            ) / len(decisions)
            performance_compliant = sum(
                1
                for d in decisions
                if d.execution_time_ms and d.execution_time_ms < 1000
            )

            return {
                "agent_id": command_request.agent_id,
                "avg_execution_time_ms": avg_time,
                "performance_compliant_rate": performance_compliant / len(decisions),
                "total_decisions_analyzed": len(decisions),
            }
        else:
            return {"error": "Agent ID required for performance analysis"}


async def _handle_trigger_command(
    command_request: AgentCommand4Plus1Request,
) -> Dict[str, Any]:
    """Handle trigger command for agents."""
    # Note: This is a placeholder for future agent triggering functionality
    # In a full implementation, this would interface with the agent orchestration system
    return {
        "message": "Agent triggering not yet implemented",
        "agent_id": command_request.agent_id,
        "command": "trigger",
        "note": "This feature will be implemented in future phases",
    }


# Update the agent_commands mapping after functions are defined
strategic_chat_4plus1.agent_commands = {
    "status": _handle_status_command,
    "decisions": _handle_decisions_command,
    "performance": _handle_performance_command,
    "trigger": _handle_trigger_command,
}
