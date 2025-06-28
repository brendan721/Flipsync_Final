#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Recommendation Feedback UI

This module provides components for collecting explicit user feedback on
recommendations through various UI elements and interfaces.

It includes:
1. Feedback collection UI components (buttons, sliders, etc.)
2. Feedback display widgets and visualizations
3. A/B testing integrations for feedback UI
4. Event tracking for feedback interactions
5. Analytics dashboard components for feedback metrics
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from fs_agt_clean.core.models.api_response import ApiResponse
from fs_agt_clean.core.types import FeedbackEvent, JsonDict

logger = logging.getLogger(__name__)


class FeedbackType(str, Enum):
    """Types of feedback that can be collected from users."""

    LIKE = "like"  # Simple like/positive indicator
    DISLIKE = "dislike"  # Simple dislike/negative indicator
    RATING = "rating"  # Numerical rating (e.g., 1-5 stars)
    HELPFUL = "helpful"  # Helpfulness indicator
    NOT_HELPFUL = "not_helpful"  # Not helpful indicator
    HIDE = "hide"  # Request to hide this recommendation
    SAVE = "save"  # Save/bookmark this recommendation
    CLICKED = "clicked"  # UnifiedUser clicked on the recommendation
    PURCHASED = "purchased"  # UnifiedUser purchased the recommended item
    CUSTOM = "custom"  # Custom feedback with additional data


class FeedbackUIStyle(str, Enum):
    """Styles for feedback UI elements."""

    MINIMAL = "minimal"  # Simple, unobtrusive buttons
    STANDARD = "standard"  # Standard-sized UI elements
    PROMINENT = "prominent"  # More visible, attention-grabbing
    EMBEDDED = "embedded"  # Embedded within recommendation display
    MODAL = "modal"  # Shows in a modal dialog
    INLINE = "inline"  # Inline with the content
    CUSTOM = "custom"  # Custom styling


@dataclass
class FeedbackUIConfig:
    """Configuration for feedback UI elements."""

    feedback_types: List[FeedbackType] = field(
        default_factory=lambda: [FeedbackType.LIKE, FeedbackType.DISLIKE]
    )
    style: FeedbackUIStyle = FeedbackUIStyle.STANDARD
    prompt_text: str = "Was this recommendation helpful?"
    thank_you_text: str = "Thank you for your feedback!"
    show_aggregate_stats: bool = False
    allow_comments: bool = False
    comment_placeholder: str = "Tell us why..."
    position: str = "bottom"  # top, bottom, left, right
    display_timeout_ms: int = 0  # 0 = no timeout
    custom_css: Optional[Dict[str, str]] = None
    enable_analytics: bool = True
    ab_test_enabled: bool = False
    ab_test_variants: List[str] = field(default_factory=list)
    require_authentication: bool = False
    locale: str = "en-US"


