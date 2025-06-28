"""
UnifiedUser Preference Learner

This module analyzes user actions to extract and learn user preferences
for personalizing the FlipSync application experience.
"""

import json
import logging
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from fs_agt_clean.api.routes.monitoring_routes import get_database
from fs_agt_clean.core.utils.time.time_utils import get_current_timestamp
from fs_agt_clean.services.personalization.user_action_tracker import (
    UnifiedUserActionTracker,
    UnifiedUserActionType,
)

logger = logging.getLogger(__name__)


class PreferenceCategory:
    """Categories of user preferences that can be learned."""

    UI_LAYOUT = "ui_layout"
    COLOR_SCHEME = "color_scheme"
    FEATURE_USAGE = "feature_usage"
    CONTENT_INTERESTS = "content_interests"
    WORKFLOW_PATTERNS = "workflow_patterns"
    SEARCH_BEHAVIOR = "search_behavior"
    SORTING_PREFERENCE = "sorting_preference"
    FILTERING_PREFERENCE = "filtering_preference"
    TIME_OF_DAY = "time_of_day"
    SESSION_DURATION = "session_duration"


class PreferenceLearner:
    """
    Analyzes user actions to learn and extract user preferences.

    This class processes tracked user actions to identify patterns and
    preferences, which can then be used to personalize the user experience.
    """

    def __init__(self, user_id: str):
        """
        Initialize the preference learner for a specific user.

        Args:
            user_id: The ID of the user whose preferences are being learned
        """
        self.user_id = user_id
        self.db = get_database()
        self.action_tracker = UnifiedUserActionTracker(user_id)
        self._init_db_tables()

    def _init_db_tables(self):
        """Ensure that the necessary database tables exist."""
        try:
            # Table for storing learned preferences
            self.db.execute(
                """
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    preference_key TEXT NOT NULL,
                    preference_value TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    last_updated INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(user_id, category, preference_key)
                )
            """
            )

            self.db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id
                ON user_preferences(user_id)
            """
            )

            # Table for preference history (for tracking changes over time)
            self.db.execute(
                """
                CREATE TABLE IF NOT EXISTS user_preference_history (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    preference_key TEXT NOT NULL,
                    preference_value TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    timestamp INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
            """
            )
        except Exception as e:
            logger.error("Failed to initialize preference learner tables: %s", e)

    def learn_preferences(
        self, days_to_analyze: int = 30, min_confidence: float = 0.6
    ) -> Dict[str, Dict[str, Any]]:
        """
        Analyze user actions to learn preferences.

        Args:
            days_to_analyze: Number of days of action history to analyze
            min_confidence: Minimum confidence threshold for learned preferences

        Returns:
            Dictionary of learned preferences by category
        """
        start_time = get_current_timestamp() - (
            days_to_analyze * 86400
        )  # Convert days to seconds

        # Get user actions for the specified time period
        actions = self.action_tracker.get_user_actions(
            start_time=start_time, limit=10000
        )

        if not actions:
            logger.info(
                "No actions found for user %s in the last %s days",
                self.user_id,
                days_to_analyze,
            )
            return {}

        # Process different aspects of user behavior to extract preferences
        preferences = {}

        # Learn UI layout preferences
        ui_prefs = self._learn_ui_preferences(actions)
        if ui_prefs:
            preferences[PreferenceCategory.UI_LAYOUT] = ui_prefs

        # Learn feature usage preferences
        feature_prefs = self._learn_feature_usage(actions)
        if feature_prefs:
            preferences[PreferenceCategory.FEATURE_USAGE] = feature_prefs

        # Learn content interests
        content_prefs = self._learn_content_interests(actions)
        if content_prefs:
            preferences[PreferenceCategory.CONTENT_INTERESTS] = content_prefs

        # Learn workflow patterns
        workflow_prefs = self._learn_workflow_patterns(actions)
        if workflow_prefs:
            preferences[PreferenceCategory.WORKFLOW_PATTERNS] = workflow_prefs

        # Learn search behavior
        search_prefs = self._learn_search_behavior(actions)
        if search_prefs:
            preferences[PreferenceCategory.SEARCH_BEHAVIOR] = search_prefs

        # Learn sorting preferences
        sorting_prefs = self._learn_sorting_preferences(actions)
        if sorting_prefs:
            preferences[PreferenceCategory.SORTING_PREFERENCE] = sorting_prefs

        # Learn filtering preferences
        filtering_prefs = self._learn_filtering_preferences(actions)
        if filtering_prefs:
            preferences[PreferenceCategory.FILTERING_PREFERENCE] = filtering_prefs

        # Learn time of day patterns
        time_prefs = self._learn_time_patterns(actions)
        if time_prefs:
            preferences[PreferenceCategory.TIME_OF_DAY] = time_prefs

        # Save the learned preferences
        self._save_preferences(preferences, min_confidence)

        # Remove preferences below confidence threshold for the return value
        filtered_preferences = {}
        for category, prefs in preferences.items():
            filtered_prefs = {
                k: v
                for k, v in prefs.items()
                if v.get("confidence", 0) >= min_confidence
            }
            if filtered_prefs:
                filtered_preferences[category] = filtered_prefs

        return filtered_preferences

    def _learn_ui_preferences(
        self, actions: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract UI layout preferences from user actions.

        Args:
            actions: List of user action records

        Returns:
            Dictionary of UI preferences with confidence scores
        """
        ui_prefs = {}

        # Filter actions related to UI interaction
        ui_actions = [
            a
            for a in actions
            if a["action_type"]
            in [
                UnifiedUserActionType.PAGE_VIEW,
                UnifiedUserActionType.BUTTON_CLICK,
                UnifiedUserActionType.NAVIGATION,
            ]
        ]

        if not ui_actions:
            return {}

        # Analyze page view durations to determine preferred views
        page_views = {}
        for i, action in enumerate(ui_actions):
            if action["action_type"] == UnifiedUserActionType.PAGE_VIEW:
                page = action.get("action_context")
                if not page:
                    continue

                # Find the next action to calculate duration
                if i < len(ui_actions) - 1:
                    duration = ui_actions[i + 1]["timestamp"] - action["timestamp"]

                    # Only count reasonable durations (between 5 seconds and 30 minutes)
                    if 5 <= duration <= 1800:
                        if page not in page_views:
                            page_views[page] = []
                        page_views[page].append(duration)

        # Calculate average time spent on each page
        page_durations = {}
        for page, durations in page_views.items():
            if len(durations) >= 3:  # Require at least 3 visits for confidence
                avg_duration = sum(durations) / len(durations)
                page_durations[page] = {
                    "value": avg_duration,
                    "confidence": min(
                        0.5 + (len(durations) / 20), 0.95
                    ),  # More visits = higher confidence
                    "sample_size": len(durations),
                }

        # Determine preferred pages based on visit frequency and duration
        if page_durations:
            # Find the most viewed pages
            view_counts = Counter(
                [
                    a.get("action_context")
                    for a in ui_actions
                    if a["action_type"] == UnifiedUserActionType.PAGE_VIEW
                    and a.get("action_context")
                ]
            )

            # Combine frequency and duration to determine favorite pages
            favorite_pages = []
            for page, count in view_counts.most_common(5):
                if page in page_durations:
                    score = (count * page_durations[page]["value"]) / 100
                    confidence = min(
                        page_durations[page]["confidence"] + (count / 100), 0.95
                    )
                    favorite_pages.append((page, score, confidence))

            if favorite_pages:
                ui_prefs["preferred_pages"] = {
                    "value": [
                        p[0]
                        for p in sorted(
                            favorite_pages, key=lambda x: x[1], reverse=True
                        )
                    ],
                    "confidence": max([p[2] for p in favorite_pages]),
                }

        # Analyze navigation patterns
        nav_actions = [
            a for a in ui_actions if a["action_type"] == UnifiedUserActionType.NAVIGATION
        ]
        if nav_actions:
            nav_patterns = {}
            for i in range(len(nav_actions) - 1):
                from_page = nav_actions[i].get("action_context")
                to_page = nav_actions[i + 1].get("action_context")
                if from_page and to_page:
                    key = f"{from_page}->{to_page}"
                    nav_patterns[key] = nav_patterns.get(key, 0) + 1

            # Find common navigation patterns
            if nav_patterns:
                total_transitions = sum(nav_patterns.values())
                common_patterns = []
                for pattern, count in sorted(
                    nav_patterns.items(), key=lambda x: x[1], reverse=True
                )[:5]:
                    confidence = min(0.5 + (count / total_transitions), 0.9)
                    if count >= 3:  # Require at least 3 occurrences
                        common_patterns.append((pattern, count, confidence))

                if common_patterns:
                    ui_prefs["navigation_patterns"] = {
                        "value": [p[0] for p in common_patterns],
                        "confidence": max([p[2] for p in common_patterns]),
                    }

        return ui_prefs

    def _learn_feature_usage(
        self, actions: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract feature usage preferences from user actions.

        Args:
            actions: List of user action records

        Returns:
            Dictionary of feature usage preferences with confidence scores
        """
        feature_prefs = {}

        # Filter actions related to feature usage
        feature_actions = [
            a for a in actions if a["action_type"] == UnifiedUserActionType.FEATURE_USE
        ]

        if not feature_actions:
            return {}

        # Count feature usage
        feature_counts = Counter()
        for action in feature_actions:
            if action.get("action_data") and "feature_id" in action["action_data"]:
                feature_id = action["action_data"]["feature_id"]
                feature_counts[feature_id] += 1

        if not feature_counts:
            return {}

        # Determine most used features
        total_usage = sum(feature_counts.values())
        most_used = []
        for feature, count in feature_counts.most_common(5):
            usage_ratio = count / total_usage
            confidence = min(0.5 + usage_ratio, 0.9)
            if count >= 3:  # Require at least 3 uses
                most_used.append((feature, count, confidence))

        if most_used:
            feature_prefs["most_used_features"] = {
                "value": [f[0] for f in most_used],
                "confidence": max([f[2] for f in most_used]),
            }

        return feature_prefs

    def _learn_content_interests(
        self, actions: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract content interest preferences from user actions.

        Args:
            actions: List of user action records

        Returns:
            Dictionary of content interest preferences with confidence scores
        """
        content_prefs = {}

        # Filter actions related to content viewing
        content_actions = [
            a for a in actions if a["action_type"] == UnifiedUserActionType.ITEM_VIEW
        ]

        if not content_actions:
            return {}

        # Analyze content categories
        categories = Counter()
        for action in content_actions:
            if action.get("action_data") and "category" in action["action_data"]:
                category = action["action_data"]["category"]
                categories[category] += 1

        if not categories:
            return {}

        # Determine favorite categories
        total_views = sum(categories.values())
        favorite_categories = []
        for category, count in categories.most_common(5):
            view_ratio = count / total_views
            confidence = min(0.5 + view_ratio, 0.9)
            if count >= 3:  # Require at least 3 views
                favorite_categories.append((category, count, confidence))

        if favorite_categories:
            content_prefs["favorite_categories"] = {
                "value": [c[0] for c in favorite_categories],
                "confidence": max([c[2] for c in favorite_categories]),
            }

        return content_prefs

    def _learn_workflow_patterns(
        self, actions: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract workflow pattern preferences from user actions.

        Args:
            actions: List of user action records

        Returns:
            Dictionary of workflow pattern preferences with confidence scores
        """
        workflow_prefs = {}

        # Sort actions by timestamp
        sorted_actions = sorted(actions, key=lambda x: x["timestamp"])

        # Identify common sequences of actions (workflows)
        sequences = []
        current_sequence = []

        for i, action in enumerate(sorted_actions):
            if i > 0:
                time_diff = action["timestamp"] - sorted_actions[i - 1]["timestamp"]
                if time_diff > 300:  # New sequence if more than 5 minutes gap
                    if len(current_sequence) >= 3:
                        sequences.append(current_sequence)
                    current_sequence = []

            # Add action type to the sequence
            current_sequence.append(action["action_type"])

            # Cap sequence length
            if len(current_sequence) > 10:
                sequences.append(current_sequence)
                current_sequence = current_sequence[-5:]  # Keep the last 5 actions

        # Add the final sequence if it exists
        if current_sequence and len(current_sequence) >= 3:
            sequences.append(current_sequence)

        if not sequences:
            return {}

        # Find common subsequences
        common_sequences = Counter()
        for sequence in sequences:
            for i in range(len(sequence) - 2):
                subsequence = tuple(sequence[i : i + 3])  # 3-action subsequences
                common_sequences[subsequence] += 1

        if not common_sequences:
            return {}

        # Get the most common workflows
        total_sequences = sum(common_sequences.values())
        common_workflows = []
        for subseq, count in common_sequences.most_common(5):
            freq_ratio = count / total_sequences
            confidence = min(0.5 + freq_ratio, 0.9)
            if count >= 3:  # Require at least 3 occurrences
                common_workflows.append((subseq, count, confidence))

        if common_workflows:
            workflow_prefs["common_workflows"] = {
                "value": [list(w[0]) for w in common_workflows],
                "confidence": max([w[2] for w in common_workflows]),
            }

        return workflow_prefs

    def _learn_search_behavior(
        self, actions: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract search behavior preferences from user actions.

        Args:
            actions: List of user action records

        Returns:
            Dictionary of search behavior preferences with confidence scores
        """
        search_prefs = {}

        # Filter search-related actions
        search_actions = [
            a for a in actions if a["action_type"] == UnifiedUserActionType.SEARCH_QUERY
        ]

        if not search_actions:
            return {}

        # Analyze search terms
        search_terms = []
        for action in search_actions:
            if action.get("action_data") and "query" in action["action_data"]:
                search_terms.append(action["action_data"]["query"])

        if not search_terms:
            return {}

        # Extract common words in search queries
        words = Counter()
        for term in search_terms:
            for word in term.lower().split():
                if len(word) > 3:  # Ignore short words
                    words[word] += 1

        # Get most common search terms
        common_terms = []
        for word, count in words.most_common(10):
            confidence = min(0.5 + (count / len(search_terms)), 0.9)
            if count >= 2:  # Require at least 2 occurrences
                common_terms.append((word, count, confidence))

        if common_terms:
            search_prefs["common_search_terms"] = {
                "value": [t[0] for t in common_terms],
                "confidence": max([t[2] for t in common_terms]),
            }

        # Analyze search patterns (frequency, time between searches, etc.)
        if len(search_actions) >= 3:
            search_intervals = []
            for i in range(1, len(search_actions)):
                interval = (
                    search_actions[i]["timestamp"] - search_actions[i - 1]["timestamp"]
                )
                if interval < 3600:  # Only consider intervals less than an hour
                    search_intervals.append(interval)

            if search_intervals:
                avg_interval = sum(search_intervals) / len(search_intervals)
                search_prefs["search_frequency"] = {
                    "value": avg_interval,
                    "confidence": min(0.5 + (len(search_intervals) / 10), 0.9),
                }

        return search_prefs

    def _learn_sorting_preferences(
        self, actions: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract sorting preferences from user actions.

        Args:
            actions: List of user action records

        Returns:
            Dictionary of sorting preferences with confidence scores
        """
        sort_prefs = {}

        # Filter sort-related actions
        sort_actions = [
            a for a in actions if a["action_type"] == UnifiedUserActionType.SORT_APPLY
        ]

        if not sort_actions:
            return {}

        # Group by context (e.g., which page/view the sort was applied on)
        context_sorts = defaultdict(Counter)
        for action in sort_actions:
            context = action.get("action_context", "default")
            if action.get("action_data") and "sort_by" in action["action_data"]:
                sort_by = action["action_data"]["sort_by"]
                context_sorts[context][sort_by] += 1

        # Extract preferred sort for each context
        preferred_sorts = {}
        for context, sorts in context_sorts.items():
            total_sorts = sum(sorts.values())
            if total_sorts >= 3:  # Require at least 3 sort actions in this context
                most_common = sorts.most_common(1)[0]
                sort_by, count = most_common
                confidence = min(0.5 + (count / total_sorts), 0.9)
                preferred_sorts[context] = {"value": sort_by, "confidence": confidence}

        if preferred_sorts:
            sort_prefs["preferred_sort_by"] = preferred_sorts

        return sort_prefs

    def _learn_filtering_preferences(
        self, actions: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract filtering preferences from user actions.

        Args:
            actions: List of user action records

        Returns:
            Dictionary of filtering preferences with confidence scores
        """
        filter_prefs = {}

        # Filter filter-related actions
        filter_actions = [
            a for a in actions if a["action_type"] == UnifiedUserActionType.FILTER_APPLY
        ]

        if not filter_actions:
            return {}

        # Group by context (e.g., which page/view the filter was applied on)
        context_filters = defaultdict(list)
        for action in filter_actions:
            context = action.get("action_context", "default")
            if action.get("action_data") and "filters" in action["action_data"]:
                filters = action["action_data"]["filters"]
                context_filters[context].append(filters)

        # Extract common filters for each context
        common_filters = {}
        for context, filter_list in context_filters.items():
            if (
                len(filter_list) >= 3
            ):  # Require at least 3 filter actions in this context
                # Count individual filter keys and values
                filter_counts = defaultdict(Counter)
                for filters in filter_list:
                    for key, value in filters.items():
                        filter_counts[key][value] += 1

                # Extract most common value for each filter key
                preferred_filters = {}
                for key, values in filter_counts.items():
                    total_uses = sum(values.values())
                    if total_uses >= 2:  # Require at least 2 uses of this filter key
                        most_common = values.most_common(1)[0]
                        value, count = most_common
                        confidence = min(0.5 + (count / total_uses), 0.9)
                        if count / total_uses > 0.5:  # More than 50% of the time
                            preferred_filters[key] = {
                                "value": value,
                                "confidence": confidence,
                            }

                if preferred_filters:
                    common_filters[context] = preferred_filters

        if common_filters:
            filter_prefs["preferred_filters"] = common_filters

        return filter_prefs

    def _learn_time_patterns(
        self, actions: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract time-of-day usage patterns from user actions.

        Args:
            actions: List of user action records

        Returns:
            Dictionary of time pattern preferences with confidence scores
        """
        time_prefs = {}

        if not actions:
            return {}

        # Convert timestamps to hour of day
        hours = []
        for action in actions:
            timestamp = action["timestamp"]
            dt = datetime.fromtimestamp(timestamp)
            hours.append(dt.hour)

        # Count actions by hour of day
        hour_counts = Counter(hours)
        total_actions = len(actions)

        # Define time periods
        periods = {
            "morning": range(5, 12),  # 5am - 11am
            "afternoon": range(12, 18),  # 12pm - 5pm
            "evening": range(18, 23),  # 6pm - 10pm
            "night": [23, 0, 1, 2, 3, 4],  # 11pm - 4am
        }

        # Count actions in each period
        period_counts = {
            period: sum(hour_counts[h] for h in hours)
            for period, hours in periods.items()
        }

        # Find the most active period
        most_active_period = max(period_counts.items(), key=lambda x: x[1])
        period, count = most_active_period

        if count > 10:  # Require at least 10 actions in a period
            fraction = count / total_actions
            confidence = min(0.5 + fraction, 0.9)

            time_prefs["active_period"] = {"value": period, "confidence": confidence}

        # Identify peak hours (top 3 hours)
        peak_hours = []
        for hour, count in hour_counts.most_common(3):
            if count >= 5:  # Require at least 5 actions in an hour
                fraction = count / total_actions
                confidence = min(0.5 + fraction, 0.9)
                peak_hours.append((hour, confidence))

        if peak_hours:
            time_prefs["peak_hours"] = {
                "value": [h[0] for h in peak_hours],
                "confidence": max([h[1] for h in peak_hours]),
            }

        return time_prefs

    def _save_preferences(
        self, preferences: Dict[str, Dict[str, Any]], min_confidence: float = 0.0
    ):
        """
        Save the learned preferences to the database.

        Args:
            preferences: Dictionary of preferences by category
            min_confidence: Minimum confidence threshold for saving preferences
        """
        timestamp = get_current_timestamp()

        for category, prefs in preferences.items():
            for pref_key, pref_data in prefs.items():
                # Skip if below minimum confidence
                confidence = pref_data.get("confidence", 0)
                if confidence < min_confidence:
                    continue

                # Convert value to JSON string
                value = pref_data.get("value")
                value_str = json.dumps(value)

                # Check if preference already exists
                cursor = self.db.execute(
                    """
                    SELECT id, preference_value, confidence
                    FROM user_preferences
                    WHERE user_id = ? AND category = ? AND preference_key = ?
                    """,
                    (self.user_id, category, pref_key),
                )
                existing = cursor.fetchone()

                if existing:
                    # Only update if the confidence is higher or value has changed
                    existing_id, existing_value, existing_confidence = existing
                    existing_value = json.loads(existing_value)

                    # Check if value has changed or confidence is significantly higher
                    value_changed = existing_value != value
                    confidence_improved = confidence > existing_confidence + 0.1

                    if value_changed or confidence_improved:
                        # Update the preference
                        self.db.execute(
                            """
                            UPDATE user_preferences
                            SET preference_value = ?, confidence = ?, last_updated = ?
                            WHERE id = ?
                            """,
                            (value_str, confidence, timestamp, existing_id),
                        )

                        # Record in history
                        self.db.execute(
                            """
                            INSERT INTO user_preference_history
                            (id, user_id, category, preference_key, preference_value, confidence, timestamp, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                str(uuid.uuid4()),
                                self.user_id,
                                category,
                                pref_key,
                                value_str,
                                confidence,
                                timestamp,
                                datetime.now().isoformat(),
                            ),
                        )
                else:
                    # Insert new preference
                    self.db.execute(
                        """
                        INSERT INTO user_preferences
                        (id, user_id, category, preference_key, preference_value, confidence, last_updated, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            str(uuid.uuid4()),
                            self.user_id,
                            category,
                            pref_key,
                            value_str,
                            confidence,
                            timestamp,
                            datetime.now().isoformat(),
                        ),
                    )

                    # Record in history
                    self.db.execute(
                        """
                        INSERT INTO user_preference_history
                        (id, user_id, category, preference_key, preference_value, confidence, timestamp, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            str(uuid.uuid4()),
                            self.user_id,
                            category,
                            pref_key,
                            value_str,
                            confidence,
                            timestamp,
                            datetime.now().isoformat(),
                        ),
                    )

    def get_user_preferences(
        self, category: Optional[str] = None, min_confidence: float = 0.0
    ) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve stored user preferences.

        Args:
            category: Optional category to filter by
            min_confidence: Minimum confidence threshold

        Returns:
            Dictionary of user preferences by category
        """
        query = """
            SELECT category, preference_key, preference_value, confidence
            FROM user_preferences
            WHERE user_id = ? AND confidence >= ?
        """
        params = [self.user_id, min_confidence]

        if category:
            query += " AND category = ?"
            params.append(category)

        try:
            cursor = self.db.execute(query, tuple(params))

            # Group preferences by category
            preferences = defaultdict(dict)
            for row in cursor.fetchall():
                cat, key, value_str, confidence = row
                value = json.loads(value_str)

                preferences[cat][key] = {"value": value, "confidence": confidence}

            return dict(preferences)
        except Exception as e:
            logger.error("Failed to retrieve user preferences: %s", e)
            return {}
