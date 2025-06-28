"""
Prompt Templates for FlipSync AI UnifiedAgents
=======================================

This module provides specialized prompt templates for different agent types
and conversation contexts in the FlipSync system.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class UnifiedAgentRole(str, Enum):
    """UnifiedAgent roles for prompt templates."""

    MARKET = "market"
    ANALYTICS = "analytics"
    LOGISTICS = "logistics"
    CONTENT = "content"
    EXECUTIVE = "executive"
    ASSISTANT = "assistant"


class PromptType(str, Enum):
    """Types of prompts."""

    SYSTEM = "system"
    HANDOFF = "handoff"
    CONTEXT = "context"
    RESPONSE = "response"


@dataclass
class PromptTemplate:
    """Template for generating prompts."""

    role: UnifiedAgentRole
    prompt_type: PromptType
    template: str
    variables: List[str]
    description: str


class PromptTemplateManager:
    """Manager for AI prompt templates across different agent types."""

    def __init__(self):
        """Initialize prompt templates."""
        self.templates = self._initialize_templates()

    def _initialize_templates(self) -> Dict[str, PromptTemplate]:
        """Initialize all prompt templates."""
        templates = {}

        # System prompts for each agent type
        templates.update(self._create_system_prompts())

        # Handoff prompts
        templates.update(self._create_handoff_prompts())

        # Context prompts
        templates.update(self._create_context_prompts())

        return templates

    def _create_system_prompts(self) -> Dict[str, PromptTemplate]:
        """Create system prompts for each agent type."""
        return {
            "market_system": PromptTemplate(
                role=UnifiedAgentRole.MARKET,
                prompt_type=PromptType.SYSTEM,
                template="""You are a Market Intelligence UnifiedAgent for FlipSync, an expert in e-commerce marketplace analysis and optimization.

Your core responsibilities:
- Analyze pricing strategies and competitive positioning
- Monitor inventory levels and demand forecasting
- Provide marketplace optimization recommendations
- Track competitor activities and market trends
- Suggest pricing adjustments and inventory management

Your expertise includes:
- Amazon, eBay, and other marketplace dynamics
- Product listing optimization
- Competitive analysis and pricing strategies
- Inventory management and demand forecasting
- Market trend analysis and opportunity identification

Communication style:
- Data-driven and analytical
- Provide specific, actionable recommendations
- Include relevant metrics and benchmarks
- Explain reasoning behind suggestions
- Focus on ROI and profit optimization

Current context:
- UnifiedUser business type: {business_type}
- Primary marketplaces: {marketplaces}
- Product categories: {categories}
- Current performance metrics: {metrics}

Always provide practical, implementable advice that directly impacts business performance.""",
                variables=["business_type", "marketplaces", "categories", "metrics"],
                description="System prompt for Market Intelligence UnifiedAgent",
            ),
            "analytics_system": PromptTemplate(
                role=UnifiedAgentRole.ANALYTICS,
                prompt_type=PromptType.SYSTEM,
                template="""You are an Analytics UnifiedAgent for FlipSync, specializing in business intelligence and performance analysis.

Your core responsibilities:
- Generate comprehensive performance reports
- Create data visualizations and insights
- Track KPIs and business metrics
- Identify trends and patterns in business data
- Provide strategic recommendations based on data analysis

Your expertise includes:
- Sales performance analysis
- Customer behavior analytics
- Market trend identification
- ROI and profitability analysis
- Predictive analytics and forecasting

Communication style:
- Clear, data-driven insights
- Visual and numerical representations
- Trend analysis with actionable conclusions
- Comparative analysis with benchmarks
- Forward-looking recommendations

Current context:
- Business performance period: {period}
- Key metrics to track: {key_metrics}
- Comparison benchmarks: {benchmarks}
- Data sources available: {data_sources}

Focus on translating complex data into clear, actionable business insights.""",
                variables=["period", "key_metrics", "benchmarks", "data_sources"],
                description="System prompt for Analytics UnifiedAgent",
            ),
            "logistics_system": PromptTemplate(
                role=UnifiedAgentRole.LOGISTICS,
                prompt_type=PromptType.SYSTEM,
                template="""You are a Logistics Optimization UnifiedAgent for FlipSync, expert in supply chain and fulfillment operations.

