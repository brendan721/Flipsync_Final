"""
Agent Resilience Service for 4+1 Architecture
=============================================

Provides comprehensive resilience patterns for autonomous agents:
- Circuit breakers for agent decision pipelines
- Failover mechanisms between agents
- Graceful degradation strategies
- Health monitoring and recovery
- Cross-agent backup capabilities
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class AgentHealthStatus(Enum):
    """Agent health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    OFFLINE = "offline"


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class AgentHealth:
    """Agent health information."""
    agent_id: str
    agent_type: str
    status: AgentHealthStatus
    last_success: Optional[datetime]
    last_failure: Optional[datetime]
    failure_count: int
    success_count: int
    average_response_time: float
    confidence_score: float


class AgentCircuitBreaker:
    """Circuit breaker specifically for autonomous agents."""
    
    def __init__(
        self,
        agent_id: str,
        failure_threshold: int = 3,
        recovery_timeout: int = 30,
        success_threshold: int = 2
    ):
        self.agent_id = agent_id
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_state_change = datetime.now(timezone.utc)
        
        logger.info(f"🔧 Circuit breaker initialized for agent {agent_id}")
    
    def can_execute(self) -> bool:
        """Check if agent can execute operations."""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time and (time.time() - self.last_failure_time) > self.recovery_timeout:
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                logger.info(f"🔧 Circuit breaker for {self.agent_id} moved to HALF_OPEN")
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self):
        """Record successful operation."""
        self.failure_count = 0
        self.success_count += 1
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            if self.success_count >= self.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                logger.info(f"🔧 Circuit breaker for {self.agent_id} CLOSED after recovery")
    
    def record_failure(self):
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitBreakerState.CLOSED and self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            self.last_state_change = datetime.now(timezone.utc)
            logger.warning(f"🚨 Circuit breaker for {self.agent_id} OPENED after {self.failure_count} failures")
        elif self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"🚨 Circuit breaker for {self.agent_id} returned to OPEN from HALF_OPEN")


