"""
Unified WebSocket System for FlipSync Agentic Architecture
=========================================================

This module provides the integrated WebSocket solution that consolidates:
- Chat messaging with agent routing
- Agent status monitoring
- System notifications
- Real-time updates

Replaces multiple conflicting endpoints with single /ws/flipsync endpoint.
"""

# NOTE: OrchestrationService disabled for 4+1 architecture compliance


import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from fs_agt_clean.api.dependencies.dependencies import (
    get_agent_manager,
    get_orchestration_service,
    get_pipeline_controller,
    get_state_manager,
    DisabledOrchestrationService,
)
from fs_agt_clean.core.agents.autonomous_agent_manager import AutonomousAgentManager
from fs_agt_clean.core.pipeline.controller import PipelineController
from fs_agt_clean.core.state_management.state_manager import StateManager
from fs_agt_clean.core.websocket.manager import websocket_manager
from fs_agt_clean.services.workflows.conversational_interface import (
    ConversationMode,
    ConversationalInterfaceRequest,
    ConversationalInterfaceWorkflow,
    ResponseStyle,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket-unified"])


class UnifiedWebSocketMessage(BaseModel):
    """Unified message format for all WebSocket communication."""

    type: str = Field(
        ...,
        description="Message type: chat_message, agent_status, system_notification, typing",
    )
    conversation_id: Optional[str] = Field(None, description="Conversation identifier")
    data: Dict[str, Any] = Field(default_factory=dict, description="Message payload")
    routing: Optional[Dict[str, Any]] = Field(None, description="Routing information")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class UnifiedWebSocketHandler:
    """Unified handler for all WebSocket message types."""

    def __init__(
        self,
        agent_manager: AutonomousAgentManager,
        orchestration_service: DisabledOrchestrationService,
        pipeline_controller: PipelineController,
        state_manager: StateManager,
    ):
        self.agent_manager = agent_manager
        self.orchestration_service = orchestration_service
        self.pipeline_controller = pipeline_controller
        self.state_manager = state_manager
        self.response_queue: Dict[str, List[Dict[str, Any]]] = {}

        logger.info("Unified WebSocket Handler initialized")

    async def handle_message(
        self, websocket: WebSocket, client_id: str, message: UnifiedWebSocketMessage
    ) -> Optional[Dict[str, Any]]:
        """Route message to appropriate handler based on type."""
        try:
            if message.type == "chat_message":
                return await self._handle_chat_message(websocket, client_id, message)
            elif message.type == "agent_status":
                return await self._handle_agent_status(websocket, client_id, message)
            elif message.type == "system_notification":
                return await self._handle_system_notification(
                    websocket, client_id, message
                )
            elif message.type == "typing":
                return await self._handle_typing(websocket, client_id, message)
            elif message.type == "ping":
                return {
                    "type": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            else:
                logger.warning(f"Unknown message type: {message.type}")
                return {
                    "type": "error",
                    "message": f"Unknown message type: {message.type}",
                }

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return {"type": "error", "message": str(e)}

    async def _handle_chat_message(
        self, websocket: WebSocket, client_id: str, message: UnifiedWebSocketMessage
    ) -> Dict[str, Any]:
        """Handle chat messages with agent routing."""
        try:
            conversation_id = message.conversation_id or str(uuid4())
            user_message = message.data.get("message", "")

            if not user_message:
                return {"type": "error", "message": "Empty message"}

            # Send processing indicator
            await self._send_processing_indicator(websocket, conversation_id)

            # Create conversational interface request
            request = ConversationalInterfaceRequest(
                user_message=user_message,
                conversation_id=conversation_id,
                user_id=message.data.get("user_id"),
                conversation_mode=ConversationMode.SINGLE_QUERY,  # Fixed: Use valid enum value
                response_style=ResponseStyle.BUSINESS_FOCUSED,  # Fixed: Use valid enum value
                user_context=message.data.get("context", {}),
                personalization_preferences=message.routing or {},
            )

            # Process through conversational workflow
            workflow = ConversationalInterfaceWorkflow(
                agent_manager=self.agent_manager,
                orchestration_service=self.orchestration_service,
                pipeline_controller=self.pipeline_controller,
                state_manager=self.state_manager,
            )

            # Execute workflow and stream responses
            final_response_sent = False
            async for response_chunk in workflow.execute_streaming(request):
                response_message = {
                    "type": "agent_response_stream",
                    "conversation_id": conversation_id,
                    "data": response_chunk,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                await websocket.send_text(json.dumps(response_message))

                # Check if this is the final response
                if (
                    response_chunk.get("status") == "completed"
                    and response_chunk.get("step") == "final_response"
                ):
                    final_response_sent = True
                    # Add a small delay immediately after sending the final response
                    await asyncio.sleep(0.1)

                    logger.info(
                        f"🚀 WEBSOCKET DEBUG: Final response sent to client {client_id}"
                    )

            # Ensure final response was delivered before returning
            if final_response_sent:
                # Send a completion confirmation message
                completion_message = {
                    "type": "workflow_completed",
                    "conversation_id": conversation_id,
                    "data": {
                        "status": "completed",
                        "message": "Workflow processing complete",
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                await websocket.send_text(json.dumps(completion_message))

                # Extended delay to ensure client receives all messages
                await asyncio.sleep(1.0)  # Increased to 1 second
                logger.info(
                    f"🚀 WEBSOCKET DEBUG: Completion signal sent and extended delay (1000ms) applied"
                )

            return {
                "type": "message_processed",
                "conversation_id": conversation_id,
                "status": "completed",
            }

        except Exception as e:
            logger.error(f"Error handling chat message: {e}")
            return {"type": "error", "message": str(e)}

    async def _handle_agent_status(
        self, websocket: WebSocket, client_id: str, message: UnifiedWebSocketMessage
    ) -> Dict[str, Any]:
        """Handle agent status requests."""
        try:
            agent_id = message.data.get("agent_id")

            if agent_id:
                # Get specific agent status
                agent_status = await self.agent_manager.get_agent_status(agent_id)
                return {
                    "type": "agent_status_response",
                    "agent_id": agent_id,
                    "status": agent_status,
                }
            else:
                # Get all agent statuses
                all_statuses = await self.agent_manager.get_all_agent_statuses()
                return {"type": "all_agent_statuses", "statuses": all_statuses}

        except Exception as e:
            logger.error(f"Error handling agent status: {e}")
            return {"type": "error", "message": str(e)}

    async def _handle_system_notification(
        self, websocket: WebSocket, client_id: str, message: UnifiedWebSocketMessage
    ) -> Dict[str, Any]:
        """Handle system notifications."""
        # System notifications are typically broadcast, so just acknowledge
        return {
            "type": "notification_received",
            "notification_id": message.data.get("notification_id"),
        }

    async def _handle_typing(
        self, websocket: WebSocket, client_id: str, message: UnifiedWebSocketMessage
    ) -> Dict[str, Any]:
        """Handle typing indicators."""
        conversation_id = message.conversation_id
        if conversation_id:
            # Broadcast typing indicator to other clients in conversation
            await websocket_manager.send_to_conversation(
                conversation_id,
                {
                    "type": "typing",
                    "client_id": client_id,
                    "is_typing": message.data.get("is_typing", False),
                },
                exclude_client=client_id,
            )

        return {"type": "typing_acknowledged"}

    async def _send_processing_indicator(
        self, websocket: WebSocket, conversation_id: str
    ):
        """Send processing indicator to prevent client timeout."""
        await websocket.send_text(
            json.dumps(
                {
                    "type": "processing",
                    "conversation_id": conversation_id,
                    "status": "agent_thinking",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        )


async def authenticate_websocket_unified(
    websocket: WebSocket, token: Optional[str] = None
) -> bool:
    """
    Authenticate WebSocket connection using token from query parameters or headers.

    Returns:
        bool: True if authenticated, False otherwise
    """
    try:
        logger.info("🔒 WebSocket authentication function called")

        # Check for token in query parameters first
        if not token:
            token = websocket.query_params.get("token")
            logger.info(
                f"🔒 Token from query params: {'Found' if token else 'Not found'}"
            )

        # Check for token in headers if not in query params
        if not token:
            auth_header = websocket.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]  # Remove "Bearer " prefix
                logger.info("🔒 Token from Authorization header: Found")
            else:
                logger.info("🔒 Token from Authorization header: Not found")

        if not token:
            logger.warning(
                "🔒 Unified WebSocket authentication failed: No token provided"
            )
            return False

        logger.info(f"🔒 Token received: {token[:30]}...")

        # PRODUCTION FIX: Use proper JWT validation with consistent secret logic
        from fs_agt_clean.core.websocket.mobile_auth_fix import _validate_jwt_token

        if _validate_jwt_token(token):
            logger.info("🔒 Unified WebSocket authentication successful with valid JWT")
            return True
        else:
            logger.warning(
                "🔒 Unified WebSocket authentication failed: Invalid JWT token"
            )
            return False

    except Exception as e:
        logger.error(f"🔒 Unified WebSocket authentication error: {e}")
        return False


@router.websocket("/test")
async def test_websocket_endpoint(websocket: WebSocket):
    """Simple test WebSocket endpoint to debug routing issues."""
    logger.info("🔒 TEST WebSocket endpoint called!")
    await websocket.accept()
    await websocket.send_text(
        json.dumps({"type": "test", "message": "Test endpoint working"})
    )
    await websocket.close()


@router.websocket("/flipsync")
async def unified_websocket_endpoint(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None, description="Client identifier"),
    user_id: Optional[str] = Query(None, description="User identifier"),
    conversation_id: Optional[str] = Query(None, description="Conversation identifier"),
    token: Optional[str] = Query(None, description="Authentication token"),
):
    """
    Unified WebSocket endpoint for all FlipSync real-time communication.

    Handles:
    - Chat messages with agent routing
    - Agent status monitoring
    - System notifications
    - Typing indicators
    - Real-time updates

    Message Format:
    {
        "type": "chat_message|agent_status|system_notification|typing",
        "conversation_id": "uuid",
        "data": { ... },
        "routing": { "target_agent": "market_agent", "priority": "high" },
        "metadata": { ... }
    }
    """
    if not client_id:
        client_id = f"unified_client_{uuid4()}"

    logger.info(
        f"Unified WebSocket connection: client={client_id}, user={user_id}, conversation={conversation_id}"
    )

    # FIXED: Accept WebSocket connection first, then authenticate
    await websocket.accept()

    # Authenticate WebSocket connection after accepting
    if not await authenticate_websocket_unified(websocket, token):
        await websocket.close(code=1008, reason="Authentication required")
        return

    try:
        # Send connection confirmation
        await websocket.send_text(
            json.dumps(
                {
                    "type": "connection_established",
                    "client_id": client_id,
                    "server_time": datetime.now(timezone.utc).isoformat(),
                    "capabilities": [
                        "chat_message",
                        "agent_status",
                        "system_notification",
                        "typing",
                        "real_time_updates",
                    ],
                }
            )
        )

        # Message handling loop
        while True:
            try:
                # Receive message with timeout
                raw_message = await asyncio.wait_for(
                    websocket.receive_text(), timeout=300.0  # 5 minutes timeout
                )

                # Parse message
                try:
                    message_data = json.loads(raw_message)
                    message = UnifiedWebSocketMessage(**message_data)
                except (json.JSONDecodeError, ValueError) as e:
                    await websocket.send_text(
                        json.dumps(
                            {"type": "error", "message": f"Invalid message format: {e}"}
                        )
                    )
                    continue

                # Simple echo response for now
                response = {
                    "type": "echo",
                    "original_message": message_data,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "client_id": client_id,
                    "status": "received",
                }

                # Send response if available
                if response:
                    await websocket.send_text(json.dumps(response))

            except asyncio.TimeoutError:
                # Send ping to check connection
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "ping",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                )
            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected")
                break
            except Exception as e:
                logger.error(f"Error handling message from client {client_id}: {e}")
                await websocket.send_text(
                    json.dumps({"type": "error", "message": "Internal server error"})
                )

    except WebSocketDisconnect:
        logger.info(f"Unified WebSocket disconnected: client={client_id}")
    except Exception as e:
        logger.error(f"Unified WebSocket error: {e}")
    finally:
        # Cleanup connection
        logger.info(f"Unified WebSocket cleanup completed: client={client_id}")
