"""
UnifiedUser Action Tracker

This module tracks user interactions and actions within the FlipSync application,
providing data for personalization algorithms to analyze and learn from.
"""

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from fs_agt_clean.api.routes.monitoring_routes import get_database
from fs_agt_clean.core.utils.time.time_utils import get_current_timestamp

logger = logging.getLogger(__name__)


class UnifiedUserActionType:
    """Enumeration of possible user action types."""

    PAGE_VIEW = "page_view"
    BUTTON_CLICK = "button_click"
    FORM_SUBMIT = "form_submit"
    SEARCH_QUERY = "search_query"
    FILTER_APPLY = "filter_apply"
    SORT_APPLY = "sort_apply"
    ITEM_VIEW = "item_view"
    FEATURE_USE = "feature_use"
    NAVIGATION = "navigation"
    TIME_SPENT = "time_spent"
    PREFERENCE_SET = "preference_set"


class UnifiedUserActionTracker:
    """
    Tracks and stores user actions for analysis and personalization.

    This class provides methods to record various user interactions with
    the application, store them in a database, and retrieve them for
    analysis by personalization algorithms.
    """

    def __init__(self, user_id: str):
        """
        Initialize the user action tracker for a specific user.

        Args:
            user_id: The ID of the user whose actions are being tracked
        """
        self.user_id = user_id
        self.db = get_database()
        self.session_id = str(uuid.uuid4())
        self.session_start_time = get_current_timestamp()
        self._init_db_tables()

    def _init_db_tables(self):
        """Ensure that the necessary database tables exist."""
        try:
            self.db.execute(
                """
                CREATE TABLE IF NOT EXISTS user_actions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    action_context TEXT,
                    action_data TEXT,
                    timestamp INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
            """
            )
            self.db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_user_actions_user_id
                ON user_actions(user_id)
            """
            )
            self.db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_user_actions_timestamp
                ON user_actions(timestamp)
            """
            )
        except Exception as e:
            logger.error("Failed to initialize user action tracker tables: %s", e)

    def track_action(
        self,
        action_type: str,
        action_context: Optional[str] = None,
        action_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Record a user action in the database.

        Args:
            action_type: The type of action (see UnifiedUserActionType)
            action_context: Additional context about where the action occurred
            action_data: Any additional data related to the action

        Returns:
            The ID of the recorded action
        """
        action_id = str(uuid.uuid4())
        timestamp = get_current_timestamp()

        try:
            self.db.execute(
                """
                INSERT INTO user_actions
                (id, user_id, session_id, action_type, action_context, action_data, timestamp, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    action_id,
                    self.user_id,
                    self.session_id,
                    action_type,
                    action_context,
                    json.dumps(action_data) if action_data else None,
                    timestamp,
                    datetime.now().isoformat(),
                ),
            )
            logger.debug(
                "Tracked user action: %s for user %s", action_type, self.user_id
            )
            return action_id
        except Exception as e:
            logger.error("Failed to track user action: %s", e)
            return None

    def get_user_actions(
        self,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        action_types: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve user actions within a specified time range.

        Args:
            start_time: Optional start timestamp for filtering actions
            end_time: Optional end timestamp for filtering actions
            action_types: Optional list of action types to filter by
            limit: Maximum number of actions to return
            offset: Number of actions to skip (for pagination)

        Returns:
            List of user action records
        """
        query = "SELECT * FROM user_actions WHERE user_id = ?"
        params = [self.user_id]

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)

        if action_types:
            placeholders = ", ".join(["?"] * len(action_types))
            query += f" AND action_type IN ({placeholders})"
            params.extend(action_types)

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        try:
            cursor = self.db.execute(query, tuple(params))
            results = []
            for row in cursor.fetchall():
                action = {
                    "id": row[0],
                    "user_id": row[1],
                    "session_id": row[2],
                    "action_type": row[3],
                    "action_context": row[4],
                    "action_data": json.loads(row[5]) if row[5] else None,
                    "timestamp": row[6],
                    "created_at": row[7],
                }
                results.append(action)
            return results
        except Exception as e:
            logger.error("Failed to retrieve user actions: %s", e)
            return []

    def get_action_count_by_type(
        self, start_time: Optional[int] = None, end_time: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Get a count of actions grouped by action type.

        Args:
            start_time: Optional start timestamp for filtering actions
            end_time: Optional end timestamp for filtering actions

        Returns:
            Dictionary mapping action types to counts
        """
        query = """
            SELECT action_type, COUNT(*) as count
            FROM user_actions
            WHERE user_id = ?
        """
        params = [self.user_id]

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)

        query += " GROUP BY action_type"

        try:
            cursor = self.db.execute(query, tuple(params))
            return {row[0]: row[1] for row in cursor.fetchall()}
        except Exception as e:
            logger.error("Failed to get action counts by type: %s", e)
            return {}

    def end_session(self):
        """
        End the current tracking session and calculate session metrics.

        This records the session duration and other session-level metrics.
        """
        session_end_time = get_current_timestamp()
        session_duration = session_end_time - self.session_start_time

        # Record the session itself
        try:
            self.db.execute(
                """
                INSERT INTO user_sessions
                (id, user_id, start_time, end_time, duration)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    self.session_id,
                    self.user_id,
                    self.session_start_time,
                    session_end_time,
                    session_duration,
                ),
            )
            logger.debug("Ended session %s for user %s", self.session_id, self.user_id)
        except Exception as e:
            # If the table doesn't exist yet, create it
            if "no such table" in str(e).lower():
                self.db.execute(
                    """
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        start_time INTEGER NOT NULL,
                        end_time INTEGER NOT NULL,
                        duration INTEGER NOT NULL
                    )
                """
                )
                # Try again
                self.end_session()
            else:
                logger.error("Failed to end user session: %s", e)
