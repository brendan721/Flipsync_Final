"""
Distributed Decision Making System for Phase 4 Multi-Agent Coordination
=======================================================================

This module provides distributed decision making capabilities that enable
multiple agents to collaborate on complex decisions, share decision context,
and reach consensus on optimal solutions.

Features:
- Distributed decision making across multiple agents
- Decision context sharing and aggregation
- Consensus building mechanisms
- Decision quality assessment and validation
- Real-time decision coordination
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

logger = logging.getLogger(__name__)


class DecisionType(Enum):
    """Types of distributed decisions."""
    STRATEGIC = "strategic"
    OPERATIONAL = "operational"
    TACTICAL = "tactical"
    EMERGENCY = "emergency"
    OPTIMIZATION = "optimization"


class DecisionStatus(Enum):
    """Status of distributed decisions."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    CONSENSUS_REACHED = "consensus_reached"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class AgentDecisionInput:
    """Input from an agent for a distributed decision."""
    agent_id: str
    decision_option: str
    confidence: float
    reasoning: str
    supporting_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DistributedDecision:
    """Represents a decision that requires input from multiple agents."""
    decision_id: str
    decision_type: DecisionType
    description: str
    context: Dict[str, Any]
    participating_agents: List[str]
    required_consensus: float = 0.7  # Minimum consensus required
    deadline: Optional[datetime] = None
    status: DecisionStatus = DecisionStatus.PENDING
    agent_inputs: List[AgentDecisionInput] = field(default_factory=list)
    final_decision: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class DistributedDecisionSystem:
    """System for coordinating distributed decisions across multiple agents."""
    
    def __init__(self, system_id: str = "distributed_decision_system"):
        """Initialize the distributed decision system.
        
        Args:
            system_id: Unique identifier for this system
        """
        self.system_id = system_id
        self.active_decisions: Dict[str, DistributedDecision] = {}
        self.decision_history: List[DistributedDecision] = []
        self.agent_decision_profiles: Dict[str, Dict[str, Any]] = {}
        
        # System metrics
        self.system_metrics = {
            "total_decisions": 0,
            "successful_decisions": 0,
            "consensus_reached": 0,
            "average_decision_time": 0.0,
            "agent_participation_rate": {},
            "decision_quality_score": 0.0
        }
        
        logger.info(f"✅ Distributed Decision System initialized: {self.system_id}")
    
    async def initiate_distributed_decision(
        self,
        decision_type: DecisionType,
        description: str,
        context: Dict[str, Any],
        participating_agents: List[str],
        required_consensus: float = 0.7,
        deadline_minutes: int = 30
    ) -> str:
        """Initiate a new distributed decision process.
        
        Args:
            decision_type: Type of decision to make
            description: Description of the decision
            context: Context information for the decision
            participating_agents: List of agents to participate
            required_consensus: Minimum consensus required (0.0 to 1.0)
            deadline_minutes: Deadline in minutes from now
            
        Returns:
            Decision ID of the initiated decision
        """
        decision_id = f"dist_decision_{uuid4()}"
        
        deadline = datetime.now() + timedelta(minutes=deadline_minutes)
        
        decision = DistributedDecision(
            decision_id=decision_id,
            decision_type=decision_type,
            description=description,
            context=context,
            participating_agents=participating_agents,
            required_consensus=required_consensus,
            deadline=deadline
        )
        
        self.active_decisions[decision_id] = decision
        self.system_metrics["total_decisions"] += 1
        
        # Initialize agent participation tracking
        for agent_id in participating_agents:
            if agent_id not in self.agent_decision_profiles:
                self.agent_decision_profiles[agent_id] = {
                    "decisions_participated": 0,
                    "decisions_contributed": 0,
                    "average_confidence": 0.0,
                    "decision_quality": 0.0
                }
            self.agent_decision_profiles[agent_id]["decisions_participated"] += 1
        
        logger.info(f"🎯 Initiated distributed decision: {decision_id} ({decision_type.value})")
        return decision_id
    
    async def submit_agent_decision_input(
        self,
        decision_id: str,
        agent_id: str,
        decision_option: str,
        confidence: float,
        reasoning: str,
        supporting_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Submit an agent's input for a distributed decision.
        
        Args:
            decision_id: ID of the decision
            agent_id: ID of the contributing agent
            decision_option: The agent's preferred decision option
            confidence: Confidence level (0.0 to 1.0)
            reasoning: Reasoning behind the decision
            supporting_data: Optional supporting data
            
        Returns:
            True if input was successfully submitted, False otherwise
        """
        try:
            if decision_id not in self.active_decisions:
                logger.error(f"Decision {decision_id} not found")
                return False
            
            decision = self.active_decisions[decision_id]
            
            if agent_id not in decision.participating_agents:
                logger.error(f"Agent {agent_id} not authorized for decision {decision_id}")
                return False
            
            if decision.status not in [DecisionStatus.PENDING, DecisionStatus.IN_PROGRESS]:
                logger.error(f"Decision {decision_id} is not accepting inputs (status: {decision.status})")
                return False
            
            # Check if agent already submitted input
            existing_input = next(
                (inp for inp in decision.agent_inputs if inp.agent_id == agent_id),
                None
            )
            
            if existing_input:
                # Update existing input
                existing_input.decision_option = decision_option
                existing_input.confidence = confidence
                existing_input.reasoning = reasoning
                existing_input.supporting_data = supporting_data or {}
                existing_input.timestamp = datetime.now()
                logger.info(f"🔄 Updated input from {agent_id} for decision {decision_id}")
            else:
                # Add new input
                agent_input = AgentDecisionInput(
                    agent_id=agent_id,
                    decision_option=decision_option,
                    confidence=confidence,
                    reasoning=reasoning,
                    supporting_data=supporting_data or {}
                )
                decision.agent_inputs.append(agent_input)
                
                # Update agent profile
                if agent_id in self.agent_decision_profiles:
                    profile = self.agent_decision_profiles[agent_id]
                    profile["decisions_contributed"] += 1
                    
                    # Update average confidence
                    total_confidence = profile["average_confidence"] * (profile["decisions_contributed"] - 1) + confidence
                    profile["average_confidence"] = total_confidence / profile["decisions_contributed"]
                
                logger.info(f"📝 Received input from {agent_id} for decision {decision_id}")
            
            # Update decision status
            if decision.status == DecisionStatus.PENDING:
                decision.status = DecisionStatus.IN_PROGRESS
            
            # Check if we can reach consensus
            await self._check_consensus(decision)
            
            return True
            
        except Exception as e:
            logger.error(f"Error submitting agent input for decision {decision_id}: {e}")
            return False
    
    async def _check_consensus(self, decision: DistributedDecision) -> bool:
        """Check if consensus has been reached for a decision."""
        try:
            if len(decision.agent_inputs) < len(decision.participating_agents):
                # Not all agents have provided input yet
                return False
            
            # Analyze decision options and confidence levels
            option_votes = {}
            total_confidence = 0.0
            
            for agent_input in decision.agent_inputs:
                option = agent_input.decision_option
                confidence = agent_input.confidence
                
                if option not in option_votes:
                    option_votes[option] = {"votes": 0, "total_confidence": 0.0, "agents": []}
                
                option_votes[option]["votes"] += 1
                option_votes[option]["total_confidence"] += confidence
                option_votes[option]["agents"].append(agent_input.agent_id)
                total_confidence += confidence
            
            # Find the option with highest support
            best_option = max(option_votes.keys(), key=lambda k: option_votes[k]["votes"])
            best_option_data = option_votes[best_option]
            
            # Calculate consensus metrics
            consensus_percentage = best_option_data["votes"] / len(decision.participating_agents)
            average_confidence = best_option_data["total_confidence"] / best_option_data["votes"]
            overall_confidence = total_confidence / len(decision.agent_inputs)
            
            # Check if consensus requirements are met
            consensus_reached = (
                consensus_percentage >= decision.required_consensus and
                average_confidence >= 0.6  # Minimum confidence threshold
            )
            
            if consensus_reached:
                decision.status = DecisionStatus.CONSENSUS_REACHED
                decision.final_decision = {
                    "chosen_option": best_option,
                    "consensus_percentage": consensus_percentage,
                    "average_confidence": average_confidence,
                    "overall_confidence": overall_confidence,
                    "supporting_agents": best_option_data["agents"],
                    "all_options": option_votes,
                    "decision_quality": self._calculate_decision_quality(decision)
                }
                
                # Complete the decision
                await self._complete_decision(decision)
                
                logger.info(f"✅ Consensus reached for decision {decision.decision_id}: {best_option}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking consensus for decision {decision.decision_id}: {e}")
            return False
    
    def _calculate_decision_quality(self, decision: DistributedDecision) -> float:
        """Calculate the quality score of a decision."""
        if not decision.agent_inputs:
            return 0.0
        
        # Factors for decision quality
        confidence_score = sum(inp.confidence for inp in decision.agent_inputs) / len(decision.agent_inputs)
        
        # Participation score (higher when more agents participate)
        participation_score = len(decision.agent_inputs) / len(decision.participating_agents)
        
        # Reasoning quality score (simplified - based on reasoning length)
        reasoning_scores = [
            min(1.0, len(inp.reasoning) / 100) for inp in decision.agent_inputs
        ]
        reasoning_score = sum(reasoning_scores) / len(reasoning_scores) if reasoning_scores else 0.0
        
        # Time efficiency score (faster decisions get higher scores)
        if decision.deadline:
            time_taken = (datetime.now() - decision.created_at).total_seconds()
            deadline_duration = (decision.deadline - decision.created_at).total_seconds()
            time_efficiency = max(0.0, 1.0 - (time_taken / deadline_duration))
        else:
            time_efficiency = 0.8  # Default score when no deadline
        
        # Combine scores
        quality_score = (
            confidence_score * 0.3 +
            participation_score * 0.3 +
            reasoning_score * 0.2 +
            time_efficiency * 0.2
        )
        
        return min(1.0, quality_score)
    
    async def _complete_decision(self, decision: DistributedDecision):
        """Complete a distributed decision."""
        decision.status = DecisionStatus.COMPLETED
        decision.completed_at = datetime.now()
        
        # Move to history
        self.decision_history.append(decision)
        if decision.decision_id in self.active_decisions:
            del self.active_decisions[decision.decision_id]
        
        # Update system metrics
        self.system_metrics["successful_decisions"] += 1
        if decision.final_decision:
            self.system_metrics["consensus_reached"] += 1
            
            # Update decision quality
            quality = decision.final_decision.get("decision_quality", 0.0)
            current_quality = self.system_metrics["decision_quality_score"]
            total_decisions = self.system_metrics["successful_decisions"]
            self.system_metrics["decision_quality_score"] = (
                (current_quality * (total_decisions - 1) + quality) / total_decisions
            )
        
        # Update average decision time
        decision_time = (decision.completed_at - decision.created_at).total_seconds()
        current_avg = self.system_metrics["average_decision_time"]
        total_successful = self.system_metrics["successful_decisions"]
        self.system_metrics["average_decision_time"] = (
            (current_avg * (total_successful - 1) + decision_time) / total_successful
        )
        
        logger.info(f"🎯 Completed distributed decision: {decision.decision_id}")
    
    async def get_decision_status(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a distributed decision.
        
        Args:
            decision_id: ID of the decision
            
        Returns:
            Dictionary containing decision status information
        """
        decision = self.active_decisions.get(decision_id)
        if not decision:
            # Check history
            historical_decision = next(
                (d for d in self.decision_history if d.decision_id == decision_id),
                None
            )
            if historical_decision:
                decision = historical_decision
            else:
                return None
        
        return {
            "decision_id": decision.decision_id,
            "status": decision.status.value,
            "description": decision.description,
            "participating_agents": decision.participating_agents,
            "inputs_received": len(decision.agent_inputs),
            "inputs_required": len(decision.participating_agents),
            "consensus_required": decision.required_consensus,
            "deadline": decision.deadline.isoformat() if decision.deadline else None,
            "final_decision": decision.final_decision,
            "created_at": decision.created_at.isoformat(),
            "completed_at": decision.completed_at.isoformat() if decision.completed_at else None
        }
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics."""
        # Calculate agent participation rates
        for agent_id, profile in self.agent_decision_profiles.items():
            if profile["decisions_participated"] > 0:
                participation_rate = profile["decisions_contributed"] / profile["decisions_participated"]
                self.system_metrics["agent_participation_rate"][agent_id] = participation_rate
        
        return {
            **self.system_metrics,
            "active_decisions": len(self.active_decisions),
            "completed_decisions": len(self.decision_history),
            "registered_agents": len(self.agent_decision_profiles),
            "success_rate": (
                self.system_metrics["successful_decisions"] / max(1, self.system_metrics["total_decisions"])
            ),
            "consensus_rate": (
                self.system_metrics["consensus_reached"] / max(1, self.system_metrics["successful_decisions"])
            )
        }
    
    async def cleanup_expired_decisions(self) -> int:
        """Clean up decisions that have exceeded their deadlines."""
        expired_count = 0
        current_time = datetime.now()
        
        expired_decisions = [
            decision_id for decision_id, decision in self.active_decisions.items()
            if decision.deadline and current_time > decision.deadline
        ]
        
        for decision_id in expired_decisions:
            decision = self.active_decisions[decision_id]
            decision.status = DecisionStatus.TIMEOUT
            decision.completed_at = current_time
            
            # Move to history
            self.decision_history.append(decision)
            del self.active_decisions[decision_id]
            
            expired_count += 1
            logger.warning(f"⏰ Decision {decision_id} expired due to timeout")
        
        return expired_count
