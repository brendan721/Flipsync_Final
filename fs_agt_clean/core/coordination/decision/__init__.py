"""
Decision Pipeline component for the FlipSync application.

This module provides the decision pipeline component for FlipSync, which
enables intelligent, adaptive decision making. It provides a structured
approach to making decisions, incorporating multiple inputs and learning
from outcomes.

The decision pipeline consists of:
- Decision Maker: Makes decisions based on context and options
- Decision Validator: Validates decisions against rules and constraints
- Decision Tracker: Tracks decision status and outcomes
- Feedback Processor: Processes feedback on decision outcomes
- Learning Engine: Learns from decision outcomes to improve future decisions

The decision pipeline is designed to be:
- Mobile-optimized: Efficient operation on mobile devices
- Vision-aligned: Supporting all core vision elements
- Robust: Comprehensive error handling and recovery
- Scalable: Capable of handling complex agent ecosystems
"""

# Re-export implementations
from fs_agt_clean.core.coordination.decision.decision_maker import (
    BaseDecisionMaker,
    InMemoryDecisionMaker,
)
from fs_agt_clean.core.coordination.decision.decision_tracker import (
    BaseDecisionTracker,
    InMemoryDecisionTracker,
)
from fs_agt_clean.core.coordination.decision.decision_validator import (
    BaseDecisionValidator,
    RuleBasedValidator,
)
from fs_agt_clean.core.coordination.decision.feedback_processor import (
    BaseFeedbackProcessor,
    InMemoryFeedbackProcessor,
)

# Re-export core interfaces
from fs_agt_clean.core.coordination.decision.interfaces import (
    DecisionMaker,
    DecisionPipeline,
    DecisionTracker,
    DecisionValidator,
    FeedbackProcessor,
    LearningEngine,
)
from fs_agt_clean.core.coordination.decision.learning_engine import (
    BaseLearningEngine,
    InMemoryLearningEngine,
)

# Re-export core models
from fs_agt_clean.core.coordination.decision.models import (
    Decision,
    DecisionConfidence,
    DecisionError,
    DecisionMetadata,
    DecisionStatus,
    DecisionType,
)
from fs_agt_clean.core.coordination.decision.pipeline import (
    BaseDecisionPipeline,
    StandardDecisionPipeline,
)
