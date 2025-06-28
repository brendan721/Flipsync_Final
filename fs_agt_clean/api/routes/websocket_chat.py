"""
WebSocket Chat System for FlipSync Frontend Integration.

This module provides the WebSocket chat endpoint with intelligent agent routing
and real-time conversational interface integration.

Features:
- WebSocket endpoint at /ws/chat with agent routing capabilities
- Real-time conversational interface integration with Phase 2 Conversational Interface Workflow
- Intelligent agent selection based on user intent
- Real-time progress updates for ongoing workflows
- Integration with the foundation layer (Pipeline Controller, UnifiedAgent Manager, WebSocket system, State Management)
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from fs_agt_clean.api.dependencies.dependencies import (
    get_agent_manager,
    get_orchestration_service,
    get_pipeline_controller,
    get_state_manager,
)
from fs_agt_clean.core.agents.real_agent_manager import RealUnifiedAgentManager
from fs_agt_clean.core.pipeline.controller import PipelineController
from fs_agt_clean.core.state_management.state_manager import StateManager
from fs_agt_clean.core.websocket.events import (
    UnifiedAgentType,
    EventType,
    SenderType,
    WebSocketMessage,
    create_message_event,
    create_typing_event,
)
from fs_agt_clean.core.websocket.manager import websocket_manager
from fs_agt_clean.services.agent_orchestration import UnifiedAgentOrchestrationService
from fs_agt_clean.services.workflows.conversational_interface import (
    ConversationMode,
    ConversationalInterfaceRequest,
    ConversationalInterfaceWorkflow,
    ResponseStyle,
)

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(tags=["websocket-chat"])


class ChatMessage(BaseModel):
    """Chat message structure for WebSocket communication."""

    type: str = Field(description="Message type")
    content: str = Field(description="Message content")
    conversation_id: str = Field(description="Conversation identifier")
    user_id: Optional[str] = Field(default=None, description="UnifiedUser identifier")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class ChatResponse(BaseModel):
    """Chat response structure for WebSocket communication."""

    type: str = Field(description="Response type")
    content: str = Field(description="Response content")
    conversation_id: str = Field(description="Conversation identifier")
    agent_type: Optional[str] = Field(default=None, description="Responding agent type")
    confidence: Optional[float] = Field(default=None, description="Response confidence")
    workflow_id: Optional[str] = Field(
        default=None, description="Associated workflow ID"
    )
    agents_consulted: List[str] = Field(
        default_factory=list, description="UnifiedAgents consulted"
    )
    follow_up_suggestions: List[str] = Field(
        default_factory=list, description="Follow-up suggestions"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class WebSocketChatHandler:
    """WebSocket chat handler with conversational interface integration."""

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

        # Initialize conversational interface workflow
        self.conversational_workflow = ConversationalInterfaceWorkflow(
            agent_manager=agent_manager,
            pipeline_controller=pipeline_controller,
            state_manager=state_manager,
            orchestration_service=orchestration_service,
        )

        # Chat session tracking
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.conversation_history: Dict[str, List[Dict[str, Any]]] = {}

        logger.info(
            "WebSocket Chat Handler initialized with Conversational Interface Workflow"
        )

    async def handle_connection(
        self,
        websocket: WebSocket,
        client_id: str,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ):
        """Handle new WebSocket connection for chat."""
        try:
            # Generate conversation ID if not provided
            if not conversation_id:
                conversation_id = f"chat_{int(time.time())}_{client_id[:8]}"

            # Connect to WebSocket manager
            connection = await websocket_manager.connect(
                websocket=websocket,
                client_id=client_id,
                user_id=user_id,
                conversation_id=conversation_id,
            )

            # Initialize chat session
            self.active_sessions[client_id] = {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "connected_at": datetime.now(timezone.utc).isoformat(),
                "message_count": 0,
                "last_activity": time.time(),
            }

            # Initialize conversation history
            if conversation_id not in self.conversation_history:
                self.conversation_history[conversation_id] = []

            logger.info(
                f"Chat connection established: {client_id} -> {conversation_id}"
            )

            # Send welcome message
            welcome_message = {
                "type": "system_message",
                "content": "Welcome to FlipSync! I'm your AI assistant ready to help with e-commerce automation, product analysis, sales optimization, and more. How can I assist you today?",
                "conversation_id": conversation_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent_type": "system",
                "metadata": {
                    "available_capabilities": [
                        "Product Analysis & Listing Creation",
                        "Sales Optimization & Competitive Analysis",
                        "Market Synchronization & Inventory Management",
                        "Business Strategy & Decision Support",
                        "Real-time Workflow Automation",
                    ]
                },
            }

            await websocket_manager.send_to_client(client_id, welcome_message)

            # Start message handling loop
            await self._handle_messages(websocket, client_id, conversation_id, user_id)

        except WebSocketDisconnect:
            logger.info(f"Chat client {client_id} disconnected")
            await self._cleanup_session(client_id)
        except Exception as e:
            logger.error(f"Error handling chat connection {client_id}: {e}")
            await self._cleanup_session(client_id)

    async def _handle_messages(
        self,
        websocket: WebSocket,
        client_id: str,
        conversation_id: str,
        user_id: Optional[str],
    ):
        """Handle incoming WebSocket messages."""
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)

                # Update session activity
                if client_id in self.active_sessions:
                    self.active_sessions[client_id]["last_activity"] = time.time()
                    self.active_sessions[client_id]["message_count"] += 1

                # Process message based on type
                message_type = message_data.get("type", "message")

                if message_type == "message":
                    await self._handle_chat_message(
                        client_id, conversation_id, user_id, message_data
                    )
                elif message_type == "typing":
                    await self._handle_typing_indicator(
                        client_id, conversation_id, user_id, message_data
                    )
                elif message_type == "pong":
                    # Update ping response
                    if client_id in websocket_manager.active_connections:
                        websocket_manager.active_connections[client_id].last_ping = (
                            time.time()
                        )
                else:
                    logger.warning(f"Unknown message type: {message_type}")

        except WebSocketDisconnect:
            logger.info(f"Chat client {client_id} disconnected during message handling")
        except Exception as e:
            logger.error(f"Error handling messages for {client_id}: {e}")
            # Send error message to client
            error_message = {
                "type": "error",
                "content": "An error occurred processing your message. Please try again.",
                "conversation_id": conversation_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error_code": "message_processing_error",
            }
            await websocket_manager.send_to_client(client_id, error_message)

    async def _handle_chat_message(
        self,
        client_id: str,
        conversation_id: str,
        user_id: Optional[str],
        message_data: Dict[str, Any],
    ):
        """Handle chat message with conversational interface workflow integration."""
        try:
            user_message = message_data.get("content", "").strip()
            if not user_message:
                return

            logger.info(
                f"Processing chat message from {client_id}: {user_message[:100]}..."
            )

            # Add user message to conversation history
            user_message_entry = {
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": user_id,
            }
            self.conversation_history[conversation_id].append(user_message_entry)

            # Send typing indicator
            await self._send_typing_indicator(conversation_id, True, "assistant")

            # Determine conversation mode and response style
            conversation_mode = self._determine_conversation_mode(
                user_message, conversation_id
            )
            response_style = self._determine_response_style(
                user_message, message_data.get("metadata", {})
            )

            # Create conversational interface request
            conversational_request = ConversationalInterfaceRequest(
                user_message=user_message,
                conversation_mode=conversation_mode,
                response_style=response_style,
                conversation_history=self.conversation_history[conversation_id],
                user_context=message_data.get("metadata", {}).get("user_context", {}),
                personalization_preferences=message_data.get("metadata", {}).get(
                    "preferences", {}
                ),
                conversation_id=conversation_id,
                user_id=user_id,
            )

            # Execute conversational interface workflow
            workflow_result = await self.conversational_workflow.process_conversation(
                conversational_request
            )

            # Stop typing indicator
            await self._send_typing_indicator(conversation_id, False, "assistant")

            # Send response to client
            if workflow_result.success:
                response_message = {
                    "type": "message",
                    "content": workflow_result.final_response,
                    "conversation_id": conversation_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "sender": "agent",
                    "agent_type": "assistant",
                    "confidence": workflow_result.confidence_score,
                    "workflow_id": workflow_result.workflow_id,
                    "agents_consulted": workflow_result.agents_consulted,
                    "follow_up_suggestions": workflow_result.follow_up_suggestions,
                    "metadata": {
                        "intent_recognition": workflow_result.intent_recognition_results,
                        "agent_routing": workflow_result.agent_routing_results,
                        "execution_time": workflow_result.execution_time_seconds,
                        "agents_involved": workflow_result.agents_involved,
                    },
                }

                # Add assistant response to conversation history
                assistant_message_entry = {
                    "role": "assistant",
                    "content": workflow_result.final_response,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "workflow_id": workflow_result.workflow_id,
                    "confidence": workflow_result.confidence_score,
                    "agents_consulted": workflow_result.agents_consulted,
                }
                self.conversation_history[conversation_id].append(
                    assistant_message_entry
                )

            else:
                response_message = {
                    "type": "error",
                    "content": workflow_result.final_response,
                    "conversation_id": conversation_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "error_code": "workflow_execution_error",
                    "error_message": workflow_result.error_message,
                }

            await websocket_manager.send_to_client(client_id, response_message)

            logger.info(
                f"Chat response sent to {client_id} (workflow: {workflow_result.workflow_id})"
            )

        except Exception as e:
            logger.error(f"Error handling chat message from {client_id}: {e}")
            # Send error response
            error_response = {
                "type": "error",
                "content": "I apologize, but I encountered an issue processing your message. Please try again.",
                "conversation_id": conversation_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error_code": "chat_processing_error",
            }
            await websocket_manager.send_to_client(client_id, error_response)

    async def _handle_typing_indicator(
        self,
        client_id: str,
        conversation_id: str,
        user_id: Optional[str],
        message_data: Dict[str, Any],
    ):
        """Handle typing indicator events."""
        try:
            is_typing = message_data.get("is_typing", False)

            # Broadcast typing indicator to other clients in conversation
            typing_event = create_typing_event(
                conversation_id=conversation_id,
                is_typing=is_typing,
                user_id=user_id,
            )

            # Send to all clients in conversation except sender
            await websocket_manager.send_to_conversation(
                conversation_id, typing_event.dict()
            )

        except Exception as e:
            logger.error(f"Error handling typing indicator from {client_id}: {e}")

    async def _send_typing_indicator(
        self,
        conversation_id: str,
        is_typing: bool,
        agent_type: str = "assistant",
    ):
        """Send typing indicator for agent responses."""
        try:
            typing_event = create_typing_event(
                conversation_id=conversation_id,
                is_typing=is_typing,
                agent_type=UnifiedAgentType.ASSISTANT if agent_type == "assistant" else None,
            )

            await websocket_manager.send_to_conversation(
                conversation_id, typing_event.dict()
            )

        except Exception as e:
            logger.error(f"Error sending typing indicator: {e}")

    def _determine_conversation_mode(
        self, user_message: str, conversation_id: str
    ) -> ConversationMode:
        """Determine conversation mode based on message content and history."""
        try:
            # Check conversation history length
            history_length = len(self.conversation_history.get(conversation_id, []))

            # Analyze message content for mode indicators
            message_lower = user_message.lower()

            # Workflow-guided mode indicators
            workflow_keywords = [
                "create product",
                "analyze image",
                "optimize sales",
                "sync inventory",
                "generate listing",
                "competitive analysis",
                "workflow",
                "automation",
            ]

            if any(keyword in message_lower for keyword in workflow_keywords):
                return ConversationMode.WORKFLOW_GUIDED

            # Multi-turn conversation indicators
            if history_length > 2:
                return ConversationMode.MULTI_TURN

            # Contextual assistance indicators
            contextual_keywords = [
                "help with",
                "assist me",
                "guide me",
                "show me how",
                "what should i",
                "how do i",
                "can you help",
            ]

            if any(keyword in message_lower for keyword in contextual_keywords):
                return ConversationMode.CONTEXTUAL_ASSISTANCE

            # Default to single query
            return ConversationMode.SINGLE_QUERY

        except Exception as e:
            logger.warning(f"Error determining conversation mode: {e}")
            return ConversationMode.SINGLE_QUERY

    def _determine_response_style(
        self, user_message: str, metadata: Dict[str, Any]
    ) -> ResponseStyle:
        """Determine response style based on message content and user preferences."""
        try:
            # Check user preferences in metadata
            preferred_style = metadata.get("response_style")
            if preferred_style and hasattr(ResponseStyle, preferred_style.upper()):
                return getattr(ResponseStyle, preferred_style.upper())

            # Analyze message content for style indicators
            message_lower = user_message.lower()

            # Technical style indicators
            technical_keywords = [
                "api",
                "integration",
                "technical",
                "code",
                "implementation",
                "configuration",
                "setup",
                "parameters",
                "algorithm",
            ]

            if any(keyword in message_lower for keyword in technical_keywords):
                return ResponseStyle.TECHNICAL

            # Detailed style indicators
            detailed_keywords = [
                "explain",
                "detailed",
                "comprehensive",
                "step by step",
                "in depth",
                "thorough",
                "complete guide",
            ]

            if any(keyword in message_lower for keyword in detailed_keywords):
                return ResponseStyle.DETAILED

            # Concise style indicators
            concise_keywords = [
                "quick",
                "brief",
                "short",
                "summary",
                "tldr",
                "simple",
                "fast",
                "just tell me",
            ]

            if any(keyword in message_lower for keyword in concise_keywords):
                return ResponseStyle.CONCISE

            # Default to business focused
            return ResponseStyle.BUSINESS_FOCUSED

        except Exception as e:
            logger.warning(f"Error determining response style: {e}")
            return ResponseStyle.BUSINESS_FOCUSED

    async def _cleanup_session(self, client_id: str):
        """Clean up chat session resources."""
        try:
            # Remove from active sessions
            if client_id in self.active_sessions:
                session_info = self.active_sessions[client_id]
                conversation_id = session_info.get("conversation_id")

                # Clean up conversation history if no other active sessions
                if conversation_id and conversation_id in self.conversation_history:
                    # Check if other clients are still in this conversation
                    active_in_conversation = any(
                        session.get("conversation_id") == conversation_id
                        for cid, session in self.active_sessions.items()
                        if cid != client_id
                    )

                    if not active_in_conversation:
                        # Archive conversation history (keep last 50 messages)
                        if len(self.conversation_history[conversation_id]) > 50:
                            self.conversation_history[conversation_id] = (
                                self.conversation_history[conversation_id][-50:]
                            )

                del self.active_sessions[client_id]
                logger.info(f"Cleaned up chat session for {client_id}")

            # Disconnect from WebSocket manager
            await websocket_manager.disconnect(client_id, "session_cleanup")

        except Exception as e:
            logger.error(f"Error cleaning up session {client_id}: {e}")

    def get_session_stats(self) -> Dict[str, Any]:
        """Get current chat session statistics."""
        try:
            total_sessions = len(self.active_sessions)
            total_conversations = len(self.conversation_history)

            # Calculate session metrics
            session_durations = []
            message_counts = []
            current_time = time.time()

            for session in self.active_sessions.values():
                connected_at = datetime.fromisoformat(
                    session["connected_at"].replace("Z", "+00:00")
                )
                duration = current_time - connected_at.timestamp()
                session_durations.append(duration)
                message_counts.append(session["message_count"])

            avg_session_duration = (
                sum(session_durations) / len(session_durations)
                if session_durations
                else 0
            )
            avg_messages_per_session = (
                sum(message_counts) / len(message_counts) if message_counts else 0
            )

            return {
                "active_sessions": total_sessions,
                "total_conversations": total_conversations,
                "average_session_duration_seconds": avg_session_duration,
                "average_messages_per_session": avg_messages_per_session,
                "websocket_stats": websocket_manager.get_connection_stats(),
            }

        except Exception as e:
            logger.error(f"Error getting session stats: {e}")
            return {"error": str(e)}


# Global chat handler instance
_chat_handler: Optional[WebSocketChatHandler] = None


async def get_chat_handler(
    agent_manager: RealUnifiedAgentManager = Depends(get_agent_manager),
    pipeline_controller: PipelineController = Depends(get_pipeline_controller),
    state_manager: StateManager = Depends(get_state_manager),
    orchestration_service: UnifiedAgentOrchestrationService = Depends(
        get_orchestration_service
    ),
) -> WebSocketChatHandler:
    """Get or create the global chat handler instance."""
    global _chat_handler

    if _chat_handler is None:
        _chat_handler = WebSocketChatHandler(
            agent_manager=agent_manager,
            pipeline_controller=pipeline_controller,
            state_manager=state_manager,
            orchestration_service=orchestration_service,
        )

    return _chat_handler


@router.websocket("/ws/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    client_id: str,
    user_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    chat_handler: WebSocketChatHandler = Depends(get_chat_handler),
):
    """
    WebSocket chat endpoint with intelligent agent routing.

    This endpoint provides:
    - Real-time conversational interface with FlipSync's 35+ agent ecosystem
    - Intelligent agent routing based on user intent recognition
    - Integration with Phase 2 Conversational Interface Workflow
    - Real-time progress updates for ongoing workflows
    - Multi-agent coordination for complex business automation tasks

    Query Parameters:
    - client_id: Unique client identifier (required)
    - user_id: UnifiedUser identifier for personalization (optional)
    - conversation_id: Conversation identifier for session continuity (optional)
    """
    await chat_handler.handle_connection(
        websocket=websocket,
        client_id=client_id,
        user_id=user_id,
        conversation_id=conversation_id,
    )


@router.get("/chat/stats")
async def get_chat_stats(
    chat_handler: WebSocketChatHandler = Depends(get_chat_handler),
):
    """Get current chat system statistics."""
    return chat_handler.get_session_stats()
