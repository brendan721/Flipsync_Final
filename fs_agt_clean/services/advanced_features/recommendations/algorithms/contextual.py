#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Contextual Recommendation Algorithm

This module implements a contextual recommendation system that enhances
recommendations by incorporating contextual information about users,
such as time, location, device, or recent activity.

The implementation supports both pre-filtering and post-filtering approaches
as well as contextual score adjustments.
"""

import logging
import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, time, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import numpy as np

# Import base recommendation algorithms
from fs_agt_clean.core.recommendations.algorithms.hybrid import (
    HybridRecommender,
)
from fs_agt_clean.core.recommendations.algorithms.hybrid import (
    Recommendation as HybridRecommendation,
)

logger = logging.getLogger(__name__)


class ContextType(str, Enum):
    """Types of context that can be used for contextual recommendations."""

    TIME = "time"
    LOCATION = "location"
    DEVICE = "device"
    WEATHER = "weather"
    USER_STATE = "user_state"
    SESSION = "session"
    RECENT_ACTIVITY = "recent_activity"
    CUSTOM = "custom"


class ContextualStrategy(str, Enum):
    """Strategies for incorporating context into recommendations."""

    PRE_FILTER = "pre_filter"  # Filter items before recommendation generation
    POST_FILTER = "post_filter"  # Filter recommendations after generation
    CONTEXTUAL_MODELING = "contextual_modeling"  # Incorporate context into the model
    SCORE_ADJUSTMENT = "score_adjustment"  # Adjust scores based on context


@dataclass
class TimeContext:
    """Time-based context information."""

    time_of_day: Optional[str] = None  # morning, afternoon, evening, night
    day_of_week: Optional[int] = None  # 0-6 (Monday to Sunday)
    weekend: Optional[bool] = None
    season: Optional[str] = None  # spring, summer, fall, winter
    holiday: Optional[bool] = None
    timestamp: Optional[datetime] = None  # Exact timestamp


@dataclass
class LocationContext:
    """Location-based context information."""

    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    store_proximity: Optional[List[str]] = None  # Nearby store IDs
    coordinates: Optional[Tuple[float, float]] = None  # lat, lng
    location_type: Optional[str] = None  # home, work, travel, etc.


@dataclass
class DeviceContext:
    """Device-based context information."""

    device_type: Optional[str] = None  # desktop, mobile, tablet, etc.
    os: Optional[str] = None
    browser: Optional[str] = None
    screen_size: Optional[str] = None  # small, medium, large
    connection_type: Optional[str] = None  # wifi, cellular, etc.


@dataclass
class SessionContext:
    """Session-based context information."""

    session_id: Optional[str] = None
    session_duration: Optional[int] = None  # in seconds
    page_views: Optional[int] = None
    referrer: Optional[str] = None
    search_query: Optional[str] = None
    entry_page: Optional[str] = None


@dataclass
class UnifiedUserStateContext:
    """UnifiedUser state context information."""

    logged_in: Optional[bool] = None
    account_age: Optional[int] = None  # in days
    subscription_status: Optional[str] = None
    user_segment: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


@dataclass
class RecentActivityContext:
    """UnifiedUser's recent activity context."""

    recently_viewed: Optional[List[str]] = None  # item IDs
    recently_purchased: Optional[List[str]] = None  # item IDs
    recent_searches: Optional[List[str]] = None  # search queries
    cart_items: Optional[List[str]] = None  # item IDs
    wishlist_items: Optional[List[str]] = None  # item IDs


@dataclass
class WeatherContext:
    """Weather-based context information."""

    temperature: Optional[float] = None  # in Celsius
    condition: Optional[str] = None  # sunny, rainy, cloudy, etc.
    season: Optional[str] = None
    is_precipitation: Optional[bool] = None


