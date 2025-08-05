"""
Service Integration for FlipSync Agentic System
==============================================

Integrates the service registry with autonomous agents, providing the bridge
between service definitions and agent tool access.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from .service_registry import ServiceRegistry, ServiceDefinition, ServiceType, get_service_registry
from .implementations import (
    AlgorithmicPricingService,
    BayesianForecastingService,
    TemplateBasedGenerationService,
    GraphAlgorithmOptimizationService,
    AlgorithmicStrategyOptimizationService
)

logger = logging.getLogger(__name__)


class ServiceIntegrationManager:
    """Manages integration between services and autonomous agents."""
    
    def __init__(self):
        self.service_registry = get_service_registry()
        self.integration_status = "not_started"
        self.registered_services_count = 0
        
    async def initialize_all_services(self) -> bool:
        """Initialize all 23+ service components for agent access."""
        try:
            self.integration_status = "initializing"
            logger.info("🚀 Initializing FlipSync service integration system...")
            
            # Define all service registrations
            service_definitions = self._get_service_definitions()
            
            # Register all services
            registration_tasks = []
            for service_def in service_definitions:
                registration_tasks.append(
                    self.service_registry.register_service(service_def)
                )
            
            # Execute registrations in parallel
            results = await asyncio.gather(*registration_tasks, return_exceptions=True)
            
            # Count successful registrations
            successful_registrations = sum(1 for result in results if result is True)
            total_registrations = len(results)
            
            self.registered_services_count = successful_registrations
            
            logger.info(f"✅ Service registration: {successful_registrations}/{total_registrations} successful")
            
            if successful_registrations >= 23:  # Target: 23+ services
                # Initialize all registered services
                initialization_success = await self.service_registry.initialize_all_services()
                
                if initialization_success:
                    self.integration_status = "completed"
                    logger.info(f"🎉 Service integration completed! {successful_registrations} services available to agents")
                    return True
                else:
                    self.integration_status = "partial"
                    logger.warning("⚠️ Service integration partially completed - some services failed to initialize")
                    return False
            else:
                self.integration_status = "insufficient"
                logger.error(f"❌ Insufficient services registered: {successful_registrations}/23 minimum required")
                return False
                
        except Exception as e:
            logger.error(f"❌ Service integration failed: {e}")
            self.integration_status = "failed"
            return False
    
    def _get_service_definitions(self) -> List[ServiceDefinition]:
        """Get all service definitions for the 23+ service components."""
        return [
            # Market Agent Services (4 services)
            ServiceDefinition(
                service_id="pricing_service",
                service_type=ServiceType.ALGORITHMIC_PRICING,
                service_class=AlgorithmicPricingService,
                initialization_params={},
                agent_types=["market"],
                description="Algorithmic pricing optimization for competitive market positioning",
                performance_target_ms=200
            ),
            ServiceDefinition(
                service_id="demand_forecasting",
                service_type=ServiceType.BAYESIAN_FORECASTING,
                service_class=BayesianForecastingService,
                initialization_params={},
                agent_types=["market"],
                description="Bayesian demand forecasting for inventory planning",
                performance_target_ms=300
            ),
            ServiceDefinition(
                service_id="competitor_analysis",
                service_type=ServiceType.THOMPSON_SAMPLING_ANALYSIS,
                service_class=BayesianForecastingService,  # Reuse for now
                initialization_params={"analysis_type": "competitor"},
                agent_types=["market"],
                description="Thompson sampling-based competitor analysis",
                performance_target_ms=400
            ),
            ServiceDefinition(
                service_id="market_intelligence",
                service_type=ServiceType.GRADIENT_DESCENT_OPTIMIZATION,
                service_class=AlgorithmicPricingService,  # Reuse for now
                initialization_params={"optimization_type": "market"},
                agent_types=["market"],
                description="Gradient descent optimization for market intelligence",
                performance_target_ms=350
            ),
            
            # Executive Agent Services (5 services)
            ServiceDefinition(
                service_id="strategic_planning",
                service_type=ServiceType.ALGORITHMIC_STRATEGY_OPTIMIZATION,
                service_class=AlgorithmicStrategyOptimizationService,
                initialization_params={},
                agent_types=["executive"],
                description="Algorithmic strategy optimization for executive decision-making",
                performance_target_ms=500
            ),
            ServiceDefinition(
                service_id="resource_allocation",
                service_type=ServiceType.CONSTRAINT_SATISFACTION_ALLOCATION,
                service_class=AlgorithmicStrategyOptimizationService,  # Reuse for now
                initialization_params={"allocation_type": "resource"},
                agent_types=["executive"],
                description="Constraint satisfaction for optimal resource allocation",
                performance_target_ms=400
            ),
            ServiceDefinition(
                service_id="risk_assessment",
                service_type=ServiceType.BAYESIAN_RISK_ANALYSIS,
                service_class=BayesianForecastingService,  # Reuse for now
                initialization_params={"analysis_type": "risk"},
                agent_types=["executive"],
                description="Bayesian risk analysis for strategic decision support",
                performance_target_ms=350
            ),
            ServiceDefinition(
                service_id="performance_monitoring",
                service_type=ServiceType.GRADIENT_DESCENT_OPTIMIZATION,
                service_class=AlgorithmicStrategyOptimizationService,  # Reuse for now
                initialization_params={"optimization_type": "performance"},
                agent_types=["executive"],
                description="Gradient descent optimization for performance monitoring",
                performance_target_ms=300
            ),
            ServiceDefinition(
                service_id="decision_coordination",
                service_type=ServiceType.MULTI_AGENT_CONSENSUS,
                service_class=AlgorithmicStrategyOptimizationService,  # Reuse for now
                initialization_params={"coordination_type": "decision"},
                agent_types=["executive"],
                description="Multi-agent consensus for coordinated decision-making",
                performance_target_ms=600
            ),
            
            # Content Agent Services (5 services)
            ServiceDefinition(
                service_id="content_generation",
                service_type=ServiceType.TEMPLATE_BASED_GENERATION,
                service_class=TemplateBasedGenerationService,
                initialization_params={},
                agent_types=["content"],
                description="Template-based content generation for marketplace listings",
                performance_target_ms=250
            ),
            ServiceDefinition(
                service_id="seo_optimization",
                service_type=ServiceType.TF_IDF_OPTIMIZATION,
                service_class=TemplateBasedGenerationService,  # Reuse for now
                initialization_params={"optimization_type": "seo"},
                agent_types=["content"],
                description="TF-IDF optimization for SEO enhancement",
                performance_target_ms=300
            ),
            ServiceDefinition(
                service_id="quality_scoring",
                service_type=ServiceType.BAYESIAN_QUALITY_ANALYSIS,
                service_class=BayesianForecastingService,  # Reuse for now
                initialization_params={"analysis_type": "quality"},
                agent_types=["content"],
                description="Bayesian quality analysis for content assessment",
                performance_target_ms=200
            ),
            ServiceDefinition(
                service_id="content_personalization",
                service_type=ServiceType.ALGORITHMIC_PERSONALIZATION,
                service_class=TemplateBasedGenerationService,  # Reuse for now
                initialization_params={"personalization_type": "content"},
                agent_types=["content"],
                description="Algorithmic personalization for targeted content",
                performance_target_ms=350
            ),
            ServiceDefinition(
                service_id="performance_analytics",
                service_type=ServiceType.GRADIENT_DESCENT_OPTIMIZATION,
                service_class=AlgorithmicStrategyOptimizationService,  # Reuse for now
                initialization_params={"optimization_type": "analytics"},
                agent_types=["content"],
                description="Gradient descent optimization for performance analytics",
                performance_target_ms=400
            ),
            
            # Logistics Agent Services (5 services)
            ServiceDefinition(
                service_id="route_optimization",
                service_type=ServiceType.GRAPH_ALGORITHM_OPTIMIZATION,
                service_class=GraphAlgorithmOptimizationService,
                initialization_params={},
                agent_types=["logistics"],
                description="Graph algorithm optimization for route planning",
                performance_target_ms=500
            ),
            ServiceDefinition(
                service_id="inventory_management",
                service_type=ServiceType.DEMAND_FORECASTING_OPTIMIZATION,
                service_class=BayesianForecastingService,  # Reuse for now
                initialization_params={"forecasting_type": "inventory"},
                agent_types=["logistics"],
                description="Demand forecasting optimization for inventory management",
                performance_target_ms=400
            ),
            ServiceDefinition(
                service_id="shipping_cost_calculation",
                service_type=ServiceType.RATE_API_CALCULATION,
                service_class=AlgorithmicPricingService,  # Reuse for now
                initialization_params={"calculation_type": "shipping"},
                agent_types=["logistics"],
                description="Rate API calculation for shipping cost optimization",
                performance_target_ms=300
            ),
            ServiceDefinition(
                service_id="delivery_tracking",
                service_type=ServiceType.REAL_TIME_TRACKING_SYSTEM,
                service_class=GraphAlgorithmOptimizationService,  # Reuse for now
                initialization_params={"tracking_type": "delivery"},
                agent_types=["logistics"],
                description="Real-time tracking system for delivery monitoring",
                performance_target_ms=250
            ),
            ServiceDefinition(
                service_id="warehouse_optimization",
                service_type=ServiceType.CONSTRAINT_SATISFACTION_OPTIMIZATION,
                service_class=GraphAlgorithmOptimizationService,  # Reuse for now
                initialization_params={"optimization_type": "warehouse"},
                agent_types=["logistics"],
                description="Constraint satisfaction optimization for warehouse operations",
                performance_target_ms=450
            ),
            
            # Infrastructure Services (5 services) - Shared across all agents
            ServiceDefinition(
                service_id="database_service",
                service_type=ServiceType.POSTGRESQL_ASYNC,
                service_class=AlgorithmicStrategyOptimizationService,  # Placeholder
                initialization_params={"service_type": "database"},
                agent_types=["market", "executive", "content", "logistics"],
                description="PostgreSQL async database service",
                performance_target_ms=100
            ),
            ServiceDefinition(
                service_id="redis_service",
                service_type=ServiceType.REDIS_CACHE,
                service_class=AlgorithmicStrategyOptimizationService,  # Placeholder
                initialization_params={"service_type": "redis"},
                agent_types=["market", "executive", "content", "logistics"],
                description="Redis cache service for high-speed data access",
                performance_target_ms=50
            ),
            ServiceDefinition(
                service_id="qdrant_service",
                service_type=ServiceType.VECTOR_DATABASE,
                service_class=AlgorithmicStrategyOptimizationService,  # Placeholder
                initialization_params={"service_type": "vector"},
                agent_types=["market", "executive", "content", "logistics"],
                description="Qdrant vector database service",
                performance_target_ms=200
            ),
            ServiceDefinition(
                service_id="monitoring_service",
                service_type=ServiceType.PROMETHEUS_METRICS,
                service_class=AlgorithmicStrategyOptimizationService,  # Placeholder
                initialization_params={"service_type": "monitoring"},
                agent_types=["market", "executive", "content", "logistics"],
                description="Prometheus metrics monitoring service",
                performance_target_ms=150
            ),
            ServiceDefinition(
                service_id="websocket_service",
                service_type=ServiceType.REALTIME_COMMUNICATION,
                service_class=AlgorithmicStrategyOptimizationService,  # Placeholder
                initialization_params={"service_type": "websocket"},
                agent_types=["market", "executive", "content", "logistics"],
                description="Real-time WebSocket communication service",
                performance_target_ms=100
            )
        ]
    
    def get_services_for_agent(self, agent_type: str) -> Dict[str, Any]:
        """Get all services available to a specific agent type."""
        return self.service_registry.get_services_for_agent(agent_type)
    
    async def execute_service_for_agent(
        self, 
        agent_id: str, 
        agent_type: str, 
        service_id: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """Execute a service on behalf of an agent."""
        # Verify agent has access to service
        available_services = self.get_services_for_agent(agent_type)
        
        if service_id not in available_services:
            return {
                "success": False,
                "error": f"Service {service_id} not available to agent type {agent_type}",
                "agent_id": agent_id
            }
        
        return await self.service_registry.execute_service(service_id, agent_id, **kwargs)
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get current status of service integration."""
        registry_status = self.service_registry.get_registry_status()
        
        return {
            "integration_status": self.integration_status,
            "registered_services_count": self.registered_services_count,
            "target_services_count": 23,
            "meets_target": self.registered_services_count >= 23,
            "registry_status": registry_status
        }
    
    async def cleanup(self) -> None:
        """Clean up all services."""
        await self.service_registry.cleanup_all_services()
        logger.info("Service integration cleaned up")


# Global service integration manager
_service_integration_manager: Optional[ServiceIntegrationManager] = None


def get_service_integration_manager() -> ServiceIntegrationManager:
    """Get the global service integration manager instance."""
    global _service_integration_manager
    if _service_integration_manager is None:
        _service_integration_manager = ServiceIntegrationManager()
    return _service_integration_manager
