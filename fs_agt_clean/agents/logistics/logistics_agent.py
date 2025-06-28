"""
Logistics UnifiedAgent for FlipSync - Conversational Logistics Management and Optimization

This agent specializes in:
- Shipping and fulfillment optimization
- Inventory rebalancing and management
- Carrier service coordination
- Delivery tracking and logistics planning
- Warehouse operations guidance
- Supply chain optimization
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fs_agt_clean.agents.base_conversational_agent import (
    UnifiedAgentResponse,
    BaseConversationalUnifiedAgent,
)
from fs_agt_clean.core.ai.prompt_templates import UnifiedAgentRole

# Import logistics services with error handling
try:
    from fs_agt_clean.services.logistics.shipping_service import ShippingService
except ImportError:
    ShippingService = None

try:
    from fs_agt_clean.services.inventory_management.manager import InventoryManager
except ImportError:
    InventoryManager = None

try:
    from fs_agt_clean.agents.logistics.warehouse_agent import WarehouseUnifiedAgent
except ImportError:
    WarehouseUnifiedAgent = None

try:
    from fs_agt_clean.agents.logistics.shipping_agent import ShippingUnifiedAgent
except ImportError:
    ShippingUnifiedAgent = None

logger = logging.getLogger(__name__)


class LogisticsUnifiedAgent(BaseConversationalUnifiedAgent):
    """
    Logistics UnifiedAgent for comprehensive supply chain and fulfillment management.

    Capabilities:
    - Shipping rate calculation and optimization
    - Inventory rebalancing recommendations
    - Carrier service management
    - Delivery tracking and status updates
    - Warehouse operations guidance
    - Fulfillment strategy optimization
    """

    def __init__(self, agent_id: str = None):
        """Initialize the Logistics UnifiedAgent."""
        super().__init__(
            agent_role=UnifiedAgentRole.LOGISTICS,
            agent_id=agent_id
            or f"logistics_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
        )

        # Initialize logistics services with error handling
        try:
            self.shipping_service = ShippingService() if ShippingService else None
        except Exception:
            self.shipping_service = None

        try:
            self.inventory_manager = InventoryManager() if InventoryManager else None
        except Exception:
            self.inventory_manager = None

        # Initialize specialized agents
        self.warehouse_agent = None
        self.shipping_agent = None

        # Logistics agent capabilities
        self.capabilities = [
            "shipping_optimization",
            "inventory_rebalancing",
            "carrier_management",
            "delivery_tracking",
            "warehouse_operations",
            "fulfillment_planning",
            "supply_chain_optimization",
            "cost_analysis",
        ]

        # Logistics-specific patterns for message processing
        self.logistics_patterns = {
            "shipping": [
                "ship",
                "shipping",
                "delivery",
                "carrier",
                "fedex",
                "ups",
                "usps",
                "track",
                "tracking",
                "package",
                "label",
                "rate",
                "cost",
            ],
            "inventory": [
                "inventory",
                "stock",
                "rebalance",
                "warehouse",
                "storage",
                "fulfillment",
                "reorder",
                "quantity",
                "availability",
                "allocation",
            ],
            "tracking": [
                "track",
                "tracking",
                "status",
                "delivery",
                "shipment",
                "package",
                "where",
                "when",
                "arrived",
                "transit",
            ],
            "optimization": [
                "optimize",
                "improve",
                "efficiency",
                "cost",
                "reduce",
                "faster",
                "better",
                "strategy",
                "plan",
                "recommend",
            ],
        }

        logger.info(f"Logistics UnifiedAgent initialized: {self.agent_id}")

    async def process_message(
        self,
        message: str,
        user_id: str = "test_user",
        conversation_id: str = "test_conversation",
        conversation_history: Optional[List[Dict]] = None,
        context: Dict[str, Any] = None,
    ) -> UnifiedAgentResponse:
        """
        Process logistics-related queries and provide optimization guidance.

        Args:
            message: UnifiedUser message requesting logistics assistance
            user_id: UnifiedUser identifier
            conversation_id: Conversation identifier
            conversation_history: Previous conversation messages
            context: Additional context for logistics operations

        Returns:
            UnifiedAgentResponse with logistics recommendations
        """
        try:
            # Classify the logistics request type
            request_type = self._classify_logistics_request(message)

            # Extract logistics information from message
            logistics_info = self._extract_logistics_info(message, context or {})

            # Generate logistics-specific response based on request type
            if request_type == "shipping":
                response_data = await self._handle_shipping_request(
                    message, logistics_info, context or {}
                )
            elif request_type == "inventory":
                response_data = await self._handle_inventory_request(
                    message, logistics_info, context or {}
                )
            elif request_type == "tracking":
                response_data = await self._handle_tracking_request(
                    message, logistics_info, context or {}
                )
            elif request_type == "optimization":
                response_data = await self._handle_optimization_request(
                    message, logistics_info, context or {}
                )
            else:
                response_data = await self._handle_general_logistics_query(
                    message, context or {}
                )

            # Generate LLM response with logistics context
            llm_response = await self._generate_logistics_response(
                message, response_data, request_type
            )

            return UnifiedAgentResponse(
                content=llm_response,
                agent_type="logistics",
                confidence=response_data.get("confidence", 0.8),
                response_time=0.25,  # Mock response time
                metadata={
                    "agent_id": self.agent_id,
                    "request_type": request_type,
                    "data": response_data,
                    "requires_approval": response_data.get("requires_approval", False),
                },
            )

        except Exception as e:
            logger.error(f"Error processing logistics message: {e}")
            return UnifiedAgentResponse(
                content="I apologize, but I encountered an issue with your logistics request. Please provide more specific details about what type of logistics assistance you need.",
                agent_type="logistics",
                confidence=0.1,
                response_time=0.1,
                metadata={
                    "agent_id": self.agent_id,
                    "error": str(e),
                    "requires_approval": False,
                },
            )

    async def _process_response(
        self,
        llm_response: str,
        original_message: str,
        conversation_id: str,
        context: Dict[str, Any],
    ) -> str:
        """Process LLM response with logistics-specific enhancements."""
        try:
            # Classify the logistics request type
            request_type = self._classify_logistics_request(original_message)

            # Extract logistics information from message
            logistics_info = self._extract_logistics_info(original_message, context)

            # Enhance response based on request type
            if request_type == "shipping":
                enhanced_response = await self._enhance_shipping_response(
                    llm_response, logistics_info, original_message
                )
            elif request_type == "inventory":
                enhanced_response = await self._enhance_inventory_response(
                    llm_response, logistics_info, original_message
                )
            elif request_type == "tracking":
                enhanced_response = await self._enhance_tracking_response(
                    llm_response, logistics_info, original_message
                )
            elif request_type == "optimization":
                enhanced_response = await self._enhance_optimization_response(
                    llm_response, logistics_info, original_message
                )
            else:
                enhanced_response = await self._enhance_general_response(
                    llm_response, original_message
                )

            return enhanced_response

        except Exception as e:
            logger.error(f"Error processing logistics response: {e}")
            return f"{llm_response}\n\n*Note: Some logistics features may be temporarily unavailable.*"

    def _classify_logistics_request(self, message: str) -> str:
        """Classify the type of logistics request."""
        message_lower = message.lower()

        # Count pattern matches for each category
        pattern_scores = {}
        for category, patterns in self.logistics_patterns.items():
            score = sum(1 for pattern in patterns if pattern in message_lower)
            pattern_scores[category] = score

        # Return category with highest score, default to general
        if not pattern_scores or max(pattern_scores.values()) == 0:
            return "general"

        return max(pattern_scores, key=pattern_scores.get)

    def _extract_logistics_info(
        self, message: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract logistics information from the message and context."""
        logistics_info = {
            "tracking_number": None,
            "carrier": None,
            "destination": None,
            "weight": None,
            "dimensions": None,
            "service_type": None,
            "order_id": None,
            "sku": None,
            "quantity": None,
        }

        # Extract tracking number patterns
        tracking_patterns = [
            r"tracking[:\s]+([A-Z0-9]{10,})",
            r"track[:\s]+([A-Z0-9]{10,})",
            r"([0-9]{12,22})",  # Common tracking number format
        ]

        for pattern in tracking_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                logistics_info["tracking_number"] = match.group(1).strip()
                break

        # Extract carrier mentions
        carriers = ["fedex", "ups", "usps", "dhl", "amazon"]
        for carrier in carriers:
            if carrier in message.lower():
                logistics_info["carrier"] = carrier.upper()
                break

        # Extract order ID patterns
        order_patterns = [
            r"order[:\s#]+([A-Z0-9\-]{6,})",
            r"order id[:\s]+([A-Z0-9\-]{6,})",
        ]

        for pattern in order_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                logistics_info["order_id"] = match.group(1).strip()
                break

        # Extract quantity mentions
        quantity_pattern = r"(\d+)\s*(?:units?|pieces?|items?|qty)"
        quantity_match = re.search(quantity_pattern, message, re.IGNORECASE)
        if quantity_match:
            logistics_info["quantity"] = int(quantity_match.group(1))

        return logistics_info

    # Required abstract methods from BaseConversationalUnifiedAgent

    async def _get_agent_context(self, conversation_id: str) -> Dict[str, Any]:
        """Get agent-specific context for prompt generation."""
        return {
            "agent_type": "logistics_optimization_specialist",
            "capabilities": self.capabilities,
            "specializations": [
                "Shipping optimization",
                "Inventory management",
                "Carrier coordination",
                "Fulfillment planning",
            ],
            "supported_carriers": ["FedEx", "UPS", "USPS", "DHL", "Amazon"],
            "logistics_operations": [
                "shipping",
                "tracking",
                "inventory",
                "warehousing",
            ],
        }

    # Handler methods for different logistics request types

    async def _handle_shipping_request(
        self, message: str, logistics_info: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle shipping-related requests."""
        try:
            # Generate shipping recommendations
            shipping_options = [
                {
                    "carrier": "FedEx",
                    "service": "Ground",
                    "cost": 12.50,
                    "delivery_days": "3-5",
                    "tracking": True,
                },
                {
                    "carrier": "UPS",
                    "service": "Ground",
                    "cost": 11.75,
                    "delivery_days": "3-5",
                    "tracking": True,
                },
                {
                    "carrier": "USPS",
                    "service": "Priority Mail",
                    "cost": 8.95,
                    "delivery_days": "2-3",
                    "tracking": True,
                },
            ]

            recommendations = [
                "Consider USPS Priority Mail for best value on small packages",
                "Use FedEx or UPS for time-sensitive shipments",
                "Negotiate volume discounts for regular shipping",
                "Implement zone skipping for cross-country shipments",
            ]

            return {
                "request_type": "shipping",
                "shipping_options": shipping_options,
                "recommendations": recommendations,
                "confidence": 0.9,
                "requires_approval": False,
            }

        except Exception as e:
            logger.error(f"Error in shipping request: {e}")
            return {
                "request_type": "shipping",
                "error": str(e),
                "confidence": 0.1,
                "requires_approval": False,
            }

    async def _handle_inventory_request(
        self, message: str, logistics_info: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle inventory management requests."""
        try:
            rebalancing_strategies = [
                "Move slow-moving inventory to lower-cost storage",
                "Redistribute high-demand items to multiple warehouses",
                "Implement just-in-time ordering for fast-moving SKUs",
                "Use seasonal forecasting for inventory planning",
            ]

            optimization_tips = [
                "Maintain 30-day safety stock for core products",
                "Use ABC analysis for inventory prioritization",
                "Implement automated reorder points",
                "Monitor inventory turnover ratios monthly",
            ]

            return {
                "request_type": "inventory",
                "rebalancing_strategies": rebalancing_strategies,
                "optimization_tips": optimization_tips,
                "confidence": 0.85,
                "requires_approval": False,
            }

        except Exception as e:
            logger.error(f"Error in inventory request: {e}")
            return {
                "request_type": "inventory",
                "error": str(e),
                "confidence": 0.1,
                "requires_approval": False,
            }

    async def _handle_tracking_request(
        self, message: str, logistics_info: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle tracking and delivery status requests."""
        try:
            tracking_number = logistics_info.get("tracking_number")
            carrier = logistics_info.get("carrier", "Unknown")

            # Mock tracking information
            tracking_info = {
                "tracking_number": tracking_number or "1234567890",
                "carrier": carrier,
                "status": "In Transit",
                "location": "Distribution Center - Chicago, IL",
                "estimated_delivery": "Tomorrow by 8:00 PM",
                "last_update": datetime.now(timezone.utc).strftime(
                    "%Y-%m-%d %H:%M:%S UTC"
                ),
            }

            tracking_tips = [
                "Set up delivery notifications for important shipments",
                "Use carrier-specific tracking for most accurate updates",
                "Consider signature confirmation for high-value items",
                "Track delivery performance metrics for carrier evaluation",
            ]

            return {
                "request_type": "tracking",
                "tracking_info": tracking_info,
                "tracking_tips": tracking_tips,
                "confidence": 0.9,
                "requires_approval": False,
            }

        except Exception as e:
            logger.error(f"Error in tracking request: {e}")
            return {
                "request_type": "tracking",
                "error": str(e),
                "confidence": 0.1,
                "requires_approval": False,
            }

    async def _handle_optimization_request(
        self, message: str, logistics_info: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle logistics optimization requests."""
        try:
            optimization_areas = [
                {
                    "area": "Shipping Costs",
                    "potential_savings": "15-25%",
                    "strategies": [
                        "Negotiate carrier rates",
                        "Optimize packaging",
                        "Zone skipping",
                    ],
                },
                {
                    "area": "Delivery Speed",
                    "potential_improvement": "20-30%",
                    "strategies": [
                        "Strategic warehouse placement",
                        "Carrier diversification",
                        "Local fulfillment",
                    ],
                },
                {
                    "area": "Inventory Efficiency",
                    "potential_improvement": "10-20%",
                    "strategies": [
                        "Demand forecasting",
                        "ABC analysis",
                        "Automated reordering",
                    ],
                },
            ]

            return {
                "request_type": "optimization",
                "optimization_areas": optimization_areas,
                "confidence": 0.85,
                "requires_approval": True,  # Optimization changes may need approval
            }

        except Exception as e:
            logger.error(f"Error in optimization request: {e}")
            return {
                "request_type": "optimization",
                "error": str(e),
                "confidence": 0.1,
                "requires_approval": False,
            }

    async def _handle_general_logistics_query(
        self, message: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle general logistics-related queries."""
        try:
            services = [
                "Shipping: Rate calculation and carrier optimization",
                "Inventory: Stock management and rebalancing strategies",
                "Tracking: Shipment monitoring and delivery updates",
                "Optimization: Cost reduction and efficiency improvements",
            ]

            return {
                "request_type": "general",
                "available_services": services,
                "confidence": 0.7,
                "requires_approval": False,
            }

        except Exception as e:
            logger.error(f"Error in general logistics query: {e}")
            return {
                "request_type": "general",
                "error": str(e),
                "confidence": 0.1,
                "requires_approval": False,
            }

    # LLM response generation and enhancement methods

    async def _generate_logistics_response(
        self, message: str, response_data: Dict[str, Any], request_type: str
    ) -> str:
        """Generate LLM response with logistics context."""
        try:
            # Create a context-aware prompt
            context_prompt = f"Logistics Request Type: {request_type}\n"
            context_prompt += f"UnifiedUser Message: {message}\n\n"

            if response_data.get("shipping_options"):
                context_prompt += "Shipping Options:\n"
                for option in response_data["shipping_options"]:
                    context_prompt += f"• {option['carrier']} {option['service']}: ${option['cost']} ({option['delivery_days']} days)\n"
                context_prompt += "\n"

            if response_data.get("tracking_info"):
                tracking = response_data["tracking_info"]
                context_prompt += f"Tracking Information:\n"
                context_prompt += f"• Tracking Number: {tracking['tracking_number']}\n"
                context_prompt += f"• Carrier: {tracking['carrier']}\n"
                context_prompt += f"• Status: {tracking['status']}\n"
                context_prompt += f"• Location: {tracking['location']}\n"
                context_prompt += (
                    f"• Estimated Delivery: {tracking['estimated_delivery']}\n\n"
                )

            if response_data.get("recommendations"):
                context_prompt += "Recommendations:\n"
                for rec in response_data["recommendations"]:
                    context_prompt += f"• {rec}\n"
                context_prompt += "\n"

            # Use the LLM client to generate a natural response
            system_prompt = """You are a logistics optimization expert helping with supply chain and fulfillment operations.
            Provide helpful, actionable advice based on the logistics analysis and recommendations provided.
            Be conversational but professional, and focus on practical implementation."""

            if hasattr(self, "llm_client") and self.llm_client:
                llm_response = await self.llm_client.generate_response(
                    prompt=context_prompt, system_prompt=system_prompt
                )
                return (
                    llm_response.content
                    if hasattr(llm_response, "content")
                    else str(llm_response)
                )
            else:
                # Fallback response
                return self._create_fallback_response(request_type, response_data)

        except Exception as e:
            logger.error(f"Error generating logistics response: {e}")
            return self._create_fallback_response(request_type, response_data)

    def _create_fallback_response(
        self, request_type: str, response_data: Dict[str, Any]
    ) -> str:
        """Create a fallback response when LLM is unavailable."""
        if request_type == "shipping":
            return "I can help you optimize your shipping operations. I've analyzed available carrier options and can provide rate comparisons and delivery time estimates to help you choose the best shipping solution."
        elif request_type == "inventory":
            return "I've analyzed your inventory management needs and can provide rebalancing strategies, optimization tips, and recommendations for improving your stock management efficiency."
        elif request_type == "tracking":
            return "I can help you track shipments and monitor delivery status. I've provided tracking information and tips for managing your delivery operations more effectively."
        elif request_type == "optimization":
            return "I've identified several logistics optimization opportunities that could reduce costs and improve efficiency. These recommendations focus on shipping, inventory, and fulfillment improvements."
        else:
            return "I'm here to help with all your logistics needs including shipping optimization, inventory management, tracking, and supply chain efficiency. What specific logistics assistance can I provide?"

    # Enhancement methods for different response types

    async def _enhance_shipping_response(
        self, llm_response: str, logistics_info: Dict[str, Any], original_message: str
    ) -> str:
        """Enhance shipping-related responses."""
        try:
            enhanced_response = f"{llm_response}\n\n"
            enhanced_response += "**Shipping Optimization Tips:**\n\n"

            tips = [
                "**Rate Shopping:** Compare rates across multiple carriers for each shipment",
                "**Packaging:** Optimize box sizes to reduce dimensional weight charges",
                "**Volume Discounts:** Negotiate better rates based on shipping volume",
                "**Zone Skipping:** Use regional carriers for local deliveries",
                "**Delivery Speed:** Balance cost vs. speed based on customer expectations",
            ]

            for tip in tips:
                enhanced_response += f"• {tip}\n"

            enhanced_response += "\n**Carrier Recommendations:**\n"
            enhanced_response += "• **USPS:** Best for small, lightweight packages\n"
            enhanced_response += "• **FedEx:** Reliable for time-sensitive shipments\n"
            enhanced_response += "• **UPS:** Good for business-to-business deliveries\n"
            enhanced_response += (
                "• **Regional Carriers:** Cost-effective for local zones\n"
            )

            return enhanced_response

        except Exception as e:
            logger.error(f"Error enhancing shipping response: {e}")
            return llm_response

    async def _enhance_inventory_response(
        self, llm_response: str, logistics_info: Dict[str, Any], original_message: str
    ) -> str:
        """Enhance inventory management responses."""
        try:
            enhanced_response = f"{llm_response}\n\n"
            enhanced_response += "**Inventory Management Best Practices:**\n\n"

            practices = [
                "**ABC Analysis:** Categorize inventory by value and turnover rate",
                "**Safety Stock:** Maintain buffer inventory for demand variability",
                "**Reorder Points:** Set automated triggers for replenishment",
                "**Demand Forecasting:** Use historical data for future planning",
                "**Cycle Counting:** Regular inventory audits for accuracy",
            ]

            for practice in practices:
                enhanced_response += f"• {practice}\n"

            enhanced_response += "\n**Rebalancing Strategies:**\n"
            enhanced_response += "• Move slow-moving items to lower-cost storage\n"
            enhanced_response += (
                "• Distribute fast-moving items across multiple locations\n"
            )
            enhanced_response += "• Use cross-docking for high-velocity products\n"
            enhanced_response += "• Implement just-in-time for predictable demand\n"

            return enhanced_response

        except Exception as e:
            logger.error(f"Error enhancing inventory response: {e}")
            return llm_response

    async def _enhance_tracking_response(
        self, llm_response: str, logistics_info: Dict[str, Any], original_message: str
    ) -> str:
        """Enhance tracking and delivery responses."""
        try:
            enhanced_response = f"{llm_response}\n\n"
            enhanced_response += "**Tracking Management Tips:**\n\n"

            tips = [
                "**Proactive Notifications:** Set up alerts for delivery exceptions",
                "**Customer Communication:** Provide tracking numbers immediately",
                "**Delivery Confirmation:** Use signature or photo confirmation",
                "**Performance Monitoring:** Track carrier delivery performance",
                "**Exception Handling:** Have processes for failed deliveries",
            ]

            for tip in tips:
                enhanced_response += f"• {tip}\n"

            enhanced_response += "\n**Common Tracking Statuses:**\n"
            enhanced_response += (
                "• **In Transit:** Package is moving through carrier network\n"
            )
            enhanced_response += (
                "• **Out for Delivery:** Package is on delivery truck\n"
            )
            enhanced_response += "• **Delivered:** Package has been delivered\n"
            enhanced_response += "• **Exception:** Delivery issue requiring attention\n"

            return enhanced_response

        except Exception as e:
            logger.error(f"Error enhancing tracking response: {e}")
            return llm_response

    async def _enhance_optimization_response(
        self, llm_response: str, logistics_info: Dict[str, Any], original_message: str
    ) -> str:
        """Enhance logistics optimization responses."""
        try:
            enhanced_response = f"{llm_response}\n\n"
            enhanced_response += "**Logistics Optimization Framework:**\n\n"

            framework = [
                "**Cost Analysis:** Identify all logistics-related expenses",
                "**Performance Metrics:** Track KPIs like delivery time and accuracy",
                "**Process Mapping:** Document current logistics workflows",
                "**Technology Integration:** Leverage automation and AI",
                "**Continuous Improvement:** Regular review and optimization",
            ]

            for item in framework:
                enhanced_response += f"• {item}\n"

            enhanced_response += "\n**Key Optimization Areas:**\n"
            enhanced_response += (
                "• **Transportation:** Route optimization and carrier selection\n"
            )
            enhanced_response += (
                "• **Warehousing:** Layout optimization and automation\n"
            )
            enhanced_response += (
                "• **Inventory:** Stock level optimization and forecasting\n"
            )
            enhanced_response += "• **Technology:** WMS, TMS, and integration systems\n"

            return enhanced_response

        except Exception as e:
            logger.error(f"Error enhancing optimization response: {e}")
            return llm_response

    async def _enhance_general_response(
        self, llm_response: str, original_message: str
    ) -> str:
        """Enhance general logistics responses."""
        try:
            enhanced_response = f"{llm_response}\n\n"
            enhanced_response += "**Logistics Services Available:**\n"
            enhanced_response += "• **Shipping:** Rate calculation, carrier selection, and optimization\n"
            enhanced_response += (
                "• **Inventory:** Stock management, rebalancing, and forecasting\n"
            )
            enhanced_response += (
                "• **Tracking:** Shipment monitoring and delivery management\n"
            )
            enhanced_response += (
                "• **Optimization:** Cost reduction and efficiency improvements\n\n"
            )
            enhanced_response += "*Ask me about shipping rates, inventory management, tracking shipments, or logistics optimization!*"

            return enhanced_response

        except Exception as e:
            logger.error(f"Error enhancing general response: {e}")
            return llm_response
