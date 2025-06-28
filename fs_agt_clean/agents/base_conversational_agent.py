"""
Base Conversational UnifiedAgent for FlipSync AI System
===============================================

This module provides the base class for all conversational agents in the
FlipSync system, with common functionality for message handling, context
management, and response generation.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from fs_agt_clean.core.ai.llm_adapter import ConversationContext, LLMClientAdapter
from fs_agt_clean.core.ai.prompt_templates import UnifiedAgentRole, PromptTemplateManager

# Legacy LLMClient removed - using SimpleLLMClient architecture
from fs_agt_clean.core.ai.simple_llm_client import SimpleLLMClient
from fs_agt_clean.core.db.database import get_database
from fs_agt_clean.database.repositories.agent_repository import UnifiedAgentRepository
from fs_agt_clean.database.repositories.chat_repository import ChatRepository

logger = logging.getLogger(__name__)


class UnifiedAgentState(str, Enum):
    """UnifiedAgent operational states."""

    IDLE = "idle"
    PROCESSING = "processing"
    WAITING = "waiting"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class UnifiedAgentResponse:
    """Response from a conversational agent."""

    content: str
    agent_type: str
    confidence: float
    response_time: float
    metadata: Dict[str, Any]
    requires_followup: bool = False
    suggested_actions: List[str] = None
    handoff_suggestion: Optional[str] = None


@dataclass
class UnifiedAgentMetrics:
    """Performance metrics for an agent."""

    total_conversations: int
    total_messages: int
    average_response_time: float
    success_rate: float
    user_satisfaction: float
    last_updated: str


class BaseConversationalUnifiedAgent(ABC):
    """Base class for all conversational agents in FlipSync."""

    def __init__(
        self,
        agent_role: UnifiedAgentRole,
        agent_id: Optional[str] = None,
        use_fast_model: bool = True,
    ):
        """
        Initialize the base conversational agent.

        Args:
            agent_role: The role/type of this agent
            agent_id: Unique identifier for this agent instance
            use_fast_model: Whether to use fast/cheap model for responses
        """
        self.agent_role = agent_role
        self.agent_id = (
            agent_id or f"{agent_role.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        # Initialize AI components
        self.llm_client = self._create_llm_client(use_fast_model)
        self.prompt_manager = PromptTemplateManager()

        # Initialize database components
        self.chat_repository = ChatRepository()
        self.agent_repository = UnifiedAgentRepository()
        self.database = get_database()

        # UnifiedAgent state and metrics
        self.state = UnifiedAgentState.IDLE
        self.active_conversations = set()
        self.metrics = UnifiedAgentMetrics(
            total_conversations=0,
            total_messages=0,
            average_response_time=0.0,
            success_rate=1.0,
            user_satisfaction=0.0,
            last_updated=datetime.now(timezone.utc).isoformat(),
        )

        # Conversation contexts
        self.conversation_contexts = {}

        logger.info(f"Initialized {self.agent_role.value} agent: {self.agent_id}")

    def _create_llm_client(self, use_fast_model: bool):
        """Create LLM client with environment-based configuration."""
        try:
            # Try to use configured Ollama client first
            from fs_agt_clean.core.config.llm_config import (
                create_configured_llm_client,
                get_business_llm_client,
            )

            # For business agents (market, executive, content), use business-optimized client
            if self.agent_role in [
                UnifiedAgentRole.MARKET,
                UnifiedAgentRole.EXECUTIVE,
                UnifiedAgentRole.CONTENT,
            ]:
                client = get_business_llm_client()
                logger.info(
                    f"Created business LLM client for {self.agent_role.value} agent"
                )
                return client
            else:
                client = create_configured_llm_client()
                logger.info(
                    f"Created configured LLM client for {self.agent_role.value} agent"
                )
                return client

        except Exception as e:
            logger.warning(
                f"Failed to create configured LLM client: {e}, falling back to unified factory"
            )
            # Fallback to unified model factory - use gemma3:4b for all agents
            try:
                from fs_agt_clean.core.ai.llm_adapter import FlipSyncLLMFactory

                client = FlipSyncLLMFactory.create_smart_client()
                logger.info(
                    f"Created FlipSync LLM client for {self.agent_role.value} agent"
                )
                return client
            except Exception as fallback_error:
                logger.error(
                    f"Fallback factory also failed: {fallback_error}, using direct SimpleLLMClient"
                )
                # Last resort: create OpenAI client directly for production
                try:
                    # Import required classes to avoid scoping issues
                    import os
                    from fs_agt_clean.core.ai.simple_llm_client import (
                        SimpleLLMClientFactory,
                        ModelType,
                    )
                    from fs_agt_clean.core.ai.llm_adapter import LLMClientAdapter

                    # PRODUCTION: Use OpenAI exclusively - no Ollama fallbacks
                    api_key = os.getenv("OPENAI_API_KEY")
                    if not api_key:
                        raise ValueError(
                            "OPENAI_API_KEY environment variable is required for production"
                        )

                    simple_client = SimpleLLMClientFactory.create_openai_client(
                        model_type=ModelType.GPT_4O_MINI, temperature=0.7
                    )
                    client = LLMClientAdapter(simple_client)
                    logger.info(
                        f"Created direct OpenAI client for {self.agent_role.value} agent"
                    )
                    return client
                except Exception as final_error:
                    logger.error(
                        f"All LLM client creation methods failed: {final_error}"
                    )
                    # Re-raise the error instead of using a mock
                    raise RuntimeError(
                        f"Failed to create LLM client: {final_error}"
                    ) from final_error

    async def handle_message(
        self,
        message: str,
        user_id: str,
        conversation_id: str,
        conversation_history: Optional[List[Dict]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> UnifiedAgentResponse:
        """
        Handle an incoming message and generate a response.

        Args:
            message: UnifiedUser message content
            user_id: UnifiedUser identifier
            conversation_id: Conversation identifier
            conversation_history: Previous conversation messages
            context: Additional context information

        Returns:
            UnifiedAgentResponse with generated content and metadata
        """
        start_time = datetime.now()
        self.state = UnifiedAgentState.PROCESSING

        try:
            # Add conversation to active set
            self.active_conversations.add(conversation_id)

            # Update conversation context
            await self._update_conversation_context(
                conversation_id, message, user_id, conversation_history, context
            )

            # Get system prompt with context
            system_prompt = await self._get_system_prompt(conversation_id, context)

            # Prepare conversation context for LLM
            llm_context = self._prepare_llm_context(
                conversation_id, conversation_history
            )

            # Generate response using LLM
            llm_response = await self.llm_client.generate_response(
                prompt=message, system_prompt=system_prompt, context=llm_context
            )

            # Process the response through agent-specific logic
            processed_response = await self._process_response(
                llm_response.content, message, conversation_id, context
            )

            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds()

            # Update metrics
            await self._update_metrics(response_time, True)

            # Log the interaction
            await self._log_interaction(
                conversation_id, user_id, message, processed_response, response_time
            )

            # Create agent response
            agent_response = UnifiedAgentResponse(
                content=processed_response,
                agent_type=self.agent_role.value,
                confidence=self._calculate_confidence(llm_response, processed_response),
                response_time=response_time,
                metadata={
                    "agent_id": self.agent_id,
                    "llm_tokens": llm_response.tokens_used,
                    "llm_cost": llm_response.metadata.get("estimated_cost", 0),
                    "timestamp": start_time.isoformat(),
                },
                requires_followup=await self._requires_followup(
                    processed_response, context
                ),
                suggested_actions=await self._get_suggested_actions(
                    processed_response, context
                ),
                handoff_suggestion=await self._get_handoff_suggestion(
                    processed_response, context
                ),
            )

            self.state = UnifiedAgentState.IDLE
            return agent_response

        except Exception as e:
            logger.error(
                f"Error handling message in {self.agent_role.value} agent: {e}"
            )
            self.state = UnifiedAgentState.ERROR

            # Update metrics for failure
            response_time = (datetime.now() - start_time).total_seconds()
            await self._update_metrics(response_time, False)

            # DEBUGGING: Remove fallback to expose actual AI performance issues
            raise RuntimeError(
                f"{self.agent_role.value} agent failed: {e}. Response time: {response_time:.2f}s"
            ) from e
        finally:
            # Remove from active conversations
            self.active_conversations.discard(conversation_id)

    async def _update_conversation_context(
        self,
        conversation_id: str,
        message: str,
        user_id: str,
        conversation_history: Optional[List[Dict]],
        context: Optional[Dict[str, Any]],
    ):
        """Update the conversation context for this agent."""
        if conversation_id not in self.conversation_contexts:
            self.conversation_contexts[conversation_id] = {
                "user_id": user_id,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "messages": [],
                "context": context or {},
                "agent_specific_data": {},
            }

        # Add current message to context
        self.conversation_contexts[conversation_id]["messages"].append(
            {
                "role": "user",
                "content": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        # Update context
        if context:
            self.conversation_contexts[conversation_id]["context"].update(context)

        # Keep only last 20 messages for efficiency
        if len(self.conversation_contexts[conversation_id]["messages"]) > 20:
            self.conversation_contexts[conversation_id]["messages"] = (
                self.conversation_contexts[conversation_id]["messages"][-20:]
            )

    async def _get_system_prompt(
        self, conversation_id: str, context: Optional[Dict[str, Any]]
    ) -> str:
        """Get the system prompt for this agent with current context."""
        # Get base system prompt
        context_variables = context or {}

        # Add agent-specific context
        agent_context = await self._get_agent_context(conversation_id)
        context_variables.update(agent_context)

        return self.prompt_manager.get_system_prompt(self.agent_role, context_variables)

    def _prepare_llm_context(
        self, conversation_id: str, conversation_history: Optional[List[Dict]]
    ) -> ConversationContext:
        """Prepare conversation context for the LLM."""
        messages = []

        # Use conversation history if provided, otherwise use internal context
        if conversation_history:
            messages = [
                {"role": msg.get("sender", "user"), "content": msg.get("content", "")}
                for msg in conversation_history[-10:]  # Last 10 messages
            ]
        elif conversation_id in self.conversation_contexts:
            messages = self.conversation_contexts[conversation_id]["messages"][-10:]

        return ConversationContext(conversation_id=conversation_id, messages=messages)

    @abstractmethod
    async def _process_response(
        self,
        llm_response: str,
        original_message: str,
        conversation_id: str,
        context: Optional[Dict[str, Any]],
    ) -> str:
        """
        Process the LLM response with agent-specific logic.

        This method should be implemented by each specific agent to add
        their specialized processing, data enrichment, or formatting.
        """
        pass

    @abstractmethod
    async def _get_agent_context(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get agent-specific context for prompt generation.

        This method should be implemented by each specific agent to provide
        relevant context variables for their system prompt.
        """
        pass

    async def _requires_followup(
        self, response: str, context: Optional[Dict[str, Any]]
    ) -> bool:
        """Determine if the response requires a followup."""
        # Default implementation - can be overridden by specific agents
        followup_indicators = [
            "would you like",
            "do you want",
            "shall i",
            "should i",
            "more information",
            "additional details",
            "follow up",
        ]

        return any(indicator in response.lower() for indicator in followup_indicators)

    async def _get_suggested_actions(
        self, response: str, context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Get suggested actions based on the response."""
        # Default implementation - can be overridden by specific agents
        return []

    async def _get_handoff_suggestion(
        self, response: str, context: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """Determine if a handoff to another agent is suggested."""
        # Default implementation - can be overridden by specific agents
        return None

    def _calculate_confidence(self, llm_response, processed_response: str) -> float:
        """Calculate confidence score for the response."""
        # Base confidence from LLM response quality
        base_confidence = 0.8

        # Adjust based on response length and content
        if len(processed_response) < 20:
            base_confidence -= 0.2
        elif len(processed_response) > 500:
            base_confidence += 0.1

        # Check for uncertainty indicators
        uncertainty_indicators = ["not sure", "might be", "possibly", "perhaps"]
        if any(
            indicator in processed_response.lower()
            for indicator in uncertainty_indicators
        ):
            base_confidence -= 0.2

        return max(0.1, min(1.0, base_confidence))

    async def _update_metrics(self, response_time: float, success: bool):
        """Update agent performance metrics."""
        self.metrics.total_messages += 1

        # Update average response time
        current_avg = self.metrics.average_response_time
        total_messages = self.metrics.total_messages
        self.metrics.average_response_time = (
            current_avg * (total_messages - 1) + response_time
        ) / total_messages

        # Update success rate
        if success:
            current_success = self.metrics.success_rate * (total_messages - 1)
            self.metrics.success_rate = (current_success + 1) / total_messages
        else:
            current_success = self.metrics.success_rate * (total_messages - 1)
            self.metrics.success_rate = current_success / total_messages

        self.metrics.last_updated = datetime.now(timezone.utc).isoformat()

    async def _log_interaction(
        self,
        conversation_id: str,
        user_id: str,
        message: str,
        response: str,
        response_time: float,
    ):
        """Log the interaction to the database."""
        try:
            # Check if database is initialized
            if (
                not self.database
                or not hasattr(self.database, "_session_factory")
                or not self.database._session_factory
            ):
                logger.warning(
                    "Database not initialized - skipping interaction logging"
                )
                return

            async with self.database.get_session() as session:
                await self.agent_repository.log_agent_decision(
                    session=session,
                    agent_id=self.agent_id,
                    agent_type=self.agent_role.value,
                    decision_type="conversation_response",
                    parameters={
                        "conversation_id": conversation_id,
                        "user_id": user_id,
                        "message_length": len(message),
                        "response_length": len(response),
                        "response_time": response_time,
                    },
                    confidence=self._calculate_confidence(None, response),
                    rationale=f"Generated response for {self.agent_role.value} agent",
                    requires_approval=False,
                )
        except Exception as e:
            logger.error(f"Error logging interaction: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status and metrics."""
        return {
            "agent_id": self.agent_id,
            "agent_role": self.agent_role.value,
            "state": self.state.value,
            "active_conversations": len(self.active_conversations),
            "metrics": {
                "total_conversations": self.metrics.total_conversations,
                "total_messages": self.metrics.total_messages,
                "average_response_time": self.metrics.average_response_time,
                "success_rate": self.metrics.success_rate,
                "user_satisfaction": self.metrics.user_satisfaction,
                "last_updated": self.metrics.last_updated,
            },
            "llm_usage": self.llm_client.get_usage_stats(),
        }

    async def shutdown(self):
        """Gracefully shutdown the agent."""
        logger.info(f"Shutting down {self.agent_role.value} agent: {self.agent_id}")
        self.state = UnifiedAgentState.OFFLINE

        # Close LLM client connections
        if hasattr(self.llm_client, "close"):
            try:
                await self.llm_client.close()
            except Exception as e:
                logger.warning(f"Error closing LLM client: {e}")

        # Clear active conversations
        self.active_conversations.clear()

        # Clear conversation contexts
        self.conversation_contexts.clear()