@dataclass
class FeedbackUIComponent:
    """Base class for feedback UI components."""

    component_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    component_type: str = "base"
    config: FeedbackUIConfig = field(default_factory=FeedbackUIConfig)
    parent_id: Optional[str] = None
    recommendation_id: Optional[str] = None
    product_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert component to dictionary representation for rendering."""
        return {
            "id": self.component_id,
            "type": self.component_type,
            "config": {
                "feedback_types": [ft.value for ft in self.config.feedback_types],
                "style": self.config.style.value,
                "prompt_text": self.config.prompt_text,
                "thank_you_text": self.config.thank_you_text,
                "show_aggregate_stats": self.config.show_aggregate_stats,
                "allow_comments": self.config.allow_comments,
                "comment_placeholder": self.config.comment_placeholder,
                "position": self.config.position,
                "display_timeout_ms": self.config.display_timeout_ms,
                "custom_css": self.config.custom_css,
                "enable_analytics": self.config.enable_analytics,
                "locale": self.config.locale,
            },
            "parent_id": self.parent_id,
            "recommendation_id": self.recommendation_id,
            "product_id": self.product_id,
            "created_at": self.created_at.isoformat(),
        }

    def to_json(self) -> str:
        """Convert component to JSON string."""
        return json.dumps(self.to_dict())


class ButtonGroupComponent(FeedbackUIComponent):
    """Button group component for collecting binary or multi-option feedback."""

    def __init__(self, feedback_types: List[FeedbackType] = None, **kwargs):
        super().__init__(component_type="button_group", **kwargs)
        if feedback_types:
            self.config.feedback_types = feedback_types


class RatingComponent(FeedbackUIComponent):
    """Star or numerical rating component."""

    def __init__(self, max_rating: int = 5, initial_rating: int = 0, **kwargs):
        super().__init__(component_type="rating", **kwargs)
        self.max_rating = max_rating
        self.initial_rating = initial_rating

    def to_dict(self) -> Dict[str, Any]:
        """Convert component to dictionary representation."""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "max_rating": self.max_rating,
                "initial_rating": self.initial_rating,
            }
        )
        return base_dict


class CommentComponent(FeedbackUIComponent):
    """Text area for collecting free-form feedback."""

    def __init__(
        self,
        min_length: int = 0,
        max_length: int = 500,
        required: bool = False,
        **kwargs,
    ):
        super().__init__(component_type="comment", **kwargs)
        self.min_length = min_length
        self.max_length = max_length
        self.required = required

    def to_dict(self) -> Dict[str, Any]:
        """Convert component to dictionary representation."""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "min_length": self.min_length,
                "max_length": self.max_length,
                "required": self.required,
            }
        )
        return base_dict


class ModalFeedbackComponent(FeedbackUIComponent):
    """Modal dialog for collecting comprehensive feedback."""

    def __init__(
        self,
        title: str = "Please rate this recommendation",
        child_components: List[FeedbackUIComponent] = None,
        dismissible: bool = True,
        show_on_exit: bool = False,
        **kwargs,
    ):
        super().__init__(component_type="modal", **kwargs)
        self.title = title
        self.child_components = child_components or []
        self.dismissible = dismissible
        self.show_on_exit = show_on_exit

    def to_dict(self) -> Dict[str, Any]:
        """Convert component to dictionary representation."""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "title": self.title,
                "child_components": [comp.to_dict() for comp in self.child_components],
                "dismissible": self.dismissible,
                "show_on_exit": self.show_on_exit,
            }
        )
        return base_dict

    def add_component(self, component: FeedbackUIComponent) -> None:
        """Add a child component to this modal."""
        component.parent_id = self.component_id
        self.child_components.append(component)


class FeedbackUIService:
    """Service for creating and managing feedback UI components."""

    def __init__(self, analytics_service=None, ab_test_service=None):
        self.analytics_service = analytics_service
        self.ab_test_service = ab_test_service
        self._components = {}  # Store active components

    def create_component(
        self,
        component_type: str,
        recommendation_id: str,
        product_id: str,
        config: Optional[FeedbackUIConfig] = None,
        **kwargs,
    ) -> FeedbackUIComponent:
        """Create a new feedback UI component."""
        component_class = self._get_component_class(component_type)
        if not component_class:
            raise ValueError(f"Unknown component type: {component_type}")

        component = component_class(
            config=config or FeedbackUIConfig(),
            recommendation_id=recommendation_id,
            product_id=product_id,
            **kwargs,
        )

        # Store the component
        self._components[component.component_id] = component

        # Apply A/B testing if enabled
        if self.ab_test_service and component.config.ab_test_enabled:
            self._apply_ab_test_variant(component)

        return component

    def _get_component_class(self, component_type: str) -> Optional[type]:
        """Get the component class for a given component type."""
        component_map = {
            "button_group": ButtonGroupComponent,
            "rating": RatingComponent,
            "comment": CommentComponent,
            "modal": ModalFeedbackComponent,
        }
        return component_map.get(component_type)

    def _apply_ab_test_variant(self, component: FeedbackUIComponent) -> None:
        """Apply A/B test variant to component configuration."""
        if not self.ab_test_service or not component.config.ab_test_enabled:
            return

        # Get variant for this user/session
        variant = self.ab_test_service.get_variant(
            test_name="feedback_ui",
            variants=component.config.ab_test_variants or ["A", "B"],
            user_id=None,  # Would come from session or user context
        )

        # Apply variant-specific configurations
        if variant == "A":
            component.config.style = FeedbackUIStyle.STANDARD
        elif variant == "B":
            component.config.style = FeedbackUIStyle.PROMINENT
        # Additional variants could be handled here

    def process_feedback(
        self,
        component_id: str,
        feedback_type: str,
        value: Any,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> APIResponse:
        """Process feedback submitted by a user."""
        component = self._components.get(component_id)
        if not component:
            return APIResponse(
                success=False,
                message=f"Component with ID {component_id} not found",
                status_code=404,
            )

        try:
            # Create feedback event
            event = FeedbackEvent(
                feedback_type=feedback_type,
                value=value,
                user_id=user_id,
                session_id=session_id,
                component_id=component_id,
                recommendation_id=component.recommendation_id,
                product_id=component.product_id,
                timestamp=datetime.now(),
                metadata=metadata or {},
            )

            # Track event in analytics if enabled
            if self.analytics_service and component.config.enable_analytics:
                self.analytics_service.track_event(
                    event_type="recommendation_feedback", properties=event.__dict__
                )

            # TODO: Send to feedback processing pipeline

            return APIResponse(
                success=True,
                message="Feedback received successfully",
                data={"event_id": str(uuid.uuid4())},
            )

        except Exception as e:
            logger.error("Error processing feedback: %s", str(e))
            return APIResponse(
                success=False,
                message=f"Error processing feedback: {str(e)}",
                status_code=500,
            )

    def get_component(self, component_id: str) -> Optional[FeedbackUIComponent]:
        """Retrieve a component by ID."""
        return self._components.get(component_id)

    def remove_component(self, component_id: str) -> bool:
        """Remove a component by ID."""
        if component_id in self._components:
            del self._components[component_id]
            return True
        return False


# Factory functions for creating common feedback components


def create_simple_thumbs_component(
    recommendation_id: str,
    product_id: str,
    prompt_text: str = "Was this recommendation helpful?",
    service: Optional[FeedbackUIService] = None,
) -> ButtonGroupComponent:
    """Create a simple thumbs up/down component."""
    if service is None:
        service = FeedbackUIService()

    config = FeedbackUIConfig(
        feedback_types=[FeedbackType.LIKE, FeedbackType.DISLIKE],
        prompt_text=prompt_text,
        style=FeedbackUIStyle.MINIMAL,
    )

    return service.create_component(
        component_type="button_group",
        recommendation_id=recommendation_id,
        product_id=product_id,
        config=config,
    )


def create_standard_rating_component(
    recommendation_id: str,
    product_id: str,
    max_rating: int = 5,
    prompt_text: str = "Rate this recommendation:",
    service: Optional[FeedbackUIService] = None,
) -> RatingComponent:
    """Create a standard star rating component."""
    if service is None:
        service = FeedbackUIService()

    config = FeedbackUIConfig(
        feedback_types=[FeedbackType.RATING],
        prompt_text=prompt_text,
        style=FeedbackUIStyle.STANDARD,
    )

    return service.create_component(
        component_type="rating",
        recommendation_id=recommendation_id,
        product_id=product_id,
        config=config,
        max_rating=max_rating,
    )


def create_comprehensive_feedback_modal(
    recommendation_id: str,
    product_id: str,
    title: str = "Help us improve your recommendations",
    service: Optional[FeedbackUIService] = None,
) -> ModalFeedbackComponent:
    """Create a comprehensive feedback modal with multiple components."""
    if service is None:
        service = FeedbackUIService()

    config = FeedbackUIConfig(style=FeedbackUIStyle.MODAL, allow_comments=True)

    modal = service.create_component(
        component_type="modal",
        recommendation_id=recommendation_id,
        product_id=product_id,
        config=config,
        title=title,
    )

    # Add rating component
    rating_config = FeedbackUIConfig(
        feedback_types=[FeedbackType.RATING],
        prompt_text="How would you rate this recommendation?",
        style=FeedbackUIStyle.STANDARD,
    )
    rating = RatingComponent(
        config=rating_config,
        recommendation_id=recommendation_id,
        product_id=product_id,
        parent_id=modal.component_id,
    )
    modal.add_component(rating)

    # Add comment component
    comment_config = FeedbackUIConfig(
        prompt_text="Additional comments (optional):", style=FeedbackUIStyle.STANDARD
    )
    comment = CommentComponent(
        config=comment_config,
        recommendation_id=recommendation_id,
        product_id=product_id,
        parent_id=modal.component_id,
        required=False,
        max_length=500,
    )
    modal.add_component(comment)

    return modal