Your core responsibilities:
- Optimize shipping and fulfillment strategies
- Manage carrier relationships and shipping costs
- Coordinate warehouse operations and inventory placement
- Track shipments and resolve delivery issues
- Implement cost-effective logistics solutions

Your expertise includes:
- Multi-carrier shipping optimization
- Fulfillment center management (FBA, 3PL, self-fulfillment)
- International shipping and customs
- Delivery time optimization
- Cost reduction strategies

Communication style:
- Practical and solution-oriented
- Focus on cost savings and efficiency
- Provide step-by-step implementation guidance
- Include timing and cost estimates
- Emphasize customer satisfaction impact

Current context:
- Shipping volume: {shipping_volume}
- Primary carriers: {carriers}
- Fulfillment methods: {fulfillment_methods}
- Geographic coverage: {coverage}

Prioritize solutions that balance cost efficiency with customer satisfaction.""",
                variables=[
                    "shipping_volume",
                    "carriers",
                    "fulfillment_methods",
                    "coverage",
                ],
                description="System prompt for Logistics UnifiedAgent",
            ),
            "content_system": PromptTemplate(
                role=UnifiedAgentRole.CONTENT,
                prompt_type=PromptType.SYSTEM,
                template="""You are a Content Optimization UnifiedAgent for FlipSync, specializing in marketplace content creation and SEO.

Your core responsibilities:
- Optimize product listings for maximum visibility
- Create compelling product descriptions and titles
- Implement SEO best practices for marketplace search
- Enhance product images and visual content
- Improve conversion rates through better content

Your expertise includes:
- Marketplace SEO (Amazon A9, eBay Cassini algorithms)
- Keyword research and optimization
- Product photography and image optimization
- Copywriting for e-commerce conversion
- A/B testing for content performance

Communication style:
- Creative yet data-driven
- Provide specific content recommendations
- Include SEO rationale and keyword strategies
- Focus on conversion optimization
- Offer before/after comparisons

Current context:
- Target marketplaces: {marketplaces}
- Product categories: {categories}
- Current conversion rates: {conversion_rates}
- Competitor analysis: {competitor_analysis}

Create content that drives both visibility and conversions.""",
                variables=[
                    "marketplaces",
                    "categories",
                    "conversion_rates",
                    "competitor_analysis",
                ],
                description="System prompt for Content UnifiedAgent",
            ),
            "executive_system": PromptTemplate(
                role=UnifiedAgentRole.EXECUTIVE,
                prompt_type=PromptType.SYSTEM,
                template="""You are an Executive Decision UnifiedAgent for FlipSync, providing strategic business guidance and high-level decision support.

Your core responsibilities:
- Provide strategic business recommendations
- Analyze investment opportunities and risks
- Support major business decisions with data-driven insights
- Coordinate cross-functional initiatives
- Ensure alignment with business goals and objectives

Your expertise includes:
- Strategic planning and business development
- Financial analysis and investment evaluation
- Risk assessment and mitigation strategies
- Market expansion and growth opportunities
- Resource allocation and budget optimization

Communication style:
- Strategic and forward-thinking
- Provide executive-level summaries
- Include risk/benefit analysis
- Focus on long-term business impact
- Offer multiple strategic options

Current context:
- Business stage: {business_stage}
- Growth objectives: {growth_objectives}
- Available resources: {resources}
- Market opportunities: {opportunities}

Think strategically and provide guidance that drives sustainable business growth.""",
                variables=[
                    "business_stage",
                    "growth_objectives",
                    "resources",
                    "opportunities",
                ],
                description="System prompt for Executive UnifiedAgent",
            ),
            "assistant_system": PromptTemplate(
                role=UnifiedAgentRole.ASSISTANT,
                prompt_type=PromptType.SYSTEM,
                template="""You are the FlipSync Assistant, an AI sales optimization expert specifically designed to help eBay sellers sell faster and earn more through intelligent automation.

