#!/usr/bin/env python3
"""
Brain/Intelligence System Integration Adapter
============================================

This module provides the integration layer between the sophisticated brain system
in fs_agt_clean/services/advanced_features/ai_integration/brain/ and the 4 core
autonomous agents, maintaining <500ms decision times and 85% autonomous operation.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

# Brain system imports
from fs_agt_clean.services.advanced_features.ai_integration.brain.decision_engine import (
    DecisionEngine, Decision
)
from fs_agt_clean.services.advanced_features.ai_integration.brain.memory.memory_manager import (
    MemoryManager, Memory
)
from fs_agt_clean.services.advanced_features.ai_integration.brain.workflow_engine import (
    WorkflowEngine
)

logger = logging.getLogger(__name__)


@dataclass
class BrainIntegrationConfig:
    """Configuration for brain system integration."""
    
    enable_memory_management: bool = True
    enable_workflow_patterns: bool = True
    enable_decision_enhancement: bool = True
    memory_retention_hours: int = 24
    pattern_recognition_threshold: float = 0.7
    max_decision_time_ms: int = 500
    

class BrainIntegrationAdapter:
    """
    Adapter that integrates the sophisticated brain system with autonomous agents.
    
    This adapter provides:
    - Enhanced decision making through the brain's decision engine
    - Memory management for agent experiences and learnings
    - Workflow pattern recognition and optimization
    - Strategic intelligence coordination
    """
    
    def __init__(self, agent_id: str, agent_type: str, config: Optional[BrainIntegrationConfig] = None):
        """Initialize brain integration adapter for an autonomous agent."""
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.config = config or BrainIntegrationConfig()
        
        # Initialize brain components
        self.decision_engine = DecisionEngine()
        self.memory_manager = MemoryManager()
        self.workflow_engine = WorkflowEngine()
        
        # Performance tracking
        self.performance_metrics = {
            "decisions_enhanced": 0,
            "memories_stored": 0,
            "patterns_recognized": 0,
            "avg_decision_time_ms": 0.0,
        }
        
        self._initialized = False
        logger.info(f"Brain integration adapter initialized for {agent_type} agent {agent_id}")
    
    async def initialize(self) -> bool:
        """Initialize the brain integration adapter."""
        try:
            start_time = time.perf_counter()
            
            # Initialize workflow engine with agent-specific patterns
            await self._initialize_agent_workflows()
            
            # Set up memory management for this agent
            await self._initialize_agent_memory()
            
            # Configure decision enhancement
            await self._initialize_decision_enhancement()
            
            initialization_time = (time.perf_counter() - start_time) * 1000
            
            if initialization_time > self.config.max_decision_time_ms:
                logger.warning(
                    f"Brain adapter initialization took {initialization_time:.2f}ms "
                    f"(exceeds {self.config.max_decision_time_ms}ms target)"
                )
            
            self._initialized = True
            logger.info(f"Brain integration adapter initialized in {initialization_time:.2f}ms")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize brain integration adapter: {e}")
            return False
    
    async def enhance_decision(
        self, 
        context: Dict[str, Any], 
        available_actions: List[str],
        agent_memory_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Enhance agent decision-making using brain intelligence.
        
        Args:
            context: Decision context from the agent
            available_actions: List of available actions
            agent_memory_context: Optional memory context from agent
            
        Returns:
            Enhanced decision with brain intelligence insights
        """
        if not self._initialized:
            logger.warning("Brain adapter not initialized, using fallback")
            return self._fallback_decision(context, available_actions)
        
        start_time = time.perf_counter()
        
        try:
            # Retrieve relevant memories
            relevant_memories = await self._get_relevant_memories(context)
            
            # Prepare memory context for decision engine
            memory_context = {
                "agent_memory": agent_memory_context or {},
                "brain_memories": [
                    {
                        "content": mem.content,
                        "context": mem.context,
                        "importance": mem.importance,
                        "created_at": mem.created_at.isoformat()
                    }
                    for mem in relevant_memories
                ],
                "agent_type": self.agent_type,
                "agent_id": self.agent_id
            }
            
            # Use brain decision engine to enhance decision
            brain_decision = await self.decision_engine.make_decision(
                context=context,
                actions=available_actions,
                memory_context=memory_context
            )
            
            # Check for workflow patterns
            workflow_insights = await self._analyze_workflow_patterns(context, brain_decision)
            
            decision_time = (time.perf_counter() - start_time) * 1000
            
            # Update performance metrics
            self.performance_metrics["decisions_enhanced"] += 1
            self.performance_metrics["avg_decision_time_ms"] = (
                (self.performance_metrics["avg_decision_time_ms"] * 
                 (self.performance_metrics["decisions_enhanced"] - 1) + decision_time) /
                self.performance_metrics["decisions_enhanced"]
            )
            
            # Store this decision as a memory for future reference
            if self.config.enable_memory_management:
                await self._store_decision_memory(context, brain_decision, decision_time)
            
            enhanced_decision = {
                "action": brain_decision.action,
                "confidence": brain_decision.confidence,
                "reasoning": brain_decision.reasoning,
                "brain_enhanced": True,
                "decision_time_ms": decision_time,
                "workflow_insights": workflow_insights,
                "memory_context_used": len(relevant_memories),
                "metadata": brain_decision.metadata or {}
            }
            
            if decision_time > self.config.max_decision_time_ms:
                logger.warning(
                    f"Brain-enhanced decision took {decision_time:.2f}ms "
                    f"(exceeds {self.config.max_decision_time_ms}ms target)"
                )
            
            return enhanced_decision
            
        except Exception as e:
            decision_time = (time.perf_counter() - start_time) * 1000
            logger.error(f"Brain decision enhancement failed in {decision_time:.2f}ms: {e}")
            return self._fallback_decision(context, available_actions)
    
    async def store_experience(
        self, 
        experience_content: str, 
        context: Dict[str, Any], 
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Store an experience in the brain's memory system."""
        if not self.config.enable_memory_management:
            return True
        
        try:
            # Enhance context with agent information
            enhanced_context = {
                **context,
                "agent_id": self.agent_id,
                "agent_type": self.agent_type,
                "stored_at": datetime.now(timezone.utc).isoformat()
            }
            
            memory = self.memory_manager.store(
                content=experience_content,
                context=enhanced_context,
                importance=importance,
                metadata=metadata
            )
            
            self.performance_metrics["memories_stored"] += 1
            
            logger.debug(f"Stored experience memory: {memory.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store experience: {e}")
            return False
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the brain integration."""
        return {
            **self.performance_metrics,
            "initialized": self._initialized,
            "config": {
                "memory_management": self.config.enable_memory_management,
                "workflow_patterns": self.config.enable_workflow_patterns,
                "decision_enhancement": self.config.enable_decision_enhancement,
                "max_decision_time_ms": self.config.max_decision_time_ms
            }
        }
    
    async def _initialize_agent_workflows(self):
        """Initialize agent-specific workflow patterns."""
        if not self.config.enable_workflow_patterns:
            return
        
        # Register agent-specific workflow patterns
        agent_workflows = {
            "market": [
                {
                    "workflow_id": f"{self.agent_id}_pricing_analysis",
                    "steps": [
                        {"action": "gather_market_data", "timeout": 100},
                        {"action": "analyze_competitors", "timeout": 150},
                        {"action": "calculate_optimal_price", "timeout": 100},
                        {"action": "validate_pricing", "timeout": 50}
                    ]
                }
            ],
            "content": [
                {
                    "workflow_id": f"{self.agent_id}_content_optimization",
                    "steps": [
                        {"action": "analyze_content_requirements", "timeout": 100},
                        {"action": "generate_content", "timeout": 200},
                        {"action": "optimize_seo", "timeout": 100},
                        {"action": "validate_content", "timeout": 100}
                    ]
                }
            ],
            "executive": [
                {
                    "workflow_id": f"{self.agent_id}_strategic_planning",
                    "steps": [
                        {"action": "assess_business_context", "timeout": 150},
                        {"action": "analyze_alternatives", "timeout": 200},
                        {"action": "evaluate_risks", "timeout": 100},
                        {"action": "make_strategic_decision", "timeout": 50}
                    ]
                }
            ],
            "logistics": [
                {
                    "workflow_id": f"{self.agent_id}_shipping_optimization",
                    "steps": [
                        {"action": "analyze_shipping_requirements", "timeout": 100},
                        {"action": "calculate_routes", "timeout": 150},
                        {"action": "optimize_costs", "timeout": 100},
                        {"action": "select_carrier", "timeout": 50}
                    ]
                }
            ]
        }
        
        workflows = agent_workflows.get(self.agent_type, [])
        for workflow in workflows:
            await self.workflow_engine.register_workflow(
                workflow["workflow_id"],
                workflow["steps"]
            )
    
    async def _initialize_agent_memory(self):
        """Initialize memory management for this agent."""
        if not self.config.enable_memory_management:
            return
        
        # Memory manager is already initialized in __init__
        # This method can be extended for agent-specific memory setup
        logger.debug(f"Memory management initialized for {self.agent_type} agent")
    
    async def _initialize_decision_enhancement(self):
        """Initialize decision enhancement capabilities."""
        if not self.config.enable_decision_enhancement:
            return
        
        # Decision engine is already initialized in __init__
        # This method can be extended for agent-specific decision setup
        logger.debug(f"Decision enhancement initialized for {self.agent_type} agent")
    
    async def _get_relevant_memories(self, context: Dict[str, Any]) -> List[Memory]:
        """Retrieve memories relevant to the current context."""
        try:
            # Use memory manager's search functionality
            # This is a simplified implementation - could be enhanced with semantic search
            relevant_memories = self.memory_manager.search(
                query=context.get("query", ""),
                context_filter={"agent_type": self.agent_type},
                limit=5
            )
            return relevant_memories
        except Exception as e:
            logger.error(f"Failed to retrieve relevant memories: {e}")
            return []
    
    async def _analyze_workflow_patterns(
        self, context: Dict[str, Any], decision: Decision
    ) -> Dict[str, Any]:
        """Analyze workflow patterns for insights."""
        if not self.config.enable_workflow_patterns:
            return {}
        
        try:
            # This is a simplified pattern analysis
            # Could be enhanced with more sophisticated pattern recognition
            return {
                "pattern_detected": False,
                "confidence": 0.0,
                "recommendations": []
            }
        except Exception as e:
            logger.error(f"Failed to analyze workflow patterns: {e}")
            return {}
    
    async def _store_decision_memory(
        self, context: Dict[str, Any], decision: Decision, decision_time: float
    ):
        """Store decision as memory for future reference."""
        try:
            memory_content = f"Decision: {decision.action} (confidence: {decision.confidence:.2f})"
            memory_context = {
                **context,
                "decision_action": decision.action,
                "decision_confidence": decision.confidence,
                "decision_time_ms": decision_time,
                "reasoning": decision.reasoning
            }
            
            await self.store_experience(
                experience_content=memory_content,
                context=memory_context,
                importance=decision.confidence,
                metadata={"type": "decision", "agent_type": self.agent_type}
            )
        except Exception as e:
            logger.error(f"Failed to store decision memory: {e}")
    
    def _fallback_decision(self, context: Dict[str, Any], available_actions: List[str]) -> Dict[str, Any]:
        """Fallback decision when brain enhancement fails."""
        return {
            "action": available_actions[0] if available_actions else "default",
            "confidence": 0.5,
            "reasoning": "Fallback decision due to brain enhancement failure",
            "brain_enhanced": False,
            "decision_time_ms": 0.0,
            "workflow_insights": {},
            "memory_context_used": 0,
            "metadata": {"fallback": True}
        }
