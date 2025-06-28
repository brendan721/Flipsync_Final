"""Service for dashboard operations."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fs_agt_clean.core.config.manager import ConfigManager
from fs_agt_clean.core.db.database import Database

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for dashboard operations."""

    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        metrics_service: Optional[Any] = None,
        database: Optional[Database] = None,
    ):
        """Initialize the service.

        Args:
            config_manager: Configuration manager
            metrics_service: Metrics service
            database: Database instance
        """
        self.config_manager = config_manager
        self.metrics_service = metrics_service
        self.database = database
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the service."""
        try:
            # Initialize database if not provided
            if not self.database:
                if self.config_manager:
                    self.database = Database(self.config_manager)
                else:
                    # Use default database configuration
                    from fs_agt_clean.core.db.database import get_database

                    self.database = get_database()

            # Ensure database is connected
            if hasattr(self.database, "create_tables"):
                await self.database.create_tables()

            self._initialized = True
            logger.info("Dashboard service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize dashboard service: {e}")
            raise

    async def create_dashboard(self, dashboard_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new dashboard.

        Args:
            dashboard_data: Dashboard data

        Returns:
            Dict[str, Any]: Created dashboard data
        """
        if not self._initialized:
            await self.initialize()

        # For now, return a mock dashboard since we don't have the full repository
        dashboard_id = dashboard_data.get(
            "id", f"dashboard_{datetime.now().timestamp()}"
        )

        created_dashboard = {
            "id": dashboard_id,
            "name": dashboard_data.get("name", "New Dashboard"),
            "description": dashboard_data.get("description", ""),
            "config": dashboard_data.get("config", {}),
            "user_id": dashboard_data.get("user_id"),
            "is_public": dashboard_data.get("is_public", False),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(f"Created dashboard: {dashboard_id}")
        return created_dashboard

    async def get_dashboard(self, dashboard_id: str) -> Optional[Dict[str, Any]]:
        """Get a dashboard by ID.

        Args:
            dashboard_id: Dashboard ID

        Returns:
            Optional[Dict[str, Any]]: Dashboard data if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()

        # Mock dashboard data for development
        if dashboard_id == "test_dashboard":
            return {
                "id": dashboard_id,
                "name": "Test Dashboard",
                "description": "A test dashboard for development",
                "config": {
                    "widgets": [
                        {"type": "metric", "title": "Total Sales", "value": 12500},
                        {"type": "chart", "title": "Sales Trend", "data": []},
                    ]
                },
                "user_id": "test_user",
                "is_public": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

        logger.debug(f"Dashboard not found: {dashboard_id}")
        return None

    async def get_dashboards_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get dashboards by user ID.

        Args:
            user_id: UnifiedUser ID

        Returns:
            List[Dict[str, Any]]: List of dashboard data
        """
        if not self._initialized:
            await self.initialize()

        # Mock dashboards for development
        return [
            {
                "id": f"dashboard_1_{user_id}",
                "name": "Sales Dashboard",
                "description": "Sales performance dashboard",
                "config": {"widgets": []},
                "user_id": user_id,
                "is_public": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        ]

    async def get_public_dashboards(self) -> List[Dict[str, Any]]:
        """Get public dashboards.

        Returns:
            List[Dict[str, Any]]: List of public dashboard data
        """
        if not self._initialized:
            await self.initialize()

        # Mock public dashboards
        return [
            {
                "id": "public_dashboard_1",
                "name": "Public Sales Dashboard",
                "description": "Public sales performance dashboard",
                "config": {"widgets": []},
                "user_id": "system",
                "is_public": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        ]

    async def list_dashboards(self) -> List[Dict[str, Any]]:
        """Get all dashboards.

        Returns:
            List[Dict[str, Any]]: List of dashboard data
        """
        if not self._initialized:
            await self.initialize()

        # Combine user and public dashboards
        public_dashboards = await self.get_public_dashboards()
        return public_dashboards

    async def update_dashboard(
        self, dashboard_id: str, dashboard_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a dashboard.

        Args:
            dashboard_id: Dashboard ID
            dashboard_data: Dashboard data to update

        Returns:
            Optional[Dict[str, Any]]: Updated dashboard data if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()

        # Mock update - return updated dashboard
        existing = await self.get_dashboard(dashboard_id)
        if existing:
            existing.update(dashboard_data)
            existing["updated_at"] = datetime.now(timezone.utc).isoformat()
            logger.info(f"Updated dashboard: {dashboard_id}")
            return existing

        return None

    async def delete_dashboard(self, dashboard_id: str) -> bool:
        """Delete a dashboard.

        Args:
            dashboard_id: Dashboard ID

        Returns:
            bool: True if dashboard was deleted, False otherwise
        """
        if not self._initialized:
            await self.initialize()

        # Mock deletion - always return True for existing dashboards
        existing = await self.get_dashboard(dashboard_id)
        if existing:
            logger.info(f"Deleted dashboard: {dashboard_id}")
            return True

        return False

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics.

        Returns:
            Dict[str, Any]: Dashboard statistics
        """
        if not self._initialized:
            await self.initialize()

        return {
            "total_dashboards": 2,
            "public_dashboards": 1,
            "private_dashboards": 1,
            "active_users": 1,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    async def shutdown(self) -> None:
        """Shutdown the service."""
        try:
            if self.database and hasattr(self.database, "close"):
                await self.database.close()
            logger.info("Dashboard service shutdown successfully")
        except Exception as e:
            logger.error(f"Error shutting down dashboard service: {e}")
        finally:
            self._initialized = False