@dataclass
class Context:
    """Combined context information for contextual recommendations."""

    time: Optional[TimeContext] = None
    location: Optional[LocationContext] = None
    device: Optional[DeviceContext] = None
    session: Optional[SessionContext] = None
    user_state: Optional[UnifiedUserStateContext] = None
    recent_activity: Optional[RecentActivityContext] = None
    weather: Optional[WeatherContext] = None
    custom: Optional[Dict[str, Any]] = None


@dataclass
class ContextRule:
    """Rule for contextual filtering or score adjustment."""

    context_type: ContextType
    condition: Callable[[Any], bool]
    item_filter: Optional[Callable[[Dict[str, Any]], bool]] = None
    score_adjustment: Optional[float] = None
    applies_to_categories: Optional[List[str]] = None
    applies_to_items: Optional[List[str]] = None
    description: str = ""


@dataclass
class ContextualConfig:
    """Configuration for the contextual recommendation algorithm."""

    strategy: ContextualStrategy = ContextualStrategy.SCORE_ADJUSTMENT
    top_n_recommendations: int = 10  # Number of recommendations to generate
    min_final_score: float = 0.1  # Minimum score threshold after contextual adjustment
    time_weight: float = 1.0  # Weight for time context
    location_weight: float = 1.0  # Weight for location context
    device_weight: float = 0.5  # Weight for device context
    weather_weight: float = 0.8  # Weight for weather context
    recent_activity_weight: float = 2.0  # Weight for recent activity context
    contextual_boost_factor: float = 0.3  # Maximum score boost for context relevance


@dataclass
class Recommendation:
    """Recommendation result with contextual information."""

    id: str
    score: float
    confidence: float
    context_relevance: float = 0.0  # How relevant is this item to the current context
    metadata: Optional[Dict[str, Any]] = None
    sources: List[str] = field(default_factory=list)