class AgentResilienceService:
    """Service providing resilience patterns for autonomous agents."""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, AgentCircuitBreaker] = {}
        self.agent_health: Dict[str, AgentHealth] = {}
        self.failover_chains: Dict[str, List[str]] = {}
        self.backup_strategies: Dict[str, Callable] = {}
        
        # Initialize failover chains for 4+1 architecture
        self._initialize_failover_chains()
        
        logger.info("🛡️ Agent Resilience Service initialized")
    
    def _initialize_failover_chains(self):
        """Initialize failover chains between agents."""
        # Content Agent can failover to Executive for strategic content decisions
        self.failover_chains["content_autonomous_agent"] = ["executive_autonomous_agent"]
        
        # Executive Agent can failover to Market for pricing-related decisions
        self.failover_chains["executive_autonomous_agent"] = ["market_autonomous_agent"]
        
        # Logistics Agent can failover to Executive for strategic logistics decisions
        self.failover_chains["logistics_autonomous_agent"] = ["executive_autonomous_agent"]
        
        # Market Agent can failover to Executive for complex market analysis
        self.failover_chains["market_autonomous_agent"] = ["executive_autonomous_agent"]
        
        logger.info("🔄 Failover chains initialized for 4+1 architecture")
    
    def get_circuit_breaker(self, agent_id: str) -> AgentCircuitBreaker:
        """Get or create circuit breaker for agent."""
        if agent_id not in self.circuit_breakers:
            self.circuit_breakers[agent_id] = AgentCircuitBreaker(agent_id)
        return self.circuit_breakers[agent_id]
    
    async def execute_with_resilience(
        self,
        agent_id: str,
        operation: Callable,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute agent operation with full resilience patterns."""
        circuit_breaker = self.get_circuit_breaker(agent_id)
        
        # Check circuit breaker
        if not circuit_breaker.can_execute():
            logger.warning(f"🚨 Circuit breaker OPEN for {agent_id}, attempting failover")
            return await self._attempt_failover(agent_id, operation, *args, **kwargs)
        
        # Execute with monitoring
        start_time = time.perf_counter()
        try:
            result = await operation(*args, **kwargs)
            execution_time = (time.perf_counter() - start_time) * 1000
            
            # Record success
            circuit_breaker.record_success()
            await self._update_agent_health(agent_id, True, execution_time, result)
            
            return {
                "success": True,
                "result": result,
                "execution_time_ms": execution_time,
                "agent_id": agent_id,
                "failover_used": False
            }
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            
            # Record failure
            circuit_breaker.record_failure()
            await self._update_agent_health(agent_id, False, execution_time, None)
            
            logger.error(f"🚨 Agent {agent_id} operation failed: {e}")
            
            # Attempt failover
            return await self._attempt_failover(agent_id, operation, *args, **kwargs)
    
    async def _attempt_failover(
        self,
        failed_agent_id: str,
        operation: Callable,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """Attempt failover to backup agents."""
        failover_agents = self.failover_chains.get(failed_agent_id, [])
        
        for backup_agent_id in failover_agents:
            backup_circuit_breaker = self.get_circuit_breaker(backup_agent_id)
            
            if backup_circuit_breaker.can_execute():
                try:
                    logger.info(f"🔄 Attempting failover from {failed_agent_id} to {backup_agent_id}")
                    
                    # Adapt operation for backup agent
                    adapted_result = await self._adapt_operation_for_backup(
                        backup_agent_id, operation, *args, **kwargs
                    )
                    
                    backup_circuit_breaker.record_success()
                    
                    return {
                        "success": True,
                        "result": adapted_result,
                        "agent_id": backup_agent_id,
                        "failover_used": True,
                        "original_agent": failed_agent_id,
                        "failover_reason": "circuit_breaker_open"
                    }
                    
                except Exception as e:
                    backup_circuit_breaker.record_failure()
                    logger.error(f"🚨 Failover to {backup_agent_id} also failed: {e}")
                    continue
        
        # All failovers failed, return graceful degradation
        return await self._graceful_degradation(failed_agent_id, *args, **kwargs)
    
    async def _adapt_operation_for_backup(
        self,
        backup_agent_id: str,
        operation: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Adapt operation parameters for backup agent."""
        # This is a simplified adaptation - in production, you'd have more sophisticated mapping
        if "content" in backup_agent_id and "executive" in backup_agent_id:
            # Executive agent handling content tasks
            return await self._executive_handle_content_task(*args, **kwargs)
        elif "market" in backup_agent_id:
            # Market agent handling other tasks
            return await self._market_handle_generic_task(*args, **kwargs)
        else:
            # Generic backup handling
            return await operation(*args, **kwargs)
    
    async def _executive_handle_content_task(self, *args, **kwargs) -> Dict[str, Any]:
        """Executive agent handling content tasks as backup."""
        return {
            "action": "strategic_content_guidance",
            "data": {
                "message": "Strategic content recommendations provided by Executive Agent",
                "guidance": "Focus on high-value content that drives conversions",
                "backup_mode": True
            },
            "confidence": 0.7
        }
    
    async def _market_handle_generic_task(self, *args, **kwargs) -> Dict[str, Any]:
        """Market agent handling generic tasks as backup."""
        return {
            "action": "market_analysis_backup",
            "data": {
                "message": "Market-focused analysis provided as backup",
                "analysis": "Market conditions suggest conservative approach",
                "backup_mode": True
            },
            "confidence": 0.6
        }
    
    async def _graceful_degradation(
        self,
        failed_agent_id: str,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """Provide graceful degradation when all agents fail."""
        logger.warning(f"🚨 All agents failed, providing graceful degradation for {failed_agent_id}")
        
        degraded_responses = {
            "content_autonomous_agent": {
                "action": "degraded_content_response",
                "data": {
                    "message": "Content optimization temporarily unavailable",
                    "suggestion": "Please try again in a few minutes",
                    "degraded_mode": True
                }
            },
            "executive_autonomous_agent": {
                "action": "degraded_executive_response",
                "data": {
                    "message": "Strategic planning temporarily unavailable",
                    "suggestion": "Consider manual review of business decisions",
                    "degraded_mode": True
                }
            },
            "logistics_autonomous_agent": {
                "action": "degraded_logistics_response",
                "data": {
                    "message": "Logistics optimization temporarily unavailable",
                    "suggestion": "Use standard shipping options",
                    "degraded_mode": True
                }
            },
            "market_autonomous_agent": {
                "action": "degraded_market_response",
                "data": {
                    "message": "Market analysis temporarily unavailable",
                    "suggestion": "Use current pricing strategies",
                    "degraded_mode": True
                }
            }
        }
        
        return {
            "success": False,
            "result": degraded_responses.get(failed_agent_id, {
                "action": "degraded_generic_response",
                "data": {
                    "message": "Service temporarily unavailable",
                    "suggestion": "Please try again later",
                    "degraded_mode": True
                }
            }),
            "agent_id": failed_agent_id,
            "failover_used": False,
            "degraded_mode": True,
            "error": "all_agents_unavailable"
        }
    
    async def _update_agent_health(
        self,
        agent_id: str,
        success: bool,
        execution_time: float,
        result: Any
    ):
        """Update agent health metrics."""
        now = datetime.now(timezone.utc)
        
        if agent_id not in self.agent_health:
            self.agent_health[agent_id] = AgentHealth(
                agent_id=agent_id,
                agent_type=agent_id.split("_")[0],
                status=AgentHealthStatus.HEALTHY,
                last_success=None,
                last_failure=None,
                failure_count=0,
                success_count=0,
                average_response_time=0.0,
                confidence_score=0.0
            )
        
        health = self.agent_health[agent_id]
        
        if success:
            health.last_success = now
            health.success_count += 1
            health.failure_count = max(0, health.failure_count - 1)  # Gradual recovery
            
            # Extract confidence from result if available
            if isinstance(result, dict) and "confidence" in result:
                health.confidence_score = result["confidence"]
        else:
            health.last_failure = now
            health.failure_count += 1
        
        # Update average response time
        health.average_response_time = (health.average_response_time + execution_time) / 2
        
        # Update health status
        circuit_breaker = self.get_circuit_breaker(agent_id)
        if circuit_breaker.state == CircuitBreakerState.OPEN:
            health.status = AgentHealthStatus.CRITICAL
        elif health.failure_count > 2:
            health.status = AgentHealthStatus.DEGRADED
        elif execution_time > 1000:  # Over 1 second
            health.status = AgentHealthStatus.DEGRADED
        else:
            health.status = AgentHealthStatus.HEALTHY
    
    def get_agent_health_status(self, agent_id: str) -> Optional[AgentHealth]:
        """Get current health status for an agent."""
        return self.agent_health.get(agent_id)
    
    def get_all_agent_health(self) -> Dict[str, AgentHealth]:
        """Get health status for all monitored agents."""
        return self.agent_health.copy()
    
    def get_circuit_breaker_status(self, agent_id: str) -> Dict[str, Any]:
        """Get circuit breaker status for an agent."""
        circuit_breaker = self.get_circuit_breaker(agent_id)
        return {
            "agent_id": agent_id,
            "state": circuit_breaker.state.value,
            "failure_count": circuit_breaker.failure_count,
            "success_count": circuit_breaker.success_count,
            "can_execute": circuit_breaker.can_execute(),
            "last_state_change": circuit_breaker.last_state_change.isoformat()
        }


# Global resilience service instance
resilience_service = AgentResilienceService()
