"""
Database-backed Distributed Decision System for FlipSync Agentic System

This module extends the existing DistributedDecisionSystem to add database persistence
for decision quality assessment, real-time tracking, and cross-restart continuity.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update

from fs_agt_clean.core.coordination.database_models import (
    DistributedDecisionState,
)
from fs_agt_clean.core.coordination.decision.models import DecisionStatus, DecisionType
from fs_agt_clean.core.db.database import Database

logger = logging.getLogger(__name__)


class DatabaseDistributedDecisionSystem:
    """Database-backed Distributed Decision System with persistent state.
    
    This class provides:
    - Decision quality assessment with database tracking
    - Real-time decision tracking with database state
    - Distributed decision making across agent restarts
    - Decision analytics and performance metrics
    """
    
    def __init__(
        self,
        system_id: str,
        database: Database,
        required_consensus: float = 0.7,
        decision_timeout_seconds: int = 300
    ):
        """Initialize the database-backed distributed decision system.
        
        Args:
            system_id: Unique identifier for this decision system
            database: Database instance for persistence
            required_consensus: Minimum consensus required for decisions (0.0 to 1.0)
            decision_timeout_seconds: Timeout for decision processes in seconds
        """
        self.system_id = system_id
        self.database = database
        self.required_consensus = required_consensus
        self.decision_timeout_seconds = decision_timeout_seconds
        self.active_decisions: Dict[str, DistributedDecisionState] = {}
        
        logger.info(f"Initialized DatabaseDistributedDecisionSystem {system_id}")
    
    async def initialize(self) -> bool:
        """Initialize the database-backed distributed decision system.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # Load active decisions from database
            await self._load_active_decisions()
            
            logger.info(f"✅ DatabaseDistributedDecisionSystem initialized for {self.system_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize DatabaseDistributedDecisionSystem: {e}")
            return False
    
    async def initiate_distributed_decision(
        self,
        decision_id: str,
        decision_type: DecisionType,
        decision_description: str,
        participating_agents: List[str],
        decision_context: Dict[str, Any],
        required_consensus: Optional[float] = None,
        deadline_minutes: Optional[int] = None
    ) -> bool:
        """Initiate a new distributed decision process with database persistence.
        
        Args:
            decision_id: Unique identifier for the decision
            decision_type: Type of decision being made
            decision_description: Description of the decision
            participating_agents: List of agents participating in the decision
            decision_context: Context data for the decision
            required_consensus: Override default consensus requirement
            deadline_minutes: Decision deadline in minutes from now
            
        Returns:
            True if decision was initiated successfully, False otherwise
        """
        try:
            deadline = None
            if deadline_minutes:
                deadline = datetime.now(timezone.utc).replace(
                    minute=datetime.now(timezone.utc).minute + deadline_minutes
                )
            
            consensus_threshold = required_consensus or self.required_consensus
            
            async with self.database.get_session() as session:
                decision_record = DistributedDecisionState(
                    decision_id=decision_id,
                    decision_type=decision_type,
                    decision_description=decision_description,
                    decision_context=decision_context,
                    participating_agents=participating_agents,
                    required_consensus=consensus_threshold,
                    deadline=deadline,
                    status=DecisionStatus.PENDING
                )
                
                session.add(decision_record)
                await session.commit()
                
                # Cache the decision state
                self.active_decisions[decision_id] = decision_record
                
                logger.info(f"Initiated distributed decision {decision_id} with {len(participating_agents)} agents")
                return True
                
        except Exception as e:
            logger.error(f"Failed to initiate distributed decision {decision_id}: {e}")
            return False
    
    async def submit_agent_input(
        self,
        decision_id: str,
        agent_id: str,
        agent_input: Dict[str, Any],
        confidence_score: float = 1.0
    ) -> bool:
        """Submit an agent's input for a distributed decision.
        
        Args:
            decision_id: Decision identifier
            agent_id: Agent submitting input
            agent_input: Agent's decision input data
            confidence_score: Agent's confidence in their input (0.0 to 1.0)
            
        Returns:
            True if input was submitted successfully, False otherwise
        """
        try:
            async with self.database.get_session() as session:
                # Get current decision state
                result = await session.execute(
                    select(DistributedDecisionState).where(
                        DistributedDecisionState.decision_id == decision_id
                    )
                )
                
                decision_record = result.scalar_one_or_none()
                if not decision_record:
                    logger.error(f"Decision {decision_id} not found")
                    return False
                
                # Add agent input
                agent_inputs = decision_record.agent_inputs or []
                agent_inputs.append({
                    "agent_id": agent_id,
                    "input_data": agent_input,
                    "confidence_score": confidence_score,
                    "submitted_at": datetime.now(timezone.utc).isoformat()
                })
                
                # Update decision record
                await session.execute(
                    update(DistributedDecisionState)
                    .where(DistributedDecisionState.decision_id == decision_id)
                    .values(
                        agent_inputs=agent_inputs,
                        last_updated=datetime.now(timezone.utc)
                    )
                )
                
                await session.commit()
                
                # Check if we have all inputs and can evaluate consensus
                if len(agent_inputs) >= len(decision_record.participating_agents):
                    await self._evaluate_consensus(decision_id)
                
                logger.debug(f"Agent {agent_id} submitted input for decision {decision_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to submit agent input for decision {decision_id}: {e}")
            return False
    
    async def get_decision_status(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a distributed decision.
        
        Args:
            decision_id: Decision identifier
            
        Returns:
            Decision status data or None if not found
        """
        try:
            async with self.database.get_session() as session:
                result = await session.execute(
                    select(DistributedDecisionState).where(
                        DistributedDecisionState.decision_id == decision_id
                    )
                )
                
                decision_record = result.scalar_one_or_none()
                if not decision_record:
                    return None
                
                return {
                    "decision_id": decision_record.decision_id,
                    "decision_type": decision_record.decision_type.value,
                    "description": decision_record.decision_description,
                    "status": decision_record.status.value,
                    "participating_agents": decision_record.participating_agents,
                    "required_consensus": decision_record.required_consensus,
                    "consensus_reached": decision_record.consensus_reached,
                    "consensus_score": decision_record.consensus_score,
                    "agent_inputs_count": len(decision_record.agent_inputs or []),
                    "final_decision": decision_record.final_decision,
                    "decision_quality_score": decision_record.decision_quality_score,
                    "created_at": decision_record.created_at.isoformat(),
                    "completed_at": decision_record.completed_at.isoformat() if decision_record.completed_at else None,
                    "deadline": decision_record.deadline.isoformat() if decision_record.deadline else None
                }
                
        except Exception as e:
            logger.error(f"Failed to get decision status for {decision_id}: {e}")
            return None
    
    async def get_decision_quality_metrics(
        self,
        time_period_hours: int = 24
    ) -> Dict[str, Any]:
        """Get decision quality assessment metrics over a time period.
        
        Args:
            time_period_hours: Time period to analyze in hours
            
        Returns:
            Decision quality metrics
        """
        try:
            since_time = datetime.now(timezone.utc).replace(
                hour=datetime.now(timezone.utc).hour - time_period_hours
            )
            
            async with self.database.get_session() as session:
                result = await session.execute(
                    select(DistributedDecisionState).where(
                        DistributedDecisionState.created_at >= since_time
                    )
                )
                
                decisions = result.scalars().all()
                
                if not decisions:
                    return {
                        "total_decisions": 0,
                        "time_period_hours": time_period_hours,
                        "generated_at": datetime.now(timezone.utc).isoformat()
                    }
                
                # Calculate metrics
                total_decisions = len(decisions)
                completed_decisions = [d for d in decisions if d.status == DecisionStatus.COMPLETED]
                consensus_reached = [d for d in decisions if d.consensus_reached]
                
                avg_consensus_score = sum(d.consensus_score or 0 for d in decisions) / total_decisions
                avg_quality_score = sum(d.decision_quality_score or 0 for d in completed_decisions) / len(completed_decisions) if completed_decisions else 0
                
                # Calculate average decision time
                decision_times = []
                for decision in completed_decisions:
                    if decision.completed_at and decision.created_at:
                        decision_time = (decision.completed_at - decision.created_at).total_seconds()
                        decision_times.append(decision_time)
                
                avg_decision_time = sum(decision_times) / len(decision_times) if decision_times else 0
                
                return {
                    "total_decisions": total_decisions,
                    "completed_decisions": len(completed_decisions),
                    "consensus_reached_count": len(consensus_reached),
                    "completion_rate": len(completed_decisions) / total_decisions,
                    "consensus_rate": len(consensus_reached) / total_decisions,
                    "average_consensus_score": avg_consensus_score,
                    "average_quality_score": avg_quality_score,
                    "average_decision_time_seconds": avg_decision_time,
                    "time_period_hours": time_period_hours,
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get decision quality metrics: {e}")
            return {
                "error": str(e),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
    
    async def _evaluate_consensus(self, decision_id: str):
        """Evaluate consensus for a decision and finalize if threshold is met."""
        try:
            async with self.database.get_session() as session:
                result = await session.execute(
                    select(DistributedDecisionState).where(
                        DistributedDecisionState.decision_id == decision_id
                    )
                )
                
                decision_record = result.scalar_one_or_none()
                if not decision_record:
                    return
                
                agent_inputs = decision_record.agent_inputs or []
                if len(agent_inputs) < len(decision_record.participating_agents):
                    return  # Not all agents have submitted inputs
                
                # Calculate consensus score (simplified implementation)
                # In a real implementation, this would use sophisticated consensus algorithms
                confidence_scores = [inp.get("confidence_score", 0) for inp in agent_inputs]
                consensus_score = sum(confidence_scores) / len(confidence_scores)
                
                consensus_reached = consensus_score >= decision_record.required_consensus
                
                # Calculate decision quality score
                quality_score = self._calculate_decision_quality(agent_inputs, consensus_score)
                
                # Finalize decision if consensus is reached
                final_decision = None
                status = DecisionStatus.PENDING
                
                if consensus_reached:
                    # Aggregate agent inputs into final decision
                    final_decision = self._aggregate_agent_inputs(agent_inputs)
                    status = DecisionStatus.COMPLETED
                
                # Update decision record
                await session.execute(
                    update(DistributedDecisionState)
                    .where(DistributedDecisionState.decision_id == decision_id)
                    .values(
                        consensus_score=consensus_score,
                        consensus_reached=consensus_reached,
                        final_decision=final_decision,
                        decision_quality_score=quality_score,
                        status=status,
                        completed_at=datetime.now(timezone.utc) if consensus_reached else None,
                        last_updated=datetime.now(timezone.utc)
                    )
                )
                
                await session.commit()
                
                logger.info(f"Evaluated consensus for decision {decision_id}: {consensus_reached} (score: {consensus_score:.3f})")
                
        except Exception as e:
            logger.error(f"Failed to evaluate consensus for decision {decision_id}: {e}")
    
    def _calculate_decision_quality(self, agent_inputs: List[Dict[str, Any]], consensus_score: float) -> float:
        """Calculate decision quality score based on agent inputs and consensus."""
        # Simplified quality calculation
        # In a real implementation, this would consider multiple factors
        input_diversity = len(set(str(inp.get("input_data", {})) for inp in agent_inputs)) / len(agent_inputs)
        avg_confidence = sum(inp.get("confidence_score", 0) for inp in agent_inputs) / len(agent_inputs)
        
        quality_score = (consensus_score * 0.4) + (input_diversity * 0.3) + (avg_confidence * 0.3)
        return min(1.0, max(0.0, quality_score))
    
    def _aggregate_agent_inputs(self, agent_inputs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate agent inputs into a final decision."""
        # Simplified aggregation - in a real implementation, this would be more sophisticated
        aggregated_data = {}
        
        for agent_input in agent_inputs:
            input_data = agent_input.get("input_data", {})
            for key, value in input_data.items():
                if key not in aggregated_data:
                    aggregated_data[key] = []
                aggregated_data[key].append(value)
        
        # Take the most common value for each key
        final_decision = {}
        for key, values in aggregated_data.items():
            if values:
                # For numeric values, take average; for others, take most common
                if all(isinstance(v, (int, float)) for v in values):
                    final_decision[key] = sum(values) / len(values)
                else:
                    final_decision[key] = max(set(values), key=values.count)
        
        return final_decision
    
    async def _load_active_decisions(self):
        """Load active decisions from database."""
        try:
            async with self.database.get_session() as session:
                result = await session.execute(
                    select(DistributedDecisionState).where(
                        DistributedDecisionState.status.in_([DecisionStatus.PENDING, DecisionStatus.IN_PROGRESS])
                    )
                )
                
                active_decisions = result.scalars().all()
                
                for decision in active_decisions:
                    self.active_decisions[decision.decision_id] = decision
                    logger.debug(f"Loaded active decision: {decision.decision_id}")
                
                logger.info(f"Loaded {len(active_decisions)} active decisions")
                
        except Exception as e:
            logger.error(f"Failed to load active decisions: {e}")
