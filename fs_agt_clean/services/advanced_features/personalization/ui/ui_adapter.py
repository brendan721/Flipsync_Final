"""
UI Adapter for Personalization

This module provides functionality to adapt the user interface based on
learned user preferences and behavior patterns.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from fs_agt_clean.core.utils.time.time_utils import get_current_timestamp
from fs_agt_clean.services.database import get_database
from fs_agt_clean.services.personalization.preference_learner import (
    PreferenceCategory,
    PreferenceLearner,
)

logger = logging.getLogger(__name__)


class UIComponent:
    """Enumeration of UI components that can be personalized."""

    DASHBOARD = "dashboard"
    NAVIGATION = "navigation"
    PRODUCT_LIST = "product_list"
    SEARCH_RESULTS = "search_results"
    DETAIL_VIEW = "detail_view"
    REPORTING = "reporting"
    SETTINGS = "settings"
    WORKFLOW = "workflow"


class UIAdapter:
    """
    Adapts the user interface based on learned user preferences.

    This class applies personalization settings to various UI components
    based on the user's learned preferences and current context.
    """

    def __init__(self, user_id: str):
        """
        Initialize the UI adapter for a specific user.

        Args:
            user_id: The ID of the user for whom the UI is being adapted
        """
        self.user_id = user_id
        self.db = get_database()
        self.preference_learner = PreferenceLearner(user_id)
        self._init_db_tables()

    def _init_db_tables(self):
        """Ensure that the necessary database tables exist."""
        try:
            # Table for storing UI personalization settings
            self.db.execute(
                """
                CREATE TABLE IF NOT EXISTS ui_personalization (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    component TEXT NOT NULL,
                    settings TEXT NOT NULL,
                    applied_at INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(user_id, component)
                )
            """
            )

            self.db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_ui_personalization_user_id
                ON ui_personalization(user_id)
            """
            )
        except Exception as e:
            logger.error("Failed to initialize UI adapter tables: %s", e)

    def get_personalized_ui(
        self,
        component: str,
        context: Optional[Dict[str, Any]] = None,
        min_confidence: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Get personalized UI settings for a specific component.

        Args:
            component: The UI component to personalize (see UIComponent)
            context: Additional context information for the current view
            min_confidence: Minimum confidence required for applying a preference

        Returns:
            Dictionary of personalized UI settings
        """
        # Get user preferences with sufficient confidence
        preferences = self.preference_learner.get_user_preferences(
            min_confidence=min_confidence
        )

        # Personalization settings to apply
        personalization = {}

        # Apply appropriate personalization based on the component
        if component == UIComponent.DASHBOARD:
            personalization = self._personalize_dashboard(preferences, context)
        elif component == UIComponent.NAVIGATION:
            personalization = self._personalize_navigation(preferences, context)
        elif component == UIComponent.PRODUCT_LIST:
            personalization = self._personalize_product_list(preferences, context)
        elif component == UIComponent.SEARCH_RESULTS:
            personalization = self._personalize_search_results(preferences, context)
        elif component == UIComponent.DETAIL_VIEW:
            personalization = self._personalize_detail_view(preferences, context)
        elif component == UIComponent.REPORTING:
            personalization = self._personalize_reporting(preferences, context)
        elif component == UIComponent.SETTINGS:
            personalization = self._personalize_settings(preferences, context)
        elif component == UIComponent.WORKFLOW:
            personalization = self._personalize_workflow(preferences, context)
        else:
            logger.warning("Unknown UI component: %s", component)

        # Save the applied personalization
        if personalization:
            self._save_personalization(component, personalization)

        return personalization

    def _personalize_dashboard(
        self,
        preferences: Dict[str, Dict[str, Dict[str, Any]]],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Personalize the dashboard UI component.

        Args:
            preferences: UnifiedUser preferences by category
            context: Additional context information

        Returns:
            Dictionary of personalized dashboard settings
        """
        dashboard_settings = {
            "layout": "default",
            "widgets": [],
            "default_view": "overview",
        }

        # Use feature usage preferences to prioritize widgets
        if PreferenceCategory.FEATURE_USAGE in preferences:
            feature_prefs = preferences[PreferenceCategory.FEATURE_USAGE]
            if "most_used_features" in feature_prefs:
                most_used = feature_prefs["most_used_features"]["value"]
                # Map features to relevant widgets
                widgets = []
                for feature in most_used:
                    if feature == "analytics":
                        widgets.append("analytics_summary")
                    elif feature == "inventory":
                        widgets.append("inventory_status")
                    elif feature == "orders":
                        widgets.append("recent_orders")
                    elif feature == "products":
                        widgets.append("product_performance")
                    elif feature == "campaigns":
                        widgets.append("campaign_metrics")

                if widgets:
                    dashboard_settings["widgets"] = widgets

        # Use UI layout preferences for layout and default view
        if PreferenceCategory.UI_LAYOUT in preferences:
            ui_prefs = preferences[PreferenceCategory.UI_LAYOUT]
            if "preferred_pages" in ui_prefs:
                preferred_pages = ui_prefs["preferred_pages"]["value"]
                # Set default view based on most preferred page
                if preferred_pages:
                    for page in preferred_pages:
                        if "dashboard" in page:
                            view = page.split("-")[-1] if "-" in page else "overview"
                            dashboard_settings["default_view"] = view
                            break

        # Use content preferences to highlight relevant content
        if PreferenceCategory.CONTENT_INTERESTS in preferences:
            content_prefs = preferences[PreferenceCategory.CONTENT_INTERESTS]
            if "favorite_categories" in content_prefs:
                favorite_categories = content_prefs["favorite_categories"]["value"]
                dashboard_settings["highlighted_categories"] = favorite_categories[:3]

        # Use time of day to adjust layout
        if (
            PreferenceCategory.TIME_OF_DAY in preferences
            and context
            and "current_hour" in context
        ):
            time_prefs = preferences[PreferenceCategory.TIME_OF_DAY]
            current_hour = context["current_hour"]

            # Adjust layout based on time of day
            if "active_period" in time_prefs:
                active_period = time_prefs["active_period"]["value"]
                if active_period == "morning":
                    dashboard_settings["layout"] = "focused"
                elif active_period == "afternoon":
                    dashboard_settings["layout"] = "balanced"
                elif active_period == "evening":
                    dashboard_settings["layout"] = "compact"
                elif active_period == "night":
                    dashboard_settings["layout"] = "dark_mode"

        return dashboard_settings

    def _personalize_navigation(
        self,
        preferences: Dict[str, Dict[str, Dict[str, Any]]],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Personalize the navigation UI component.

        Args:
            preferences: UnifiedUser preferences by category
            context: Additional context information

        Returns:
            Dictionary of personalized navigation settings
        """
        nav_settings = {"style": "standard", "quick_links": [], "expanded_sections": []}

        # Use UI layout preferences for navigation patterns
        if PreferenceCategory.UI_LAYOUT in preferences:
            ui_prefs = preferences[PreferenceCategory.UI_LAYOUT]

            # Set quick links based on preferred pages
            if "preferred_pages" in ui_prefs:
                preferred_pages = ui_prefs["preferred_pages"]["value"]
                if preferred_pages:
                    nav_settings["quick_links"] = preferred_pages[:5]

            # Set expanded sections based on navigation patterns
            if "navigation_patterns" in ui_prefs:
                nav_patterns = ui_prefs["navigation_patterns"]["value"]
                if nav_patterns:
                    # Extract starting points of common navigation flows
                    start_points = set()
                    for pattern in nav_patterns:
                        if "->" in pattern:
                            start = pattern.split("->")[0]
                            start_section = (
                                start.split("/")[0] if "/" in start else start
                            )
                            start_points.add(start_section)

                    if start_points:
                        nav_settings["expanded_sections"] = list(start_points)

        # Use workflow patterns to suggest next actions
        if PreferenceCategory.WORKFLOW_PATTERNS in preferences:
            workflow_prefs = preferences[PreferenceCategory.WORKFLOW_PATTERNS]
            if (
                "common_workflows" in workflow_prefs
                and context
                and "current_page" in context
            ):
                current_page = context["current_page"]
                common_workflows = workflow_prefs["common_workflows"]["value"]

                # Find workflows that start with the current page
                next_steps = []
                for workflow in common_workflows:
                    workflow_str = "->".join(workflow)
                    if workflow_str.startswith(current_page) and "->" in workflow_str:
                        next_step = workflow_str.split("->")[1]
                        next_steps.append(next_step)

                if next_steps:
                    nav_settings["suggested_next"] = next_steps[:3]

        # Use feature usage to highlight important sections
        if PreferenceCategory.FEATURE_USAGE in preferences:
            feature_prefs = preferences[PreferenceCategory.FEATURE_USAGE]
            if "most_used_features" in feature_prefs:
                most_used = feature_prefs["most_used_features"]["value"]
                nav_settings["highlighted_sections"] = most_used[:3]

        return nav_settings

    def _personalize_product_list(
        self,
        preferences: Dict[str, Dict[str, Dict[str, Any]]],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Personalize the product list UI component.

        Args:
            preferences: UnifiedUser preferences by category
            context: Additional context information

        Returns:
            Dictionary of personalized product list settings
        """
        list_settings = {
            "default_view": "grid",
            "sort_by": "relevance",
            "columns_to_show": ["name", "price", "stock", "category"],
            "items_per_page": 20,
        }

        # Use sorting preferences
        if PreferenceCategory.SORTING_PREFERENCE in preferences:
            sort_prefs = preferences[PreferenceCategory.SORTING_PREFERENCE]
            if "preferred_sort_by" in sort_prefs:
                preferred_sorts = sort_prefs["preferred_sort_by"]
                if "product_list" in preferred_sorts:
                    list_settings["sort_by"] = preferred_sorts["product_list"]["value"]
                elif "default" in preferred_sorts:
                    list_settings["sort_by"] = preferred_sorts["default"]["value"]

        # Use filtering preferences
        if PreferenceCategory.FILTERING_PREFERENCE in preferences:
            filter_prefs = preferences[PreferenceCategory.FILTERING_PREFERENCE]
            if "preferred_filters" in filter_prefs:
                preferred_filters = filter_prefs["preferred_filters"]
                if "product_list" in preferred_filters:
                    list_settings["default_filters"] = preferred_filters["product_list"]

        # Use content interests for highlighting
        if PreferenceCategory.CONTENT_INTERESTS in preferences:
            content_prefs = preferences[PreferenceCategory.CONTENT_INTERESTS]
            if "favorite_categories" in content_prefs:
                favorite_categories = content_prefs["favorite_categories"]["value"]
                list_settings["highlighted_categories"] = favorite_categories[:3]

        # Use UI layout preferences for view type
        if PreferenceCategory.UI_LAYOUT in preferences:
            ui_prefs = preferences[PreferenceCategory.UI_LAYOUT]

            # Set preferred view type (grid vs list)
            if "preferred_view_type" in ui_prefs:
                list_settings["default_view"] = ui_prefs["preferred_view_type"]["value"]

            # Adjust items per page based on preferred density
            if "preferred_density" in ui_prefs:
                density = ui_prefs["preferred_density"]["value"]
                if density == "compact":
                    list_settings["items_per_page"] = 40
                elif density == "comfortable":
                    list_settings["items_per_page"] = 15

        return list_settings

    def _personalize_search_results(
        self,
        preferences: Dict[str, Dict[str, Dict[str, Any]]],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Personalize the search results UI component.

        Args:
            preferences: UnifiedUser preferences by category
            context: Additional context information

        Returns:
            Dictionary of personalized search results settings
        """
        search_settings = {
            "default_view": "list",
            "sort_by": "relevance",
            "filters_expanded": False,
            "results_per_page": 20,
        }

        # Use search behavior preferences
        if PreferenceCategory.SEARCH_BEHAVIOR in preferences:
            search_prefs = preferences[PreferenceCategory.SEARCH_BEHAVIOR]

            # Set up search suggestions based on common search terms
            if "common_search_terms" in search_prefs:
                common_terms = search_prefs["common_search_terms"]["value"]
                search_settings["search_suggestions"] = common_terms

            # Adjust relevance weighting based on search frequency
            if "search_frequency" in search_prefs:
                frequency = search_prefs["search_frequency"]["value"]
                if frequency < 60:  # Less than a minute between searches
                    search_settings["relevance_weighting"] = "recent"
                elif frequency < 300:  # Less than 5 minutes
                    search_settings["relevance_weighting"] = "balanced"
                else:
                    search_settings["relevance_weighting"] = "exact"

        # Use sorting preferences
        if PreferenceCategory.SORTING_PREFERENCE in preferences:
            sort_prefs = preferences[PreferenceCategory.SORTING_PREFERENCE]
            if "preferred_sort_by" in sort_prefs:
                preferred_sorts = sort_prefs["preferred_sort_by"]
                if "search_results" in preferred_sorts:
                    search_settings["sort_by"] = preferred_sorts["search_results"][
                        "value"
                    ]

        # Use filtering preferences
        if PreferenceCategory.FILTERING_PREFERENCE in preferences:
            filter_prefs = preferences[PreferenceCategory.FILTERING_PREFERENCE]

            # Determine if filters should be expanded by default
            if "filter_usage_frequency" in filter_prefs:
                frequency = filter_prefs["filter_usage_frequency"]["value"]
                if frequency > 0.5:  # UnifiedUser filters more than half the time
                    search_settings["filters_expanded"] = True

            # Apply default filters
            if "preferred_filters" in filter_prefs:
                preferred_filters = filter_prefs["preferred_filters"]
                if "search_results" in preferred_filters:
                    search_settings["default_filters"] = preferred_filters[
                        "search_results"
                    ]

        # Use content interests to boost certain results
        if PreferenceCategory.CONTENT_INTERESTS in preferences:
            content_prefs = preferences[PreferenceCategory.CONTENT_INTERESTS]
            if "favorite_categories" in content_prefs:
                favorite_categories = content_prefs["favorite_categories"]["value"]
                search_settings["boosted_categories"] = favorite_categories

        return search_settings

    def _personalize_detail_view(
        self,
        preferences: Dict[str, Dict[str, Dict[str, Any]]],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Personalize the detail view UI component.

        Args:
            preferences: UnifiedUser preferences by category
            context: Additional context information

        Returns:
            Dictionary of personalized detail view settings
        """
        detail_settings = {
            "sections_order": ["summary", "details", "related", "actions"],
            "expanded_sections": ["summary"],
            "highlight_fields": [],
        }

        # Use UI layout preferences for section ordering
        if PreferenceCategory.UI_LAYOUT in preferences:
            ui_prefs = preferences[PreferenceCategory.UI_LAYOUT]

            # Set expanded sections based on dwell time
            if "section_dwell_time" in ui_prefs:
                dwell_times = ui_prefs["section_dwell_time"]["value"]
                if isinstance(dwell_times, dict):
                    # Sort sections by dwell time
                    sorted_sections = sorted(
                        dwell_times.items(), key=lambda x: x[1], reverse=True
                    )
                    # Expand the top 2 sections
                    detail_settings["expanded_sections"] = [
                        s[0] for s in sorted_sections[:2]
                    ]
                    # Order sections by dwell time
                    detail_settings["sections_order"] = [s[0] for s in sorted_sections]

        # Use feature usage to highlight important actions
        if PreferenceCategory.FEATURE_USAGE in preferences:
            feature_prefs = preferences[PreferenceCategory.FEATURE_USAGE]
            if "most_used_features" in feature_prefs:
                most_used = feature_prefs["most_used_features"]["value"]

                # Map features to detail view actions
                important_actions = []
                for feature in most_used:
                    if feature == "edit":
                        important_actions.append("edit_button")
                    elif feature == "duplicate":
                        important_actions.append("duplicate_button")
                    elif feature == "delete":
                        important_actions.append("delete_button")
                    elif feature == "share":
                        important_actions.append("share_button")

                if important_actions:
                    detail_settings["highlighted_actions"] = important_actions

        # Use workflow patterns for suggested next steps
        if PreferenceCategory.WORKFLOW_PATTERNS in preferences:
            workflow_prefs = preferences[PreferenceCategory.WORKFLOW_PATTERNS]
            if (
                "common_workflows" in workflow_prefs
                and context
                and "item_type" in context
            ):
                item_type = context["item_type"]
                common_workflows = workflow_prefs["common_workflows"]["value"]

                # Find workflows related to this item type
                next_steps = []
                for workflow in common_workflows:
                    if len(workflow) >= 2 and workflow[0] == f"view_{item_type}":
                        next_steps.append(workflow[1])

                if next_steps:
                    detail_settings["suggested_actions"] = next_steps

        # Use content interests to highlight certain fields
        if PreferenceCategory.CONTENT_INTERESTS in preferences:
            content_prefs = preferences[PreferenceCategory.CONTENT_INTERESTS]
            if (
                "favorite_categories" in content_prefs
                and context
                and "fields" in context
            ):
                favorite_categories = content_prefs["favorite_categories"]["value"]
                available_fields = context["fields"]

                # Highlight fields related to favorite categories
                highlight_fields = []
                for field in available_fields:
                    for category in favorite_categories:
                        if category.lower() in field.lower():
                            highlight_fields.append(field)
                            break

                if highlight_fields:
                    detail_settings["highlight_fields"] = highlight_fields

        return detail_settings

    def _personalize_reporting(
        self,
        preferences: Dict[str, Dict[str, Dict[str, Any]]],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Personalize the reporting UI component.

        Args:
            preferences: UnifiedUser preferences by category
            context: Additional context information

        Returns:
            Dictionary of personalized reporting settings
        """
        report_settings = {
            "default_view": "summary",
            "default_period": "last_30_days",
            "default_charts": ["line_chart", "bar_chart", "pie_chart"],
            "metrics_to_show": ["revenue", "orders", "conversion_rate", "traffic"],
        }

        # Use content interests for metrics prioritization
        if PreferenceCategory.CONTENT_INTERESTS in preferences:
            content_prefs = preferences[PreferenceCategory.CONTENT_INTERESTS]
            if "favorite_categories" in content_prefs:
                favorite_categories = content_prefs["favorite_categories"]["value"]

                # Map categories to relevant metrics
                prioritized_metrics = []
                for category in favorite_categories:
                    if category == "sales":
                        prioritized_metrics.extend(["revenue", "orders", "aov"])
                    elif category == "marketing":
                        prioritized_metrics.extend(
                            ["traffic", "conversion_rate", "cac"]
                        )
                    elif category == "products":
                        prioritized_metrics.extend(
                            ["top_products", "inventory_turnover"]
                        )
                    elif category == "customers":
                        prioritized_metrics.extend(
                            ["new_customers", "ltv", "retention"]
                        )

                if prioritized_metrics:
                    # Remove duplicates while preserving order
                    seen = set()
                    unique_metrics = [
                        m for m in prioritized_metrics if not (m in seen or seen.add(m))
                    ]
                    report_settings["metrics_to_show"] = unique_metrics[
                        :6
                    ]  # Limit to 6 metrics

        # Use UI layout preferences for view and chart types
        if PreferenceCategory.UI_LAYOUT in preferences:
            ui_prefs = preferences[PreferenceCategory.UI_LAYOUT]

            # Set default view based on preferred pages
            if "preferred_pages" in ui_prefs:
                preferred_pages = ui_prefs["preferred_pages"]["value"]
                for page in preferred_pages:
                    if "reports" in page and "-" in page:
                        view = page.split("-")[1]
                        report_settings["default_view"] = view
                        break

            # Set preferred chart types
            if "preferred_charts" in ui_prefs:
                preferred_charts = ui_prefs["preferred_charts"]["value"]
                if preferred_charts:
                    report_settings["default_charts"] = preferred_charts

        # Use time patterns for default period selection
        if PreferenceCategory.TIME_OF_DAY in preferences:
            time_prefs = preferences[PreferenceCategory.TIME_OF_DAY]

            # Adjust time period based on typical usage patterns
            if "active_period" in time_prefs:
                active_period = time_prefs["active_period"]["value"]
                if active_period == "morning":
                    # Morning users often check daily reports
                    report_settings["default_period"] = "yesterday"
                elif active_period == "evening" or active_period == "night":
                    # Evening/night users often look at longer trends
                    report_settings["default_period"] = "last_90_days"

        # Use session duration for detail level
        if PreferenceCategory.SESSION_DURATION in preferences:
            duration_prefs = preferences[PreferenceCategory.SESSION_DURATION]

            # Adjust detail level based on typical session length
            if "average_duration" in duration_prefs:
                avg_duration = duration_prefs["average_duration"]["value"]
                if avg_duration < 300:  # Less than 5 minutes
                    report_settings["detail_level"] = "summary"
                elif avg_duration < 900:  # Less than 15 minutes
                    report_settings["detail_level"] = "standard"
                else:
                    report_settings["detail_level"] = "detailed"

        return report_settings

    def _personalize_settings(
        self,
        preferences: Dict[str, Dict[str, Dict[str, Any]]],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Personalize the settings UI component.

        Args:
            preferences: UnifiedUser preferences by category
            context: Additional context information

        Returns:
            Dictionary of personalized settings page settings
        """
        settings_personalization = {
            "highlight_sections": [],
            "expanded_sections": ["general"],
            "suggested_changes": [],
        }

        # Use feature usage to highlight important settings sections
        if PreferenceCategory.FEATURE_USAGE in preferences:
            feature_prefs = preferences[PreferenceCategory.FEATURE_USAGE]
            if "most_used_features" in feature_prefs:
                most_used = feature_prefs["most_used_features"]["value"]

                # Map features to settings sections
                important_sections = []
                for feature in most_used:
                    if feature == "notifications":
                        important_sections.append("notifications")
                    elif feature == "account":
                        important_sections.append("account")
                    elif feature == "integrations":
                        important_sections.append("integrations")
                    elif feature == "team":
                        important_sections.append("team")
                    elif feature == "billing":
                        important_sections.append("billing")

                if important_sections:
                    settings_personalization["highlight_sections"] = important_sections
                    # Expand the most used section
                    if important_sections:
                        settings_personalization["expanded_sections"] = [
                            important_sections[0]
                        ]

        # Use UI layout preferences for sections to expand
        if PreferenceCategory.UI_LAYOUT in preferences:
            ui_prefs = preferences[PreferenceCategory.UI_LAYOUT]

            # Expand sections with high dwell time
            if "section_dwell_time" in ui_prefs:
                dwell_times = ui_prefs["section_dwell_time"]["value"]
                if isinstance(dwell_times, dict):
                    # Get settings-related sections with high dwell time
                    settings_sections = {
                        k: v
                        for k, v in dwell_times.items()
                        if k.startswith("settings-")
                    }
                    if settings_sections:
                        # Sort by dwell time and expand top 2
                        sorted_sections = sorted(
                            settings_sections.items(), key=lambda x: x[1], reverse=True
                        )
                        settings_personalization["expanded_sections"] = [
                            s[0].replace("settings-", "") for s in sorted_sections[:2]
                        ]

        # Based on user activity, suggest settings changes
        if context and "usage_stats" in context:
            usage_stats = context["usage_stats"]
            suggestions = []

            # Suggest notification settings based on frequency
            if (
                "notification_open_rate" in usage_stats
                and usage_stats["notification_open_rate"] < 0.2
            ):
                suggestions.append(
                    {
                        "setting": "notifications",
                        "suggestion": "Reduce notification frequency",
                        "reason": "You open less than 20% of notifications",
                    }
                )

            # Suggest color scheme based on time of day
            if PreferenceCategory.TIME_OF_DAY in preferences:
                time_prefs = preferences[PreferenceCategory.TIME_OF_DAY]
                if (
                    "active_period" in time_prefs
                    and time_prefs["active_period"]["value"] == "night"
                ):
                    suggestions.append(
                        {
                            "setting": "appearance",
                            "suggestion": "Enable dark mode",
                            "reason": "You often use the app during nighttime",
                        }
                    )

            if suggestions:
                settings_personalization["suggested_changes"] = suggestions

        return settings_personalization

    def _personalize_workflow(
        self,
        preferences: Dict[str, Dict[str, Dict[str, Any]]],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Personalize workflow-related UI components.

        Args:
            preferences: UnifiedUser preferences by category
            context: Additional context information

        Returns:
            Dictionary of personalized workflow settings
        """
        workflow_settings = {
            "quick_actions": [],
            "default_steps": [],
            "suggested_automations": [],
        }

        # Use workflow patterns for suggested flows and steps
        if PreferenceCategory.WORKFLOW_PATTERNS in preferences:
            workflow_prefs = preferences[PreferenceCategory.WORKFLOW_PATTERNS]

            # Set up quick actions based on common workflows
            if "common_workflows" in workflow_prefs:
                common_workflows = workflow_prefs["common_workflows"]["value"]

                # Extract starting points of common workflows
                quick_actions = []
                for workflow in common_workflows:
                    if len(workflow) > 0:
                        quick_actions.append(workflow[0])

                if quick_actions:
                    # Remove duplicates while preserving order
                    seen = set()
                    workflow_settings["quick_actions"] = [
                        action
                        for action in quick_actions
                        if not (action in seen or seen.add(action))
                    ][
                        :5
                    ]  # Limit to 5 actions

                # Find the most common complete workflow for default steps
                if common_workflows and len(common_workflows[0]) >= 3:
                    workflow_settings["default_steps"] = common_workflows[0]

        # Use feature usage for suggested automations
        if PreferenceCategory.FEATURE_USAGE in preferences:
            feature_prefs = preferences[PreferenceCategory.FEATURE_USAGE]
            if "repetitive_actions" in feature_prefs:
                repetitive = feature_prefs["repetitive_actions"]["value"]

                # Suggest automations for repetitive tasks
                automations = []
                for action in repetitive:
                    if action == "product_update":
                        automations.append(
                            {
                                "name": "Automate Product Updates",
                                "description": "Automatically update product information from spreadsheets",
                            }
                        )
                    elif action == "order_processing":
                        automations.append(
                            {
                                "name": "Order Workflow Automation",
                                "description": "Automatically process orders based on predefined rules",
                            }
                        )
                    elif action == "inventory_check":
                        automations.append(
                            {
                                "name": "Inventory Alerts",
                                "description": "Get notified when inventory reaches threshold levels",
                            }
                        )
                    elif action == "reporting":
                        automations.append(
                            {
                                "name": "Scheduled Reports",
                                "description": "Automatically generate and send reports on schedule",
                            }
                        )

                if automations:
                    workflow_settings["suggested_automations"] = automations

        # Adjust based on time patterns
        if (
            PreferenceCategory.TIME_OF_DAY in preferences
            and context
            and "current_hour" in context
        ):
            time_prefs = preferences[PreferenceCategory.TIME_OF_DAY]
            current_hour = context["current_hour"]

            # Prioritize morning/evening specific workflows
            if "active_period" in time_prefs:
                active_period = time_prefs["active_period"]["value"]

                if active_period == "morning":
                    workflow_settings["morning_priority"] = True
                    if (
                        "quick_actions" in workflow_settings
                        and workflow_settings["quick_actions"]
                    ):
                        # Prioritize planning and review actions in the morning
                        morning_actions = [
                            "review_dashboard",
                            "check_reports",
                            "plan_campaigns",
                        ]
                        prioritized = [
                            a
                            for a in morning_actions
                            if a in workflow_settings["quick_actions"]
                        ]
                        remaining = [
                            a
                            for a in workflow_settings["quick_actions"]
                            if a not in morning_actions
                        ]
                        workflow_settings["quick_actions"] = prioritized + remaining

                elif active_period == "evening":
                    workflow_settings["evening_priority"] = True
                    if (
                        "quick_actions" in workflow_settings
                        and workflow_settings["quick_actions"]
                    ):
                        # Prioritize wrap-up actions in the evening
                        evening_actions = [
                            "finalize_orders",
                            "schedule_tasks",
                            "review_performance",
                        ]
                        prioritized = [
                            a
                            for a in evening_actions
                            if a in workflow_settings["quick_actions"]
                        ]
                        remaining = [
                            a
                            for a in workflow_settings["quick_actions"]
                            if a not in evening_actions
                        ]
                        workflow_settings["quick_actions"] = prioritized + remaining

        return workflow_settings

    def _save_personalization(self, component: str, settings: Dict[str, Any]):
        """
        Save the applied personalization settings to the database.

        Args:
            component: The UI component that was personalized
            settings: The personalization settings that were applied
        """
        timestamp = get_current_timestamp()
        settings_json = json.dumps(settings)

        try:
            # Check if settings already exist for this component
            cursor = self.db.execute(
                """
                SELECT id
                FROM ui_personalization
                WHERE user_id = ? AND component = ?
                """,
                (self.user_id, component),
            )
            existing = cursor.fetchone()

            if existing:
                # Update existing settings
                self.db.execute(
                    """
                    UPDATE ui_personalization
                    SET settings = ?, applied_at = ?
                    WHERE id = ?
                    """,
                    (settings_json, timestamp, existing[0]),
                )
            else:
                # Insert new settings
                self.db.execute(
                    """
                    INSERT INTO ui_personalization
                    (id, user_id, component, settings, applied_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        self.user_id,
                        component,
                        settings_json,
                        timestamp,
                        datetime.now().isoformat(),
                    ),
                )
        except Exception as e:
            logger.error("Failed to save UI personalization settings: %s", e)

    def get_all_personalization_settings(self) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve all saved UI personalization settings for the user.

        Returns:
            Dictionary of personalization settings by component
        """
        try:
            cursor = self.db.execute(
                """
                SELECT component, settings
                FROM ui_personalization
                WHERE user_id = ?
                """,
                (self.user_id,),
            )

            settings = {}
            for row in cursor.fetchall():
                component, settings_json = row
                settings[component] = json.loads(settings_json)

            return settings
        except Exception as e:
            logger.error("Failed to retrieve UI personalization settings: %s", e)
            return {}
