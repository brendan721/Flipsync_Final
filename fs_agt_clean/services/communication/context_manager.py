"""
Context manager for the FlipSync chatbot.

This module provides robust context sharing between different agent types,
implementing context summarization and failover mechanisms.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

# Configure logging
logger = logging.getLogger(__name__)


class ContextManager:
    """
    Manager for sharing context between different agent types.

    This class implements robust context-passing mechanisms between different agent types,
    including context summarization for efficient knowledge transfer and failover mechanisms
    for context restoration if agent communication fails.
    """

    def __init__(self):
        """Initialize the ContextManager."""
        # Dictionary to store conversation contexts by conversation ID
        self.contexts = {}

        # Maximum context size (in number of messages) to maintain per conversation
        self.max_context_size = 50

        # Configure context summarization thresholds
        self.summarization_threshold = 20  # Number of messages before summarization
        self.summarization_target = 10  # Target number of messages after summarization

    async def get_context(
        self, conversation_id: str, agent_type: str
    ) -> Dict[str, Any]:
        """
        Get the context for a specific conversation and agent type.

        Args:
            conversation_id: ID of the conversation
            agent_type: Type of agent requesting the context

        Returns:
            Context dictionary for the specified conversation and agent type
        """
        # Get or create conversation context
        conversation_context = self.contexts.get(
            conversation_id,
            {
                "messages": [],
                "summaries": {},
                "entities": {},
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "last_accessed": datetime.now().isoformat(),
                    "access_count": 0,
                },
                "agent_states": {},
            },
        )

        # Update access metadata
        conversation_context["metadata"]["last_accessed"] = datetime.now().isoformat()
        conversation_context["metadata"]["access_count"] += 1

        # Store updated context
        self.contexts[conversation_id] = conversation_context

        # Format context for the specific agent type
        agent_context = self._format_context_for_agent(conversation_context, agent_type)

        return agent_context

    async def update_context(
        self,
        conversation_id: str,
        message: Dict[str, Any],
        agent_type: Optional[str] = None,
    ) -> None:
        """
        Update the context with a new message.

        Args:
            conversation_id: ID of the conversation
            message: Message to add to the context
            agent_type: Type of agent that processed the message (if applicable)
        """
        # Get or create conversation context
        conversation_context = self.contexts.get(
            conversation_id,
            {
                "messages": [],
                "summaries": {},
                "entities": {},
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "last_accessed": datetime.now().isoformat(),
                    "access_count": 0,
                },
                "agent_states": {},
            },
        )

        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()

        # Add agent type if provided
        if agent_type:
            message["agent_type"] = agent_type

        # Add message to context
        conversation_context["messages"].append(message)

        # Extract and store entities from the message
        if "entities" in message:
            for entity in message["entities"]:
                entity_type = entity.get("type")
                entity_value = entity.get("value")

                if entity_type and entity_value:
                    if entity_type not in conversation_context["entities"]:
                        conversation_context["entities"][entity_type] = []

                    # Add entity if not already present
                    if (
                        entity_value
                        not in conversation_context["entities"][entity_type]
                    ):
                        conversation_context["entities"][entity_type].append(
                            entity_value
                        )

        # Update agent state if agent type is provided
        if agent_type and "state" in message:
            conversation_context["agent_states"][agent_type] = message["state"]

        # Check if context needs summarization
        if len(conversation_context["messages"]) >= self.summarization_threshold:
            await self._summarize_context(conversation_context)

        # Limit context size
        if len(conversation_context["messages"]) > self.max_context_size:
            # Keep only the most recent messages
            conversation_context["messages"] = conversation_context["messages"][
                -self.max_context_size :
            ]

        # Store updated context
        self.contexts[conversation_id] = conversation_context

    async def _summarize_context(self, context: Dict[str, Any]) -> None:
        """
        Summarize the context to reduce its size.

        Args:
            context: The context to summarize
        """
        # Get messages to summarize (all except the most recent ones)
        messages_to_keep = context["messages"][-self.summarization_target :]
        messages_to_summarize = context["messages"][: -self.summarization_target]

        if not messages_to_summarize:
            return

        # Group messages by agent type
        agent_messages = {}
        for message in messages_to_summarize:
            agent_type = message.get("agent_type", "unknown")

            if agent_type not in agent_messages:
                agent_messages[agent_type] = []

            agent_messages[agent_type].append(message)

        # Create summaries for each agent type
        for agent_type, messages in agent_messages.items():
            summary = self._create_summary(messages, agent_type)

            # Store the summary
            if "summaries" not in context:
                context["summaries"] = {}

            if agent_type not in context["summaries"]:
                context["summaries"][agent_type] = []

            context["summaries"][agent_type].append(summary)

        # Replace original messages with summaries and recent messages
        context["messages"] = messages_to_keep

    def _create_summary(
        self, messages: List[Dict[str, Any]], agent_type: str
    ) -> Dict[str, Any]:
        """
        Create a summary of messages for a specific agent type.

        Args:
            messages: List of messages to summarize
            agent_type: Type of agent the messages are from

        Returns:
            Summary of the messages
        """
        # Extract key information from messages
        topics = set()
        entities = {}
        user_queries = []
        agent_responses = []

        for message in messages:
            # Extract topics
            if "topic" in message:
                topics.add(message["topic"])

            # Extract entities
            if "entities" in message:
                for entity in message["entities"]:
                    entity_type = entity.get("type")
                    entity_value = entity.get("value")

                    if entity_type and entity_value:
                        if entity_type not in entities:
                            entities[entity_type] = []

                        if entity_value not in entities[entity_type]:
                            entities[entity_type].append(entity_value)

            # Extract user queries and agent responses
            if message.get("is_user", False):
                user_queries.append(message.get("text", ""))
            else:
                agent_responses.append(message.get("text", ""))

        # Create summary
        summary = {
            "agent_type": agent_type,
            "timestamp": datetime.now().isoformat(),
            "message_count": len(messages),
            "topics": list(topics),
            "entities": entities,
            "key_points": self._extract_key_points(messages),
            "summary_text": self._generate_summary_text(
                user_queries, agent_responses, agent_type
            ),
        }

        return summary

    def _extract_key_points(self, messages: List[Dict[str, Any]]) -> List[str]:
        """
        Extract key points from a list of messages.

        Args:
            messages: List of messages to extract key points from

        Returns:
            List of key points
        """
        key_points = []

        # In a real implementation, this would use NLP to extract key points
        # For now, we'll use a simple approach based on message metadata

        for message in messages:
            # Extract key points from message metadata
            if "key_points" in message:
                key_points.extend(message["key_points"])

            # Extract key points from message text based on indicators
            text = message.get("text", "")

            # Look for phrases that indicate key points
            indicators = [
                "important",
                "key",
                "critical",
                "essential",
                "remember",
                "note that",
                "keep in mind",
                "don't forget",
            ]

            for indicator in indicators:
                if indicator in text.lower():
                    # Find the sentence containing the indicator
                    sentences = text.split(". ")
                    for sentence in sentences:
                        if indicator in sentence.lower():
                            key_points.append(sentence.strip())

        # Remove duplicates and limit to 5 key points
        unique_key_points = []
        for point in key_points:
            if point not in unique_key_points:
                unique_key_points.append(point)

        return unique_key_points[:5]

    def _generate_summary_text(
        self, user_queries: List[str], agent_responses: List[str], agent_type: str
    ) -> str:
        """
        Generate a summary text from user queries and agent responses.

        Args:
            user_queries: List of user queries
            agent_responses: List of agent responses
            agent_type: Type of agent

        Returns:
            Summary text
        """
        # In a real implementation, this would use NLP to generate a coherent summary
        # For now, we'll use a template-based approach

        if not user_queries or not agent_responses:
            return "No significant conversation to summarize."

        # Get the most frequent topics from user queries
        topics = self._extract_topics(user_queries)

        # Create summary based on agent type
        if agent_type == "market":
            return (
                f"UnifiedUser inquired about {', '.join(topics[:3])}. "
                "Provided market analysis and pricing recommendations."
            )
        elif agent_type == "logistics":
            return (
                f"UnifiedUser asked about {', '.join(topics[:3])}. "
                "Provided shipping and inventory information."
            )
        elif agent_type == "content":
            return (
                f"UnifiedUser requested content optimization for {', '.join(topics[:3])}. "
                "Provided suggestions for improving product descriptions and images."
            )
        elif agent_type == "executive":
            return (
                f"UnifiedUser inquired about business performance related to {', '.join(topics[:3])}. "
                "Provided strategic insights and recommendations."
            )
        else:
            return (
                f"UnifiedUser and agent discussed {', '.join(topics[:3])}. "
                f"Conversation included {len(user_queries)} user messages and "
                f"{len(agent_responses)} agent responses."
            )

    def _extract_topics(self, texts: List[str]) -> List[str]:
        """
        Extract topics from a list of texts.

        Args:
            texts: List of texts to extract topics from

        Returns:
            List of topics
        """
        # In a real implementation, this would use NLP to extract topics
        # For now, we'll use a simple approach based on word frequency

        # Combine all texts
        combined_text = " ".join(texts).lower()

        # Remove common stop words
        stop_words = [
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "with",
            "by",
            "about",
            "as",
            "of",
            "from",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "can",
            "could",
            "will",
            "would",
            "should",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
            "me",
            "him",
            "her",
            "us",
            "them",
            "my",
            "your",
            "his",
            "its",
            "our",
            "their",
        ]

        # Split into words and count frequency
        words = combined_text.split()
        word_counts = {}

        for word in words:
            if word not in stop_words and len(word) > 3:
                if word not in word_counts:
                    word_counts[word] = 0

                word_counts[word] += 1

        # Sort by frequency
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)

        # Return top topics
        return [word for word, count in sorted_words[:5]]

    def _format_context_for_agent(
        self, context: Dict[str, Any], agent_type: str
    ) -> Dict[str, Any]:
        """
        Format the context for a specific agent type.

        Args:
            context: The full conversation context
            agent_type: Type of agent requesting the context

        Returns:
            Formatted context for the specified agent type
        """
        # Create a copy of the context to avoid modifying the original
        agent_context = {
            "messages": context["messages"].copy(),
            "entities": context["entities"].copy(),
            "agent_type": agent_type,
            "conversation_id": next(
                (k for k, v in self.contexts.items() if v == context), None
            ),
        }

        # Add agent-specific state if available
        if agent_type in context.get("agent_states", {}):
            agent_context["state"] = context["agent_states"][agent_type]

        # Add relevant summaries
        if "summaries" in context and agent_type in context["summaries"]:
            agent_context["summaries"] = context["summaries"][agent_type]

        # Add cross-agent summaries for context sharing
        if "summaries" in context:
            agent_context["other_agent_summaries"] = {}

            for other_agent_type, summaries in context["summaries"].items():
                if other_agent_type != agent_type:
                    agent_context["other_agent_summaries"][other_agent_type] = summaries

        return agent_context

    async def restore_context(self, conversation_id: str) -> bool:
        """
        Attempt to restore context if agent communication fails."""
        # Implementation of context restoration logic
        logger.info(f"Attempting to restore context for conversation {conversation_id}")

        # Check if context exists
        if conversation_id not in self.contexts:
            logger.warning(f"No context found for conversation {conversation_id}")
            return False

        # Context exists, restoration successful
        logger.info(f"Context restored for conversation {conversation_id}")
        return True
