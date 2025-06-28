"""
WebSocket Integration for Conversational UnifiedAgents
==============================================

This module provides real-time WebSocket integration for conversational agents,
enabling live agent responses, approval notifications, and status updates.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fs_agt_clean.agents.base_conversational_agent import UnifiedAgentResponse
from fs_agt_clean.core.websocket.events import (
    UnifiedAgentType,
    EventType,
    SenderType,
    create_agent_status_event,
    create_message_event,
    create_system_alert_event,
    create_typing_event,
)
from fs_agt_clean.core.websocket.manager import websocket_manager
from fs_agt_clean.services.approval import ApprovalIntegrationService

logger = logging.getLogger(__name__)


class ConversationalUnifiedAgentWebSocketIntegration:
    """
    Integrates conversational agents with WebSocket for real-time communication.

    Features:
    - Real-time agent response streaming
    - Approval workflow notifications
    - UnifiedAgent status broadcasting
    - Performance monitoring (<100ms latency)
    """

    def __init__(self, approval_service: Optional[ApprovalIntegrationService] = None):
        """Initialize the WebSocket integration service."""
        self.approval_service = approval_service or ApprovalIntegrationService()

        # Performance tracking
        self.response_times = []
        self.max_response_time = 0.1  # 100ms target

        # UnifiedAgent type mapping
        self.agent_type_mapping = {
            "content": UnifiedAgentType.CONTENT,
            "logistics": UnifiedAgentType.LOGISTICS,
            "executive": UnifiedAgentType.EXECUTIVE,
            "market": UnifiedAgentType.MARKET,
            "assistant": UnifiedAgentType.ASSISTANT,
        }

        logger.info("Conversational UnifiedAgent WebSocket Integration initialized")

    async def stream_agent_response(
        self,
        agent_response: UnifiedAgentResponse,
        conversation_id: str,
        user_id: str,
        original_message: str,
        stream_chunks: bool = True,
    ) -> Dict[str, Any]:
        """
        Stream agent response through WebSocket with real-time updates.

        Args:
            agent_response: The agent response to stream
            conversation_id: Target conversation ID
            user_id: UnifiedUser who initiated the request
            original_message: Original user message
            stream_chunks: Whether to stream response in chunks

        Returns:
            Dictionary with streaming results and approval info
        """
        start_time = time.time()

        try:
            # Get agent type for WebSocket events
            ws_agent_type = self.agent_type_mapping.get(
                agent_response.agent_type, UnifiedAgentType.ASSISTANT
            )

            # Send typing indicator
            await self._send_typing_indicator(conversation_id, ws_agent_type, True)

            # Process approval workflow if needed
            approval_result = await self.approval_service.process_agent_response(
                agent_response=agent_response,
                user_id=user_id,
                conversation_id=conversation_id,
                original_message=original_message,
            )

            # Stream response content
            if stream_chunks and len(agent_response.content) > 100:
                await self._stream_response_chunks(
                    conversation_id, agent_response.content, ws_agent_type
                )
            else:
                await self._send_complete_response(
                    conversation_id, agent_response, ws_agent_type
                )

            # Send approval notifications if needed
            if approval_result.get("approval_required"):
                await self._send_approval_notification(
                    conversation_id, approval_result, user_id
                )

            # Stop typing indicator
            await self._send_typing_indicator(conversation_id, ws_agent_type, False)

            # Track performance
            response_time = time.time() - start_time
            self._track_performance(response_time)

            return {
                "success": True,
                "response_time": response_time,
                "approval_result": approval_result,
                "recipients": websocket_manager.get_conversation_client_count(
                    conversation_id
                ),
            }

        except Exception as e:
            logger.error(f"Error streaming agent response: {e}")

            # Send error notification
            await self._send_error_notification(conversation_id, str(e))

            return {
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time,
            }

    async def broadcast_agent_status(
        self,
        agent_id: str,
        agent_type: str,
        status: str,
        metrics: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None,
    ) -> int:
        """
        Broadcast agent status updates through WebSocket.

        Args:
            agent_id: UnifiedAgent identifier
            agent_type: Type of agent
            status: Current status
            metrics: Performance metrics
            conversation_id: Optional conversation to target

        Returns:
            Number of recipients
        """
        try:
            ws_agent_type = self.agent_type_mapping.get(agent_type, UnifiedAgentType.ASSISTANT)

            # Create status event
            status_event = create_agent_status_event(
                agent_id=agent_id,
                agent_type=ws_agent_type,
                status=status,
                metrics=metrics or {},
                error_message=None,
            )

            # Broadcast to appropriate audience
            if conversation_id:
                recipients = await websocket_manager.send_to_conversation(
                    conversation_id, status_event.dict()
                )
            else:
                recipients = await websocket_manager.broadcast(status_event.dict())

            logger.debug(
                f"UnifiedAgent status broadcasted: {agent_id} -> {status} ({recipients} recipients)"
            )
            return recipients

        except Exception as e:
            logger.error(f"Error broadcasting agent status: {e}")
            return 0

    async def send_approval_update(
        self,
        approval_id: str,
        status: str,
        approved_by: Optional[str] = None,
        reason: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> int:
        """
        Send approval workflow updates through WebSocket.

        Args:
            approval_id: Approval workflow identifier
            status: New approval status
            approved_by: Who approved/rejected
            reason: Reason for decision
            conversation_id: Target conversation

        Returns:
            Number of recipients
        """
        try:
            # Create approval update event
            approval_event = {
                "type": EventType.AGENT_DECISION,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "approval_id": approval_id,
                    "status": status,
                    "approved_by": approved_by,
                    "reason": reason,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            }

            # Send to conversation or broadcast
            if conversation_id:
                recipients = await websocket_manager.send_to_conversation(
                    conversation_id, approval_event
                )
            else:
                recipients = await websocket_manager.broadcast(approval_event)

            logger.info(
                f"Approval update sent: {approval_id} -> {status} ({recipients} recipients)"
            )
            return recipients

        except Exception as e:
            logger.error(f"Error sending approval update: {e}")
            return 0

    async def _stream_response_chunks(
        self,
        conversation_id: str,
        content: str,
        agent_type: UnifiedAgentType,
        chunk_size: int = 50,
    ):
        """Stream response content in chunks for real-time effect."""
        try:
            words = content.split()
            chunks = [
                " ".join(words[i : i + chunk_size])
                for i in range(0, len(words), chunk_size)
            ]

            for i, chunk in enumerate(chunks):
                # Create streaming message event
                message_event = create_message_event(
                    conversation_id=conversation_id,
                    message_id=f"stream_{int(time.time() * 1000)}_{i}",
                    content=chunk,
                    sender=SenderType.AGENT,
                    agent_type=agent_type,
                    metadata={
                        "is_streaming": True,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "is_final": i == len(chunks) - 1,
                    },
                )

                await websocket_manager.send_to_conversation(
                    conversation_id, message_event.dict()
                )

                # Small delay for streaming effect
                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Error streaming response chunks: {e}")

    async def _send_complete_response(
        self, conversation_id: str, agent_response: UnifiedAgentResponse, agent_type: UnifiedAgentType
    ):
        """Send complete agent response."""
        try:
            message_event = create_message_event(
                conversation_id=conversation_id,
                message_id=f"response_{int(time.time() * 1000)}",
                content=agent_response.content,
                sender=SenderType.AGENT,
                agent_type=agent_type,
                metadata={
                    "confidence": agent_response.confidence,
                    "response_time": agent_response.response_time,
                    "agent_metadata": agent_response.metadata,
                },
            )

            await websocket_manager.send_to_conversation(
                conversation_id, message_event.dict()
            )

        except Exception as e:
            logger.error(f"Error sending complete response: {e}")

    async def _send_typing_indicator(
        self, conversation_id: str, agent_type: UnifiedAgentType, is_typing: bool
    ):
        """Send typing indicator for agent."""
        try:
            typing_event = create_typing_event(
                conversation_id=conversation_id,
                is_typing=is_typing,
                agent_type=agent_type,
            )

            await websocket_manager.send_to_conversation(
                conversation_id, typing_event.dict()
            )

        except Exception as e:
            logger.error(f"Error sending typing indicator: {e}")

    async def _send_approval_notification(
        self, conversation_id: str, approval_result: Dict[str, Any], user_id: str
    ):
        """Send approval workflow notification."""
        try:
            notification_event = create_system_alert_event(
                severity="info",
                title="Approval Required",
                message=f"UnifiedAgent recommendation requires approval. ID: {approval_result['approval_id']}",
                source="approval_system",
                action_required=not approval_result["auto_approve"],
            )

            await websocket_manager.send_to_conversation(
                conversation_id, notification_event.dict()
            )

        except Exception as e:
            logger.error(f"Error sending approval notification: {e}")

    async def _send_error_notification(self, conversation_id: str, error_message: str):
        """Send error notification."""
        try:
            error_event = {
                "type": EventType.ERROR,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "conversation_id": conversation_id,
                "data": {"error_code": "AGENT_ERROR", "message": error_message},
            }

            await websocket_manager.send_to_conversation(conversation_id, error_event)

        except Exception as e:
            logger.error(f"Error sending error notification: {e}")

    def _track_performance(self, response_time: float):
        """Track response time performance."""
        self.response_times.append(response_time)

        # Keep only last 100 measurements
        if len(self.response_times) > 100:
            self.response_times = self.response_times[-100:]

        # Log performance warnings
        if response_time > self.max_response_time:
            logger.warning(
                f"Response time exceeded target: {response_time:.3f}s > {self.max_response_time:.3f}s"
            )

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        if not self.response_times:
            return {"status": "no_data"}

        avg_time = sum(self.response_times) / len(self.response_times)
        max_time = max(self.response_times)
        min_time = min(self.response_times)

        return {
            "average_response_time": avg_time,
            "max_response_time": max_time,
            "min_response_time": min_time,
            "target_response_time": self.max_response_time,
            "within_target_percentage": sum(
                1 for t in self.response_times if t <= self.max_response_time
            )
            / len(self.response_times)
            * 100,
            "total_measurements": len(self.response_times),
        }


# Global instance
agent_websocket_integration = ConversationalUnifiedAgentWebSocketIntegration()
