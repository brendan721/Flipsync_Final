"""
Agent Orchestration API Routes for Phase 1
==========================================

Enhanced API endpoints that integrate with the service orchestration framework
to provide real-time agent coordination, workflow management, and performance monitoring.

Built for the confirmed 4+1 architecture with sub-1000ms Docker-aware performance targets.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field

from fs_agt_clean.core.coordination.enhanced_realtime_communication import (
    enhanced_agent_communication,
    AgentCommunicationType,
    AgentCommunicationPriority,
)
from fs_agt_clean.agents.market.market_agent import MarketAutonomousAgent
from fs_agt_clean.agents.executive.executive_agent import ExecutiveAutonomousAgent
from fs_agt_clean.agents.content.content_agent import ContentAutonomousAgent
from fs_agt_clean.agents.logistics.logistics_agent import LogisticsAutonomousAgent

logger = logging.getLogger(__name__)

# Create router for agent orchestration
router = APIRouter(prefix="/api/v1/orchestration", tags=["agent-orchestration"])


# Request/Response Models
class AgentCommunicationRequest(BaseModel):
    """Request model for agent-to-agent communication."""
    from_agent: str
    to_agent: str
    message_type: str = "coordination"
    priority: str = "normal"
    content: Dict[str, Any]
    requires_response: bool = False
    timeout: float = 5.0


class AgentCommunicationResponse(BaseModel):
    """Response model for agent communication."""
    success: bool
    message_id: Optional[str] = None
    latency_ms: Optional[float] = None
    response_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AgentDecisionRequest(BaseModel):
    """Request model for agent decision execution."""
    agent_type: str
    decision_type: str
    context: Dict[str, Any]
    priority: str = "normal"
    timeout: float = 10.0


class AgentDecisionResponse(BaseModel):
    """Response model for agent decision."""
    success: bool
    decision_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[float] = None
    confidence: Optional[float] = None
    error: Optional[str] = None


class WorkflowExecutionRequest(BaseModel):
    """Request model for multi-agent workflow execution."""
    workflow_type: str
    agents: List[str]
    context: Dict[str, Any]
    coordination_strategy: str = "sequential"
    timeout: float = 30.0


class WorkflowExecutionResponse(BaseModel):
    """Response model for workflow execution."""
    success: bool
    workflow_id: Optional[str] = None
    execution_time_ms: Optional[float] = None
    agent_results: Dict[str, Any] = Field(default_factory=dict)
    coordination_metrics: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class SystemMetricsResponse(BaseModel):
    """Response model for system performance metrics."""
    communication_metrics: Dict[str, Any]
    agent_metrics: Dict[str, Any]
    orchestration_metrics: Dict[str, Any]
    timestamp: str


# Agent Management
_agent_instances: Dict[str, Any] = {}


async def get_agent_instance(agent_type: str) -> Any:
    """Get or create an agent instance."""
    if agent_type not in _agent_instances:
        agent_classes = {
            "market": MarketAutonomousAgent,
            "executive": ExecutiveAutonomousAgent,
            "content": ContentAutonomousAgent,
            "logistics": LogisticsAutonomousAgent,
        }
        
        if agent_type not in agent_classes:
            raise HTTPException(status_code=400, detail=f"Unknown agent type: {agent_type}")
        
        agent_class = agent_classes[agent_type]
        agent_id = f"{agent_type}_orchestration_agent"
        agent = agent_class(agent_id)
        
        # Initialize the agent
        await agent.initialize_async()
        
        _agent_instances[agent_type] = agent
        logger.info(f"Created and initialized {agent_type} agent for orchestration")
    
    return _agent_instances[agent_type]


# API Endpoints

@router.post("/communication/send", response_model=AgentCommunicationResponse)
async def send_agent_communication(request: AgentCommunicationRequest):
    """Send a real-time message between agents."""
    start_time = time.perf_counter()
    
    try:
        # Validate agent types
        valid_agents = ["market_agent", "executive_agent", "content_agent", "logistics_agent"]
        if request.from_agent not in valid_agents or request.to_agent not in valid_agents:
            raise HTTPException(status_code=400, detail="Invalid agent ID")
        
        # Convert string enums
        try:
            message_type = getattr(AgentCommunicationType, request.message_type.upper())
            priority = getattr(AgentCommunicationPriority, request.priority.upper())
        except AttributeError:
            raise HTTPException(status_code=400, detail="Invalid message type or priority")
        
        # Send message via enhanced communication system
        result = await enhanced_agent_communication.send_message(
            from_agent=request.from_agent,
            to_agent=request.to_agent,
            message_type=message_type,
            content=request.content,
            priority=priority,
            requires_response=request.requires_response,
            timeout=request.timeout,
        )
        
        execution_time = (time.perf_counter() - start_time) * 1000
        
        if result:
            return AgentCommunicationResponse(
                success=True,
                message_id=result.get("message_id"),
                latency_ms=execution_time,
                response_data=result.get("response_data"),
            )
        else:
            return AgentCommunicationResponse(
                success=False,
                error="Failed to send message",
                latency_ms=execution_time,
            )
            
    except Exception as e:
        execution_time = (time.perf_counter() - start_time) * 1000
        logger.error(f"Error in agent communication: {e}")
        return AgentCommunicationResponse(
            success=False,
            error=str(e),
            latency_ms=execution_time,
        )


@router.post("/decision/execute", response_model=AgentDecisionResponse)
async def execute_agent_decision(request: AgentDecisionRequest):
    """Execute a decision using an autonomous agent."""
    start_time = time.perf_counter()
    
    try:
        # Get agent instance
        agent = await get_agent_instance(request.agent_type)
        
        # Execute decision
        result = await agent.make_decision(request.decision_type, request.context)
        
        execution_time = (time.perf_counter() - start_time) * 1000
        
        return AgentDecisionResponse(
            success=True,
            decision_id=result.get("decision_id"),
            result=result,
            execution_time_ms=execution_time,
            confidence=result.get("confidence"),
        )
        
    except Exception as e:
        execution_time = (time.perf_counter() - start_time) * 1000
        logger.error(f"Error executing agent decision: {e}")
        return AgentDecisionResponse(
            success=False,
            error=str(e),
            execution_time_ms=execution_time,
        )


@router.post("/workflow/execute", response_model=WorkflowExecutionResponse)
async def execute_multi_agent_workflow(request: WorkflowExecutionRequest):
    """Execute a coordinated workflow across multiple agents."""
    start_time = time.perf_counter()
    workflow_id = str(uuid4())
    
    try:
        agent_results = {}
        coordination_metrics = {
            "agents_involved": len(request.agents),
            "coordination_strategy": request.coordination_strategy,
            "start_time": datetime.now(timezone.utc).isoformat(),
        }
        
        if request.coordination_strategy == "sequential":
            # Execute agents sequentially
            for agent_type in request.agents:
                agent_start = time.perf_counter()
                agent = await get_agent_instance(agent_type)
                
                # Execute agent-specific workflow step
                agent_context = {
                    **request.context,
                    "workflow_id": workflow_id,
                    "workflow_type": request.workflow_type,
                    "agent_position": len(agent_results) + 1,
                    "total_agents": len(request.agents),
                }
                
                result = await agent.make_decision(request.workflow_type, agent_context)
                agent_time = (time.perf_counter() - agent_start) * 1000
                
                agent_results[agent_type] = {
                    "result": result,
                    "execution_time_ms": agent_time,
                    "success": True,
                }
                
        elif request.coordination_strategy == "parallel":
            # Execute agents in parallel
            tasks = []
            for agent_type in request.agents:
                agent = await get_agent_instance(agent_type)
                agent_context = {
                    **request.context,
                    "workflow_id": workflow_id,
                    "workflow_type": request.workflow_type,
                }
                task = asyncio.create_task(agent.make_decision(request.workflow_type, agent_context))
                tasks.append((agent_type, task))
            
            # Wait for all tasks to complete
            for agent_type, task in tasks:
                try:
                    result = await task
                    agent_results[agent_type] = {
                        "result": result,
                        "success": True,
                    }
                except Exception as e:
                    agent_results[agent_type] = {
                        "error": str(e),
                        "success": False,
                    }
        
        execution_time = (time.perf_counter() - start_time) * 1000
        coordination_metrics["total_execution_time_ms"] = execution_time
        coordination_metrics["end_time"] = datetime.now(timezone.utc).isoformat()
        
        return WorkflowExecutionResponse(
            success=True,
            workflow_id=workflow_id,
            execution_time_ms=execution_time,
            agent_results=agent_results,
            coordination_metrics=coordination_metrics,
        )
        
    except Exception as e:
        execution_time = (time.perf_counter() - start_time) * 1000
        logger.error(f"Error executing multi-agent workflow: {e}")
        return WorkflowExecutionResponse(
            success=False,
            error=str(e),
            execution_time_ms=execution_time,
        )


@router.get("/metrics", response_model=SystemMetricsResponse)
async def get_orchestration_metrics():
    """Get current system orchestration metrics."""
    try:
        # Get communication metrics
        communication_metrics = enhanced_agent_communication.get_performance_metrics()
        
        # Get agent metrics
        agent_metrics = {}
        for agent_type, agent in _agent_instances.items():
            if hasattr(agent, 'get_performance_metrics'):
                agent_metrics[agent_type] = await agent.get_performance_metrics()
        
        # Get orchestration metrics
        orchestration_metrics = {
            "active_agent_instances": len(_agent_instances),
            "supported_agent_types": ["market", "executive", "content", "logistics"],
            "api_endpoints_available": 4,
            "realtime_communication_enabled": enhanced_agent_communication.is_running,
        }
        
        return SystemMetricsResponse(
            communication_metrics=communication_metrics,
            agent_metrics=agent_metrics,
            orchestration_metrics=orchestration_metrics,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        
    except Exception as e:
        logger.error(f"Error getting orchestration metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_orchestration_health():
    """Get orchestration system health status."""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {
                "realtime_communication": enhanced_agent_communication.is_running,
                "agent_instances": len(_agent_instances),
                "api_endpoints": "operational",
            },
            "performance": {
                "average_latency_ms": enhanced_agent_communication.performance_metrics.get("average_latency", 0),
                "active_connections": enhanced_agent_communication.performance_metrics.get("active_connections", 0),
                "message_success_rate": (
                    1.0 - (enhanced_agent_communication.performance_metrics.get("failed_deliveries", 0) / 
                           max(enhanced_agent_communication.performance_metrics.get("messages_sent", 1), 1))
                ),
            },
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error getting orchestration health: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
