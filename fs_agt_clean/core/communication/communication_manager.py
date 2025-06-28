"""
Communication Manager for FlipSync UnifiedAgent Communication Protocol.

This module provides the high-level interface for agent communication,
integrating the message router with the Pipeline Controller and UnifiedAgent Manager.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable
from uuid import uuid4

from fs_agt_clean.core.protocols.agent_protocol import (
    UnifiedAgentMessage,
    MessageType,
    Priority,
    UpdateMessage,
    AlertMessage,
    QueryMessage,
    CommandMessage,
    ResponseMessage,
    UnifiedAgentCategoryType,
)
from fs_agt_clean.core.communication.agent_message_router import UnifiedAgentMessageRouter

logger = logging.getLogger(__name__)


class CommunicationManager:
    """
    High-level manager for agent communication in FlipSync.
    
    This manager coordinates between the Pipeline Controller, UnifiedAgent Manager,
    and Message Router to enable sophisticated multi-agent workflows.
    """

    def __init__(self, agent_manager=None, pipeline_controller=None):
        """
        Initialize the communication manager.
        
        Args:
            agent_manager: The agent manager instance
            pipeline_controller: The pipeline controller instance
        """
        self.agent_manager = agent_manager
        self.pipeline_controller = pipeline_controller
        self.message_router = UnifiedAgentMessageRouter(agent_manager)
        self.workflow_coordinators: Dict[str, Dict[str, Any]] = {}
        self.agent_communication_handlers: Dict[str, Callable] = {}
        
        logger.info("Communication Manager initialized")

    async def initialize(self) -> bool:
        """Initialize the communication manager."""
        try:
            logger.info("Initializing Communication Manager...")
            
            # Initialize message router
            if not await self.message_router.initialize():
                logger.error("Failed to initialize message router")
                return False
            
            # Register agents with the message router
            if self.agent_manager:
                await self._register_agents_with_router()
            
            # Connect with pipeline controller
            if self.pipeline_controller:
                await self._integrate_with_pipeline_controller()
            
            logger.info("Communication Manager initialization completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Communication Manager: {e}")
            return False

    async def _register_agents_with_router(self):
        """Register all active agents with the message router."""
        try:
            for agent_id, agent_info in self.agent_manager.agents.items():
                if agent_info.get("status") == "active":
                    # Create a message handler for this agent
                    handler = self._create_agent_message_handler(agent_id, agent_info)
                    await self.message_router.register_agent(agent_id, handler)
                    
            logger.info(f"Registered {len(self.agent_manager.agents)} agents with message router")
            
        except Exception as e:
            logger.error(f"Failed to register agents with router: {e}")

    def _create_agent_message_handler(self, agent_id: str, agent_info: Dict[str, Any]) -> Callable:
        """Create a message handler for a specific agent."""
        async def handle_message(message: UnifiedAgentMessage) -> Optional[UnifiedAgentMessage]:
            try:
                logger.info(f"UnifiedAgent {agent_id} received message from {message.sender_id} (type: {message.message_type.value})")
                
                # Get the agent instance
                agent_instance = agent_info.get("instance")
                if not agent_instance:
                    logger.error(f"No instance found for agent {agent_id}")
                    return None
                
                # Process message based on type
                if message.message_type == MessageType.COMMAND:
                    return await self._handle_command_message(agent_id, agent_instance, message)
                elif message.message_type == MessageType.QUERY:
                    return await self._handle_query_message(agent_id, agent_instance, message)
                elif message.message_type == MessageType.UPDATE:
                    return await self._handle_update_message(agent_id, agent_instance, message)
                elif message.message_type == MessageType.ALERT:
                    return await self._handle_alert_message(agent_id, agent_instance, message)
                else:
                    logger.warning(f"Unknown message type: {message.message_type}")
                    return None
                    
            except Exception as e:
                logger.error(f"Error handling message for agent {agent_id}: {e}")
                return None
        
        return handle_message

    async def _handle_command_message(self, agent_id: str, agent_instance, message: UnifiedAgentMessage) -> Optional[UnifiedAgentMessage]:
        """Handle a command message for an agent."""
        try:
            command_data = message.content
            command = command_data.get("command", "")
            parameters = command_data.get("parameters", {})
            
            # Execute command based on agent type and capabilities
            result = None
            if hasattr(agent_instance, "execute_command"):
                result = await agent_instance.execute_command(command, parameters)
            elif hasattr(agent_instance, "process_message"):
                # Fallback to generic message processing
                result = await agent_instance.process_message(
                    f"Execute command: {command}",
                    context=parameters
                )
            
            # Create response message
            return ResponseMessage(
                sender_id=agent_id,
                receiver_id=message.sender_id,
                correlation_id=message.correlation_id,
                request_id=message.message_id,
                status="success" if result else "failed",
                result={"command_result": result} if result else {},
                execution_time=0.1,  # Mock execution time
            )
            
        except Exception as e:
            logger.error(f"Error executing command for agent {agent_id}: {e}")
            return ResponseMessage(
                sender_id=agent_id,
                receiver_id=message.sender_id,
                correlation_id=message.correlation_id,
                request_id=message.message_id,
                status="error",
                errors=[str(e)],
            )

    async def _handle_query_message(self, agent_id: str, agent_instance, message: UnifiedAgentMessage) -> Optional[UnifiedAgentMessage]:
        """Handle a query message for an agent."""
        try:
            query = message.content.get("query", "")
            context = message.content.get("context", {})
            
            # Process query based on agent capabilities
            result = None
            if hasattr(agent_instance, "answer_query"):
                result = await agent_instance.answer_query(query, context)
            elif hasattr(agent_instance, "process_message"):
                # Fallback to generic message processing
                result = await agent_instance.process_message(query, context=context)
            
            # Create response message
            return ResponseMessage(
                sender_id=agent_id,
                receiver_id=message.sender_id,
                correlation_id=message.correlation_id,
                request_id=message.message_id,
                status="success" if result else "no_answer",
                result={"query_result": result} if result else {},
            )
            
        except Exception as e:
            logger.error(f"Error processing query for agent {agent_id}: {e}")
            return ResponseMessage(
                sender_id=agent_id,
                receiver_id=message.sender_id,
                correlation_id=message.correlation_id,
                request_id=message.message_id,
                status="error",
                errors=[str(e)],
            )

    async def _handle_update_message(self, agent_id: str, agent_instance, message: UnifiedAgentMessage) -> Optional[UnifiedAgentMessage]:
        """Handle an update message for an agent."""
        try:
            # Update messages typically don't require responses
            # Just log the update for now
            logger.info(f"UnifiedAgent {agent_id} received update: {message.content}")
            return None
            
        except Exception as e:
            logger.error(f"Error handling update for agent {agent_id}: {e}")
            return None

    async def _handle_alert_message(self, agent_id: str, agent_instance, message: UnifiedAgentMessage) -> Optional[UnifiedAgentMessage]:
        """Handle an alert message for an agent."""
        try:
            # Alert messages may require acknowledgment
            logger.warning(f"UnifiedAgent {agent_id} received alert: {message.content}")
            
            # Send acknowledgment
            return UpdateMessage(
                sender_id=agent_id,
                receiver_id=message.sender_id,
                correlation_id=message.correlation_id,
                content={"alert_acknowledged": True, "alert_id": message.message_id},
            )
            
        except Exception as e:
            logger.error(f"Error handling alert for agent {agent_id}: {e}")
            return None

    async def _integrate_with_pipeline_controller(self):
        """Integrate communication manager with pipeline controller."""
        try:
            # Add communication capabilities to pipeline controller
            if hasattr(self.pipeline_controller, "set_communication_manager"):
                self.pipeline_controller.set_communication_manager(self)
            
            logger.info("Integrated with Pipeline Controller")
            
        except Exception as e:
            logger.error(f"Failed to integrate with Pipeline Controller: {e}")

    async def send_agent_message(self, message: UnifiedAgentMessage) -> bool:
        """Send a message between agents."""
        return await self.message_router.send_message(message)

    async def broadcast_to_category(self, message: UnifiedAgentMessage, category: UnifiedAgentCategoryType) -> int:
        """Broadcast a message to all agents in a specific category."""
        category_mapping = {
            UnifiedAgentCategoryType.MARKET: "market",
            UnifiedAgentCategoryType.EXECUTIVE: "executive", 
            UnifiedAgentCategoryType.CONTENT: "content",
            UnifiedAgentCategoryType.LOGISTICS: "logistics",
            UnifiedAgentCategoryType.SYSTEM: "system",
        }
        
        agent_type = category_mapping.get(category)
        return await self.message_router.broadcast_message(message, agent_type)

    async def coordinate_workflow(self, workflow_id: str, participants: List[str], workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate a multi-agent workflow."""
        try:
            logger.info(f"Starting workflow coordination: {workflow_id}")
            
            # Create workflow coordination context
            correlation_id = str(uuid4())
            self.workflow_coordinators[workflow_id] = {
                "correlation_id": correlation_id,
                "participants": participants,
                "workflow_data": workflow_data,
                "started_at": datetime.now(timezone.utc),
                "status": "active",
                "messages": [],
            }
            
            # Send initial workflow command to all participants
            for participant in participants:
                command_message = CommandMessage(
                    sender_id="communication_manager",
                    receiver_id=participant,
                    correlation_id=correlation_id,
                    command="start_workflow",
                    parameters={
                        "workflow_id": workflow_id,
                        "workflow_data": workflow_data,
                        "participants": participants,
                    },
                )
                
                await self.send_agent_message(command_message)
            
            logger.info(f"Workflow {workflow_id} coordination initiated with {len(participants)} participants")
            
            return {
                "workflow_id": workflow_id,
                "correlation_id": correlation_id,
                "status": "initiated",
                "participants": len(participants),
            }
            
        except Exception as e:
            logger.error(f"Failed to coordinate workflow {workflow_id}: {e}")
            return {"workflow_id": workflow_id, "status": "failed", "error": str(e)}

    async def get_communication_stats(self) -> Dict[str, Any]:
        """Get communication statistics."""
        try:
            stats = {
                "registered_agents": len(self.message_router.publishers),
                "active_workflows": len(self.workflow_coordinators),
                "total_messages": len(self.message_router.message_history),
                "active_conversations": len(self.message_router.active_conversations),
            }
            
            # Add per-agent stats
            agent_stats = {}
            for agent_id in self.message_router.publishers.keys():
                agent_stats[agent_id] = await self.message_router.get_agent_message_stats(agent_id)
            
            stats["agent_stats"] = agent_stats
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get communication stats: {e}")
            return {"error": str(e)}

    async def shutdown(self):
        """Shutdown the communication manager."""
        try:
            await self.message_router.shutdown()
            self.workflow_coordinators.clear()
            logger.info("Communication Manager shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during communication manager shutdown: {e}")
