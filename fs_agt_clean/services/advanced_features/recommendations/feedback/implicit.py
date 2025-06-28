#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Implicit Recommendation Feedback Tracking

This module handles the collection and processing of implicit feedback for
recommendations, such as clicks, view time, purchases, and other user behaviors
that indirectly indicate preference.

It includes:
1. Event tracking for implicit user actions
2. Signal extraction from behavioral data
3. Confidence scoring for implicit feedback
4. Integration with recommendation algorithms
5. Real-time feedback processing
"""

import json
import logging
import math
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from fs_agt_clean.core.models.api_response import ApiResponse
from fs_agt_clean.core.types import FeedbackEvent, JsonDict

logger = logging.getLogger(__name__)


class ImplicitSignalType(str, Enum):
    """Types of implicit signals that can be tracked."""

    VIEW = "view"  # UnifiedUser viewed the recommendation
    CLICK = "click"  # UnifiedUser clicked the recommendation
    ADD_TO_CART = "add_to_cart"  # UnifiedUser added to cart
    PURCHASE = "purchase"  # UnifiedUser purchased the item
    SHARE = "share"  # UnifiedUser shared the item
    BOOKMARK = "bookmark"  # UnifiedUser bookmarked/saved the item
    EXTENDED_VIEW = "extended_view"  # UnifiedUser viewed for an extended time
    REPEAT_VIEW = "repeat_view"  # UnifiedUser viewed multiple times
    SEARCH = "search"  # UnifiedUser searched for the item
    COMPARISON = "comparison"  # UnifiedUser compared with other items
    INTERACTION = "interaction"  # General interaction with the item


class ImplicitSignalStrength(str, Enum):
    """Strength classifications for implicit signals."""

    VERY_WEAK = "very_weak"  # Minimal indication
    WEAK = "weak"  # Slight indication
    MODERATE = "moderate"  # Moderate indication
    STRONG = "strong"  # Strong indication
    VERY_STRONG = "very_strong"  # Very strong indication


class ImplicitSignalTemporality(str, Enum):
    """Temporal classifications for implicit signals."""

    IMMEDIATE = "immediate"  # Immediate reaction
    SHORT_TERM = "short_term"  # Short-term interest
    MEDIUM_TERM = "medium_term"  # Medium-term interest
    LONG_TERM = "long_term"  # Long-term interest
    PERSISTENT = "persistent"  # Persistent interest


@dataclass
class ImplicitSignalWeights:
    """Default weights for different implicit signal types."""

    view: float = 0.1
    click: float = 0.3
    add_to_cart: float = 0.5
    purchase: float = 1.0
    share: float = 0.7
    bookmark: float = 0.6
    extended_view: float = 0.4
    repeat_view: float = 0.5
    search: float = 0.4
    comparison: float = 0.3
    interaction: float = 0.2

    def get_weight(self, signal_type: ImplicitSignalType) -> float:
        """Get the weight for a specific signal type."""
        weights = {
            ImplicitSignalType.VIEW: self.view,
            ImplicitSignalType.CLICK: self.click,
            ImplicitSignalType.ADD_TO_CART: self.add_to_cart,
            ImplicitSignalType.PURCHASE: self.purchase,
            ImplicitSignalType.SHARE: self.share,
            ImplicitSignalType.BOOKMARK: self.bookmark,
            ImplicitSignalType.EXTENDED_VIEW: self.extended_view,
            ImplicitSignalType.REPEAT_VIEW: self.repeat_view,
            ImplicitSignalType.SEARCH: self.search,
            ImplicitSignalType.COMPARISON: self.comparison,
            ImplicitSignalType.INTERACTION: self.interaction,
        }
        return weights.get(signal_type, 0.1)


@dataclass
class ImplicitFeedbackConfig:
    """Configuration for implicit feedback processing."""

    enabled: bool = True
    weights: ImplicitSignalWeights = field(default_factory=ImplicitSignalWeights)
    min_confidence: float = 0.1
    recency_decay_factor: float = 0.5
    recency_half_life_days: int = 30
    session_timeout_minutes: int = 30
    extended_view_threshold_seconds: int = 10
    repeat_view_threshold: int = 3
    enable_real_time_processing: bool = True
    batch_processing_interval_minutes: int = 60
    min_events_for_batch_processing: int = 100
    correlation_window_days: int = 7
    maximum_signal_strength: float = 10.0
    enable_negative_feedback: bool = True
    negative_feedback_threshold: float = -0.3
    context_weight_factor: float = 1.2


@dataclass
class ImplicitSignal:
    """Represents a processed implicit feedback signal."""

    signal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    product_id: str = ""
    recommendation_id: Optional[str] = None
    signal_type: ImplicitSignalType = ImplicitSignalType.VIEW
    timestamp: datetime = field(default_factory=datetime.now)
    strength: float = 0.0
    confidence: float = 0.0
    context: Dict[str, Any] = field(default_factory=dict)
    temporality: ImplicitSignalTemporality = ImplicitSignalTemporality.IMMEDIATE
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "signal_id": self.signal_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "product_id": self.product_id,
            "recommendation_id": self.recommendation_id,
            "signal_type": self.signal_type.value,
            "timestamp": self.timestamp.isoformat(),
            "strength": self.strength,
            "confidence": self.confidence,
            "context": self.context,
            "temporality": self.temporality.value,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class UnifiedUserImplicitProfile:
    """UnifiedUser profile based on implicit feedback signals."""

    user_id: str
    last_updated: datetime = field(default_factory=datetime.now)
    product_affinities: Dict[str, float] = field(default_factory=dict)
    category_affinities: Dict[str, float] = field(default_factory=dict)
    feature_preferences: Dict[str, float] = field(default_factory=dict)
    price_sensitivity: float = 0.5
    brand_affinities: Dict[str, float] = field(default_factory=dict)
    seasonal_preferences: Dict[str, float] = field(default_factory=dict)
    session_history: List[Dict[str, Any]] = field(default_factory=list)
    signal_counts: Dict[str, int] = field(default_factory=dict)
    negative_preferences: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "user_id": self.user_id,
            "last_updated": self.last_updated.isoformat(),
            "product_affinities": self.product_affinities,
            "category_affinities": self.category_affinities,
            "feature_preferences": self.feature_preferences,
            "price_sensitivity": self.price_sensitivity,
            "brand_affinities": self.brand_affinities,
            "seasonal_preferences": self.seasonal_preferences,
            "session_count": len(self.session_history),
            "signal_counts": self.signal_counts,
            "negative_preferences": list(self.negative_preferences),
        }


class ImplicitFeedbackProcessor:
    """Processes implicit feedback signals from user interactions."""

    def __init__(
        self,
        config: Optional[ImplicitFeedbackConfig] = None,
        storage_service=None,
        analytics_service=None,
    ):
        self.config = config or ImplicitFeedbackConfig()
        self.storage_service = storage_service
        self.analytics_service = analytics_service

        # In-memory caches
        self._session_events = defaultdict(list)
        self._user_profiles = {}
        self._recent_signals = []
        self._product_metadata = {}

    def track_event(
        self,
        signal_type: Union[ImplicitSignalType, str],
        product_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        recommendation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ImplicitSignal:
        """Track an implicit feedback event."""
        if isinstance(signal_type, str):
            try:
                signal_type = ImplicitSignalType(signal_type)
            except ValueError:
                signal_type = ImplicitSignalType.INTERACTION

        # Create raw signal
        signal = ImplicitSignal(
            user_id=user_id,
            session_id=session_id,
            product_id=product_id,
            recommendation_id=recommendation_id,
            signal_type=signal_type,
            context=context or {},
            metadata=metadata or {},
        )

        # Process the signal
        processed_signal = self._process_signal(signal)

        # Store in session events
        if session_id:
            self._session_events[session_id].append(processed_signal)

        # Update user profile
        if user_id:
            self._update_user_profile(user_id, processed_signal)

        # Track in analytics if available
        if self.analytics_service:
            self.analytics_service.track_event(
                event_type="implicit_feedback", properties=processed_signal.to_dict()
            )

        # Store signal if storage service available
        if self.storage_service:
            self.storage_service.store_signal(processed_signal)

        # Add to recent signals for real-time processing
        self._recent_signals.append(processed_signal)

        # Process in real-time if enabled
        if self.config.enable_real_time_processing:
            self._process_real_time_signals()

        return processed_signal

    def _process_signal(self, signal: ImplicitSignal) -> ImplicitSignal:
        """Process a raw signal to compute strength, confidence, etc."""
        # Get base weight for signal type
        base_weight = self.config.weights.get_weight(signal.signal_type)

        # Apply context-based adjustments
        context_multiplier = 1.0
        if "source" in signal.context:
            if signal.context["source"] == "search":
                context_multiplier *= 1.2
            elif signal.context["source"] == "direct_link":
                context_multiplier *= 0.8

        if "device" in signal.context:
            if signal.context["device"] == "mobile":
                context_multiplier *= 0.9  # Mobile clicks may be more accidental

        # Apply session history adjustments if available
        session_multiplier = 1.0
        if signal.session_id and signal.session_id in self._session_events:
            session_events = self._session_events[signal.session_id]

            # Check for repeated views
            view_count = sum(
                1
                for e in session_events
                if e.product_id == signal.product_id
                and e.signal_type == ImplicitSignalType.VIEW
            )

            if view_count >= self.config.repeat_view_threshold:
                signal.signal_type = ImplicitSignalType.REPEAT_VIEW
                base_weight = self.config.weights.get_weight(
                    ImplicitSignalType.REPEAT_VIEW
                )
                session_multiplier *= 1.1

            # Check for extended views (time based)
            if signal.signal_type == ImplicitSignalType.VIEW and signal.metadata.get(
                "view_time_seconds"
            ):
                view_time = signal.metadata.get("view_time_seconds", 0)
                if view_time > self.config.extended_view_threshold_seconds:
                    signal.signal_type = ImplicitSignalType.EXTENDED_VIEW
                    base_weight = self.config.weights.get_weight(
                        ImplicitSignalType.EXTENDED_VIEW
                    )
                    # Scale weight by view time
                    session_multiplier *= min(
                        2.0, view_time / self.config.extended_view_threshold_seconds
                    )

        # Calculate final strength
        strength = base_weight * context_multiplier * session_multiplier
        strength = min(strength, self.config.maximum_signal_strength)

        # Determine temporality
        temporality = ImplicitSignalTemporality.IMMEDIATE
        if signal.signal_type in [
            ImplicitSignalType.PURCHASE,
            ImplicitSignalType.BOOKMARK,
        ]:
            temporality = ImplicitSignalTemporality.LONG_TERM
        elif signal.signal_type in [
            ImplicitSignalType.REPEAT_VIEW,
            ImplicitSignalType.EXTENDED_VIEW,
        ]:
            temporality = ImplicitSignalTemporality.MEDIUM_TERM
        elif signal.signal_type == ImplicitSignalType.CLICK:
            temporality = ImplicitSignalTemporality.SHORT_TERM

        # Calculate confidence
        confidence = 0.5  # Base confidence

        # Adjust confidence based on signal type
        if signal.signal_type == ImplicitSignalType.PURCHASE:
            confidence = 0.9
        elif signal.signal_type == ImplicitSignalType.ADD_TO_CART:
            confidence = 0.7
        elif signal.signal_type in [
            ImplicitSignalType.EXTENDED_VIEW,
            ImplicitSignalType.REPEAT_VIEW,
        ]:
            confidence = 0.6
        elif signal.signal_type == ImplicitSignalType.CLICK:
            confidence = 0.5
        elif signal.signal_type == ImplicitSignalType.VIEW:
            confidence = 0.3

        # Adjust confidence by context quality
        if len(signal.context) > 2:
            confidence *= 1.1

        # Set processed attributes
        signal.strength = strength
        signal.confidence = min(1.0, confidence)
        signal.temporality = temporality

        return signal

    def _update_user_profile(self, user_id: str, signal: ImplicitSignal) -> None:
        """Update a user's implicit profile with a new signal."""
        # Get or create user profile
        profile = self._user_profiles.get(user_id)
        if not profile:
            profile = UnifiedUserImplicitProfile(user_id=user_id)
            self._user_profiles[user_id] = profile

        # Update last updated timestamp
        profile.last_updated = datetime.now()

        # Update product affinity
        current_affinity = profile.product_affinities.get(signal.product_id, 0.0)

        # Apply temporal decay to previous affinity
        days_since_update = 0
        if "last_updated_for_product" in profile.metadata:
            last_product_update = profile.metadata.get(
                "last_updated_for_product", {}
            ).get(signal.product_id)
            if last_product_update:
                last_update_date = datetime.fromisoformat(last_product_update)
                days_since_update = (datetime.now() - last_update_date).days

        if days_since_update > 0:
            decay_factor = math.pow(
                0.5, days_since_update / self.config.recency_half_life_days
            )
            current_affinity *= decay_factor

        # Update with new signal
        product_affinity = current_affinity + (signal.strength * signal.confidence)

        # Apply negative feedback if enabled
        if self.config.enable_negative_feedback and signal.strength < 0:
            if product_affinity < self.config.negative_feedback_threshold:
                profile.negative_preferences.add(signal.product_id)

        profile.product_affinities[signal.product_id] = product_affinity

        # Update category affinities if available
        if "category" in signal.metadata and signal.metadata["category"]:
            category = signal.metadata["category"]
            current_cat_affinity = profile.category_affinities.get(category, 0.0)
            profile.category_affinities[category] = current_cat_affinity + (
                signal.strength * signal.confidence * 0.5
            )

        # Update feature preferences if available
        if "features" in signal.metadata and signal.metadata["features"]:
            for feature in signal.metadata["features"]:
                current_feature_pref = profile.feature_preferences.get(feature, 0.0)
                profile.feature_preferences[feature] = current_feature_pref + (
                    signal.strength * signal.confidence * 0.3
                )

        # Update brand affinities if available
        if "brand" in signal.metadata and signal.metadata["brand"]:
            brand = signal.metadata["brand"]
            current_brand_affinity = profile.brand_affinities.get(brand, 0.0)
            profile.brand_affinities[brand] = current_brand_affinity + (
                signal.strength * signal.confidence * 0.4
            )

        # Update signal counts
        profile.signal_counts[signal.signal_type.value] = (
            profile.signal_counts.get(signal.signal_type.value, 0) + 1
        )

        # Track last update for this product
        if "last_updated_for_product" not in profile.metadata:
            profile.metadata["last_updated_for_product"] = {}
        profile.metadata["last_updated_for_product"][
            signal.product_id
        ] = datetime.now().isoformat()

        # Persist user profile if storage service available
        if self.storage_service:
            self.storage_service.update_user_profile(profile)

    def _process_real_time_signals(self) -> None:
        """Process recent signals in real-time."""
        if not self._recent_signals:
            return

        # Only process signals from the last minute to avoid duplicate processing
        cutoff_time = datetime.now() - timedelta(minutes=1)
        recent_signals = [s for s in self._recent_signals if s.timestamp > cutoff_time]

        if not recent_signals:
            return

        # TODO: Implement real-time signal processing logic
        # This could include:
        # - Detecting trending products
        # - Identifying correlated products
        # - Updating recommendation scores in real-time

        # Clean up processed signals
        self._recent_signals = [
            s for s in self._recent_signals if s.timestamp > cutoff_time
        ]

    def get_user_affinities(self, user_id: str) -> Dict[str, float]:
        """Get product affinities for a user."""
        profile = self._user_profiles.get(user_id)
        if not profile:
            # Try to load from storage
            if self.storage_service:
                profile_data = self.storage_service.get_user_profile(user_id)
                if profile_data:
                    profile = UnifiedUserImplicitProfile(**profile_data)
                    self._user_profiles[user_id] = profile

        if not profile:
            return {}

        return profile.product_affinities

    def get_user_category_affinities(self, user_id: str) -> Dict[str, float]:
        """Get category affinities for a user."""
        profile = self._user_profiles.get(user_id)
        if not profile and self.storage_service:
            profile_data = self.storage_service.get_user_profile(user_id)
            if profile_data:
                profile = UnifiedUserImplicitProfile(**profile_data)
                self._user_profiles[user_id] = profile

        if not profile:
            return {}

        return profile.category_affinities

    def get_user_profile(self, user_id: str) -> Optional[UnifiedUserImplicitProfile]:
        """Get the full implicit profile for a user."""
        profile = self._user_profiles.get(user_id)
        if not profile and self.storage_service:
            profile_data = self.storage_service.get_user_profile(user_id)
            if profile_data:
                profile = UnifiedUserImplicitProfile(**profile_data)
                self._user_profiles[user_id] = profile

        return profile

    def clear_session(self, session_id: str) -> None:
        """Clear session data when a session ends."""
        if session_id in self._session_events:
            del self._session_events[session_id]

    def generate_pseudonymous_profile(self, session_id: str) -> Dict[str, Any]:
        """Generate a profile for a session without a user ID."""
        if session_id not in self._session_events:
            return {}

        session_events = self._session_events[session_id]

        product_affinities = defaultdict(float)
        category_affinities = defaultdict(float)

        for signal in session_events:
            # Add product affinity
            product_affinities[signal.product_id] += signal.strength * signal.confidence

            # Add category affinity if available
            if "category" in signal.metadata and signal.metadata["category"]:
                category = signal.metadata["category"]
                category_affinities[category] += (
                    signal.strength * signal.confidence * 0.5
                )

        return {
            "session_id": session_id,
            "last_updated": datetime.now().isoformat(),
            "product_affinities": dict(product_affinities),
            "category_affinities": dict(category_affinities),
            "signal_count": len(session_events),
        }

    def run_batch_processing(self) -> Dict[str, Any]:
        """Run batch processing on accumulated signals."""
        # This would typically be called by a scheduled job

        # Skip if not enough signals
        if len(self._recent_signals) < self.config.min_events_for_batch_processing:
            return {"processed": False, "reason": "insufficient_signals"}

        # TODO: Implement batch processing logic
        # This could include:
        # - Finding correlated products across users
        # - Updating global popularity metrics
        # - Generating cross-recommendation rules

        result = {
            "processed": True,
            "signals_processed": len(self._recent_signals),
            "timestamp": datetime.now().isoformat(),
        }

        # Clear processed signals
        self._recent_signals = []

        return result

    def reset(self) -> None:
        """Reset the processor state - primarily used for testing."""
        self._session_events.clear()
        self._user_profiles.clear()
        self._recent_signals.clear()


