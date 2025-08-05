"""
Feedback Processors Module for FlipSync Agentic System

This module provides a unified interface for all feedback processor implementations,
re-exporting the various feedback processor classes for easy import.
"""

# Import all feedback processor implementations
from fs_agt_clean.core.coordination.decision.feedback_processor import (
    BaseFeedbackProcessor,
    InMemoryFeedbackProcessor,
)
from fs_agt_clean.core.coordination.decision.database_feedback_processor import (
    DatabaseFeedbackProcessor,
)

# Re-export all feedback processors for easy access
__all__ = [
    "BaseFeedbackProcessor",
    "InMemoryFeedbackProcessor",
    "DatabaseFeedbackProcessor",
]
