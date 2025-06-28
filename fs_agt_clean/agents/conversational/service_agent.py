"""
Service UnifiedAgent for FlipSync - Customer Service Integration and Support Automation

This agent specializes in:
- Customer inquiry routing and management
- Automated customer support responses
- Issue escalation and resolution tracking
- Multi-channel customer communication
- Support ticket management and prioritization
- Customer satisfaction monitoring
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from fs_agt_clean.agents.base_conversational_agent import (
    UnifiedAgentResponse,
    BaseConversationalUnifiedAgent,
)
from fs_agt_clean.core.ai.prompt_templates import UnifiedAgentRole

logger = logging.getLogger(__name__)


class TicketPriority(str, Enum):
    """Priority levels for customer service tickets."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class TicketStatus(str, Enum):
    """Status of customer service tickets."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_CUSTOMER = "pending_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


class TicketCategory(str, Enum):
    """Categories of customer service issues."""

    ORDER_INQUIRY = "order_inquiry"
    SHIPPING_ISSUE = "shipping_issue"
    RETURN_REQUEST = "return_request"
    PRODUCT_QUESTION = "product_question"
    BILLING_ISSUE = "billing_issue"
    TECHNICAL_SUPPORT = "technical_support"
    COMPLAINT = "complaint"
    GENERAL_INQUIRY = "general_inquiry"


@dataclass
class CustomerTicket:
    """Represents a customer service ticket."""

    ticket_id: str
    customer_id: str
    customer_email: str
    subject: str
    description: str
    category: TicketCategory
    priority: TicketPriority
    status: TicketStatus
    assigned_agent: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    resolved_at: Optional[datetime] = None
    messages: List[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.updated_at is None:
            self.updated_at = self.created_at
        if self.messages is None:
            self.messages = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class CustomerInteraction:
    """Represents a customer interaction."""

    interaction_id: str
    customer_id: str
    channel: str  # 'chat', 'email', 'phone', 'marketplace'
    message: str
    sentiment: str  # 'positive', 'neutral', 'negative'
    intent: str
    confidence: float
    timestamp: datetime
    resolved: bool = False
    escalated: bool = False


class ServiceUnifiedAgent(BaseConversationalUnifiedAgent):
    """
    Service UnifiedAgent for customer service integration and support automation.

    Capabilities:
    - Customer inquiry routing and classification
    - Automated response generation
    - Issue escalation management
    - Support ticket lifecycle management
    - Customer satisfaction tracking
    - Multi-channel communication coordination
    """

    def __init__(self, agent_id: Optional[str] = None, use_fast_model: bool = True):
        """Initialize the Service UnifiedAgent."""
        super().__init__(UnifiedAgentRole.ASSISTANT, agent_id, use_fast_model)

        # Service agent capabilities
        self.capabilities = [
            "customer_inquiry_routing",
            "automated_responses",
            "issue_escalation",
            "ticket_management",
            "sentiment_analysis",
            "multi_channel_support",
            "satisfaction_tracking",
            "knowledge_base_integration",
        ]

        # Active tickets and interactions
        self.active_tickets: Dict[str, CustomerTicket] = {}
        self.recent_interactions: List[CustomerInteraction] = []

        # Routing rules for different agent types
        self.routing_rules = {
            "pricing": ["market", "executive"],
            "inventory": ["logistics", "market"],
            "shipping": ["logistics", "shipping"],
            "product": ["content", "market"],
            "order": ["logistics", "executive"],
            "technical": ["executive"],
            "billing": ["executive"],
            "general": ["conversational"],
        }

        # Auto-response templates
        self.response_templates = {
            "order_status": "I can help you check your order status. Let me look that up for you.",
            "shipping_inquiry": "I'll check the shipping details for your order right away.",
            "return_request": "I understand you'd like to return an item. Let me guide you through the process.",
            "product_question": "I'm here to help with any product questions you have.",
            "general_greeting": "Hello! I'm here to help you with any questions or concerns you may have.",
        }

        # Escalation thresholds
        self.escalation_thresholds = {
            "response_time": 300,  # 5 minutes
            "negative_sentiment_count": 3,
            "unresolved_duration": 3600,  # 1 hour
        }

        logger.info(f"Service UnifiedAgent initialized: {self.agent_id}")

    async def handle_customer_inquiry(
        self,
        customer_id: str,
        customer_email: str,
        message: str,
        channel: str = "chat",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Handle a customer inquiry and route appropriately.

        Args:
            customer_id: Unique customer identifier
            customer_email: Customer email address
            message: Customer message/inquiry
            channel: Communication channel (chat, email, phone, etc.)
            metadata: Additional context information

        Returns:
            Dictionary containing response and routing information
        """
        try:
            # Analyze the customer message
            analysis = await self._analyze_customer_message(message)

            # Create interaction record
            interaction = CustomerInteraction(
                interaction_id=f"int_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{customer_id}",
                customer_id=customer_id,
                channel=channel,
                message=message,
                sentiment=analysis["sentiment"],
                intent=analysis["intent"],
                confidence=analysis["confidence"],
                timestamp=datetime.now(timezone.utc),
            )

            self.recent_interactions.append(interaction)

            # Determine if this needs to be escalated immediately
            should_escalate = await self._should_escalate(interaction, analysis)

            if should_escalate:
                # Create high-priority ticket and escalate
                ticket = await self._create_ticket(
                    customer_id, customer_email, message, analysis, TicketPriority.HIGH
                )
                return await self._escalate_to_specialist(ticket, analysis)

            # Check if we can provide an automated response
            auto_response = await self._generate_auto_response(analysis, interaction)

            if auto_response["can_auto_respond"]:
                return {
                    "response_type": "automated",
                    "message": auto_response["response"],
                    "confidence": auto_response["confidence"],
                    "interaction_id": interaction.interaction_id,
                    "requires_followup": auto_response["requires_followup"],
                }

            # Route to appropriate specialist agent
            routing_result = await self._route_to_specialist(analysis, interaction)

            return {
                "response_type": "routed",
                "target_agent": routing_result["agent_type"],
                "routing_confidence": routing_result["confidence"],
                "interaction_id": interaction.interaction_id,
                "estimated_response_time": routing_result["estimated_response_time"],
                "message": f"I'm connecting you with our {routing_result['agent_type']} specialist who can best help you with your {analysis['intent']} inquiry.",
            }

        except Exception as e:
            logger.error(f"Error handling customer inquiry: {e}")
            return {
                "response_type": "error",
                "message": "I apologize, but I'm experiencing technical difficulties. Please try again in a moment or contact our support team directly.",
                "error": str(e),
            }

    async def create_support_ticket(
        self,
        customer_id: str,
        customer_email: str,
        subject: str,
        description: str,
        category: TicketCategory,
        priority: TicketPriority = TicketPriority.MEDIUM,
    ) -> CustomerTicket:
        """Create a new customer support ticket."""
        ticket_id = f"ticket_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{customer_id}"

        ticket = CustomerTicket(
            ticket_id=ticket_id,
            customer_id=customer_id,
            customer_email=customer_email,
            subject=subject,
            description=description,
            category=category,
            priority=priority,
            status=TicketStatus.OPEN,
        )

        self.active_tickets[ticket_id] = ticket

        logger.info(f"Created support ticket {ticket_id} for customer {customer_id}")
        return ticket

    async def update_ticket_status(
        self, ticket_id: str, status: TicketStatus, message: Optional[str] = None
    ) -> bool:
        """Update the status of a support ticket."""
        if ticket_id not in self.active_tickets:
            return False

        ticket = self.active_tickets[ticket_id]
        ticket.status = status
        ticket.updated_at = datetime.now(timezone.utc)

        if status == TicketStatus.RESOLVED:
            ticket.resolved_at = datetime.now(timezone.utc)

        if message:
            ticket.messages.append(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "type": "status_update",
                    "message": message,
                    "agent_id": self.agent_id,
                }
            )

        logger.info(f"Updated ticket {ticket_id} status to {status}")
        return True

    async def get_ticket_status(self, ticket_id: str) -> Optional[CustomerTicket]:
        """Get the current status of a support ticket."""
        return self.active_tickets.get(ticket_id)

    async def list_customer_tickets(self, customer_id: str) -> List[CustomerTicket]:
        """List all tickets for a specific customer."""
        return [
            ticket
            for ticket in self.active_tickets.values()
            if ticket.customer_id == customer_id
        ]

    # Required abstract methods from BaseConversationalUnifiedAgent

    async def _process_response(
        self,
        llm_response: str,
        original_message: str,
        conversation_id: str,
        context: Optional[Dict[str, Any]],
    ) -> str:
        """Process the LLM response with service-specific logic."""
        # Add customer service context and helpful information
        if any(
            keyword in original_message.lower()
            for keyword in ["help", "support", "issue", "problem"]
        ):
            # Add service status information
            active_tickets = len(self.active_tickets)
            recent_interactions = len(self.recent_interactions)

            if active_tickets > 0:
                service_info = f"\n\n📋 **Service Status:**\n"
                service_info += f"• Active tickets: {active_tickets}\n"
                service_info += f"• Recent interactions: {recent_interactions}\n"
                service_info += "\n💡 **Tip:** I can help route your inquiry to the right specialist or create a support ticket if needed."

                llm_response += service_info

        return llm_response

    async def _get_agent_context(self, conversation_id: str) -> Dict[str, Any]:
        """Get agent-specific context for prompt generation."""
        return {
            "agent_type": "customer_service_specialist",
            "capabilities": self.capabilities,
            "specializations": [
                "Customer inquiry routing",
                "Automated support responses",
                "Issue escalation management",
                "Multi-channel communication",
            ],
            "supported_channels": ["chat", "email", "phone", "marketplace"],
            "service_metrics": {
                "active_tickets": len(self.active_tickets),
                "recent_interactions": len(self.recent_interactions),
            },
            "routing_options": list(self.routing_rules.keys()),
        }

    # Helper methods for customer service operations

    async def _analyze_customer_message(self, message: str) -> Dict[str, Any]:
        """Analyze customer message for intent, sentiment, and routing."""
        # Simple keyword-based analysis (in production, this would use NLP)
        message_lower = message.lower()

        # Determine intent
        intent = "general"
        confidence = 0.5

        intent_keywords = {
            "order": ["order", "purchase", "buy", "bought"],
            "shipping": ["ship", "delivery", "track", "arrive"],
            "return": ["return", "refund", "exchange", "cancel"],
            "product": ["product", "item", "quality", "description"],
            "billing": ["bill", "charge", "payment", "cost", "price"],
            "technical": ["error", "bug", "not working", "broken"],
        }

        for intent_type, keywords in intent_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                intent = intent_type
                confidence = 0.8
                break

        # Determine sentiment
        sentiment = "neutral"
        negative_words = ["angry", "frustrated", "terrible", "awful", "hate", "worst"]
        positive_words = ["great", "excellent", "love", "amazing", "perfect"]

        if any(word in message_lower for word in negative_words):
            sentiment = "negative"
        elif any(word in message_lower for word in positive_words):
            sentiment = "positive"

        return {
            "intent": intent,
            "sentiment": sentiment,
            "confidence": confidence,
            "keywords": [word for word in message_lower.split() if len(word) > 3],
        }

    async def _should_escalate(
        self, interaction: CustomerInteraction, analysis: Dict[str, Any]
    ) -> bool:
        """Determine if an interaction should be escalated immediately."""
        # Escalate if negative sentiment
        if analysis["sentiment"] == "negative":
            return True

        # Escalate if customer has multiple recent negative interactions
        customer_negative_count = sum(
            1
            for i in self.recent_interactions[-10:]
            if i.customer_id == interaction.customer_id and i.sentiment == "negative"
        )

        if (
            customer_negative_count
            >= self.escalation_thresholds["negative_sentiment_count"]
        ):
            return True

        # Escalate if high-priority keywords
        escalation_keywords = [
            "urgent",
            "emergency",
            "critical",
            "lawsuit",
            "complaint",
        ]
        if any(
            keyword in interaction.message.lower() for keyword in escalation_keywords
        ):
            return True

        return False

    async def _generate_auto_response(
        self, analysis: Dict[str, Any], interaction: CustomerInteraction
    ) -> Dict[str, Any]:
        """Generate an automated response if possible."""
        intent = analysis["intent"]
        confidence = analysis["confidence"]

        # Only auto-respond for high-confidence, simple intents
        if confidence < 0.7:
            return {"can_auto_respond": False}

        # Check if we have a template for this intent
        template_key = f"{intent}_inquiry"
        if template_key in self.response_templates:
            response = self.response_templates[template_key]

            # Add personalized elements
            if intent == "order":
                response += (
                    " Please provide your order number so I can look up the details."
                )
            elif intent == "shipping":
                response += " I'll need your order number or tracking information."

            return {
                "can_auto_respond": True,
                "response": response,
                "confidence": confidence,
                "requires_followup": True,
            }

        return {"can_auto_respond": False}

    async def _route_to_specialist(
        self, analysis: Dict[str, Any], interaction: CustomerInteraction
    ) -> Dict[str, Any]:
        """Route customer to appropriate specialist agent."""
        intent = analysis["intent"]

        # Get routing options for this intent
        agent_options = self.routing_rules.get(intent, ["conversational"])

        # Select the best agent (for now, just pick the first option)
        target_agent = agent_options[0]

        # Estimate response time based on agent type
        response_times = {
            "market": "2-3 minutes",
            "logistics": "3-5 minutes",
            "executive": "5-10 minutes",
            "content": "2-4 minutes",
            "conversational": "1-2 minutes",
        }

        return {
            "agent_type": target_agent,
            "confidence": analysis["confidence"],
            "estimated_response_time": response_times.get(target_agent, "3-5 minutes"),
        }

    async def _create_ticket(
        self,
        customer_id: str,
        customer_email: str,
        message: str,
        analysis: Dict[str, Any],
        priority: TicketPriority,
    ) -> CustomerTicket:
        """Create a support ticket from customer interaction."""
        # Determine category from intent
        category_mapping = {
            "order": TicketCategory.ORDER_INQUIRY,
            "shipping": TicketCategory.SHIPPING_ISSUE,
            "return": TicketCategory.RETURN_REQUEST,
            "product": TicketCategory.PRODUCT_QUESTION,
            "billing": TicketCategory.BILLING_ISSUE,
            "technical": TicketCategory.TECHNICAL_SUPPORT,
        }

        category = category_mapping.get(
            analysis["intent"], TicketCategory.GENERAL_INQUIRY
        )

        return await self.create_support_ticket(
            customer_id=customer_id,
            customer_email=customer_email,
            subject=f"{analysis['intent'].title()} Inquiry",
            description=message,
            category=category,
            priority=priority,
        )

    async def _escalate_to_specialist(
        self, ticket: CustomerTicket, analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Escalate ticket to appropriate specialist."""
        ticket.status = TicketStatus.ESCALATED

        # Route to appropriate specialist
        routing_result = await self._route_to_specialist(analysis, None)

        return {
            "response_type": "escalated",
            "ticket_id": ticket.ticket_id,
            "target_agent": routing_result["agent_type"],
            "priority": ticket.priority.value,
            "message": f"I've created a {ticket.priority.value} priority ticket and escalated your {analysis['intent']} inquiry to our specialist team. Ticket ID: {ticket.ticket_id}",
        }
