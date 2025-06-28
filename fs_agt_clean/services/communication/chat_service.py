"""
Enhanced Chat Service with AI Routing for FlipSync
==================================================

This service provides intelligent chat handling with intent recognition,
agent routing, and conversation persistence using the database layer.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import tiktoken
from langchain.chains import ConversationChain
from langchain.memory import ConversationSummaryMemory
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
)
from langchain_community.chat_models import ChatOpenAI

from fs_agt_clean.agents.base_conversational_agent import (
    UnifiedAgentResponse,
    BaseConversationalUnifiedAgent,
)

# Legacy LLMClientFactory removed - using SimpleLLMClient architecture only
from fs_agt_clean.core.ai.prompt_templates import (
    UnifiedAgentRole,
    PromptTemplateManager,
)
from fs_agt_clean.core.db.database import get_database

# Legacy imports for backward compatibility
from fs_agt_clean.core.generation.response_generator import ResponseGenerator
from fs_agt_clean.core.memory.chat_history import ChatHistoryManager
from fs_agt_clean.core.memory.user_profile import UnifiedUserProfileManager

# WebSocket integration
from fs_agt_clean.core.websocket.agent_integration import (
    ConversationalUnifiedAgentWebSocketIntegration,
)
from fs_agt_clean.database.repositories.agent_repository import UnifiedAgentRepository

# Database components
from fs_agt_clean.database.repositories.chat_repository import ChatRepository

# Approval integration
from fs_agt_clean.services.approval import ApprovalIntegrationService
from fs_agt_clean.services.chatbot.agent_connectivity_service import (
    UnifiedAgentConnectivityService,
)
from fs_agt_clean.services.communication.agent_router import UnifiedAgentRouter, UnifiedAgentType

# FlipSync AI components
from fs_agt_clean.services.communication.intent_recognizer import IntentRecognizer

# NOTE: Removed redundant 4-agent conversational system imports
# The real 12-agent system is handled by RealUnifiedAgentManager




logger = logging.getLogger(__name__)


class EnhancedChatService:
    """Enhanced chat service with AI routing and database persistence."""

    def __init__(self, database=None, app=None):
        """Initialize the enhanced chat service."""
        # AI routing components
        self.intent_recognizer = IntentRecognizer()
        self.agent_router = UnifiedAgentRouter(database=database)
        self.prompt_manager = PromptTemplateManager()

        # Database components
        self.chat_repository = ChatRepository()
        self.agent_repository = UnifiedAgentRepository()
        self.database = database

        # Store app reference for accessing Real UnifiedAgent Manager
        self.app = app

        # LLM clients - using simplified implementation only
        from fs_agt_clean.core.ai.llm_adapter import FlipSyncLLMFactory

        self.fast_llm = FlipSyncLLMFactory.create_fast_client()
        self.smart_llm = FlipSyncLLMFactory.create_smart_client()
        logger.info(
            "✅ Initialized SimpleLLM clients with proper timeout configuration"
        )

        # Approval integration service
        self.approval_service = ApprovalIntegrationService(self.agent_repository)

        # WebSocket integration service
        self.websocket_integration = ConversationalUnifiedAgentWebSocketIntegration(
            self.approval_service
        )

        # NOTE: Removed redundant 4-agent conversational system
        # The real 12-agent system is handled by RealUnifiedAgentManager

        # UnifiedAgent instances (simplified for now - would be expanded with actual agent implementations)
        self.active_agents = {}

        # Conversation state tracking
        self.conversation_states = {}

        # Legacy support
        self.user_contexts = {}
        self.user_personas = {}
        self.memories = {}  # Langchain memory instances per user
        self.chains = {}  # Langchain conversation chains per user
        self.encoders = {}  # Cache for tiktoken encoders
        self.token_usage = {}  # Track token usage per user

        logger.info(
            "Enhanced ChatService initialized with AI routing and approval integration"
        )

    # NOTE: Removed _initialize_conversational_agents method
    # The real 12-agent system is handled by RealUnifiedAgentManager

    async def handle_message_enhanced(
        self,
        user_id: str,
        message: str,
        conversation_id: str,
        app_context: str = "flipsync",
        use_fast_model: bool = True,
        current_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Enhanced message handling with AI routing and database persistence.

        Args:
            user_id: UnifiedUser identifier
            message: UnifiedUser message content
            conversation_id: Conversation identifier
            app_context: Application context
            use_fast_model: Whether to use fast/cheap model
            current_agent: Currently assigned agent (if any)

        Returns:
            Dictionary with response and routing information
        """
        try:
            start_time = datetime.now(timezone.utc)

            # Get conversation history from database
            conversation_history = await self._get_conversation_history(conversation_id)

            # Recognize intent
            intent_result = self.intent_recognizer.recognize_intent(
                message=message,
                user_id=user_id,
                conversation_id=conversation_id,
                conversation_history=conversation_history,
            )

            # Route to appropriate agent
            current_agent_type = UnifiedAgentType(current_agent) if current_agent else None
            routing_decision = await self.agent_router.route_message(
                message=message,
                user_id=user_id,
                conversation_id=conversation_id,
                conversation_history=conversation_history,
                current_agent=current_agent_type,
            )

            # Generate response using the selected agent
            agent_response_result = await self._generate_agent_response(
                message=message,
                user_id=user_id,
                conversation_id=conversation_id,
                agent_type=routing_decision.target_agent,
                conversation_history=conversation_history,
                use_fast_model=use_fast_model,
                handoff_context=routing_decision.handoff_context,
            )

            # Process WebSocket/approval workflow result
            if isinstance(agent_response_result, dict):
                if agent_response_result.get("success"):
                    # WebSocket streaming result
                    approval_result = agent_response_result.get("approval_result", {})
                    if approval_result.get("approval_required"):
                        response_content = approval_result["response"]
                    else:
                        response_content = "Response streamed via WebSocket"
                elif agent_response_result.get("approval_required"):
                    # Direct approval result
                    approval_result = agent_response_result
                    response_content = approval_result["response"]
                else:
                    # Other dict response
                    response_content = agent_response_result.get(
                        "response", "No response generated"
                    )
            else:
                # Legacy string response
                response_content = (
                    agent_response_result
                    if isinstance(agent_response_result, str)
                    else "No response generated"
                )

            # Store message and response in database
            await self._store_conversation_messages(
                conversation_id=conversation_id,
                user_id=user_id,
                user_message=message,
                agent_response=response_content,
                agent_type=routing_decision.target_agent.value,
                intent_result=intent_result,
                routing_decision=routing_decision,
            )

            # Calculate response time
            response_time = (datetime.now(timezone.utc) - start_time).total_seconds()

            # Prepare response
            response = {
                "response": response_content,
                "agent_type": routing_decision.target_agent.value,
                "intent": {
                    "primary_intent": intent_result.primary_intent,
                    "confidence": intent_result.confidence,
                    "reasoning": intent_result.reasoning,
                },
                "routing": {
                    "target_agent": routing_decision.target_agent.value,
                    "confidence": routing_decision.confidence,
                    "reasoning": routing_decision.reasoning,
                    "requires_handoff": routing_decision.requires_handoff,
                    "estimated_response_time": routing_decision.estimated_response_time,
                },
                "metadata": {
                    "conversation_id": conversation_id,
                    "response_time": response_time,
                    "timestamp": start_time.isoformat(),
                    "model_used": "fast" if use_fast_model else "smart",
                },
            }

            # Add handoff information if applicable
            if routing_decision.requires_handoff:
                response["handoff"] = {
                    "from_agent": current_agent,
                    "to_agent": routing_decision.target_agent.value,
                    "context": routing_decision.handoff_context,
                    "handoff_message": self._generate_handoff_message(
                        routing_decision.target_agent, intent_result
                    ),
                }

            logger.info(
                f"Enhanced message handled: user={user_id}, intent={intent_result.primary_intent}, "
                f"agent={routing_decision.target_agent.value}, time={response_time:.2f}s"
            )

            return response

        except Exception as e:
            logger.error(f"Error in enhanced message handling: {e}")
            return {
                "response": "I apologize, but I encountered an error processing your message. Please try again.",
                "agent_type": "assistant",
                "error": str(e),
                "metadata": {
                    "conversation_id": conversation_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "error_occurred": True,
                },
            }

    def _get_encoder(self, model: str) -> tiktoken.Encoding:
        """Get or create a token encoder for a model."""
        if model not in self.encoders:
            try:
                self.encoders[model] = tiktoken.encoding_for_model(model)
            except KeyError:
                # Fallback to cl100k_base for unknown models
                self.encoders[model] = tiktoken.get_encoding("cl100k_base")
        return self.encoders[model]

    def _count_tokens(self, text: str, model: str) -> int:
        """Count tokens in text for specific model."""
        encoder = self._get_encoder(model)
        return len(encoder.encode(text))

    def _update_token_usage(
        self,
        user_id: str,
        input_tokens: int,
        output_tokens: int,
        task_type: Optional[str] = None,
        model: str = "gpt-4o-mini",
    ):
        """Update token usage metrics for a user."""
        if user_id not in self.token_usage:
            self.token_usage[user_id] = {
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_tokens": 0,
                "session_start": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
            }

        usage = self.token_usage[user_id]
        usage["total_input_tokens"] += input_tokens
        usage["total_output_tokens"] += output_tokens
        usage["total_tokens"] += input_tokens + output_tokens
        usage["last_updated"] = datetime.now().isoformat()

    def _initialize_user_memory(self, user_id: str, app_context: str):
        """Initialize or get Langchain memory management for a user."""
        if user_id not in self.memories:
            # Use summary memory for long-term context
            self.memories[user_id] = ConversationSummaryMemory(
                llm=ChatOpenAI(temperature=0),
                return_messages=True,
                max_token_limit=2000,
            )

            # Create a conversation chain with our custom prompt
            system_prompt = self._get_system_prompt(user_id, app_context)
            prompt = ChatPromptTemplate.from_messages(
                [
                    SystemMessagePromptTemplate.from_template(system_prompt),
                    MessagesPlaceholder(variable_name="history"),
                    HumanMessagePromptTemplate.from_template("{input}"),
                ]
            )

            self.chains[user_id] = ConversationChain(
                memory=self.memories[user_id],
                prompt=prompt,
                llm=ChatOpenAI(temperature=0.7),
            )

            # Initialize token usage tracking
            if user_id not in self.token_usage:
                self.token_usage[user_id] = {
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "total_tokens": 0,
                    "session_start": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                }

    async def analyze_ebay_data(self, user_id: str, ebay_data: Dict) -> Dict:
        """Analyze eBay messages, offers, and sales history to build initial persona."""
        persona_data = {
            "negotiation_style": self._analyze_negotiation_patterns(
                ebay_data.get("offers", [])
            ),
            "communication_tone": self._analyze_message_patterns(
                ebay_data.get("messages", [])
            ),
            "business_metrics": self._analyze_sales_patterns(
                ebay_data.get("sales", [])
            ),
            "last_updated": datetime.now().isoformat(),
        }

        self.user_personas[user_id] = persona_data
        return persona_data

    def _analyze_negotiation_patterns(self, offers: List[Dict]) -> Dict:
        """Analyze negotiation behavior from offer history."""
        if not offers:
            return {"style": "unknown", "confidence": 0.0}

        patterns = {
            "accept_rate": 0.0,
            "counter_rate": 0.0,
            "avg_discount": 0.0,
            "negotiation_speed": "unknown",
        }

        total_offers = len(offers)
        if total_offers > 0:
            accepted = sum(1 for o in offers if o.get("status") == "accepted")
            countered = sum(1 for o in offers if o.get("status") == "countered")

            patterns["accept_rate"] = accepted / total_offers
            patterns["counter_rate"] = countered / total_offers

            # Calculate average discount from listing price
            discounts = [
                (o.get("listing_price", 0) - o.get("final_price", 0))
                / o.get("listing_price", 1)
                for o in offers
                if o.get("listing_price") and o.get("final_price")
            ]
            if discounts:
                patterns["avg_discount"] = sum(discounts) / len(discounts)

            # Analyze negotiation timing
            response_times = [
                o.get("response_time_minutes", 0)
                for o in offers
                if o.get("response_time_minutes") is not None
            ]
            if response_times:
                avg_response = sum(response_times) / len(response_times)
                patterns["negotiation_speed"] = (
                    "fast"
                    if avg_response < 30
                    else "moderate" if avg_response < 120 else "slow"
                )

        return patterns

    def _analyze_message_patterns(self, messages: List[Dict]) -> Dict:
        """Analyze communication style from eBay messages."""
        if not messages:
            return {"style": "unknown", "confidence": 0.0}

        patterns = {
            "response_rate": 0.0,
            "avg_response_time": 0.0,
            "communication_style": "unknown",
            "typical_length": "unknown",
        }

        total_messages = len(messages)
        if total_messages > 0:
            # Calculate response rate
            responses = sum(1 for m in messages if m.get("is_response"))
            patterns["response_rate"] = responses / total_messages

            # Calculate average response time
            response_times = [
                m.get("response_time_minutes", 0)
                for m in messages
                if m.get("response_time_minutes") is not None
            ]
            if response_times:
                patterns["avg_response_time"] = sum(response_times) / len(
                    response_times
                )

            # Analyze message lengths
            lengths = [len(m.get("content", "")) for m in messages]
            avg_length = sum(lengths) / len(lengths) if lengths else 0
            patterns["typical_length"] = (
                "brief"
                if avg_length < 100
                else "moderate" if avg_length < 300 else "detailed"
            )

            # Basic sentiment analysis can be added here later

        return patterns

    def _analyze_sales_patterns(self, sales: List[Dict]) -> Dict:
        """Analyze business patterns from sales history."""
        if not sales:
            return {"pattern": "unknown", "confidence": 0.0}

        patterns = {
            "avg_sale_value": 0.0,
            "sales_frequency": "unknown",
            "price_flexibility": 0.0,
            "category_focus": {},
        }

        total_sales = len(sales)
        if total_sales > 0:
            # Calculate average sale value
            sale_values = [s.get("final_price", 0) for s in sales]
            patterns["avg_sale_value"] = sum(sale_values) / len(sale_values)

            # Analyze sales frequency
            dates = []
            for s in sales:
                sale_date_str = s.get("sale_date")
                if isinstance(sale_date_str, str):
                    try:
                        dates.append(datetime.fromisoformat(sale_date_str))
                    except ValueError:
                        logging.warning(
                            f"Skipping invalid date format: {sale_date_str}"
                        )
                elif sale_date_str is not None:
                    logging.warning(f"Skipping non-string date: {sale_date_str}")

            if len(dates) > 1:
                # Sort dates just in case they are not ordered
                dates.sort()
                date_diffs = [
                    (dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)
                ]
                avg_days_between = sum(date_diffs) / len(date_diffs)
                patterns["sales_frequency"] = (
                    "high"
                    if avg_days_between < 2
                    else "moderate" if avg_days_between < 7 else "low"
                )

            # Analyze price flexibility
            list_vs_sale = [
                (s.get("listing_price", 0) - s.get("final_price", 0))
                / s.get("listing_price", 1)
                for s in sales
                if s.get("listing_price") and s.get("final_price")
            ]
            if list_vs_sale:
                patterns["price_flexibility"] = sum(list_vs_sale) / len(list_vs_sale)

            # Analyze category focus
            categories = {}
            for sale in sales:
                cat = sale.get("category", "unknown")
                categories[cat] = categories.get(cat, 0) + 1
            patterns["category_focus"] = {
                k: v / total_sales for k, v in categories.items()
            }

        return patterns

    def get_onboarding_prompt(self, user_id: str, app_context: str) -> str:
        """Generate contextual onboarding prompt based on app and user."""
        base_prompts = {
            "asin_fetcher": """I'm here to help you get started with ASIN Fetcher.
            I'll guide you through connecting your Amazon account and email.
            This helps me understand your business better and provide personalized assistance.""",
            "flipsync": """Welcome to FlipSync! I'll help you connect your eBay account to get started.
            This allows me to understand your selling style and provide tailored recommendations.
            Would you like to proceed with connecting your eBay account?""",
        }

        return base_prompts.get(app_context, base_prompts["flipsync"])

    async def handle_message(
        self,
        user_id: str,
        message: str,
        app_context: str,
        use_fast_model: bool = True,
        task_type: Optional[str] = None,
    ) -> Dict:
        """Handle incoming chat messages with enhanced Langchain memory management."""
        try:
            # Initialize or get Langchain components
            self._initialize_user_memory(user_id, app_context)

            # Count input tokens
            model = "gpt-4" if not use_fast_model else "gpt-3.5-turbo"
            input_tokens = self._count_tokens(message, model)

            # Enrich context with our domain-specific data
            context = self._build_context(user_id, app_context)
            enriched_message = self._format_message_with_context(message, context)

            # Get response using Langchain conversation chain
            response = self.chains[user_id].predict(input=enriched_message)

            # Count output tokens and update usage
            output_tokens = self._count_tokens(response, model)
            self._update_token_usage(
                user_id, input_tokens, output_tokens, task_type, model
            )

            # Update our domain-specific context and persona
            self._update_user_context(user_id, message, response)
            self._update_persona(user_id, message, response)

            return {
                "response": response,
                "context_updated": True,
                "token_usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens,
                    "session_usage": self.token_usage[user_id],
                },
                "memory_summary": self.memories[user_id].load_memory_variables({}),
            }

        except Exception as e:
            logging.error("Error in chat service: %s", str(e))
            return {"error": "Failed to process message", "details": str(e)}

    def _format_message_with_context(self, message: str, context: Dict) -> str:
        """Format message with domain-specific context for Langchain."""
        context_str = json.dumps(
            {
                "user_persona": context["user_persona"],
                "business_metrics": context["business_metrics"],
                "app_context": context["app_context"],
            },
            indent=2,
        )

        return f"""Context: {context_str}

UnifiedUser Message: {message}"""

    def _build_context(self, user_id: str, app_context: str) -> Dict:
        """Build rich context for AI responses."""
        context = {
            "user_persona": self.user_personas.get(user_id, {}),
            "conversation_history": (
                self.memories[user_id].load_memory_variables({})
                if user_id in self.memories
                else []
            ),
            "app_context": app_context,
            "user_preferences": self._get_user_preferences(user_id),
            "business_metrics": self._get_business_metrics(user_id, app_context),
        }
        return context

    def _get_system_prompt(self, user_id: str, app_context: str) -> str:
        """Generate dynamic system prompt based on user stage and context."""
        persona = self.user_personas.get(user_id, {})

        if not persona:
            return self._get_onboarding_system_prompt(app_context)

        return self._get_personalized_system_prompt(persona, app_context)

    def _get_onboarding_system_prompt(self, app_context: str) -> str:
        """Generate FlipSync-specific onboarding system prompt."""
        if app_context == "flipsync":
            # Use the FlipSync assistant prompt for consistent experience
            context_variables = {
                "business_type": "eBay reseller business",
                "sales_performance": "getting started with optimization",
                "optimization_goals": "faster sales and higher profits",
                "available_features": "AI listing optimization, pricing analysis, shipping optimization",
            }
            return self.prompt_manager.get_system_prompt(
                UnifiedAgentRole.ASSISTANT, context_variables
            )

        return f"""You are an expert e-commerce assistant helping with {app_context}.
        Your goal is to:
        1. Make the user feel comfortable and understood
        2. Gather essential information naturally through conversation
        3. Assess risk tolerance and business style subtly
        4. Guide them through setup requirements conversationally
        5. Adapt your communication style to their responses

        Be helpful, professional, and empathetic. Focus on building trust while gathering necessary information."""

    def _get_personalized_system_prompt(self, persona: Dict, app_context: str) -> str:
        """Generate personalized FlipSync system prompt based on user persona."""
        if app_context == "flipsync":
            # Use the FlipSync assistant prompt with personalized context
            risk_level = persona.get("risk_tolerance", "moderate")
            communication_style = persona.get("preferred_style", "professional")

            context_variables = {
                "business_type": f"eBay business with {risk_level} risk tolerance",
                "sales_performance": persona.get(
                    "sales_performance", "moderate sales with optimization potential"
                ),
                "optimization_goals": "faster sales and higher profits with personalized approach",
                "available_features": "AI listing optimization, pricing analysis, shipping optimization",
            }
            return self.prompt_manager.get_system_prompt(
                UnifiedAgentRole.ASSISTANT, context_variables
            )

        risk_level = persona.get("risk_tolerance", "moderate")
        communication_style = persona.get("preferred_style", "professional")

        return f"""You are an expert e-commerce assistant for {app_context}.
        Based on the user's profile:
        - Risk Tolerance: {risk_level}
        - Communication Style: {communication_style}

        Adapt your suggestions and tone accordingly while maintaining professionalism.
        Focus on providing actionable insights and timely recommendations."""

    def _update_user_context(self, user_id: str, message: str, response: str):
        """Update user context and persona based on conversation."""
        # Update persona based on message content
        self._update_persona(user_id, message, response)

    def _update_persona(self, user_id: str, message: str, response: str):
        """Update user persona based on conversation analysis."""
        if user_id not in self.user_personas:
            self.user_personas[user_id] = {
                "risk_tolerance": "moderate",
                "preferred_style": "professional",
                "business_approach": "balanced",
                "created_at": datetime.now().isoformat(),
            }

        # Analyze message for persona indicators
        # This would be expanded based on specific indicators

    def _get_user_preferences(self, user_id: str) -> Dict:
        """Get user preferences from database."""
        # This would be implemented to fetch from your database
        return {}

    def _get_business_metrics(self, user_id: str, app_context: str) -> Dict:
        """Get relevant business metrics for context."""
        # This would be implemented to fetch from your database
        return {}

    # Enhanced chat service helper methods

    async def _get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """Get conversation history from database with strict conversation isolation."""
        try:
            if not self.database:
                logger.warning("Database not available for conversation history")
                return []

            # CRITICAL: Validate conversation_id to prevent contamination
            if not conversation_id or not isinstance(conversation_id, str):
                logger.error(f"Invalid conversation_id: {conversation_id}")
                return []

            logger.info(
                f"🔍 Getting conversation history for EXACT conversation_id: {conversation_id}"
            )

            async with self.database.get_session() as session:
                # CRITICAL: Use exact conversation_id match to prevent cross-contamination
                messages = await self.chat_repository.get_conversation_messages(
                    session,
                    conversation_id,
                    limit=10,  # Reduced limit to prevent context pollution
                )

                # CRITICAL: Double-check that all messages belong to the correct conversation
                filtered_messages = []
                for msg in messages:
                    if str(msg.conversation_id) == str(conversation_id):
                        filtered_messages.append(
                            {
                                "id": str(msg.id),
                                "content": msg.content,
                                "sender": msg.sender,
                                "agent_type": msg.agent_type,
                                "timestamp": msg.timestamp.isoformat(),
                                "metadata": msg.extra_metadata,
                                "conversation_id": str(
                                    msg.conversation_id
                                ),  # Include for verification
                            }
                        )
                    else:
                        logger.error(
                            f"🚨 CONVERSATION CONTAMINATION DETECTED: Message {msg.id} belongs to conversation {msg.conversation_id} but was retrieved for {conversation_id}"
                        )

                logger.info(
                    f"🔍 Retrieved {len(filtered_messages)} messages for conversation {conversation_id}"
                )
                return filtered_messages

        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []

    async def _generate_agent_response(
        self,
        message: str,
        user_id: str,
        conversation_id: str,
        agent_type: UnifiedAgentType,
        conversation_history: List[Dict],
        use_fast_model: bool = True,
        handoff_context: Optional[Dict] = None,
    ):
        """Generate response using the appropriate agent."""
        try:
            logger.info(
                f"🎯 Routing to real 12-agent system for message: '{message[:50]}...'"
            )

            # Get Real UnifiedAgent Manager from app state
            real_agent_manager = None
            if self.app and hasattr(self.app, "state"):
                real_agent_manager = getattr(self.app.state, "real_agent_manager", None)

            if real_agent_manager:
                # Map UnifiedAgentType enum to agent_id strings used by Real UnifiedAgent Manager
                agent_type_mapping = {
                    UnifiedAgentType.MARKET: "market_agent",
                    UnifiedAgentType.ANALYTICS: "market_agent",  # Analytics maps to market for now
                    UnifiedAgentType.LOGISTICS: "logistics_agent",
                    UnifiedAgentType.CONTENT: "content_agent",
                    UnifiedAgentType.EXECUTIVE: "executive_agent",
                    UnifiedAgentType.ASSISTANT: "executive_agent",  # Assistant maps to executive for now
                }

                agent_id = agent_type_mapping.get(agent_type, "executive_agent")
                logger.info(f"Intent analysis: {agent_id} (score: 1)")

                # Get the agent instance from Real UnifiedAgent Manager
                agent_instance = real_agent_manager.get_agent_instance(agent_id)

                if agent_instance:
                    logger.info(f"✅ UnifiedAgent {agent_id} available, routing to real agent")

                    # Prepare context for the agent
                    context = {
                        "handoff_context": handoff_context,
                        "use_fast_model": use_fast_model,
                        "user_id": user_id,
                        "conversation_id": conversation_id,
                        "conversation_history": conversation_history,
                    }

                    # Generate response using the real agent with correct method signature
                    try:
                        if hasattr(agent_instance, "process_message"):
                            # Call with correct parameter signature: message, user_id, conversation_id, conversation_history, context
                            agent_response = await agent_instance.process_message(
                                message=message,
                                user_id=user_id,
                                conversation_id=conversation_id,
                                conversation_history=conversation_history,
                                context=context,
                            )
                            logger.info(
                                f"✅ Real agent {agent_id} response generated via process_message"
                            )
                        elif hasattr(agent_instance, "handle_request"):
                            # Fallback to handle_request method with context
                            agent_response = await agent_instance.handle_request(
                                message, context
                            )
                            logger.info(
                                f"✅ Real agent {agent_id} response generated via handle_request"
                            )
                        else:
                            # Log available methods for debugging
                            available_methods = [
                                method
                                for method in dir(agent_instance)
                                if not method.startswith("_")
                            ]
                            logger.warning(
                                f"❌ UnifiedAgent {agent_id} has no process_message or handle_request method. Available methods: {available_methods}"
                            )
                            # Fallback to a basic response from the agent
                            agent_response = f"Hello! I'm the {agent_id.replace('_', ' ').title()} and I received your message: {message[:100]}..."

                        # Handle UnifiedAgentResponse objects vs string responses
                        if hasattr(agent_response, "content"):
                            # UnifiedAgentResponse object - extract content
                            if hasattr(agent_response.content, "content"):
                                # Nested LLMResponse inside UnifiedAgentResponse
                                response_content = agent_response.content.content
                                logger.info(
                                    f"✅ Extracted nested LLMResponse content from UnifiedAgentResponse object for {agent_id}"
                                )
                            else:
                                # Direct content in UnifiedAgentResponse
                                response_content = agent_response.content
                                logger.info(
                                    f"✅ Extracted direct content from UnifiedAgentResponse object for {agent_id}"
                                )
                        else:
                            # String response
                            response_content = str(agent_response)
                            logger.info(f"✅ Using string response from {agent_id}")

                        return response_content

                    except TypeError as te:
                        logger.error(
                            f"❌ Method signature mismatch for agent {agent_id}: {te}"
                        )
                        logger.error(f"❌ UnifiedAgent instance type: {type(agent_instance)}")
                        logger.error(
                            f"❌ Available methods: {[method for method in dir(agent_instance) if not method.startswith('_')]}"
                        )
                        # Fall through to legacy response

                    except Exception as ae:
                        logger.error(f"❌ UnifiedAgent {agent_id} execution error: {ae}")
                        logger.exception(f"Full exception details for agent {agent_id}")
                        # Fall through to legacy response
                else:
                    logger.warning(
                        f"❌ UnifiedAgent {agent_id} not available in Real UnifiedAgent Manager, using fallback"
                    )
            else:
                logger.warning(f"❌ Real UnifiedAgent Manager not available, using fallback")

            # Fallback to legacy LLM-based response generation
            return await self._generate_legacy_agent_response(
                message,
                user_id,
                conversation_id,
                agent_type,
                conversation_history,
                use_fast_model,
                handoff_context,
            )

        except Exception as e:
            logger.error(f"Error generating agent response: {e}")
            return f"I apologize, but I'm having trouble processing your request right now. Please try again."

    async def _generate_legacy_agent_response(
        self,
        message: str,
        user_id: str,
        conversation_id: str,
        agent_type: UnifiedAgentType,
        conversation_history: List[Dict],
        use_fast_model: bool = True,
        handoff_context: Optional[Dict] = None,
    ) -> str:
        """Generate response using legacy LLM-based approach."""
        try:
            # Select LLM client
            llm_client = self.fast_llm if use_fast_model else self.smart_llm

            # Get agent role mapping
            agent_role_mapping = {
                UnifiedAgentType.MARKET: UnifiedAgentRole.MARKET,
                UnifiedAgentType.ANALYTICS: UnifiedAgentRole.ANALYTICS,
                UnifiedAgentType.LOGISTICS: UnifiedAgentRole.LOGISTICS,
                UnifiedAgentType.CONTENT: UnifiedAgentRole.CONTENT,
                UnifiedAgentType.EXECUTIVE: UnifiedAgentRole.EXECUTIVE,
                UnifiedAgentType.ASSISTANT: UnifiedAgentRole.ASSISTANT,
            }

            agent_role = agent_role_mapping.get(agent_type, UnifiedAgentRole.ASSISTANT)

            # Get system prompt for the agent
            context_variables = {
                "business_type": "e-commerce business",
                "marketplaces": "Amazon, eBay",
                "categories": "various product categories",
            }

            system_prompt = self.prompt_manager.get_system_prompt(
                agent_role, context_variables
            )

            # Add handoff context if provided
            if handoff_context:
                handoff_prompt = self.prompt_manager.get_handoff_prompt(
                    agent_role, handoff_context
                )
                message = f"{handoff_prompt}\n\nUnifiedUser: {message}"

            # CRITICAL: FORCE CLEAN CONTEXT - NO CONTAMINATION ALLOWED
            logger.info(f"🧹 FORCING CLEAN CONTEXT for conversation {conversation_id}")

            # CRITICAL: Start with completely clean context - no history contamination
            context_messages = []

            # CRITICAL: Only add the current user message - no history to prevent contamination
            context_messages.append({"role": "user", "content": message})

            logger.info(
                f"🧹 Using CLEAN context with only current message for conversation {conversation_id}"
            )

            # CRITICAL: Create proper ConversationContext object instead of passing raw list
            from fs_agt_clean.core.ai.llm_adapter import ConversationContext

            conversation_context = ConversationContext(
                conversation_id=conversation_id, messages=context_messages
            )

            # CRITICAL: Generate response with CLEAN context only
            llm_response = await llm_client.generate_response(
                prompt=message,
                system_prompt=system_prompt,
                context=conversation_context,  # Pass proper ConversationContext object
            )

            return llm_response.content

        except Exception as e:
            logger.error(f"Error generating legacy agent response: {e}")
            return f"I apologize, but I'm having trouble processing your request right now. Please try again."

    async def _store_conversation_messages(
        self,
        conversation_id: str,
        user_id: str,
        user_message: str,
        agent_response: str,
        agent_type: str,
        intent_result,
        routing_decision,
    ):
        """Store conversation messages in database."""
        try:
            if not self.database:
                logger.warning(
                    "Database not available for storing conversation messages"
                )
                return

            async with self.database.get_session() as session:
                # Store user message
                await self.chat_repository.create_message(
                    session=session,
                    conversation_id=conversation_id,
                    content=user_message,
                    sender="user",
                    agent_type=None,
                    metadata={
                        "intent": intent_result.primary_intent,
                        "intent_confidence": intent_result.confidence,
                        "entities": intent_result.extracted_entities,
                        "user_id": user_id,
                    },
                )

                # Store agent response
                await self.chat_repository.create_message(
                    session=session,
                    conversation_id=conversation_id,
                    content=agent_response,
                    sender="agent",
                    agent_type=agent_type,
                    metadata={
                        "routing_confidence": routing_decision.confidence,
                        "routing_reasoning": routing_decision.reasoning,
                        "requires_handoff": routing_decision.requires_handoff,
                        "generated_by": "enhanced_chat_service",
                    },
                )

        except Exception as e:
            logger.error(f"Error storing conversation messages: {e}")

    def _generate_handoff_message(self, target_agent: UnifiedAgentType, intent_result) -> str:
        """Generate a handoff message for agent transitions."""
        agent_descriptions = {
            UnifiedAgentType.MARKET: "Market Intelligence specialist",
            UnifiedAgentType.ANALYTICS: "Analytics and reporting expert",
            UnifiedAgentType.LOGISTICS: "Logistics and fulfillment specialist",
            UnifiedAgentType.CONTENT: "Content optimization expert",
            UnifiedAgentType.EXECUTIVE: "Executive decision support specialist",
            UnifiedAgentType.ASSISTANT: "General assistant",
        }

        agent_desc = agent_descriptions.get(target_agent, "specialist")

        return f"I'm connecting you with our {agent_desc} who can better assist with your {intent_result.primary_intent.replace('_', ' ')} question."

    async def start_new_session(self, user_id: str = None) -> str:
        """Start a new session with fresh conversation context."""
        try:
            logger.info(f"🔄 Starting new session for user: {user_id}")

            # Generate a new conversation ID for the session
            import uuid

            new_conversation_id = str(uuid.uuid4())

            if self.database:
                async with self.database.get_session() as session:
                    # Create a new conversation in the database
                    conversation = await self.chat_repository.create_conversation(
                        session=session,
                        conversation_id=new_conversation_id,
                        title="New Chat Session",
                        metadata={
                            "session_start": datetime.now(timezone.utc).isoformat(),
                            "user_id": user_id,
                            "session_type": "fresh_start",
                        },
                    )
                    logger.info(f"🔄 Created new conversation: {new_conversation_id}")

            return new_conversation_id

        except Exception as e:
            logger.error(f"Error starting new session: {e}")
            # Return a fallback conversation ID
            import uuid

            return str(uuid.uuid4())

    async def clear_conversation_history(self, conversation_id: str) -> bool:
        """Clear conversation history for session-based chat clearing."""
        try:
            logger.info(f"🧹 Clearing conversation history for: {conversation_id}")

            if not self.database:
                logger.warning(
                    "Database not available for clearing conversation history"
                )
                return False

            async with self.database.get_session() as session:
                # Mark messages as archived instead of deleting (for audit purposes)
                messages = await self.chat_repository.get_conversation_messages(
                    session, conversation_id, limit=1000
                )

                for msg in messages:
                    if msg.extra_metadata is None:
                        msg.extra_metadata = {}
                    msg.extra_metadata["archived"] = True
                    msg.extra_metadata["archived_at"] = datetime.now(
                        timezone.utc
                    ).isoformat()

                await session.commit()
                logger.info(
                    f"🧹 Archived {len(messages)} messages for conversation {conversation_id}"
                )
                return True

        except Exception as e:
            logger.error(f"Error clearing conversation history: {e}")
            return False

    async def get_conversation_context(self, conversation_id: str) -> Dict[str, Any]:
        """Get comprehensive conversation context."""
        try:
            if not self.database:
                logger.warning("Database not available for conversation context")
                return {}

            async with self.database.get_session() as session:
                # Get conversation details
                conversation = await self.chat_repository.get_conversation(
                    session, conversation_id
                )
                if not conversation:
                    return {}

                # Get recent messages (excluding archived ones)
                messages = await self.chat_repository.get_conversation_messages(
                    session, conversation_id, limit=10
                )

                # Filter out archived messages
                active_messages = [
                    msg
                    for msg in messages
                    if not (
                        msg.extra_metadata and msg.extra_metadata.get("archived", False)
                    )
                ]

                # Get agent decisions related to this conversation
                agent_decisions = await self.agent_repository.get_agent_decisions(
                    session, filters={"conversation_id": conversation_id}, limit=5
                )

                return {
                    "conversation": {
                        "id": str(conversation.id),
                        "title": conversation.title,
                        "created_at": conversation.created_at.isoformat(),
                        "updated_at": conversation.updated_at.isoformat(),
                        "metadata": conversation.extra_metadata,
                    },
                    "recent_messages": [
                        {
                            "content": msg.content,
                            "sender": msg.sender,
                            "agent_type": msg.agent_type,
                            "timestamp": msg.timestamp.isoformat(),
                        }
                        for msg in active_messages
                    ],
                    "agent_decisions": [
                        {
                            "agent_type": decision.agent_type,
                            "decision_type": decision.decision_type,
                            "confidence": decision.confidence,
                            "timestamp": decision.created_at.isoformat(),
                        }
                        for decision in agent_decisions
                    ],
                }

        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return {}


# Maintain backward compatibility
class ChatService(EnhancedChatService):
    """Legacy ChatService class for backward compatibility."""

    def __init__(self):
        super().__init__()