class ContextualRecommender:
    """
    Contextual recommendation system that incorporates user context.

    This class enhances recommendations by using contextual information
    to make recommendations more relevant to the user's current situation.
    """

    def __init__(
        self,
        base_recommender: Optional[HybridRecommender] = None,
        config: Optional[ContextualConfig] = None,
        context_rules: Optional[List[ContextRule]] = None,
    ):
        """
        Initialize the contextual recommender.

        Args:
            base_recommender: Underlying recommendation engine (optional)
            config: Configuration for the contextual algorithm (optional)
            context_rules: List of contextual rules (optional)
        """
        self.base_recommender = base_recommender
        self.config = config or ContextualConfig()
        self.context_rules = context_rules or []
        self.items = {}  # Dictionary of item data by item ID

        logger.info(
            "Initialized contextual recommender with %s strategy", self.config.strategy
        )

    def fit(
        self,
        user_item_interactions: Dict[str, Dict[str, float]],
        items: Dict[str, Dict[str, Any]],
    ) -> None:
        """
        Fit the base recommender with the given data.

        Args:
            user_item_interactions: UnifiedUser-item interaction data
            items: Item data with features
        """
        logger.info("Fitting contextual recommendation model")

        # Store items for later use
        self.items = items

        # Initialize and fit base recommender if not provided
        if self.base_recommender is None:
            self.base_recommender = HybridRecommender()
            self.base_recommender.fit(user_item_interactions, items)
            logger.info("Trained base recommendation model")

    def add_context_rule(self, rule: ContextRule) -> None:
        """
        Add a new context rule for filtering or score adjustment.

        Args:
            rule: Context rule to add
        """
        self.context_rules.append(rule)
        logger.info(
            "Added context rule for %s: %s", rule.context_type, rule.description
        )

    def recommend(
        self,
        user_id: str,
        context: Optional[Context] = None,
        excluded_ids: Optional[List[str]] = None,
    ) -> List[Recommendation]:
        """
        Generate context-aware recommendations for a user.

        Args:
            user_id: UnifiedUser ID to recommend for
            context: UnifiedUser's current context
            excluded_ids: Item IDs to exclude from recommendations

        Returns:
            List of contextual recommendations with scores and confidence values
        """
        excluded_ids = excluded_ids or []

        # If no context provided, fall back to base recommender
        if context is None:
            logger.info("No context provided, using base recommender")
            base_recs = self.base_recommender.recommend(
                user_id, excluded_ids=excluded_ids
            )
            return [self._convert_to_contextual_rec(rec) for rec in base_recs]

        # Choose strategy based on configuration
        if self.config.strategy == ContextualStrategy.PRE_FILTER:
            return self._pre_filter_recommendations(user_id, context, excluded_ids)
        elif self.config.strategy == ContextualStrategy.POST_FILTER:
            return self._post_filter_recommendations(user_id, context, excluded_ids)
        elif self.config.strategy == ContextualStrategy.CONTEXTUAL_MODELING:
            return self._contextual_modeling_recommendations(
                user_id, context, excluded_ids
            )
        elif self.config.strategy == ContextualStrategy.SCORE_ADJUSTMENT:
            return self._score_adjustment_recommendations(
                user_id, context, excluded_ids
            )
        else:
            # Default to score adjustment
            return self._score_adjustment_recommendations(
                user_id, context, excluded_ids
            )

    def _pre_filter_recommendations(
        self, user_id: str, context: Context, excluded_ids: List[str]
    ) -> List[Recommendation]:
        """
        Apply pre-filtering based on context before generating recommendations.

        Args:
            user_id: UnifiedUser ID to recommend for
            context: UnifiedUser's current context
            excluded_ids: Item IDs to exclude from recommendations

        Returns:
            List of contextual recommendations
        """
        # Apply pre-filtering to the item catalog based on context
        filtered_excluded_ids = excluded_ids.copy()

        # Apply each context rule
        for rule in self.context_rules:
            # Skip rules without item filters
            if not rule.item_filter:
                continue

            # Apply rule based on context
            context_value = self._get_context_value(context, rule.context_type)
            if context_value and rule.condition(context_value):
                # This rule applies to the current context
                for item_id, item in self.items.items():
                    # Skip already excluded items
                    if item_id in filtered_excluded_ids:
                        continue

                    # Apply category filter if specified
                    if rule.applies_to_categories and "category" in item:
                        item_categories = (
                            item["category"]
                            if isinstance(item["category"], list)
                            else [item["category"]]
                        )
                        if not any(
                            cat in rule.applies_to_categories for cat in item_categories
                        ):
                            continue

                    # Apply item filter if specified
                    if rule.applies_to_items and item_id not in rule.applies_to_items:
                        continue

                    # Apply the rule's filter
                    if not rule.item_filter(item):
                        filtered_excluded_ids.append(item_id)

        # Generate recommendations using the filtered excluded list
        base_recs = self.base_recommender.recommend(
            user_id, excluded_ids=filtered_excluded_ids
        )

        # Add context relevance to recommendations
        contextual_recs = []
        for rec in base_recs:
            context_relevance = self._calculate_context_relevance(rec.id, context)
            contextual_recs.append(
                Recommendation(
                    id=rec.id,
                    score=rec.score,
                    confidence=rec.confidence,
                    context_relevance=context_relevance,
                    metadata=rec.metadata,
                    sources=rec.sources + ["contextual_pre_filter"],
                )
            )

        return contextual_recs

    def _post_filter_recommendations(
        self, user_id: str, context: Context, excluded_ids: List[str]
    ) -> List[Recommendation]:
        """
        Apply post-filtering based on context after generating recommendations.

        Args:
            user_id: UnifiedUser ID to recommend for
            context: UnifiedUser's current context
            excluded_ids: Item IDs to exclude from recommendations

        Returns:
            List of contextual recommendations
        """
        # Generate base recommendations
        base_recs = self.base_recommender.recommend(
            user_id,
            excluded_ids=excluded_ids,
            # Request more recommendations than needed for filtering
            context={"top_n_override": self.config.top_n_recommendations * 2},
        )

        # Apply post-filtering based on context rules
        filtered_recs = []
        for rec in base_recs:
            item_id = rec.id
            item = self.items.get(item_id, {})

            # Check if this item passes all applicable context rules
            passes_rules = True

            for rule in self.context_rules:
                # Skip rules without item filters
                if not rule.item_filter:
                    continue

                # Apply rule based on context
                context_value = self._get_context_value(context, rule.context_type)
                if context_value and rule.condition(context_value):
                    # This rule applies to the current context

                    # Apply category filter if specified
                    if rule.applies_to_categories and "category" in item:
                        item_categories = (
                            item["category"]
                            if isinstance(item["category"], list)
                            else [item["category"]]
                        )
                        if not any(
                            cat in rule.applies_to_categories for cat in item_categories
                        ):
                            continue

                    # Apply item filter if specified
                    if rule.applies_to_items and item_id not in rule.applies_to_items:
                        continue

                    # Apply the rule's filter
                    if not rule.item_filter(item):
                        passes_rules = False
                        break

            if passes_rules:
                # Calculate context relevance for this item
                context_relevance = self._calculate_context_relevance(item_id, context)

                filtered_recs.append(
                    Recommendation(
                        id=item_id,
                        score=rec.score,
                        confidence=rec.confidence,
                        context_relevance=context_relevance,
                        metadata=rec.metadata,
                        sources=rec.sources + ["contextual_post_filter"],
                    )
                )

        # Sort by score and limit to top N
        filtered_recs.sort(key=lambda x: x.score, reverse=True)
        return filtered_recs[: self.config.top_n_recommendations]

    def _contextual_modeling_recommendations(
        self, user_id: str, context: Context, excluded_ids: List[str]
    ) -> List[Recommendation]:
        """
        Incorporate context directly into the recommendation model.

        This is a complex approach that would normally involve re-training models
        with contextual features. For now, we'll use a simplified implementation
        that modifies the recommendation request based on context.

        Args:
            user_id: UnifiedUser ID to recommend for
            context: UnifiedUser's current context
            excluded_ids: Item IDs to exclude from recommendations

        Returns:
            List of contextual recommendations
        """
        # This approach is complex and would normally require a specialized model
        # For now, we'll use a simplified implementation based on score adjustment
        logger.info(
            "Full contextual modeling not implemented. Using score adjustment approach."
        )
        return self._score_adjustment_recommendations(user_id, context, excluded_ids)

    def _score_adjustment_recommendations(
        self, user_id: str, context: Context, excluded_ids: List[str]
    ) -> List[Recommendation]:
        """
        Adjust recommendation scores based on contextual relevance.

        Args:
            user_id: UnifiedUser ID to recommend for
            context: UnifiedUser's current context
            excluded_ids: Item IDs to exclude from recommendations

        Returns:
            List of contextual recommendations with adjusted scores
        """
        # Generate base recommendations (requesting more than needed)
        base_recs = self.base_recommender.recommend(
            user_id,
            excluded_ids=excluded_ids,
            # Request more recommendations than needed for adjustment
            context={"top_n_override": self.config.top_n_recommendations * 2},
        )

        # Calculate context relevance and adjust scores
        contextual_recs = []
        for rec in base_recs:
            item_id = rec.id

            # Calculate context relevance
            context_relevance = self._calculate_context_relevance(item_id, context)

            # Apply score adjustment from rules
            score_adjustment = self._calculate_rule_score_adjustment(item_id, context)

            # Combine base score with context adjustments
            # The formula boosts scores based on context relevance up to the boost factor
            adjusted_score = rec.score * (
                1.0 + context_relevance * self.config.contextual_boost_factor
            )

            # Apply additional rule-based adjustments
            adjusted_score += score_adjustment

            # Ensure score is in [0, 1] range
            adjusted_score = max(0.0, min(1.0, adjusted_score))

            # Only include recommendations with scores above threshold
            if adjusted_score >= self.config.min_final_score:
                contextual_recs.append(
                    Recommendation(
                        id=item_id,
                        score=adjusted_score,
                        confidence=rec.confidence,
                        context_relevance=context_relevance,
                        metadata=rec.metadata,
                        sources=rec.sources + ["contextual_score_adjustment"],
                    )
                )

        # Sort by adjusted score and limit to top N
        contextual_recs.sort(key=lambda x: x.score, reverse=True)
        return contextual_recs[: self.config.top_n_recommendations]

    def _calculate_context_relevance(self, item_id: str, context: Context) -> float:
        """
        Calculate how relevant an item is to the current context.

        Args:
            item_id: Item ID to evaluate
            context: UnifiedUser's current context

        Returns:
            Context relevance score between 0 and 1
        """
        item = self.items.get(item_id, {})
        if not item:
            return 0.0

        # Initialize relevance factors for each context type
        relevance_factors = []

        # 1. Time context
        if context.time and "seasonal" in item:
            seasonal_relevance = self._calculate_time_relevance(item, context.time)
            relevance_factors.append((seasonal_relevance, self.config.time_weight))

        # 2. Location context
        if context.location and "region" in item:
            location_relevance = self._calculate_location_relevance(
                item, context.location
            )
            relevance_factors.append((location_relevance, self.config.location_weight))

        # 3. Device context
        if context.device and "device_compatibility" in item:
            device_relevance = self._calculate_device_relevance(item, context.device)
            relevance_factors.append((device_relevance, self.config.device_weight))

        # 4. Weather context
        if context.weather and "weather_appropriate" in item:
            weather_relevance = self._calculate_weather_relevance(item, context.weather)
            relevance_factors.append((weather_relevance, self.config.weather_weight))

        # 5. Recent activity context
        if context.recent_activity:
            activity_relevance = self._calculate_activity_relevance(
                item_id, item, context.recent_activity
            )
            relevance_factors.append(
                (activity_relevance, self.config.recent_activity_weight)
            )

        # Calculate weighted average of relevance factors
        if relevance_factors:
            total_weight = sum(weight for _, weight in relevance_factors)
            if total_weight > 0:
                weighted_sum = sum(
                    relevance * weight for relevance, weight in relevance_factors
                )
                return weighted_sum / total_weight

        return 0.0  # Default if no context relevance could be calculated

    def _calculate_time_relevance(
        self, item: Dict[str, Any], time_context: TimeContext
    ) -> float:
        """
        Calculate how relevant an item is to the current time context.

        Args:
            item: Item data
            time_context: Time context information

        Returns:
            Time relevance score between 0 and 1
        """
        relevance = 0.0

        # Check season relevance if available
        if "seasonal" in item and time_context.season:
            if isinstance(item["seasonal"], list):
                # Item is relevant for multiple seasons
                if time_context.season in item["seasonal"]:
                    relevance += 1.0
            elif isinstance(item["seasonal"], str):
                # Item is relevant for a single season
                if time_context.season == item["seasonal"]:
                    relevance += 1.0

        # Check time of day relevance if available
        if "time_of_day" in item and time_context.time_of_day:
            if isinstance(item["time_of_day"], list):
                # Item is relevant for multiple times of day
                if time_context.time_of_day in item["time_of_day"]:
                    relevance += 1.0
            elif isinstance(item["time_of_day"], str):
                # Item is relevant for a single time of day
                if time_context.time_of_day == item["time_of_day"]:
                    relevance += 1.0

        # Check day of week relevance if available
        if "weekend_only" in item and item["weekend_only"] and time_context.weekend:
            relevance += 1.0

        # Check holiday relevance if available
        if "holiday" in item and item["holiday"] and time_context.holiday:
            relevance += 1.0

        # Normalize to [0, 1]
        num_factors = sum(
            [
                "seasonal" in item and time_context.season is not None,
                "time_of_day" in item and time_context.time_of_day is not None,
                "weekend_only" in item and time_context.weekend is not None,
                "holiday" in item and time_context.holiday is not None,
            ]
        )

        return relevance / max(1, num_factors)

    def _calculate_location_relevance(
        self, item: Dict[str, Any], location_context: LocationContext
    ) -> float:
        """
        Calculate how relevant an item is to the current location context.

        Args:
            item: Item data
            location_context: Location context information

        Returns:
            Location relevance score between 0 and 1
        """
        relevance = 0.0

        # Check country relevance if available
        if "available_countries" in item and location_context.country:
            if isinstance(item["available_countries"], list):
                if location_context.country in item["available_countries"]:
                    relevance += 1.0
            elif item["available_countries"] == location_context.country:
                relevance += 1.0

        # Check region relevance if available
        if "region" in item and location_context.region:
            if isinstance(item["region"], list):
                if location_context.region in item["region"]:
                    relevance += 1.0
            elif item["region"] == location_context.region:
                relevance += 1.0

        # Check store proximity if available
        if "store_id" in item and location_context.store_proximity:
            if item["store_id"] in location_context.store_proximity:
                relevance += 1.0

        # Check location type relevance if available
        if "location_type" in item and location_context.location_type:
            if isinstance(item["location_type"], list):
                if location_context.location_type in item["location_type"]:
                    relevance += 1.0
            elif item["location_type"] == location_context.location_type:
                relevance += 1.0

        # Normalize to [0, 1]
        num_factors = sum(
            [
                "available_countries" in item and location_context.country is not None,
                "region" in item and location_context.region is not None,
                "store_id" in item and location_context.store_proximity is not None,
                "location_type" in item and location_context.location_type is not None,
            ]
        )

        return relevance / max(1, num_factors)

    def _calculate_device_relevance(
        self, item: Dict[str, Any], device_context: DeviceContext
    ) -> float:
        """
        Calculate how relevant an item is to the current device context.

        Args:
            item: Item data
            device_context: Device context information

        Returns:
            Device relevance score between 0 and 1
        """
        relevance = 0.0

        # Check device type compatibility if available
        if "device_compatibility" in item and device_context.device_type:
            if isinstance(item["device_compatibility"], list):
                if device_context.device_type in item["device_compatibility"]:
                    relevance += 1.0
            elif item["device_compatibility"] == device_context.device_type:
                relevance += 1.0

        # Check screen size relevance if available
        if "best_screen_size" in item and device_context.screen_size:
            if isinstance(item["best_screen_size"], list):
                if device_context.screen_size in item["best_screen_size"]:
                    relevance += 1.0
            elif item["best_screen_size"] == device_context.screen_size:
                relevance += 1.0

        # Check connection type relevance if available
        if "requires_fast_connection" in item and item["requires_fast_connection"]:
            if device_context.connection_type == "wifi":
                relevance += 1.0

        # Normalize to [0, 1]
        num_factors = sum(
            [
                "device_compatibility" in item
                and device_context.device_type is not None,
                "best_screen_size" in item and device_context.screen_size is not None,
                "requires_fast_connection" in item
                and device_context.connection_type is not None,
            ]
        )

        return relevance / max(1, num_factors)

    def _calculate_weather_relevance(
        self, item: Dict[str, Any], weather_context: WeatherContext
    ) -> float:
        """
        Calculate how relevant an item is to the current weather context.

        Args:
            item: Item data
            weather_context: Weather context information

        Returns:
            Weather relevance score between 0 and 1
        """
        relevance = 0.0

        # Check weather condition relevance if available
        if "weather_appropriate" in item and weather_context.condition:
            if isinstance(item["weather_appropriate"], list):
                if weather_context.condition in item["weather_appropriate"]:
                    relevance += 1.0
            elif item["weather_appropriate"] == weather_context.condition:
                relevance += 1.0

        # Check temperature range relevance if available
        if (
            "min_temp" in item
            and "max_temp" in item
            and weather_context.temperature is not None
        ):
            temp = weather_context.temperature
            min_temp = item["min_temp"]
            max_temp = item["max_temp"]

            if min_temp <= temp <= max_temp:
                # Temperature is in the optimal range
                relevance += 1.0
            elif temp < min_temp:
                # Temperature is below range
                # Calculate partial relevance based on how close to range
                temp_diff = min_temp - temp
                max_diff = 10.0  # Maximum difference to consider
                if temp_diff <= max_diff:
                    relevance += 1.0 - (temp_diff / max_diff)
            elif temp > max_temp:
                # Temperature is above range
                # Calculate partial relevance based on how close to range
                temp_diff = temp - max_temp
                max_diff = 10.0  # Maximum difference to consider
                if temp_diff <= max_diff:
                    relevance += 1.0 - (temp_diff / max_diff)

        # Check precipitation relevance if available
        if "water_resistant" in item and weather_context.is_precipitation:
            if item["water_resistant"]:
                relevance += 1.0

        # Normalize to [0, 1]
        num_factors = sum(
            [
                "weather_appropriate" in item and weather_context.condition is not None,
                "min_temp" in item
                and "max_temp" in item
                and weather_context.temperature is not None,
                "water_resistant" in item
                and weather_context.is_precipitation is not None,
            ]
        )

        return relevance / max(1, num_factors)

    def _calculate_activity_relevance(
        self,
        item_id: str,
        item: Dict[str, Any],
        activity_context: RecentActivityContext,
    ) -> float:
        """
        Calculate how relevant an item is to the user's recent activity.

        Args:
            item_id: Item ID to evaluate
            item: Item data
            activity_context: Recent activity context

        Returns:
            Activity relevance score between 0 and 1
        """
        relevance = 0.0

        # Check complementary products for cart and wishlist items
        if "complementary_products" in item:
            complements = item["complementary_products"]

            # Check cart items
            if activity_context.cart_items:
                for cart_item in activity_context.cart_items:
                    if cart_item in complements:
                        relevance += 0.5
                        break

            # Check wishlist items
            if activity_context.wishlist_items:
                for wishlist_item in activity_context.wishlist_items:
                    if wishlist_item in complements:
                        relevance += 0.3
                        break

        # Check category similarity for recently viewed items
        if "category" in item and activity_context.recently_viewed:
            item_categories = (
                item["category"]
                if isinstance(item["category"], list)
                else [item["category"]]
            )

            # Get categories of recently viewed items
            viewed_categories = set()
            for viewed_id in activity_context.recently_viewed:
                viewed_item = self.items.get(viewed_id, {})
                if "category" in viewed_item:
                    if isinstance(viewed_item["category"], list):
                        viewed_categories.update(viewed_item["category"])
                    else:
                        viewed_categories.add(viewed_item["category"])

            # Calculate relevance based on category match
            common_categories = set(item_categories) & viewed_categories
            if common_categories:
                relevance += 0.7 * (len(common_categories) / len(item_categories))

        # Check if item was previously viewed (lower relevance)
        if (
            activity_context.recently_viewed
            and item_id in activity_context.recently_viewed
        ):
            relevance += 0.2

        # Check search term matches
        if activity_context.recent_searches and "keywords" in item:
            item_keywords = (
                item["keywords"]
                if isinstance(item["keywords"], list)
                else [item["keywords"]]
            )

            for search in activity_context.recent_searches:
                search_terms = search.lower().split()
                for keyword in item_keywords:
                    if keyword.lower() in search_terms:
                        relevance += 0.4
                        break

        # Apply a decay function for recently purchased items (avoid recommending again)
        if (
            activity_context.recently_purchased
            and item_id in activity_context.recently_purchased
        ):
            relevance -= (
                0.8  # Significantly reduce relevance for recently purchased items
            )

        # Normalize to [0, 1] range
        return max(0.0, min(1.0, relevance))

    def _get_context_value(self, context: Context, context_type: ContextType) -> Any:
        """
        Get the appropriate context value for a given context type.

        Args:
            context: Complete context object
            context_type: Type of context to extract

        Returns:
            The context value for the specified type, or None if not available
        """
        if context_type == ContextType.TIME:
            return context.time
        elif context_type == ContextType.LOCATION:
            return context.location
        elif context_type == ContextType.DEVICE:
            return context.device
        elif context_type == ContextType.SESSION:
            return context.session
        elif context_type == ContextType.USER_STATE:
            return context.user_state
        elif context_type == ContextType.RECENT_ACTIVITY:
            return context.recent_activity
        elif context_type == ContextType.WEATHER:
            return context.weather
        elif context_type == ContextType.CUSTOM:
            return context.custom
        else:
            return None

    def _calculate_rule_score_adjustment(self, item_id: str, context: Context) -> float:
        """
        Calculate score adjustment based on context rules.

        Args:
            item_id: Item ID to evaluate
            context: UnifiedUser's current context

        Returns:
            Score adjustment (positive or negative)
        """
        item = self.items.get(item_id, {})
        if not item:
            return 0.0

        total_adjustment = 0.0

        for rule in self.context_rules:
            # Skip rules without score adjustment
            if rule.score_adjustment is None:
                continue

            # Apply rule based on context
            context_value = self._get_context_value(context, rule.context_type)
            if context_value and rule.condition(context_value):
                # This rule applies to the current context

                # Apply category filter if specified
                if rule.applies_to_categories and "category" in item:
                    item_categories = (
                        item["category"]
                        if isinstance(item["category"], list)
                        else [item["category"]]
                    )
                    if not any(
                        cat in rule.applies_to_categories for cat in item_categories
                    ):
                        continue

                # Apply item filter if specified
                if rule.applies_to_items and item_id not in rule.applies_to_items:
                    continue

                # Apply the rule's filter if present
                if rule.item_filter and not rule.item_filter(item):
                    continue

                # Apply the score adjustment
                total_adjustment += rule.score_adjustment

        return total_adjustment

    def _convert_to_contextual_rec(
        self, recommendation: HybridRecommendation
    ) -> Recommendation:
        """
        Convert a hybrid recommendation to a contextual recommendation.

        Args:
            recommendation: Hybrid recommendation to convert

        Returns:
            Contextual recommendation
        """
        return Recommendation(
            id=recommendation.id,
            score=recommendation.score,
            confidence=recommendation.confidence,
            context_relevance=0.0,  # No context evaluation was done
            metadata=recommendation.metadata,
            sources=recommendation.sources,
        )

    def evaluate(
        self,
        test_interactions: Dict[str, Dict[str, float]],
        test_contexts: Dict[str, Context],
    ) -> Dict[str, float]:
        """
        Evaluate the contextual recommendation algorithm on test data.

        Args:
            test_interactions: Test user-item interactions
            test_contexts: Test contexts for each user

        Returns:
            Dictionary with evaluation metrics
        """
        precision_sum = 0.0
        recall_sum = 0.0
        f1_sum = 0.0
        user_count = 0

        for user_id, user_items in test_interactions.items():
            if not user_items:
                continue

            # Get items the user has actually interacted with
            actual_items = set(user_items.keys())

            # Get the test context for this user if available
            context = test_contexts.get(user_id)

            # Generate recommendations for this user
            recommendations = self.recommend(user_id, context=context)
            recommended_items = {rec.id for rec in recommendations}

            # Calculate precision and recall
            if recommended_items:
                correctly_recommended = actual_items.intersection(recommended_items)
                precision = len(correctly_recommended) / len(recommended_items)
                recall = len(correctly_recommended) / len(actual_items)

                precision_sum += precision
                recall_sum += recall

                if precision + recall > 0:
                    f1 = 2 * precision * recall / (precision + recall)
                    f1_sum += f1

            user_count += 1

        if user_count == 0:
            return {"precision": 0, "recall": 0, "f1": 0}

        return {
            "precision": precision_sum / user_count,
            "recall": recall_sum / user_count,
            "f1": f1_sum / user_count,
        }
