"""
Advanced Learning Engine for Phase 3 Learning System Integration
================================================================

This module provides enhanced learning capabilities that build on the existing
InMemoryLearningEngine to add sophisticated learning algorithms, cross-agent
coordination, and advanced feedback processing.

Features:
- Reinforcement learning for decision improvement
- Cross-agent learning coordination
- Advanced pattern recognition
- Temporal learning analysis
- Multi-criteria learning evaluation
"""

import logging
import numpy as np
from datetime import datetime
from typing import Any, Dict, List
from dataclasses import dataclass

from fs_agt_clean.core.coordination.decision.learning_engine import InMemoryLearningEngine
from fs_agt_clean.core.coordination.event_system import EventPublisher

logger = logging.getLogger(__name__)


@dataclass
class LearningPattern:
    """Represents a learned pattern from decision outcomes."""
    pattern_id: str
    decision_type: str
    context_features: Dict[str, Any]
    success_rate: float
    confidence_improvement: float
    usage_count: int
    last_used: datetime


@dataclass
class CrossAgentInsight:
    """Represents insights shared between agents."""
    insight_id: str
    source_agent: str
    decision_type: str
    insight_data: Dict[str, Any]
    effectiveness_score: float
    created_at: datetime


class AdvancedLearningEngine(InMemoryLearningEngine):
    """Advanced learning engine with sophisticated learning capabilities."""
    
    def __init__(self, engine_id: str, publisher: EventPublisher, agent_id: str = None):
        """Initialize the advanced learning engine.
        
        Args:
            engine_id: Unique identifier for this engine
            publisher: Event publisher for publishing learning events
            agent_id: ID of the agent owning this learning engine
        """
        super().__init__(engine_id, publisher)
        self.agent_id = agent_id or engine_id
        
        # Advanced learning data structures
        self.learning_patterns: Dict[str, LearningPattern] = {}
        self.cross_agent_insights: Dict[str, CrossAgentInsight] = {}
        self.decision_history: List[Dict[str, Any]] = []
        self.performance_trends: Dict[str, List[float]] = {}
        
        # Learning parameters
        self.learning_rate = 0.1
        self.pattern_threshold = 0.7
        self.max_history_size = 1000
        self.insight_sharing_threshold = 0.8
        
        # Advanced learning metrics
        self.learning_data.update({
            "pattern_count": 0,
            "cross_agent_insights": 0,
            "learning_effectiveness": 0.0,
            "decision_improvement_rate": 0.0,
            "pattern_recognition_accuracy": 0.0,
        })
        
        logger.info(f"✅ Advanced Learning Engine initialized for {self.agent_id}")
    
    async def learn_from_feedback(
        self,
        feedback_data: Dict[str, Any],
        publish_event: bool = False,
        battery_efficient: bool = False,
    ) -> bool:
        """Enhanced learning from feedback with pattern recognition and cross-agent coordination.
        
        Args:
            feedback_data: Feedback data
            publish_event: Whether to publish an event about the learning
            battery_efficient: Whether to use battery-efficient learning
            
        Returns:
            True if learning was successful, False otherwise
        """
        try:
            # Call parent learning method first
            success = await super().learn_from_feedback(feedback_data, publish_event, battery_efficient)
            
            if not success:
                return False
            
            # Enhanced learning processing
            await self._process_advanced_learning(feedback_data, battery_efficient)
            
            # Pattern recognition (if not battery efficient)
            if not battery_efficient:
                await self._recognize_patterns(feedback_data)
                await self._update_performance_trends(feedback_data)
            
            # Cross-agent learning coordination
            await self._coordinate_cross_agent_learning(feedback_data)
            
            # Update advanced metrics
            await self._update_advanced_metrics()
            
            logger.debug(f"🧠 Advanced learning completed for {self.agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error in advanced learning: {e}")
            return False
    
    async def _process_advanced_learning(self, feedback_data: Dict[str, Any], battery_efficient: bool):
        """Process advanced learning algorithms."""
        decision_type = feedback_data.get("decision_type", "unknown")
        quality = feedback_data.get("quality", 0.5)
        outcome = feedback_data.get("actual_outcome", "unknown")
        
        # Reinforcement learning update
        reward = self._calculate_reward(quality, outcome)
        await self._update_q_values(decision_type, reward, battery_efficient)
        
        # Add to decision history
        decision_record = {
            "timestamp": datetime.now().isoformat(),
            "decision_type": decision_type,
            "quality": quality,
            "outcome": outcome,
            "reward": reward,
            "context": feedback_data.get("context", {})
        }
        
        self.decision_history.append(decision_record)
        
        # Maintain history size
        if len(self.decision_history) > self.max_history_size:
            self.decision_history = self.decision_history[-self.max_history_size:]
    
    async def _recognize_patterns(self, feedback_data: Dict[str, Any]):
        """Recognize patterns in decision outcomes for improved future decisions."""
        if len(self.decision_history) < 10:  # Need minimum history
            return
        
        decision_type = feedback_data.get("decision_type", "unknown")
        feedback_data.get("quality", 0.5)
        
        # Analyze recent decisions of the same type
        recent_decisions = [
            d for d in self.decision_history[-50:]  # Last 50 decisions
            if d["decision_type"] == decision_type
        ]
        
        if len(recent_decisions) < 5:
            return
        
        # Calculate pattern effectiveness
        avg_quality = np.mean([d["quality"] for d in recent_decisions])
        success_rate = len([d for d in recent_decisions if d["outcome"] == "success"]) / len(recent_decisions)
        
        # Create or update pattern
        pattern_id = f"{decision_type}_pattern_{len(self.learning_patterns)}"
        
        if success_rate > self.pattern_threshold:
            pattern = LearningPattern(
                pattern_id=pattern_id,
                decision_type=decision_type,
                context_features=self._extract_context_features(recent_decisions),
                success_rate=success_rate,
                confidence_improvement=avg_quality - 0.5,
                usage_count=len(recent_decisions),
                last_used=datetime.now()
            )
            
            self.learning_patterns[pattern_id] = pattern
            self.learning_data["pattern_count"] = len(self.learning_patterns)
            
            logger.debug(f"🔍 Recognized new pattern: {pattern_id} (success rate: {success_rate:.2f})")
    
    async def _update_performance_trends(self, feedback_data: Dict[str, Any]):
        """Update performance trends for decision types."""
        decision_type = feedback_data.get("decision_type", "unknown")
        quality = feedback_data.get("quality", 0.5)
        
        if decision_type not in self.performance_trends:
            self.performance_trends[decision_type] = []
        
        self.performance_trends[decision_type].append(quality)
        
        # Keep only recent trends (last 100 decisions)
        if len(self.performance_trends[decision_type]) > 100:
            self.performance_trends[decision_type] = self.performance_trends[decision_type][-100:]
        
        # Calculate improvement rate
        if len(self.performance_trends[decision_type]) >= 10:
            recent_avg = np.mean(self.performance_trends[decision_type][-10:])
            older_avg = np.mean(self.performance_trends[decision_type][-20:-10]) if len(self.performance_trends[decision_type]) >= 20 else recent_avg
            improvement_rate = (recent_avg - older_avg) / max(older_avg, 0.1)
            self.learning_data["decision_improvement_rate"] = improvement_rate
    
    async def _coordinate_cross_agent_learning(self, feedback_data: Dict[str, Any]):
        """Coordinate learning with other agents by sharing insights."""
        decision_type = feedback_data.get("decision_type", "unknown")
        quality = feedback_data.get("quality", 0.5)
        
        # If this decision was highly successful, create an insight to share
        if quality > self.insight_sharing_threshold:
            insight = CrossAgentInsight(
                insight_id=f"{self.agent_id}_{decision_type}_{datetime.now().timestamp()}",
                source_agent=self.agent_id,
                decision_type=decision_type,
                insight_data={
                    "quality": quality,
                    "context": feedback_data.get("context", {}),
                    "strategy": feedback_data.get("strategy_used", "unknown"),
                    "outcome": feedback_data.get("actual_outcome", "unknown")
                },
                effectiveness_score=quality,
                created_at=datetime.now()
            )
            
            self.cross_agent_insights[insight.insight_id] = insight
            self.learning_data["cross_agent_insights"] = len(self.cross_agent_insights)
            
            # Publish insight for other agents
            try:
                await self.publisher.publish_notification(
                    notification_name="cross_agent_insight",
                    data={
                        "insight_id": insight.insight_id,
                        "source_agent": self.agent_id,
                        "decision_type": decision_type,
                        "effectiveness_score": quality,
                        "timestamp": datetime.now().isoformat()
                    }
                )
                logger.debug(f"📤 Shared cross-agent insight: {insight.insight_id}")
            except Exception as e:
                logger.error(f"Error sharing cross-agent insight: {e}")
    
    def _calculate_reward(self, quality: float, outcome: str) -> float:
        """Calculate reward for reinforcement learning."""
        base_reward = quality - 0.5  # -0.5 to 0.5
        
        outcome_bonus = {
            "success": 0.3,
            "excellent": 0.5,
            "partial_success": 0.1,
            "failure": -0.3,
            "error": -0.5
        }.get(outcome, 0.0)
        
        return base_reward + outcome_bonus
    
    async def _update_q_values(self, decision_type: str, reward: float, battery_efficient: bool):
        """Update Q-values for reinforcement learning."""
        if battery_efficient:
            # Simple update for battery efficiency
            learning_rate = self.learning_rate * 0.5
        else:
            learning_rate = self.learning_rate
        
        # Update decision type weight using Q-learning approach
        current_weight = self.learning_data["decision_type_weights"].get(decision_type, 1.0)
        new_weight = current_weight + learning_rate * (reward - current_weight)
        self.learning_data["decision_type_weights"][decision_type] = max(0.1, new_weight)
    
    def _extract_context_features(self, decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract common context features from a set of decisions."""
        if not decisions:
            return {}
        
        # Extract common patterns from decision contexts
        common_features = {}
        
        # Analyze context keys that appear frequently
        context_keys = {}
        for decision in decisions:
            context = decision.get("context", {})
            for key in context.keys():
                context_keys[key] = context_keys.get(key, 0) + 1
        
        # Keep features that appear in at least 50% of decisions
        threshold = len(decisions) * 0.5
        for key, count in context_keys.items():
            if count >= threshold:
                # Get most common value for this key
                values = [d.get("context", {}).get(key) for d in decisions if key in d.get("context", {})]
                if values:
                    common_features[key] = max(set(values), key=values.count)
        
        return common_features
    
    async def _update_advanced_metrics(self):
        """Update advanced learning metrics."""
        # Calculate learning effectiveness
        if self.learning_data["feedback_count"] > 0:
            total_quality = sum(
                d["quality"] for d in self.decision_history[-50:]  # Last 50 decisions
                if "quality" in d
            )
            avg_quality = total_quality / min(len(self.decision_history), 50)
            self.learning_data["learning_effectiveness"] = avg_quality
        
        # Calculate pattern recognition accuracy
        if self.learning_patterns:
            total_accuracy = sum(p.success_rate for p in self.learning_patterns.values())
            self.learning_data["pattern_recognition_accuracy"] = total_accuracy / len(self.learning_patterns)
    
    async def get_decision_recommendations(self, decision_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get decision recommendations based on learned patterns and cross-agent insights."""
        recommendations = {
            "confidence_adjustment": 0.0,
            "recommended_strategy": "default",
            "pattern_matches": [],
            "cross_agent_insights": [],
            "learning_confidence": 0.5
        }
        
        # Check for matching patterns
        for pattern in self.learning_patterns.values():
            if pattern.decision_type == decision_type:
                # Simple pattern matching based on context similarity
                similarity = self._calculate_context_similarity(context, pattern.context_features)
                if similarity > 0.7:
                    recommendations["pattern_matches"].append({
                        "pattern_id": pattern.pattern_id,
                        "similarity": similarity,
                        "success_rate": pattern.success_rate,
                        "confidence_improvement": pattern.confidence_improvement
                    })
        
        # Check for relevant cross-agent insights
        for insight in self.cross_agent_insights.values():
            if insight.decision_type == decision_type and insight.effectiveness_score > 0.7:
                recommendations["cross_agent_insights"].append({
                    "source_agent": insight.source_agent,
                    "effectiveness_score": insight.effectiveness_score,
                    "strategy": insight.insight_data.get("strategy", "unknown")
                })
        
        # Calculate overall confidence adjustment
        if recommendations["pattern_matches"]:
            best_pattern = max(recommendations["pattern_matches"], key=lambda x: x["success_rate"])
            recommendations["confidence_adjustment"] = best_pattern["confidence_improvement"]
            recommendations["learning_confidence"] = best_pattern["success_rate"]
        
        return recommendations
    
    def _calculate_context_similarity(self, context1: Dict[str, Any], context2: Dict[str, Any]) -> float:
        """Calculate similarity between two contexts."""
        if not context1 or not context2:
            return 0.0
        
        common_keys = set(context1.keys()) & set(context2.keys())
        if not common_keys:
            return 0.0
        
        matches = 0
        for key in common_keys:
            if context1[key] == context2[key]:
                matches += 1
        
        return matches / len(common_keys)