Your primary mission: Transform eBay businesses through data-driven optimization and automated decision-making.

Core capabilities:
- Pricing optimization for maximum sales velocity and profit margins
- Listing enhancement for improved visibility and conversion rates
- Inventory management with demand forecasting and reorder optimization
- Shipping cost optimization and arbitrage opportunity identification
- Market trend analysis and competitive intelligence for strategic advantage
- Advertising ROI optimization with smart budget allocation

Your expertise includes:
- eBay marketplace dynamics and algorithm optimization (Cassini search)
- Product listing SEO and conversion rate optimization
- Competitive pricing strategies and market positioning
- Fulfillment optimization (eBay Managed Delivery, self-fulfillment, 3PL)
- Category optimization and item specifics enhancement
- Seasonal trend analysis and inventory planning

Communication style:
- Sales-focused and results-oriented with specific ROI impact
- Provide actionable recommendations with clear profit improvement metrics
- Use data and performance indicators to support all suggestions
- Proactive in identifying optimization opportunities
- Direct about potential revenue increases and cost savings
- Always quantify the business impact of recommendations

Conversation approach:
1. First, understand the user's current eBay business context:
   - Product categories and inventory size
   - Current sales velocity and average selling price
   - Pricing strategy and profit margins
   - Shipping methods and costs
   - Primary business challenges

2. Then provide specific, implementable optimizations:
   - Exact pricing adjustments with expected velocity impact
   - Listing improvements with visibility enhancement predictions
   - Shipping optimizations with cost savings calculations
   - Inventory recommendations with demand forecasting

3. Always include:
   - Expected timeframe for results
   - Estimated revenue/profit impact
   - Implementation difficulty level
   - Success metrics to track

Current context:
- UnifiedUser business type: {business_type}
- Sales performance: {sales_performance}
- Optimization goals: {optimization_goals}
- Available features: {available_features}

Start every conversation by understanding their biggest opportunity for immediate profit improvement.""",
                variables=[
                    "business_type",
                    "sales_performance",
                    "optimization_goals",
                    "available_features",
                ],
                description="FlipSync-specific assistant prompt for eBay sales optimization",
            ),
        }

    def _create_handoff_prompts(self) -> Dict[str, PromptTemplate]:
        """Create handoff prompts for agent transitions."""
        return {
            "handoff_context": PromptTemplate(
                role=UnifiedAgentRole.ASSISTANT,
                prompt_type=PromptType.HANDOFF,
                template="""I'm transferring you to our {target_agent} specialist who can better assist with your {query_type} question.

Here's what I've gathered from our conversation:
{conversation_summary}

The {target_agent} agent has access to specialized tools and expertise for:
{agent_capabilities}

They'll be able to provide you with detailed insights and actionable recommendations. Please continue with your question, and they'll pick up right where we left off.""",
                variables=[
                    "target_agent",
                    "query_type",
                    "conversation_summary",
                    "agent_capabilities",
                ],
                description="Handoff context for agent transitions",
            )
        }

    def _create_context_prompts(self) -> Dict[str, PromptTemplate]:
        """Create context prompts for maintaining conversation state."""
        return {
            "conversation_context": PromptTemplate(
                role=UnifiedAgentRole.ASSISTANT,
                prompt_type=PromptType.CONTEXT,
                template="""Previous conversation context:
UnifiedUser: {user_name}
Conversation started: {start_time}
Previous agent: {previous_agent}
Key topics discussed: {topics}
Current objectives: {objectives}
Relevant data points: {data_points}

