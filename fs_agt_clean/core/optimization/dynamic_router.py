#!/usr/bin/env python3
"""
Dynamic Routing System for FlipSync Phase 4 Advanced Optimization
=================================================================

This module provides context-aware model selection and intelligent routing
to achieve optimal performance and cost efficiency through dynamic
routing decisions based on request complexity and requirements.

Features:
- Context-aware model selection based on request complexity
- Performance-based routing decisions with real-time optimization
- Intelligent routing strategies for different operation types
- Integration with existing model router and optimization systems
- Real-time performance monitoring and route optimization
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """Dynamic routing strategies."""
    PERFORMANCE_BASED = "performance_based"
    COST_OPTIMIZED = "cost_optimized"
    QUALITY_FOCUSED = "quality_focused"
    BALANCED = "balanced"
    ADAPTIVE = "adaptive"


class ComplexityLevel(Enum):
    """Request complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"


class ModelTier(Enum):
    """Model performance tiers."""
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    EXPERT = "expert"


@dataclass
class RoutingDecision:
    """Dynamic routing decision result."""
    selected_model: str
    model_tier: ModelTier
    routing_strategy: RoutingStrategy
    complexity_assessment: ComplexityLevel
    confidence_score: float
    estimated_cost: float
    estimated_quality: float
    estimated_response_time: float
    routing_reason: str


@dataclass
class RoutePerformanceMetrics:
    """Performance metrics for routing decisions."""
    route_id: str
    model_used: str
    actual_cost: float
    actual_quality: float
    actual_response_time: float
    success: bool
    timestamp: datetime


@dataclass
class DynamicRoutingMetrics:
    """Overall dynamic routing performance metrics."""
    total_routes: int
    successful_routes: int
    average_cost_reduction: float
    average_quality_score: float
    average_response_time: float
    routing_accuracy: float
    cost_savings_achieved: float


