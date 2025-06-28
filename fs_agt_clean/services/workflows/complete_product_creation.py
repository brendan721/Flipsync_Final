"""
Complete Product Creation Workflow for FlipSync
===============================================

This workflow integrates all components for complete image-to-listing creation:
- Image analysis with OpenAI Vision
- Enhanced product research with web scraping
- Cassini optimization with researched data
- Best Offer configuration
- eBay listing creation with all optimizations
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fs_agt_clean.agents.content.listing_content_agent import CassiniOptimizer
from fs_agt_clean.core.ai.vision_clients import GPT4VisionClient
from fs_agt_clean.core.monitoring.cost_tracker import CostCategory, record_ai_cost
from fs_agt_clean.services.marketplace.best_offer_manager import (
    BestOfferManager,
    BestOfferSettings,
    create_balanced_settings
)
from fs_agt_clean.services.marketplace.ebay_optimization import EbayOptimizationService
from fs_agt_clean.services.research.enhanced_product_research import (
    EnhancedProductResearchService,
    ProductResearchResult
)

logger = logging.getLogger(__name__)


@dataclass
class CompleteProductCreationRequest:
    """Request for complete product creation workflow."""
    
    image_data: bytes
    image_filename: str
    user_id: str
    marketplace: str = "ebay"
    
    # UnifiedUser preferences
    profit_vs_speed_preference: float = 0.5  # 0.0 = speed, 1.0 = profit
    minimum_profit_margin: float = 0.15
    cost_basis: Optional[float] = None
    target_category: Optional[str] = None
    
    # Advanced options
    enable_best_offer: bool = True
    enable_cassini_optimization: bool = True
    enable_web_research: bool = True


@dataclass
class OptimizedListingResult:
    """Result of complete product creation workflow."""
    
    # Core listing data
    title: str
    description: str
    category_id: str
    item_specifics: Dict[str, str]
    
    # Pricing and offers
    suggested_price: float
    best_offer_settings: Optional[BestOfferSettings]
    
    # Optimization metrics
    cassini_score: int
    research_confidence: float
    optimization_improvements: List[str]
    
    # Metadata
    workflow_id: str
    processing_time: float
    total_cost: float
    sources_used: List[str]
    created_at: datetime


class CompleteProductCreationWorkflow:
    """Complete workflow for creating optimized eBay listings from images."""
    
    def __init__(self):
        self.vision_client = GPT4VisionClient()
        self.research_service = EnhancedProductResearchService()
        self.best_offer_manager = BestOfferManager()
        self.ebay_optimizer = EbayOptimizationService()
        
        # Cassini optimizer configuration
        self.cassini_config = {
            "relevance_weight": 0.4,
            "performance_weight": 0.3,
            "seller_quality_weight": 0.3,
            "optimal_title_length": 65,
            "title_keyword_positions": [0, 1, 2],
            "item_specifics_importance": 0.25,
            "description_keyword_density": 0.015,
        }
        self.cassini_optimizer = CassiniOptimizer(self.cassini_config)
    
    async def create_optimized_listing(
        self, request: CompleteProductCreationRequest
    ) -> OptimizedListingResult:
        """Execute complete workflow from image to optimized listing."""
        
        workflow_id = f"workflow_{int(datetime.now().timestamp())}"
        start_time = asyncio.get_event_loop().time()
        total_cost = 0.0
        sources_used = []
        
        try:
            logger.info(f"Starting complete product creation workflow {workflow_id}")
            
            # Step 1: AI Image Analysis
            logger.info("Step 1: Analyzing image with AI...")
            image_analysis = await self._analyze_image(request.image_data, request.marketplace)
            total_cost += image_analysis.get("cost", 0.0)
            sources_used.append("openai_vision")
            
            # Step 2: Enhanced Product Research (if enabled)
            research_result = None
            if request.enable_web_research:
                logger.info("Step 2: Conducting enhanced product research...")
                research_result = await self.research_service.research_product_from_image(
                    image_analysis, request.marketplace
                )
                sources_used.extend(research_result.sources_used)
            
            # Step 3: Category Optimization
            logger.info("Step 3: Optimizing category selection...")
            category_optimization = await self._optimize_category(
                image_analysis, research_result, request.target_category
            )
            
            # Step 4: Cassini Optimization (if enabled)
            optimized_content = {}
            cassini_score = 0
            if request.enable_cassini_optimization:
                logger.info("Step 4: Applying Cassini optimization...")
                optimized_content = await self._apply_cassini_optimization(
                    image_analysis, research_result, category_optimization
                )
                cassini_score = optimized_content.get("cassini_optimization", {}).get("overall_score", 0)
            
            # Step 5: Pricing Strategy
            logger.info("Step 5: Calculating optimal pricing...")
            pricing_strategy = await self._calculate_pricing_strategy(
                research_result, request.cost_basis, request.profit_vs_speed_preference
            )
            
            # Step 6: Best Offer Configuration (if enabled)
            best_offer_settings = None
            if request.enable_best_offer:
                logger.info("Step 6: Configuring Best Offer settings...")
                best_offer_settings = await self._configure_best_offer(
                    request, pricing_strategy
                )
            
            # Step 7: Compile Final Result
            logger.info("Step 7: Compiling final optimized listing...")
            result = await self._compile_final_result(
                workflow_id=workflow_id,
                image_analysis=image_analysis,
                research_result=research_result,
                category_optimization=category_optimization,
                optimized_content=optimized_content,
                pricing_strategy=pricing_strategy,
                best_offer_settings=best_offer_settings,
                cassini_score=cassini_score,
                total_cost=total_cost,
                sources_used=sources_used,
                processing_time=asyncio.get_event_loop().time() - start_time
            )
            
            logger.info(f"Workflow {workflow_id} completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in complete product creation workflow: {e}")
            raise
    
    async def _analyze_image(self, image_data: bytes, marketplace: str) -> Dict[str, Any]:
        """Analyze image using OpenAI Vision."""
        
        try:
            result = await self.vision_client.analyze_image(
                image_data=image_data,
                analysis_type="product_identification",
                marketplace=marketplace,
                additional_context="Provide detailed product identification for eBay listing optimization"
            )
            
            # Add cost tracking
            cost = result.get("metadata", {}).get("cost", 0.02)  # Estimate if not provided
            await record_ai_cost(
                category=CostCategory.VISION_ANALYSIS.value,
                model="gpt-4o-vision",
                operation="product_identification",
                cost=cost,
                agent_id="complete_workflow"
            )
            
            result["cost"] = cost
            return result
            
        except Exception as e:
            logger.error(f"Error in image analysis: {e}")
            # Return minimal result to continue workflow
            return {
                "product_data": {
                    "title": "Unknown Product",
                    "category": "General",
                    "features": ["High-quality item"]
                },
                "confidence": 0.3,
                "cost": 0.0
            }
    
    async def _optimize_category(
        self, 
        image_analysis: Dict[str, Any], 
        research_result: Optional[ProductResearchResult],
        target_category: Optional[str]
    ) -> Dict[str, Any]:
        """Optimize eBay category selection."""
        
        try:
            product_data = image_analysis.get("product_data", {})
            product_name = product_data.get("title", "Unknown Product")
            current_category = target_category or product_data.get("category", "General")
            
            # Build product attributes from analysis and research
            product_attributes = {
                "brand": product_data.get("brand", "Unknown"),
                "condition": product_data.get("condition", "used"),
                "price_range": {"min": 10, "max": 1000}  # Default range
            }
            
            # Add research data if available
            if research_result:
                product_attributes.update({
                    "specifications": research_result.specifications,
                    "features": research_result.features,
                    "market_position": research_result.market_position
                })
            
            # Use eBay optimization service
            optimization_result = await self.ebay_optimizer.optimize_category(
                product_name, current_category, product_attributes
            )
            
            return optimization_result
            
        except Exception as e:
            logger.error(f"Error in category optimization: {e}")
            return {"primary_category": {"name": "Other", "id": "99"}}
    
    async def _apply_cassini_optimization(
        self,
        image_analysis: Dict[str, Any],
        research_result: Optional[ProductResearchResult],
        category_optimization: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply Cassini optimization using all available data."""
        
        try:
            # Build content from image analysis
            product_data = image_analysis.get("product_data", {})
            base_content = {
                "title": product_data.get("title", "Unknown Product"),
                "description": f"High-quality {product_data.get('title', 'product')} in excellent condition.",
                "item_specifics": {}
            }
            
            # Enhance with research data
            if research_result:
                # Use researched features for better description
                if research_result.features:
                    features_text = "\n".join([f"• {feature}" for feature in research_result.features])
                    base_content["description"] = f"""
{research_result.brand} {research_result.product_name}

Key Features:
{features_text}

{base_content['description']}
                    """.strip()
                
                # Add specifications as item specifics
                base_content["item_specifics"].update(research_result.specifications)
                
                # Build target keywords from research
                target_keywords = [
                    research_result.brand,
                    research_result.product_name,
                    research_result.category
                ] + research_result.features[:3]  # Top 3 features as keywords
            else:
                target_keywords = [
                    product_data.get("brand", ""),
                    product_data.get("title", ""),
                    product_data.get("category", "")
                ]
            
            # Build product data for Cassini optimizer
            cassini_product_data = {
                "brand": research_result.brand if research_result else product_data.get("brand", ""),
                "category": category_optimization.get("primary_category", {}).get("name", "General"),
                "features": research_result.features if research_result else product_data.get("features", [])
            }
            
            # Apply Cassini optimization
            optimized_content = await self.cassini_optimizer.optimize_for_cassini(
                content=base_content,
                product_data=cassini_product_data,
                target_keywords=[kw for kw in target_keywords if kw]
            )
            
            return optimized_content
            
        except Exception as e:
            logger.error(f"Error in Cassini optimization: {e}")
            # Return basic content
            product_data = image_analysis.get("product_data", {})
            return {
                "title": product_data.get("title", "Unknown Product"),
                "description": "High-quality product in excellent condition.",
                "item_specifics": {},
                "cassini_optimization": {"overall_score": 0}
            }
    
    async def _calculate_pricing_strategy(
        self,
        research_result: Optional[ProductResearchResult],
        cost_basis: Optional[float],
        profit_preference: float
    ) -> Dict[str, Any]:
        """Calculate optimal pricing strategy."""
        
        try:
            # Use competitive pricing if available
            if research_result and research_result.competitive_prices:
                prices = [p["price"] for p in research_result.competitive_prices]
                avg_market_price = sum(prices) / len(prices)
                min_market_price = min(prices)
                max_market_price = max(prices)
                
                # Adjust based on profit preference
                if profit_preference > 0.7:  # High profit preference
                    suggested_price = avg_market_price * 1.05  # Price above average
                elif profit_preference < 0.3:  # High speed preference
                    suggested_price = min_market_price * 0.98  # Price below minimum
                else:  # Balanced
                    suggested_price = avg_market_price * 0.99  # Slightly below average
                
            else:
                # Fallback pricing if no market data
                if cost_basis:
                    markup = 1.5 if profit_preference > 0.5 else 1.3
                    suggested_price = cost_basis * markup
                else:
                    suggested_price = 50.0  # Default price
            
            return {
                "suggested_price": round(suggested_price, 2),
                "market_data": research_result.competitive_prices if research_result else [],
                "pricing_strategy": "competitive" if research_result else "cost_plus"
            }
            
        except Exception as e:
            logger.error(f"Error calculating pricing strategy: {e}")
            return {"suggested_price": 50.0, "pricing_strategy": "default"}
    
    async def _configure_best_offer(
        self, request: CompleteProductCreationRequest, pricing_strategy: Dict[str, Any]
    ) -> BestOfferSettings:
        """Configure Best Offer settings based on user preferences."""
        
        try:
            # Create settings based on user preferences
            settings = BestOfferSettings(
                profit_vs_speed_preference=request.profit_vs_speed_preference,
                minimum_profit_margin=request.minimum_profit_margin,
                maximum_discount_percentage=0.30 if request.profit_vs_speed_preference < 0.5 else 0.20,
                auto_accept_enabled=True,
                auto_counter_enabled=True,
                time_decay_enabled=True
            )
            
            # Configure with Best Offer manager
            await self.best_offer_manager.configure_user_settings(request.user_id, settings)
            
            return settings
            
        except Exception as e:
            logger.error(f"Error configuring Best Offer: {e}")
            return create_balanced_settings()
    
    async def _compile_final_result(self, **kwargs) -> OptimizedListingResult:
        """Compile all workflow results into final optimized listing."""
        
        optimized_content = kwargs.get("optimized_content", {})
        category_optimization = kwargs.get("category_optimization", {})
        pricing_strategy = kwargs.get("pricing_strategy", {})
        research_result = kwargs.get("research_result")
        
        # Extract optimization improvements
        improvements = []
        if optimized_content.get("cassini_optimization"):
            improvements.extend(optimized_content["cassini_optimization"].get("improvements", []))
        
        if research_result and research_result.research_confidence > 0.7:
            improvements.append("Enhanced with comprehensive product research")
        
        if category_optimization.get("confidence", 0) > 0.8:
            improvements.append("Optimized category selection")
        
        return OptimizedListingResult(
            title=optimized_content.get("title", "Unknown Product"),
            description=optimized_content.get("description", "High-quality product"),
            category_id=category_optimization.get("primary_category", {}).get("id", "99"),
            item_specifics=optimized_content.get("item_specifics", {}),
            suggested_price=pricing_strategy.get("suggested_price", 50.0),
            best_offer_settings=kwargs.get("best_offer_settings"),
            cassini_score=kwargs.get("cassini_score", 0),
            research_confidence=research_result.research_confidence if research_result else 0.3,
            optimization_improvements=improvements,
            workflow_id=kwargs.get("workflow_id", "unknown"),
            processing_time=kwargs.get("processing_time", 0.0),
            total_cost=kwargs.get("total_cost", 0.0),
            sources_used=kwargs.get("sources_used", []),
            created_at=datetime.now(timezone.utc)
        )