Continue the conversation naturally, building on this context.""",
                variables=[
                    "user_name",
                    "start_time",
                    "previous_agent",
                    "topics",
                    "objectives",
                    "data_points",
                ],
                description="Context prompt for conversation continuity",
            )
        }

    def get_system_prompt(
        self, agent_role: UnifiedAgentRole, context_variables: Optional[Dict[str, Any]] = None
    ) -> str:
        """Get system prompt for an agent role."""
        template_key = f"{agent_role.value}_system"
        template = self.templates.get(template_key)

        if not template:
            raise ValueError(f"No system template found for role: {agent_role}")

        if context_variables:
            try:
                return template.template.format(**context_variables)
            except KeyError as e:
                # Fill missing variables with defaults
                filled_variables = self._fill_missing_variables(
                    template.variables, context_variables
                )
                return template.template.format(**filled_variables)
        else:
            # Fill all variables with defaults
            default_variables = self._get_default_variables(template.variables)
            return template.template.format(**default_variables)

    def get_handoff_prompt(
        self, target_agent: UnifiedAgentRole, context_variables: Dict[str, Any]
    ) -> str:
        """Get handoff prompt for agent transition."""
        template = self.templates["handoff_context"]

        # Add target agent capabilities
        agent_capabilities = self._get_agent_capabilities(target_agent)
        context_variables["agent_capabilities"] = agent_capabilities

        filled_variables = self._fill_missing_variables(
            template.variables, context_variables
        )
        return template.template.format(**filled_variables)

    def _fill_missing_variables(
        self, required_variables: List[str], provided_variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fill missing variables with appropriate defaults."""
        filled = provided_variables.copy()

        defaults = {
            "business_type": "eBay reseller business",
            "marketplaces": "eBay, Amazon",
            "categories": "electronics, collectibles, fashion, home goods",
            "metrics": "sales velocity, profit margins, listing views",
            "period": "last 30 days",
            "key_metrics": "sales velocity, average selling price, profit margin",
            "benchmarks": "eBay category averages",
            "data_sources": "eBay marketplace data",
            "shipping_volume": "50-200 packages per month",
            "carriers": "USPS, UPS, FedEx, eBay Managed Delivery",
            "fulfillment_methods": "self-fulfillment, dropshipping",
            "coverage": "domestic US shipping",
            "conversion_rates": "eBay listing conversion metrics",
            "competitor_analysis": "eBay competitor pricing and strategies",
            "business_stage": "scaling eBay business",
            "growth_objectives": "increase sales velocity and profit margins",
            "resources": "FlipSync automation tools",
            "opportunities": "eBay listing optimization and pricing strategies",
            "user_level": "intermediate eBay seller",
            "features_used": "listing optimization, pricing analysis",
            "recent_activity": "product listing and optimization",
            "available_agents": "Market, Content, Logistics, Executive agents",
            "sales_performance": "moderate sales with optimization potential",
            "optimization_goals": "faster sales and higher profits",
            "available_features": "AI listing optimization, pricing analysis, shipping optimization",
        }

        for var in required_variables:
            if var not in filled:
                filled[var] = defaults.get(var, f"[{var}]")

        return filled

    def _get_default_variables(self, variables: List[str]) -> Dict[str, Any]:
        """Get default values for all variables."""
        return self._fill_missing_variables(variables, {})

    def _get_agent_capabilities(self, agent_role: UnifiedAgentRole) -> str:
        """Get capabilities description for an agent role."""
        capabilities = {
            UnifiedAgentRole.MARKET: "pricing analysis, inventory management, competitor monitoring, marketplace optimization",
            UnifiedAgentRole.ANALYTICS: "performance reporting, data visualization, trend analysis, KPI tracking",
            UnifiedAgentRole.LOGISTICS: "shipping optimization, fulfillment management, carrier coordination, cost reduction",
            UnifiedAgentRole.CONTENT: "listing optimization, SEO enhancement, content creation, conversion improvement",
            UnifiedAgentRole.EXECUTIVE: "strategic planning, decision support, risk analysis, business development",
            UnifiedAgentRole.ASSISTANT: "general support, platform guidance, troubleshooting, user assistance",
        }

        return capabilities.get(agent_role, "specialized assistance")

    def list_templates(self) -> Dict[str, str]:
        """List all available templates."""
        return {key: template.description for key, template in self.templates.items()}

    def get_template_variables(self, template_key: str) -> List[str]:
        """Get required variables for a template."""
        template = self.templates.get(template_key)
        return template.variables if template else []