class DynamicRoutingSystem:
    """
    Dynamic routing system for FlipSync advanced optimization.
    
    Provides context-aware model selection and intelligent routing
    to optimize performance, cost, and quality based on request
    characteristics and real-time performance data.
    """

    def __init__(self):
        """Initialize dynamic routing system."""
        
        # Model configurations
        self.model_configs = self._initialize_model_configs()
        
        # Routing performance tracking
        self.route_history: List[RoutePerformanceMetrics] = []
        self.performance_cache: Dict[str, List[RoutePerformanceMetrics]] = {}
        
        # Routing metrics
        self.metrics = DynamicRoutingMetrics(
            total_routes=0,
            successful_routes=0,
            average_cost_reduction=0.0,
            average_quality_score=0.0,
            average_response_time=0.0,
            routing_accuracy=0.0,
            cost_savings_achieved=0.0
        )
        
        # Configuration
        self.baseline_cost = 0.0012  # Phase 3 baseline
        self.quality_threshold = 0.8
        self.performance_window = 3600  # 1 hour performance window
        
        logger.info("DynamicRoutingSystem initialized with context-aware model selection")

    async def route_request(
        self,
        operation_type: str,
        content: str,
        context: Dict[str, Any],
        quality_requirement: float = 0.8,
        strategy: RoutingStrategy = RoutingStrategy.BALANCED
    ) -> RoutingDecision:
        """
        Route request to optimal model based on context and strategy.
        
        Returns:
            RoutingDecision with selected model and routing details
        """
        
        start_time = time.time()
        
        # Assess request complexity
        complexity = await self._assess_request_complexity(operation_type, content, context)
        
        # Select optimal model based on strategy and complexity
        model_selection = await self._select_optimal_model(
            operation_type, complexity, quality_requirement, strategy, context
        )
        
        # Create routing decision
        decision = RoutingDecision(
            selected_model=model_selection["model"],
            model_tier=model_selection["tier"],
            routing_strategy=strategy,
            complexity_assessment=complexity,
            confidence_score=model_selection["confidence"],
            estimated_cost=model_selection["estimated_cost"],
            estimated_quality=model_selection["estimated_quality"],
            estimated_response_time=model_selection["estimated_response_time"],
            routing_reason=model_selection["reason"]
        )
        
        # Track routing decision
        self.metrics.total_routes += 1
        
        processing_time = time.time() - start_time
        logger.debug(f"Dynamic routing completed: {decision.selected_model} for {operation_type} in {processing_time:.3f}s")
        
        return decision

    async def track_route_performance(
        self,
        route_id: str,
        routing_decision: RoutingDecision,
        actual_cost: float,
        actual_quality: float,
        actual_response_time: float,
        success: bool
    ):
        """Track actual performance of routing decision."""
        
        # Create performance record
        performance = RoutePerformanceMetrics(
            route_id=route_id,
            model_used=routing_decision.selected_model,
            actual_cost=actual_cost,
            actual_quality=actual_quality,
            actual_response_time=actual_response_time,
            success=success,
            timestamp=datetime.now()
        )
        
        # Store performance data
        self.route_history.append(performance)
        
        model_key = routing_decision.selected_model
        if model_key not in self.performance_cache:
            self.performance_cache[model_key] = []
        self.performance_cache[model_key].append(performance)
        
        # Update metrics
        if success:
            self.metrics.successful_routes += 1
            
            # Calculate cost savings
            cost_savings = self.baseline_cost - actual_cost
            self.metrics.cost_savings_achieved += cost_savings
        
        # Update running averages
        self._update_routing_metrics()
        
        # Assess routing accuracy
        cost_accuracy = 1 - abs(routing_decision.estimated_cost - actual_cost) / routing_decision.estimated_cost
        quality_accuracy = 1 - abs(routing_decision.estimated_quality - actual_quality) / routing_decision.estimated_quality
        
        routing_accuracy = (cost_accuracy + quality_accuracy) / 2
        self.metrics.routing_accuracy = (
            (self.metrics.routing_accuracy * (self.metrics.total_routes - 1) + routing_accuracy) / 
            self.metrics.total_routes
        )

    async def optimize_routing_strategy(
        self,
        operation_type: str,
        performance_target: str = "balanced"
    ) -> Dict[str, Any]:
        """
        Optimize routing strategy based on historical performance.
        
        Returns:
            Optimized routing recommendations and performance analysis
        """
        
        # Analyze historical performance by model
        model_performance = await self._analyze_model_performance()
        
        # Identify optimal routing patterns
        optimal_patterns = await self._identify_optimal_patterns(operation_type)
        
        # Generate routing recommendations
        recommendations = await self._generate_routing_recommendations(
            model_performance, optimal_patterns, performance_target
        )
        
        return {
            "model_performance": model_performance,
            "optimal_patterns": optimal_patterns,
            "recommendations": recommendations,
            "optimization_timestamp": datetime.now().isoformat()
        }

    async def get_metrics(self) -> DynamicRoutingMetrics:
        """Get dynamic routing performance metrics."""
        return self.metrics

    def _initialize_model_configs(self) -> Dict[str, Dict[str, Any]]:
        """Initialize model configurations for dynamic routing."""
        
        return {
            "gpt-4o-mini-basic": {
                "tier": ModelTier.BASIC,
                "base_cost": 0.0008,
                "quality_score": 0.82,
                "response_time": 0.8,
                "complexity_suitability": [ComplexityLevel.SIMPLE],
                "optimization_focus": "cost"
            },
            
            "gpt-4o-mini-standard": {
                "tier": ModelTier.STANDARD,
                "base_cost": 0.0012,
                "quality_score": 0.88,
                "response_time": 1.0,
                "complexity_suitability": [ComplexityLevel.SIMPLE, ComplexityLevel.MODERATE],
                "optimization_focus": "balanced"
            },
            
            "gpt-4o-mini-premium": {
                "tier": ModelTier.PREMIUM,
                "base_cost": 0.0016,
                "quality_score": 0.94,
                "response_time": 1.2,
                "complexity_suitability": [ComplexityLevel.MODERATE, ComplexityLevel.COMPLEX],
                "optimization_focus": "quality"
            },
            
            "gpt-4o-mini-expert": {
                "tier": ModelTier.EXPERT,
                "base_cost": 0.0020,
                "quality_score": 0.98,
                "response_time": 1.5,
                "complexity_suitability": [ComplexityLevel.COMPLEX, ComplexityLevel.EXPERT],
                "optimization_focus": "quality"
            }
        }

    async def _assess_request_complexity(
        self,
        operation_type: str,
        content: str,
        context: Dict[str, Any]
    ) -> ComplexityLevel:
        """Assess request complexity for routing decisions."""
        
        complexity_score = 0
        
        # Content length factor
        content_length = len(content)
        if content_length > 500:
            complexity_score += 2
        elif content_length > 200:
            complexity_score += 1
        
        # Operation type factor
        complex_operations = ["market_research", "price_optimization", "seo_optimization"]
        moderate_operations = ["listing_generation", "content_creation"]
        
        if operation_type in complex_operations:
            complexity_score += 2
        elif operation_type in moderate_operations:
            complexity_score += 1
        
        # Context complexity factor
        context_complexity = len(context.keys())
        if context_complexity > 5:
            complexity_score += 1
        
        # Quality requirement factor
        quality_req = context.get("quality_requirement", 0.8)
        if quality_req > 0.9:
            complexity_score += 2
        elif quality_req > 0.85:
            complexity_score += 1
        
        # Map score to complexity level
        if complexity_score >= 6:
            return ComplexityLevel.EXPERT
        elif complexity_score >= 4:
            return ComplexityLevel.COMPLEX
        elif complexity_score >= 2:
            return ComplexityLevel.MODERATE
        else:
            return ComplexityLevel.SIMPLE

    async def _select_optimal_model(
        self,
        operation_type: str,
        complexity: ComplexityLevel,
        quality_requirement: float,
        strategy: RoutingStrategy,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Select optimal model based on routing criteria."""
        
        # Filter models by complexity suitability
        suitable_models = {
            name: config for name, config in self.model_configs.items()
            if complexity in config["complexity_suitability"]
        }
        
        if not suitable_models:
            # Fallback to standard model
            suitable_models = {"gpt-4o-mini-standard": self.model_configs["gpt-4o-mini-standard"]}
        
        # Apply routing strategy
        if strategy == RoutingStrategy.COST_OPTIMIZED:
            selected = min(suitable_models.items(), key=lambda x: x[1]["base_cost"])
        elif strategy == RoutingStrategy.QUALITY_FOCUSED:
            selected = max(suitable_models.items(), key=lambda x: x[1]["quality_score"])
        elif strategy == RoutingStrategy.PERFORMANCE_BASED:
            selected = min(suitable_models.items(), key=lambda x: x[1]["response_time"])
        elif strategy == RoutingStrategy.ADAPTIVE:
            selected = await self._adaptive_model_selection(suitable_models, operation_type)
        else:  # BALANCED
            selected = await self._balanced_model_selection(suitable_models, quality_requirement)
        
        model_name, model_config = selected
        
        # Calculate estimates
        estimated_cost = model_config["base_cost"] * self._get_cost_multiplier(operation_type, context)
        estimated_quality = model_config["quality_score"]
        estimated_response_time = model_config["response_time"]
        
        # Calculate confidence based on historical performance
        confidence = await self._calculate_routing_confidence(model_name, operation_type)
        
        return {
            "model": model_name,
            "tier": model_config["tier"],
            "confidence": confidence,
            "estimated_cost": estimated_cost,
            "estimated_quality": estimated_quality,
            "estimated_response_time": estimated_response_time,
            "reason": f"{strategy.value}_selection_for_{complexity.value}_complexity"
        }

    async def _adaptive_model_selection(
        self,
        suitable_models: Dict[str, Dict[str, Any]],
        operation_type: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Adaptive model selection based on historical performance."""
        
        best_model = None
        best_score = 0
        
        for model_name, config in suitable_models.items():
            # Get historical performance for this model and operation type
            performance_score = await self._get_model_performance_score(model_name, operation_type)
            
            if performance_score > best_score:
                best_score = performance_score
                best_model = (model_name, config)
        
        return best_model or list(suitable_models.items())[0]

    async def _balanced_model_selection(
        self,
        suitable_models: Dict[str, Dict[str, Any]],
        quality_requirement: float
    ) -> Tuple[str, Dict[str, Any]]:
        """Balanced model selection considering cost, quality, and performance."""
        
        best_model = None
        best_score = 0
        
        for model_name, config in suitable_models.items():
            # Calculate balanced score
            cost_score = 1 - (config["base_cost"] / 0.002)  # Normalize to 0-1
            quality_score = config["quality_score"]
            performance_score = 1 - (config["response_time"] / 2.0)  # Normalize to 0-1
            
            # Weight based on quality requirement
            if quality_requirement > 0.9:
                balanced_score = quality_score * 0.5 + cost_score * 0.3 + performance_score * 0.2
            else:
                balanced_score = cost_score * 0.4 + quality_score * 0.4 + performance_score * 0.2
            
            if balanced_score > best_score:
                best_score = balanced_score
                best_model = (model_name, config)
        
        return best_model or list(suitable_models.items())[0]

    def _get_cost_multiplier(self, operation_type: str, context: Dict[str, Any]) -> float:
        """Get cost multiplier based on operation type and context."""
        
        # Base multiplier
        multiplier = 1.0
        
        # Operation type adjustments
        operation_multipliers = {
            "vision_analysis": 1.2,
            "market_research": 1.3,
            "price_optimization": 1.1,
            "listing_generation": 1.0,
            "content_creation": 0.9
        }
        
        multiplier *= operation_multipliers.get(operation_type, 1.0)
        
        # Context adjustments
        if context.get("marketplace") == "amazon":
            multiplier *= 1.1  # Amazon operations slightly more expensive
        
        if context.get("priority", 1) > 1:
            multiplier *= 1.05  # Higher priority costs more
        
        return multiplier

    async def _calculate_routing_confidence(self, model_name: str, operation_type: str) -> float:
        """Calculate confidence in routing decision based on historical data."""
        
        if model_name not in self.performance_cache:
            return 0.7  # Default confidence for new models
        
        # Get recent performance data
        recent_performance = [
            p for p in self.performance_cache[model_name]
            if (datetime.now() - p.timestamp).total_seconds() < self.performance_window
        ]
        
        if not recent_performance:
            return 0.7
        
        # Calculate confidence based on success rate and consistency
        success_rate = sum(1 for p in recent_performance if p.success) / len(recent_performance)
        
        # Calculate consistency (lower variance = higher confidence)
        if len(recent_performance) > 1:
            quality_scores = [p.actual_quality for p in recent_performance]
            quality_variance = statistics.variance(quality_scores)
            consistency_score = max(0, 1 - quality_variance)
        else:
            consistency_score = 0.5
        
        confidence = (success_rate * 0.7 + consistency_score * 0.3)
        return min(0.95, max(0.3, confidence))

    async def _get_model_performance_score(self, model_name: str, operation_type: str) -> float:
        """Get performance score for model and operation type combination."""
        
        if model_name not in self.performance_cache:
            return 0.5  # Default score
        
        # Filter performance data for this operation type
        relevant_performance = [
            p for p in self.performance_cache[model_name]
            if (datetime.now() - p.timestamp).total_seconds() < self.performance_window
        ]
        
        if not relevant_performance:
            return 0.5
        
        # Calculate composite performance score
        avg_quality = statistics.mean([p.actual_quality for p in relevant_performance])
        avg_cost_efficiency = statistics.mean([
            1 - (p.actual_cost / self.baseline_cost) for p in relevant_performance
        ])
        success_rate = sum(1 for p in relevant_performance if p.success) / len(relevant_performance)
        
        performance_score = (avg_quality * 0.4 + avg_cost_efficiency * 0.4 + success_rate * 0.2)
        return min(1.0, max(0.0, performance_score))

    async def _analyze_model_performance(self) -> Dict[str, Any]:
        """Analyze performance of all models."""
        
        analysis = {}
        
        for model_name in self.model_configs.keys():
            if model_name in self.performance_cache:
                recent_data = [
                    p for p in self.performance_cache[model_name]
                    if (datetime.now() - p.timestamp).total_seconds() < self.performance_window
                ]
                
                if recent_data:
                    analysis[model_name] = {
                        "total_requests": len(recent_data),
                        "success_rate": sum(1 for p in recent_data if p.success) / len(recent_data),
                        "average_cost": statistics.mean([p.actual_cost for p in recent_data]),
                        "average_quality": statistics.mean([p.actual_quality for p in recent_data]),
                        "average_response_time": statistics.mean([p.actual_response_time for p in recent_data])
                    }
        
        return analysis

    async def _identify_optimal_patterns(self, operation_type: str) -> Dict[str, Any]:
        """Identify optimal routing patterns for operation type."""
        
        patterns = {}
        
        # Analyze routing patterns by complexity
        for complexity in ComplexityLevel:
            best_model = None
            best_score = 0
            
            for model_name in self.model_configs.keys():
                score = await self._get_model_performance_score(model_name, operation_type)
                if score > best_score:
                    best_score = score
                    best_model = model_name
            
            if best_model:
                patterns[complexity.value] = {
                    "recommended_model": best_model,
                    "performance_score": best_score
                }
        
        return patterns

    async def _generate_routing_recommendations(
        self,
        model_performance: Dict[str, Any],
        optimal_patterns: Dict[str, Any],
        performance_target: str
    ) -> Dict[str, Any]:
        """Generate routing optimization recommendations."""
        
        recommendations = {
            "performance_target": performance_target,
            "model_recommendations": {},
            "strategy_recommendations": {},
            "optimization_opportunities": []
        }
        
        # Model-specific recommendations
        for model_name, performance in model_performance.items():
            if performance["success_rate"] < 0.8:
                recommendations["optimization_opportunities"].append(
                    f"Model {model_name} has low success rate ({performance['success_rate']:.1%})"
                )
            
            if performance["average_cost"] > self.baseline_cost * 1.2:
                recommendations["optimization_opportunities"].append(
                    f"Model {model_name} costs above baseline ({performance['average_cost']:.4f})"
                )
        
        # Strategy recommendations based on performance target
        if performance_target == "cost":
            recommendations["strategy_recommendations"]["primary"] = RoutingStrategy.COST_OPTIMIZED
            recommendations["strategy_recommendations"]["fallback"] = RoutingStrategy.BALANCED
        elif performance_target == "quality":
            recommendations["strategy_recommendations"]["primary"] = RoutingStrategy.QUALITY_FOCUSED
            recommendations["strategy_recommendations"]["fallback"] = RoutingStrategy.BALANCED
        else:
            recommendations["strategy_recommendations"]["primary"] = RoutingStrategy.ADAPTIVE
            recommendations["strategy_recommendations"]["fallback"] = RoutingStrategy.BALANCED
        
        return recommendations

    def _update_routing_metrics(self):
        """Update routing performance metrics."""
        
        if self.metrics.total_routes > 0:
            # Calculate average cost reduction
            if self.route_history:
                recent_routes = self.route_history[-100:]  # Last 100 routes
                successful_routes = [r for r in recent_routes if r.success]
                
                if successful_routes:
                    avg_cost = statistics.mean([r.actual_cost for r in successful_routes])
                    cost_reduction = (self.baseline_cost - avg_cost) / self.baseline_cost
                    self.metrics.average_cost_reduction = cost_reduction
                    
                    self.metrics.average_quality_score = statistics.mean([r.actual_quality for r in successful_routes])
                    self.metrics.average_response_time = statistics.mean([r.actual_response_time for r in successful_routes])


# Global dynamic routing system instance
_dynamic_routing_instance = None


def get_dynamic_routing_system() -> DynamicRoutingSystem:
    """Get global dynamic routing system instance."""
    global _dynamic_routing_instance
    if _dynamic_routing_instance is None:
        _dynamic_routing_instance = DynamicRoutingSystem()
    return _dynamic_routing_instance