# Helper functions


def track_product_view(
    product_id: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    view_time_seconds: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
    processor: Optional[ImplicitFeedbackProcessor] = None,
) -> ImplicitSignal:
    """Track a product view event."""
    if processor is None:
        processor = ImplicitFeedbackProcessor()

    metadata = metadata or {}
    if view_time_seconds is not None:
        metadata["view_time_seconds"] = view_time_seconds

    return processor.track_event(
        signal_type=ImplicitSignalType.VIEW,
        product_id=product_id,
        user_id=user_id,
        session_id=session_id,
        metadata=metadata,
    )


def track_product_click(
    product_id: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    recommendation_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    processor: Optional[ImplicitFeedbackProcessor] = None,
) -> ImplicitSignal:
    """Track a product click event."""
    if processor is None:
        processor = ImplicitFeedbackProcessor()

    return processor.track_event(
        signal_type=ImplicitSignalType.CLICK,
        product_id=product_id,
        user_id=user_id,
        session_id=session_id,
        recommendation_id=recommendation_id,
        metadata=metadata,
    )


def track_product_purchase(
    product_id: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    processor: Optional[ImplicitFeedbackProcessor] = None,
) -> ImplicitSignal:
    """Track a product purchase event."""
    if processor is None:
        processor = ImplicitFeedbackProcessor()

    return processor.track_event(
        signal_type=ImplicitSignalType.PURCHASE,
        product_id=product_id,
        user_id=user_id,
        session_id=session_id,
        metadata=metadata,
    )
