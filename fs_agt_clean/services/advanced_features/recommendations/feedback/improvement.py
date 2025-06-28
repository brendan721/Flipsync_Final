#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Recommendation Continuous Improvement System

This module implements a system for continuously improving recommendation quality
based on feedback data. It identifies areas for improvement, prioritizes them,
and generates actionable insights.

It includes:
1. Automated improvement suggestion generation
2. Impact estimation for potential improvements
3. A/B test setup for validating improvements
4. Implementation tracking for improvements
5. Pre/post analysis of improvement effects
"""

import json
import logging
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from fs_agt_clean.core.types import JsonDict

logger = logging.getLogger(__name__)


class ImprovementCategory(str, Enum):
    """Categories of recommendation improvements."""

    ALGORITHM = "algorithm"  # Algorithm parameter tuning
    DATA = "data"  # Data quality or quantity
    FEATURE = "feature"  # Additional features/signals
    DIVERSITY = "diversity"  # Recommendation diversity
    COVERAGE = "coverage"  # Item coverage
    RELEVANCE = "relevance"  # Recommendation relevance
    FRESHNESS = "freshness"  # Up-to-date recommendations
    PERFORMANCE = "performance"  # System performance
    UX = "ux"  # UnifiedUser experience


class ImprovementPriority(str, Enum):
    """Priority levels for improvements."""

    CRITICAL = "critical"  # Must address immediately
    HIGH = "high"  # Should address soon
    MEDIUM = "medium"  # Address when possible
    LOW = "low"  # Address if time allows
    EXPERIMENTAL = "experimental"  # For experimental improvements


class ImprovementStatus(str, Enum):
    """Status of an improvement."""

    IDENTIFIED = "identified"  # Problem identified
    PROPOSED = "proposed"  # Solution proposed
    PLANNED = "planned"  # Implementation planned
    IN_PROGRESS = "in_progress"  # Implementation in progress
    TESTING = "testing"  # Being tested/validated
    IMPLEMENTED = "implemented"  # Successfully implemented
    REVERTED = "reverted"  # Implemented but reverted
    REJECTED = "rejected"  # Proposed but rejected


@dataclass
class ImprovementSuggestion:
    """A suggestion for improving recommendation quality."""

    suggestion_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    category: ImprovementCategory = ImprovementCategory.ALGORITHM
    priority: ImprovementPriority = ImprovementPriority.MEDIUM
    status: ImprovementStatus = ImprovementStatus.IDENTIFIED
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    algorithm_id: Optional[str] = None
    metric_impacts: Dict[str, float] = field(default_factory=dict)
    estimated_effort: int = 1  # 1-5 scale
    implementation_notes: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)
    owner: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "suggestion_id": self.suggestion_id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "algorithm_id": self.algorithm_id,
            "metric_impacts": self.metric_impacts,
            "estimated_effort": self.estimated_effort,
            "implementation_notes": self.implementation_notes,
            "evidence": self.evidence,
            "owner": self.owner,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ImprovementSuggestion":
        """Create from dictionary representation."""
        try:
            # Convert string enums to enum values
            if "category" in data:
                data["category"] = ImprovementCategory(data["category"])
            if "priority" in data:
                data["priority"] = ImprovementPriority(data["priority"])
            if "status" in data:
                data["status"] = ImprovementStatus(data["status"])

            # Convert timestamp strings to datetime
            if "created_at" in data and isinstance(data["created_at"], str):
                data["created_at"] = datetime.fromisoformat(data["created_at"])
            if "updated_at" in data and isinstance(data["updated_at"], str):
                data["updated_at"] = datetime.fromisoformat(data["updated_at"])

            return cls(**data)
        except (ValueError, TypeError) as e:
            logger.error("Error creating ImprovementSuggestion from dict: %s", e)
            return cls()


@dataclass
class ImplementationResult:
    """Results from implementing an improvement."""

    suggestion_id: str
    implementation_date: datetime = field(default_factory=datetime.now)
    implemented_by: Optional[str] = None
    metric_changes: Dict[str, float] = field(default_factory=dict)
    notes: str = ""
    successful: bool = True
    user_feedback: List[Dict[str, Any]] = field(default_factory=list)
    performance_impact: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "suggestion_id": self.suggestion_id,
            "implementation_date": self.implementation_date.isoformat(),
            "implemented_by": self.implemented_by,
            "metric_changes": self.metric_changes,
            "notes": self.notes,
            "successful": self.successful,
            "user_feedback": self.user_feedback,
            "performance_impact": self.performance_impact,
        }


@dataclass
class FeedbackPattern:
    """A detected pattern in feedback data."""

    pattern_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pattern_type: str = ""
    description: str = ""
    confidence: float = 0.0
    affected_items: List[str] = field(default_factory=list)
    affected_users: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    detected_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "description": self.description,
            "confidence": self.confidence,
            "affected_items": self.affected_items,
            "affected_users": self.affected_users,
            "metrics": self.metrics,
            "detected_at": self.detected_at.isoformat(),
            "metadata": self.metadata,
        }


class ContinuousImprovement:
    """System for continuously improving recommendation quality."""

    def __init__(
        self,
        storage_service=None,
        metrics_service=None,
        tuning_service=None,
        analytics_service=None,
    ):
        self.storage_service = storage_service
        self.metrics_service = metrics_service
        self.tuning_service = tuning_service
        self.analytics_service = analytics_service

        # In-memory caches
        self._suggestions = {}  # suggestion_id -> ImprovementSuggestion
        self._results = {}  # suggestion_id -> ImplementationResult
        self._patterns = []  # List[FeedbackPattern]
        self._issue_counts = defaultdict(int)  # category -> count
        self._algorithm_suggestions = defaultdict(
            list
        )  # algorithm_id -> List[suggestion_id]

    def add_suggestion(self, suggestion: ImprovementSuggestion) -> str:
        """Add a new improvement suggestion."""
        # Store suggestion
        self._suggestions[suggestion.suggestion_id] = suggestion

        # Track by algorithm if applicable
        if suggestion.algorithm_id:
            self._algorithm_suggestions[suggestion.algorithm_id].append(
                suggestion.suggestion_id
            )

        # Track issue counts
        self._issue_counts[suggestion.category] += 1

        # Persist if storage service available
        if self.storage_service:
            self.storage_service.store_improvement_suggestion(suggestion)

        # Track in analytics if available
        if self.analytics_service:
            self.analytics_service.track_event(
                event_type="improvement_suggestion_created",
                properties=suggestion.to_dict(),
            )

        return suggestion.suggestion_id

    def update_suggestion(self, suggestion_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing improvement suggestion."""
        if suggestion_id not in self._suggestions:
            logger.warning("Cannot update unknown suggestion: %s", suggestion_id)
            return bool(False)

        suggestion = self._suggestions[suggestion_id]

        # Apply updates
        for key, value in updates.items():
            if key == "category" and isinstance(value, str):
                try:
                    suggestion.category = ImprovementCategory(value)
                except ValueError:
                    logger.warning("Invalid category: %s", value)
                    continue
            elif key == "priority" and isinstance(value, str):
                try:
                    suggestion.priority = ImprovementPriority(value)
                except ValueError:
                    logger.warning("Invalid priority: %s", value)
                    continue
            elif key == "status" and isinstance(value, str):
                try:
                    suggestion.status = ImprovementStatus(value)
                except ValueError:
                    logger.warning("Invalid status: %s", value)
                    continue
            elif hasattr(suggestion, key):
                setattr(suggestion, key, value)

        # Update timestamp
        suggestion.updated_at = datetime.now()

        # Persist if storage service available
        if self.storage_service:
            self.storage_service.update_improvement_suggestion(suggestion)

        # Track in analytics if available
        if self.analytics_service:
            self.analytics_service.track_event(
                event_type="improvement_suggestion_updated",
                properties=suggestion.to_dict(),
            )

        return True

    def get_suggestion(self, suggestion_id: str) -> Optional[ImprovementSuggestion]:
        """Get an improvement suggestion by ID."""
        return self._suggestions.get(suggestion_id)

    def list_suggestions(
        self,
        category: Optional[Union[ImprovementCategory, str]] = None,
        priority: Optional[Union[ImprovementPriority, str]] = None,
        status: Optional[Union[ImprovementStatus, str]] = None,
        algorithm_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[ImprovementSuggestion]:
        """List improvement suggestions with optional filtering."""
        # Start with all suggestions
        suggestions = list(self._suggestions.values())

        # Filter by category
        if category:
            category_enum = (
                category
                if isinstance(category, ImprovementCategory)
                else ImprovementCategory(category)
            )
            suggestions = [s for s in suggestions if s.category == category_enum]

        # Filter by priority
        if priority:
            priority_enum = (
                priority
                if isinstance(priority, ImprovementPriority)
                else ImprovementPriority(priority)
            )
            suggestions = [s for s in suggestions if s.priority == priority_enum]

        # Filter by status
        if status:
            status_enum = (
                status
                if isinstance(status, ImprovementStatus)
                else ImprovementStatus(status)
            )
            suggestions = [s for s in suggestions if s.status == status_enum]

        # Filter by algorithm
        if algorithm_id:
            suggestions = [s for s in suggestions if s.algorithm_id == algorithm_id]

        # Sort by priority (highest first) and creation date (newest first)
        priority_order = {
            ImprovementPriority.CRITICAL: 0,
            ImprovementPriority.HIGH: 1,
            ImprovementPriority.MEDIUM: 2,
            ImprovementPriority.LOW: 3,
            ImprovementPriority.EXPERIMENTAL: 4,
        }
        suggestions.sort(
            key=lambda s: (priority_order.get(s.priority, 99), s.created_at),
            reverse=True,
        )

        # Apply limit
        return suggestions[:limit]

    def add_implementation_result(self, result: ImplementationResult) -> bool:
        """Add results from implementing an improvement."""
        # Verify suggestion exists
        if result.suggestion_id not in self._suggestions:
            logger.warning(
                "Cannot add result for unknown suggestion: %s", result.suggestion_id
            )
            return bool(False)

        # Store result
        self._results[result.suggestion_id] = result

        # Update suggestion status if successful
        suggestion = self._suggestions[result.suggestion_id]
        if result.successful and suggestion.status != ImprovementStatus.REVERTED:
            suggestion.status = ImprovementStatus.IMPLEMENTED
            suggestion.updated_at = datetime.now()
        elif (
            not result.successful and suggestion.status == ImprovementStatus.IMPLEMENTED
        ):
            suggestion.status = ImprovementStatus.REVERTED
            suggestion.updated_at = datetime.now()

        # Persist if storage service available
        if self.storage_service:
            self.storage_service.store_implementation_result(result)
            if suggestion.status in [
                ImprovementStatus.IMPLEMENTED,
                ImprovementStatus.REVERTED,
            ]:
                self.storage_service.update_improvement_suggestion(suggestion)

        # Track in analytics if available
        if self.analytics_service:
            self.analytics_service.track_event(
                event_type="improvement_implemented",
                properties={**result.to_dict(), "suggestion": suggestion.to_dict()},
            )

        return True

    def add_feedback_pattern(self, pattern: FeedbackPattern) -> str:
        """Add a detected feedback pattern."""
        # Store pattern
        self._patterns.append(pattern)

        # Persist if storage service available
        if self.storage_service:
            self.storage_service.store_feedback_pattern(pattern)

        # Track in analytics if available
        if self.analytics_service:
            self.analytics_service.track_event(
                event_type="feedback_pattern_detected", properties=pattern.to_dict()
            )

        # Generate improvement suggestion based on pattern
        suggestion = self._generate_suggestion_from_pattern(pattern)
        if suggestion:
            self.add_suggestion(suggestion)

        return pattern.pattern_id

    def _generate_suggestion_from_pattern(
        self, pattern: FeedbackPattern
    ) -> Optional[ImprovementSuggestion]:
        """Generate an improvement suggestion based on a feedback pattern."""
        # Skip if not confident enough
        if pattern.confidence < 0.5:
            return None

        # Determine suggestion category based on pattern type
        category_mapping = {
            "low_relevance": ImprovementCategory.RELEVANCE,
            "low_diversity": ImprovementCategory.DIVERSITY,
            "poor_coverage": ImprovementCategory.COVERAGE,
            "algorithm_issue": ImprovementCategory.ALGORITHM,
            "data_issue": ImprovementCategory.DATA,
            "performance_issue": ImprovementCategory.PERFORMANCE,
        }

        category = category_mapping.get(
            pattern.pattern_type, ImprovementCategory.ALGORITHM
        )

        # Determine priority based on confidence and metrics
        priority = ImprovementPriority.MEDIUM
        if pattern.confidence > 0.8:
            priority = ImprovementPriority.HIGH
        if pattern.confidence > 0.9:
            priority = ImprovementPriority.CRITICAL

        # Create suggestion
        suggestion = ImprovementSuggestion(
            title=f"Address {pattern.pattern_type} issue",
            description=pattern.description,
            category=category,
            priority=priority,
            evidence={
                "pattern_id": pattern.pattern_id,
                "confidence": pattern.confidence,
                "affected_items": pattern.affected_items[:10],  # Include first 10 items
                "affected_users": pattern.affected_users[:10],  # Include first 10 users
                "metrics": pattern.metrics,
            },
        )

        return suggestion

    def generate_improvement_plan(
        self, algorithm_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a prioritized improvement plan."""
        # Get relevant suggestions
        if algorithm_id:
            suggestion_ids = self._algorithm_suggestions.get(algorithm_id, [])
            suggestions = [
                self._suggestions[sid]
                for sid in suggestion_ids
                if sid in self._suggestions
            ]
        else:
            suggestions = list(self._suggestions.values())

        # Filter to open suggestions
        open_statuses = [
            ImprovementStatus.IDENTIFIED,
            ImprovementStatus.PROPOSED,
            ImprovementStatus.PLANNED,
        ]
        open_suggestions = [s for s in suggestions if s.status in open_statuses]

        # Group by priority
        priority_groups = defaultdict(list)
        for suggestion in open_suggestions:
            priority_groups[suggestion.priority].append(suggestion.to_dict())

        # Arrange into plan
        plan = {
            "algorithm_id": algorithm_id,
            "generated_at": datetime.now().isoformat(),
            "priority_groups": {
                ImprovementPriority.CRITICAL.value: priority_groups[
                    ImprovementPriority.CRITICAL
                ],
                ImprovementPriority.HIGH.value: priority_groups[
                    ImprovementPriority.HIGH
                ],
                ImprovementPriority.MEDIUM.value: priority_groups[
                    ImprovementPriority.MEDIUM
                ],
                ImprovementPriority.LOW.value: priority_groups[ImprovementPriority.LOW],
                ImprovementPriority.EXPERIMENTAL.value: priority_groups[
                    ImprovementPriority.EXPERIMENTAL
                ],
            },
            "summary": {
                "total_suggestions": len(open_suggestions),
                "critical_count": len(priority_groups[ImprovementPriority.CRITICAL]),
                "high_count": len(priority_groups[ImprovementPriority.HIGH]),
                "medium_count": len(priority_groups[ImprovementPriority.MEDIUM]),
                "low_count": len(priority_groups[ImprovementPriority.LOW]),
                "experimental_count": len(
                    priority_groups[ImprovementPriority.EXPERIMENTAL]
                ),
            },
        }

        return plan

    def analyze_feedback_data(
        self,
        feedback_events: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]],
        algorithm_id: Optional[str] = None,
    ) -> List[FeedbackPattern]:
        """Analyze feedback data to detect patterns."""
        detected_patterns = []

        # Skip if not enough data
        if len(feedback_events) < 10 or len(recommendations) < 10:
            return detected_patterns

        # Detect low relevance pattern
        low_relevance_pattern = self._detect_low_relevance_pattern(
            feedback_events=feedback_events,
            recommendations=recommendations,
            algorithm_id=algorithm_id,
        )
        if low_relevance_pattern:
            detected_patterns.append(low_relevance_pattern)

        # Detect low diversity pattern
        low_diversity_pattern = self._detect_low_diversity_pattern(
            recommendations=recommendations, algorithm_id=algorithm_id
        )
        if low_diversity_pattern:
            detected_patterns.append(low_diversity_pattern)

        # Detect poor coverage pattern
        poor_coverage_pattern = self._detect_poor_coverage_pattern(
            recommendations=recommendations,
            feedback_events=feedback_events,
            algorithm_id=algorithm_id,
        )
        if poor_coverage_pattern:
            detected_patterns.append(poor_coverage_pattern)

        # Add all detected patterns
        for pattern in detected_patterns:
            self.add_feedback_pattern(pattern)

        return detected_patterns

    def _detect_low_relevance_pattern(
        self,
        feedback_events: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]],
        algorithm_id: Optional[str] = None,
    ) -> Optional[FeedbackPattern]:
        """Detect pattern of low relevance in recommendations."""
        # Extract click/view/conversion events
        clicks = [e for e in feedback_events if e.get("type") == "click"]
        purchases = [e for e in feedback_events if e.get("type") == "purchase"]

        # Calculate metrics
        ctr = len(clicks) / len(recommendations) if recommendations else 0
        conversion_rate = (
            len(purchases) / len(recommendations) if recommendations else 0
        )

        # Check if metrics indicate low relevance
        low_relevance = ctr < 0.1 and conversion_rate < 0.01

        if not low_relevance:
            return None

        # Find items with particularly low engagement
        item_engagement = defaultdict(int)
        for event in feedback_events:
            if event.get("type") in ["click", "view", "purchase"]:
                item_id = event.get("item_id")
                if item_id:
                    item_engagement[item_id] += 1

        # Identify items with zero or very low engagement
        low_engagement_items = [
            item_id for item_id, count in item_engagement.items() if count <= 1
        ]

        # Find users with low engagement
        user_engagement = defaultdict(int)
        for event in feedback_events:
            if event.get("type") in ["click", "view", "purchase"]:
                user_id = event.get("user_id")
                if user_id:
                    user_engagement[user_id] += 1

        # Identify users with low engagement
        low_engagement_users = [
            user_id for user_id, count in user_engagement.items() if count <= 1
        ]

        # Create pattern
        pattern = FeedbackPattern(
            pattern_type="low_relevance",
            description="Recommendations have low relevance based on engagement metrics",
            confidence=0.7,
            affected_items=low_engagement_items[:100],  # Limit to 100 items
            affected_users=low_engagement_users[:100],  # Limit to 100 users
            metrics={"ctr": ctr, "conversion_rate": conversion_rate},
            metadata={"algorithm_id": algorithm_id},
        )

        return pattern

    def _detect_low_diversity_pattern(
        self, recommendations: List[Dict[str, Any]], algorithm_id: Optional[str] = None
    ) -> Optional[FeedbackPattern]:
        """Detect pattern of low diversity in recommendations."""
        # Extract categories
        categories = [r.get("category") for r in recommendations if "category" in r]
        if not categories:
            return None

        # Calculate category diversity
        unique_categories = len(set(categories))
        category_diversity = unique_categories / len(categories) if categories else 0

        # Check if metrics indicate low diversity
        low_diversity = category_diversity < 0.3

        if not low_diversity:
            return None

        # Count occurrences of each category
        category_counts = Counter(categories)

        # Find over-represented categories
        total_items = len(categories)
        overrepresented = [
            cat for cat, count in category_counts.items() if count / total_items > 0.4
        ]  # More than 40% of recommendations

        # Create pattern
        pattern = FeedbackPattern(
            pattern_type="low_diversity",
            description="Recommendations lack diversity across categories",
            confidence=0.8,
            affected_items=[],  # No specific items for this pattern
            affected_users=[],  # No specific users for this pattern
            metrics={
                "category_diversity": category_diversity,
                "unique_categories": unique_categories,
                "total_categories": len(categories),
            },
            metadata={
                "algorithm_id": algorithm_id,
                "overrepresented_categories": overrepresented,
            },
        )

        return pattern

    def _detect_poor_coverage_pattern(
        self,
        recommendations: List[Dict[str, Any]],
        feedback_events: List[Dict[str, Any]],
        algorithm_id: Optional[str] = None,
    ) -> Optional[FeedbackPattern]:
        """Detect pattern of poor item coverage in recommendations."""
        # Extract unique item IDs from recommendations
        recommended_items = set(r.get("id") for r in recommendations if "id" in r)

        # Extract items with positive interaction
        engaged_items = set()
        for event in feedback_events:
            if event.get("type") in ["click", "purchase", "like", "save"]:
                item_id = event.get("item_id")
                if item_id:
                    engaged_items.add(item_id)

        # Calculate metrics
        coverage_ratio = (
            len(recommended_items) / 1000
        )  # Assuming catalog of ~1000 items
        engagement_diversity = (
            len(engaged_items) / len(recommended_items) if recommended_items else 0
        )

        # Check if metrics indicate poor coverage
        poor_coverage = coverage_ratio < 0.2 or engagement_diversity < 0.1

        if not poor_coverage:
            return None

        # Create pattern
        pattern = FeedbackPattern(
            pattern_type="poor_coverage",
            description="Recommendations only cover a small portion of available items",
            confidence=0.7,
            affected_items=list(recommended_items)[:100],  # Limit to 100 items
            affected_users=[],  # No specific users for this pattern
            metrics={
                "coverage_ratio": coverage_ratio,
                "engagement_diversity": engagement_diversity,
                "unique_items_recommended": len(recommended_items),
                "unique_items_engaged": len(engaged_items),
            },
            metadata={"algorithm_id": algorithm_id},
        )

        return pattern


# Helper functions for creating common improvement suggestions


def create_algorithm_tuning_suggestion(
    algorithm_id: str,
    parameter_name: str,
    current_value: Any,
    suggested_value: Any,
    metric_impacts: Dict[str, float],
    improvement_service: Optional[ContinuousImprovement] = None,
) -> ImprovementSuggestion:
    """Create an algorithm tuning suggestion."""
    suggestion = ImprovementSuggestion(
        title=f"Tune {parameter_name} parameter for {algorithm_id}",
        description=f"Change {parameter_name} from {current_value} to {suggested_value} to improve algorithm performance",
        category=ImprovementCategory.ALGORITHM,
        priority=ImprovementPriority.MEDIUM,
        algorithm_id=algorithm_id,
        metric_impacts=metric_impacts,
        estimated_effort=2,
        implementation_notes=f"Update the {parameter_name} parameter in the algorithm configuration",
    )

    # Add to improvement service if provided
    if improvement_service:
        improvement_service.add_suggestion(suggestion)

    return suggestion


def create_diversity_improvement_suggestion(
    algorithm_id: str,
    confidence: float = 0.7,
    improvement_service: Optional[ContinuousImprovement] = None,
) -> ImprovementSuggestion:
    """Create a diversity improvement suggestion."""
    suggestion = ImprovementSuggestion(
        title=f"Increase diversity for {algorithm_id}",
        description="Add diversity boost to recommendations to ensure broader category coverage",
        category=ImprovementCategory.DIVERSITY,
        priority=ImprovementPriority.MEDIUM,
        algorithm_id=algorithm_id,
        metric_impacts={
            "category_diversity": 0.15,
            "user_satisfaction": 0.08,
            "ctr": -0.02,  # Might slightly decrease CTR while improving long-term metrics
        },
        estimated_effort=3,
        implementation_notes="Implement a post-processing step that re-ranks recommendations to increase diversity",
    )

    # Set priority based on confidence
    if confidence > 0.8:
        suggestion.priority = ImprovementPriority.HIGH
    if confidence > 0.9:
        suggestion.priority = ImprovementPriority.CRITICAL

    # Add to improvement service if provided
    if improvement_service:
        improvement_service.add_suggestion(suggestion)

    return suggestion


def create_data_quality_suggestion(
    feature_name: str,
    description: str,
    algorithm_id: Optional[str] = None,
    improvement_service: Optional[ContinuousImprovement] = None,
) -> ImprovementSuggestion:
    """Create a data quality improvement suggestion."""
    suggestion = ImprovementSuggestion(
        title=f"Improve {feature_name} data quality",
        description=description,
        category=ImprovementCategory.DATA,
        priority=ImprovementPriority.HIGH,
        algorithm_id=algorithm_id,
        metric_impacts={"relevance": 0.1, "prediction_accuracy": 0.12},
        estimated_effort=4,
        implementation_notes=f"Implement data cleaning and validation for {feature_name}",
    )

    # Add to improvement service if provided
    if improvement_service:
        improvement_service.add_suggestion(suggestion)

    return suggestion


def create_coverage_improvement_suggestion(
    algorithm_id: str, improvement_service: Optional[ContinuousImprovement] = None
) -> ImprovementSuggestion:
    """Create a coverage improvement suggestion."""
    suggestion = ImprovementSuggestion(
        title=f"Improve item coverage for {algorithm_id}",
        description="Add exploration component to increase coverage of the item catalog",
        category=ImprovementCategory.COVERAGE,
        priority=ImprovementPriority.MEDIUM,
        algorithm_id=algorithm_id,
        metric_impacts={
            "coverage_ratio": 0.2,
            "long_term_engagement": 0.1,
            "serendipity": 0.15,
        },
        estimated_effort=3,
        implementation_notes="Implement epsilon-greedy exploration or similar technique",
    )

    # Add to improvement service if provided
    if improvement_service:
        improvement_service.add_suggestion(suggestion)

    return suggestion


def create_feature_addition_suggestion(
    feature_name: str,
    description: str,
    algorithm_id: Optional[str] = None,
    improvement_service: Optional[ContinuousImprovement] = None,
) -> ImprovementSuggestion:
    """Create a suggestion to add a new feature to the recommender."""
    suggestion = ImprovementSuggestion(
        title=f"Add {feature_name} feature to recommendations",
        description=description,
        category=ImprovementCategory.FEATURE,
        priority=ImprovementPriority.MEDIUM,
        algorithm_id=algorithm_id,
        metric_impacts={"relevance": 0.08, "user_satisfaction": 0.1},
        estimated_effort=4,
        implementation_notes=f"Implement {feature_name} feature extraction and add to model",
    )

    # Add to improvement service if provided
    if improvement_service:
        improvement_service.add_suggestion(suggestion)

    return suggestion
