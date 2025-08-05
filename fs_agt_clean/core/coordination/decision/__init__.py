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

# Re-export implementations (only classes that exist)
# Import order matters to avoid circular imports

# First import models
from fs_agt_clean.core.coordination.decision.models import (
    Decision,
    DecisionType,
    DecisionStatus,
    DecisionError,
)

# Then import implementations
from fs_agt_clean.core.coordination.decision.decision_validator import (
    RuleBasedValidator,
)

# Finally import pipeline (which may depend on others)
from fs_agt_clean.core.coordination.decision.pipeline import (
    StandardDecisionPipeline,
)

# Re-export core models (only classes that exist)
