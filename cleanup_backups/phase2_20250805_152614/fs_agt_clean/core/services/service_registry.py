"""
Service Registry for FlipSync Agentic System
==========================================

Central registry that connects the 23+ service components to autonomous agents
as callable tools, bridging the gap between service definitions and agent access.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Type
from enum import Enum

logger = logging.getLogger(__name__)


class ServiceType(str, Enum):
    """Types of services available in the registry."""
    
    # Market Agent Services
    ALGORITHMIC_PRICING = "algorithmic_pricing"
    BAYESIAN_FORECASTING = "bayesian_forecasting"
    THOMPSON_SAMPLING_ANALYSIS = "thompson_sampling_analysis"
    GRADIENT_DESCENT_OPTIMIZATION = "gradient_descent_optimization"
    
    # Executive Agent Services
    ALGORITHMIC_STRATEGY_OPTIMIZATION = "algorithmic_strategy_optimization"
    CONSTRAINT_SATISFACTION_ALLOCATION = "constraint_satisfaction_allocation"
    BAYESIAN_RISK_ANALYSIS = "bayesian_risk_analysis"
    MULTI_AGENT_CONSENSUS = "multi_agent_consensus"
    
    # Content Agent Services
    TEMPLATE_BASED_GENERATION = "template_based_generation"
    TF_IDF_OPTIMIZATION = "tf_idf_optimization"
    BAYESIAN_QUALITY_ANALYSIS = "bayesian_quality_analysis"
    ALGORITHMIC_PERSONALIZATION = "algorithmic_personalization"
    
    # Logistics Agent Services
    GRAPH_ALGORITHM_OPTIMIZATION = "graph_algorithm_optimization"
    DEMAND_FORECASTING_OPTIMIZATION = "demand_forecasting_optimization"
    RATE_API_CALCULATION = "rate_api_calculation"
    REAL_TIME_TRACKING_SYSTEM = "real_time_tracking_system"
    CONSTRAINT_SATISFACTION_OPTIMIZATION = "constraint_satisfaction_optimization"
    
    # Infrastructure Services
    POSTGRESQL_ASYNC = "postgresql_async"
    REDIS_CACHE = "redis_cache"
    VECTOR_DATABASE = "vector_database"
    PROMETHEUS_METRICS = "prometheus_metrics"
    REALTIME_COMMUNICATION = "realtime_communication"


@dataclass
class ServiceDefinition:
    """Definition of a service that can be registered with agents."""
    
    service_id: str
    service_type: ServiceType
    service_class: Type
    initialization_params: Dict[str, Any]
    agent_types: List[str]  # Which agents can use this service
    description: str
    performance_target_ms: Optional[int] = None
    dependencies: List[str] = None


class BaseService(ABC):
    """Base class for all services that can be registered with agents."""
    
    def __init__(self, service_id: str, **kwargs):
        self.service_id = service_id
        self.is_initialized = False
        self.performance_metrics = {}
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the service."""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the service with given parameters."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up service resources."""
        pass


class ServiceRegistry:
    """Central registry for all services available to autonomous agents."""
    
    def __init__(self):
        self.services: Dict[str, BaseService] = {}
        self.service_definitions: Dict[str, ServiceDefinition] = {}
        self.agent_service_mappings: Dict[str, List[str]] = {}
        self.initialization_status = "not_started"
        
        logger.info("Service Registry initialized")
    
    async def register_service(
        self, 
        service_definition: ServiceDefinition,
        service_instance: Optional[BaseService] = None
    ) -> bool:
        """Register a service with the registry."""
        try:
            service_id = service_definition.service_id
            
            # Store service definition
            self.service_definitions[service_id] = service_definition
            
            # Create or use provided service instance
            if service_instance:
                service = service_instance
            else:
                service = service_definition.service_class(
                    service_id=service_id,
                    **service_definition.initialization_params
                )
            
            # Initialize service
            if await service.initialize():
                self.services[service_id] = service
                
                # Update agent mappings
                for agent_type in service_definition.agent_types:
                    if agent_type not in self.agent_service_mappings:
                        self.agent_service_mappings[agent_type] = []
                    self.agent_service_mappings[agent_type].append(service_id)
                
                logger.info(f"✅ Registered service: {service_id} for agents: {service_definition.agent_types}")
                return True
            else:
                logger.error(f"❌ Failed to initialize service: {service_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error registering service {service_definition.service_id}: {e}")
            return False
    
    def get_services_for_agent(self, agent_type: str) -> Dict[str, BaseService]:
        """Get all services available to a specific agent type."""
        agent_services = {}
        service_ids = self.agent_service_mappings.get(agent_type, [])
        
        for service_id in service_ids:
            if service_id in self.services:
                agent_services[service_id] = self.services[service_id]
        
        return agent_services
    
    async def execute_service(
        self, 
        service_id: str, 
        agent_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute a service on behalf of an agent."""
        if service_id not in self.services:
            return {
                "success": False,
                "error": f"Service {service_id} not found",
                "agent_id": agent_id
            }
        
        try:
            service = self.services[service_id]
            result = await service.execute(**kwargs)
            
            return {
                "success": True,
                "result": result,
                "service_id": service_id,
                "agent_id": agent_id
            }
            
        except Exception as e:
            logger.error(f"❌ Service execution failed: {service_id} for agent {agent_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "service_id": service_id,
                "agent_id": agent_id
            }
    
    async def initialize_all_services(self) -> bool:
        """Initialize all registered services."""
        self.initialization_status = "initializing"
        
        try:
            initialization_tasks = []
            for service_id, service in self.services.items():
                if not service.is_initialized:
                    initialization_tasks.append(service.initialize())
            
            if initialization_tasks:
                results = await asyncio.gather(*initialization_tasks, return_exceptions=True)
                
                success_count = sum(1 for result in results if result is True)
                total_count = len(results)
                
                logger.info(f"Service initialization: {success_count}/{total_count} successful")
                
                if success_count == total_count:
                    self.initialization_status = "completed"
                    return True
                else:
                    self.initialization_status = "partial"
                    return False
            else:
                self.initialization_status = "completed"
                return True
                
        except Exception as e:
            logger.error(f"❌ Service registry initialization failed: {e}")
            self.initialization_status = "failed"
            return False
    
    async def cleanup_all_services(self) -> None:
        """Clean up all registered services."""
        cleanup_tasks = []
        for service in self.services.values():
            cleanup_tasks.append(service.cleanup())
        
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        logger.info("All services cleaned up")
    
    def get_registry_status(self) -> Dict[str, Any]:
        """Get current status of the service registry."""
        return {
            "total_services": len(self.services),
            "services_by_type": {
                agent_type: len(services) 
                for agent_type, services in self.agent_service_mappings.items()
            },
            "initialization_status": self.initialization_status,
            "service_list": list(self.services.keys())
        }


# Global service registry instance
_service_registry: Optional[ServiceRegistry] = None


def get_service_registry() -> ServiceRegistry:
    """Get the global service registry instance."""
    global _service_registry
    if _service_registry is None:
        _service_registry = ServiceRegistry()
    return _service_registry
