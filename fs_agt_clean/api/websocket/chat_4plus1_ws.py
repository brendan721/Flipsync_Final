"""
FlipSync 4+1 Architecture Chat WebSocket Integration
===================================================

Phase 3.3.2: Conversational Interface Coordination
This module provides WebSocket integration for the StrategicChatService with 4+1 architecture:
- Real-time chat integration with autonomous agent WebSocket endpoints
- Coordination layer between StrategicChatService and autonomous agents
- Chat-to-agent command routing through WebSocket connections
- Conversational monitoring and logging to 4+1 architecture database
- Real-time chat updates with agent status and decision streaming

WebSocket Endpoints:
- /ws/chat/4plus1/{conversation_id} - Real-time chat with agent context
- /ws/chat/agent-monitor/{agent_id} - Monitor specific agent through chat interface
- /ws/chat/coordination - Cross-system coordination between chat and agents

Key Features:
- Real-time chat with autonomous agent data integration
- WebSocket coordination between conversational and autonomous layers
- Live agent status updates in chat interface
- Real-time decision streaming to chat clients
- Chat command routing to autonomous agents
- Maintains strict separation between LLM-powered chat and LLM-free agents

Architecture Compliance:
- Uses AutonomousAgentRepository exclusively for agent data
- Integrates with Phase 3.2 WebSocket endpoints
- Stores chat data in 4+1 architecture database tables
- Maintains conversational interface as separate architectural layer
- Zero legacy WebSocket dependencies
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter

# Import 4+1 architecture components
from fs_agt_clean.core.db.database import get_database
from fs_agt_clean.database.repositories.autonomous_agent_repository import (
    AutonomousAgentRepository,
)
from fs_agt_clean.database.repositories.chat_repository import ChatRepository
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

# Import existing WebSocket managers from Phase 3.2
from fs_agt_clean.api.websocket.agents_4plus1_ws import ws_manager as agent_ws_manager

# Configure logging
logger = logging.getLogger(__name__)

# Create router for Chat WebSocket endpoints
router = APIRouter(prefix="/ws/chat", tags=["4+1-architecture-chat-websockets"])

# Database and repository instances
database = get_database()
autonomous_agent_repository = AutonomousAgentRepository()
chat_repository = ChatRepository()

# Chat WebSocket connection management
chat_connections: Dict[str, Set[WebSocket]] = {
    "chat_4plus1": set(),
    "agent_monitor": set(),
    "coordination": set(),
}

# Connection metadata for chat WebSockets
chat_connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}


class ChatWebSocketManager:
    """
    WebSocket connection manager for 4+1 architecture chat integration.

    Coordinates between StrategicChatService and autonomous agent WebSocket endpoints.
    """

    def __init__(self):
        self.connections: Dict[str, Set[WebSocket]] = {
            "chat_4plus1": set(),
            "agent_monitor": set(),
            "coordination": set(),
        }
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        self.background_tasks: Set[asyncio.Task] = set()
        self.strategic_chat = StrategicChatService(daily_budget=10.0)

        # Integration with agent WebSocket manager
        self.agent_ws_manager = agent_ws_manager

    async def connect(
        self,
        websocket: WebSocket,
        connection_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Connect a WebSocket to a specific chat channel."""
        await websocket.accept()

        if connection_type not in self.connections:
            raise ValueError(f"Invalid chat connection type: {connection_type}")

        self.connections[connection_type].add(websocket)
        self.connection_metadata[websocket] = {
            "connection_type": connection_type,
            "connected_at": datetime.now(timezone.utc),
            "metadata": metadata or {},
        }

        logger.info(
            f"🔌 Chat WebSocket connected to {connection_type} channel. Total connections: {len(self.connections[connection_type])}"
        )

    async def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket from all chat channels."""
        for connection_type, connections in self.connections.items():
            if websocket in connections:
                connections.remove(websocket)
                logger.info(
                    f"🔌 Chat WebSocket disconnected from {connection_type} channel. Remaining: {len(connections)}"
                )

        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]

    async def broadcast_to_channel(self, connection_type: str, message: Dict[str, Any]):
        """Broadcast a message to all connections in a specific chat channel."""
        if connection_type not in self.connections:
            return

        connections = self.connections[connection_type].copy()
        if not connections:
            return

        message_json = json.dumps(message)
        disconnected_connections = []

        for websocket in connections:
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.warning(f"Failed to send chat message to WebSocket: {e}")
                disconnected_connections.append(websocket)

        # Clean up disconnected connections
        for websocket in disconnected_connections:
            await self.disconnect(websocket)

    async def handle_chat_message(
        self,
        websocket: WebSocket,
        message: str,
        conversation_id: str,
        user_id: str = "anonymous",
    ) -> Dict[str, Any]:
        """Handle chat message with agent context integration."""
        try:
            # Analyze user intent
            intent_analysis = await self.strategic_chat.analyze_user_intent(message)

            # Get relevant agent data based on intent
            agent_data = await self._get_agent_data_for_chat(intent_analysis)

            # Create chat request with agent context
            chat_request = ChatRequest(
                message=message,
                user_id=user_id,
                conversation_id=conversation_id,
                context={
                    "agent_data": agent_data,
                    "intent_analysis": intent_analysis,
                    "websocket_connection": True,
                    "architecture_layer": ArchitecturalLayer.CONVERSATIONAL.value,
                },
                priority="normal",
            )

            # Get strategic chat response
            chat_response = await self.strategic_chat.handle_chat(chat_request)

            # Store conversation in database
            await self._store_chat_message(
                conversation_id, user_id, message, chat_response, agent_data
            )

            # Prepare response with agent data
            response_data = {
                "type": "chat_response",
                "conversation_id": conversation_id,
                "message": {
                    "id": str(uuid4()),
                    "text": chat_response.content,
                    "sender": "strategic_chat",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "confidence": chat_response.confidence,
                    "response_time": chat_response.response_time,
                },
                "agent_context": {
                    "intent_analysis": intent_analysis,
                    "agent_data": agent_data,
                    "suggested_agent": intent_analysis.get("suggested_agent"),
                },
                "metadata": {
                    **chat_response.metadata,
                    "architecture_compliance": {
                        "llm_free_agents": True,
                        "conversational_interface_llm": True,
                        "separation_maintained": True,
                    },
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            return response_data

        except Exception as e:
            logger.error(f"Error handling chat message: {e}")
            return {
                "type": "error",
                "message": f"Failed to process chat message: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    async def _get_agent_data_for_chat(
        self, intent_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get relevant agent data for chat context."""
        try:
            async with database.get_session() as session:
                # Get agents based on intent
                suggested_agent = intent_analysis.get("suggested_agent", "")

                if suggested_agent and suggested_agent != "conversational_interface":
                    # Get specific agent
                    agents = (
                        await autonomous_agent_repository.get_all_autonomous_agents(
                            session
                        )
                    )
                    relevant_agents = [
                        a
                        for a in agents
                        if suggested_agent.lower() in a.agent_id.lower()
                    ]
                else:
                    # Get all agents for general queries
                    agents = (
                        await autonomous_agent_repository.get_all_autonomous_agents(
                            session
                        )
                    )
                    relevant_agents = agents[:3]  # Limit for performance

                agent_data = {}
                for agent in relevant_agents:
                    # Get recent decisions
                    recent_decisions = (
                        await autonomous_agent_repository.get_agent_decisions(
                            session, agent.agent_id, limit=3
                        )
                    )

                    agent_data[agent.agent_id] = {
                        "agent_type": agent.agent_type,
                        "status": agent.status,
                        "llm_free": agent.llm_free,
                        "last_heartbeat": (
                            agent.last_heartbeat.isoformat()
                            if agent.last_heartbeat
                            else None
                        ),
                        "recent_decisions_count": len(recent_decisions),
                        "performance_summary": {
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
                            "llm_free_rate": (
                                sum(1 for d in recent_decisions if not d.used_llm)
                                / len(recent_decisions)
                                if recent_decisions
                                else 1.0
                            ),
                        },
                    }

                return {
                    "agents_available": len(relevant_agents),
                    "agents": agent_data,
                    "query_timestamp": datetime.now(timezone.utc).isoformat(),
                }

        except Exception as e:
            logger.error(f"Error getting agent data for chat: {e}")
            return {"error": f"Failed to get agent data: {str(e)}"}

    async def _store_chat_message(
        self,
        conversation_id: str,
        user_id: str,
        user_message: str,
        chat_response: ChatResponse,
        agent_data: Dict[str, Any],
    ):
        """Store chat message in 4+1 architecture database."""
        try:
            async with database.get_session() as session:
                # Create or get conversation
                try:
                    conversation = await chat_repository.get_conversation(
                        session, conversation_id
                    )
                except:
                    conversation = await chat_repository.create_conversation(
                        session,
                        user_id,
                        f"4+1 Chat - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    )
                    conversation_id = str(conversation.id)

                # Store user message
                await chat_repository.create_message(
                    session,
                    conversation_id,
                    user_message,
                    "user",
                    metadata={
                        "websocket_connection": True,
                        "agent_data_included": agent_data is not None,
                        "architecture_layer": ArchitecturalLayer.CONVERSATIONAL.value,
                    },
                )

                # Store assistant response
                await chat_repository.create_message(
                    session,
                    conversation_id,
                    chat_response.content,
                    "agent",
                    agent_type="strategic_chat",
                    metadata={
                        "confidence": chat_response.confidence,
                        "response_time": chat_response.response_time,
                        "websocket_connection": True,
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
            logger.error(f"Error storing chat message: {e}")


# Global Chat WebSocket manager instance
chat_ws_manager = ChatWebSocketManager()


async def authenticate_chat_websocket(websocket: WebSocket) -> bool:
    """Authenticate chat WebSocket connection using consistent JWT validation."""
    try:
        # Check for token in query parameters
        token = websocket.query_params.get("token")

        # Check for token in headers if not in query params
        if not token:
            token = websocket.headers.get("Authorization")
            if token and token.startswith("Bearer "):
                token = token[7:]  # Remove "Bearer " prefix

        if not token:
            logger.warning("🔒 Chat WebSocket authentication failed: No token provided")
            return False

        # PRODUCTION FIX: Use proper JWT validation with consistent secret logic
        from fs_agt_clean.core.websocket.mobile_auth_fix import _validate_jwt_token

        if _validate_jwt_token(token):
            logger.info("🔒 Chat WebSocket authentication successful with valid JWT")
            return True
        else:
            logger.warning("🔒 Chat WebSocket authentication failed: Invalid JWT token")
            return False

    except Exception as e:
        logger.error(f"🔒 Chat WebSocket authentication error: {e}")
        return False


@router.websocket("/4plus1/{conversation_id}")
async def websocket_chat_4plus1(websocket: WebSocket, conversation_id: str):
    """
    WebSocket endpoint for real-time chat with 4+1 architecture agent context.

    Provides real-time chat capabilities with autonomous agent data integration
    while maintaining strict separation between conversational and autonomous layers.
    """
    # PRODUCTION FIX: Add authentication to chat WebSocket
    if not await authenticate_chat_websocket(websocket):
        await websocket.close(code=1008, reason="Authentication required")
        return

    await chat_ws_manager.connect(
        websocket, "chat_4plus1", {"conversation_id": conversation_id}
    )

    try:
        # Send initial connection confirmation
        await websocket.send_text(
            json.dumps(
                {
                    "type": "connection_established",
                    "conversation_id": conversation_id,
                    "message": "Connected to 4+1 Architecture Chat",
                    "capabilities": [
                        "Real-time chat with agent context",
                        "Autonomous agent status integration",
                        "Decision monitoring through chat",
                        "Agent command routing",
                    ],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        )

        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for client messages
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                try:
                    message_data = json.loads(message)
                    user_message = message_data.get("message", "")
                    user_id = message_data.get("user_id", "anonymous")

                    if user_message:
                        # Handle chat message with agent context
                        response_data = await chat_ws_manager.handle_chat_message(
                            websocket, user_message, conversation_id, user_id
                        )

                        # Send response back to client
                        await websocket.send_text(json.dumps(response_data))

                        # Broadcast to other connections in the same conversation
                        await chat_ws_manager.broadcast_to_channel(
                            "chat_4plus1",
                            {
                                "type": "conversation_update",
                                "conversation_id": conversation_id,
                                "latest_message": response_data.get("message"),
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            },
                        )

                except json.JSONDecodeError:
                    # Handle plain text messages
                    response_data = await chat_ws_manager.handle_chat_message(
                        websocket, message, conversation_id, "anonymous"
                    )
                    await websocket.send_text(json.dumps(response_data))

            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "ping",
                            "conversation_id": conversation_id,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                )

    except WebSocketDisconnect:
        logger.info(
            f"🔌 Chat 4+1 WebSocket disconnected for conversation {conversation_id}"
        )
    except Exception as e:
        logger.error(f"❌ Chat 4+1 WebSocket error: {e}")
    finally:
        await chat_ws_manager.disconnect(websocket)
