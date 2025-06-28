"""
Enhanced alert service with database persistence and advanced features.

This service provides:
- Database-backed alert storage and retrieval
- Threshold-based alerting
- Alert deduplication and rate limiting
- Integration with notification systems
- Alert lifecycle management (acknowledge, resolve)
"""

import asyncio
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fs_agt_clean.core.db.database import Database
from fs_agt_clean.core.monitoring.alerts.alert_manager import Alert, AlertManager
from fs_agt_clean.database.models.metrics import (
    AlertCategory,
    AlertLevel,
    AlertRecord,
    AlertSource,
    MetricDataPoint,
    MetricThreshold,
)


class EnhancedAlertService:
    """Enhanced alert service with database persistence."""

    def __init__(
        self, database: Database, alert_manager: Optional[AlertManager] = None
    ):
        """Initialize the enhanced alert service.

        Args:
            database: Database instance for data operations
            alert_manager: Optional alert manager for in-memory operations
        """
        self.database = database
        self.alert_manager = alert_manager or AlertManager()
        self.logger = logging.getLogger(__name__)

        # Rate limiting and deduplication settings
        self.dedup_window_minutes = 5
        self.rate_limit_window_minutes = 60
        self.max_alerts_per_window = 10

        # Cache for recent alerts (for deduplication)
        self._recent_alerts: Dict[str, datetime] = {}
        self._alert_counts: Dict[str, int] = {}

    async def create_alert(
        self,
        title: str,
        message: str,
        level: AlertLevel = AlertLevel.INFO,
        category: AlertCategory = AlertCategory.SYSTEM,
        source: AlertSource = AlertSource.SYSTEM,
        details: Optional[Dict[str, Any]] = None,
        labels: Optional[Dict[str, str]] = None,
        correlation_id: Optional[str] = None,
        auto_resolve_minutes: Optional[int] = None,
    ) -> Optional[str]:
        """Create and store an alert.

        Args:
            title: Alert title
            message: Alert message
            level: Alert level
            category: Alert category
            source: Alert source
            details: Optional alert details
            labels: Optional alert labels
            correlation_id: Optional correlation ID
            auto_resolve_minutes: Optional auto-resolve time in minutes

        Returns:
            Alert ID if created, None if deduplicated
        """
        # Generate fingerprint for deduplication
        fingerprint = self._generate_fingerprint(title, message, level, category)

        # Check for deduplication
        if await self._should_deduplicate(fingerprint):
            self.logger.debug(f"Alert deduplicated: {fingerprint}")
            return None

        # Check rate limiting
        if await self._is_rate_limited(fingerprint):
            self.logger.warning(f"Alert rate limited: {fingerprint}")
            return None

        # Create alert record
        alert_id = f"alert_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{fingerprint[:8]}"

        async with self.database.get_session_context() as session:
            alert_record = AlertRecord(
                alert_id=alert_id,
                title=title,
                message=message,
                level=level,
                category=category,
                source=source,
                details=details,
                labels=labels,
                correlation_id=correlation_id,
                fingerprint=fingerprint,
                timestamp=datetime.now(timezone.utc),
            )

            session.add(alert_record)
            await session.commit()
            await session.refresh(alert_record)

        # Update deduplication cache
        self._recent_alerts[fingerprint] = datetime.now(timezone.utc)
        self._alert_counts[fingerprint] = self._alert_counts.get(fingerprint, 0) + 1

        # Send to alert manager for immediate processing
        if self.alert_manager:
            alert = Alert(
                title=title,
                message=message,
                level=level,
                category=category,
                source=source,
                details=details,
                labels=labels,
                alert_id=alert_id,
                correlation_id=correlation_id,
            )
            await self.alert_manager.create_alert(
                title=title,
                message=message,
                level=level,
                category=category,
                source=source,
                details=details,
                labels=labels,
                correlation_id=correlation_id,
            )

        self.logger.info(f"Created alert: {alert_id} - {title}")
        return alert_id

    async def acknowledge_alert(
        self, alert_id: str, acknowledged_by: str, notes: Optional[str] = None
    ) -> bool:
        """Acknowledge an alert.

        Args:
            alert_id: Alert ID to acknowledge
            acknowledged_by: UnifiedUser who acknowledged the alert
            notes: Optional acknowledgment notes

        Returns:
            True if acknowledged successfully, False otherwise
        """
        async with self.database.get_session_context() as session:
            query = select(AlertRecord).where(AlertRecord.alert_id == alert_id)
            result = await session.execute(query)
            alert = result.scalar_one_or_none()

            if not alert:
                self.logger.warning(f"Alert not found for acknowledgment: {alert_id}")
                return False

            if alert.acknowledged:
                self.logger.info(f"Alert already acknowledged: {alert_id}")
                return True

            alert.acknowledged = True
            alert.acknowledged_time = datetime.now(timezone.utc)
            alert.acknowledged_by = acknowledged_by

            if notes and alert.details:
                alert.details["acknowledgment_notes"] = notes
            elif notes:
                alert.details = {"acknowledgment_notes": notes}

            await session.commit()

            self.logger.info(f"Acknowledged alert: {alert_id} by {acknowledged_by}")
            return True

    async def resolve_alert(
        self, alert_id: str, resolved_by: str, resolution_notes: Optional[str] = None
    ) -> bool:
        """Resolve an alert.

        Args:
            alert_id: Alert ID to resolve
            resolved_by: UnifiedUser who resolved the alert
            resolution_notes: Optional resolution notes

        Returns:
            True if resolved successfully, False otherwise
        """
        async with self.database.get_session_context() as session:
            query = select(AlertRecord).where(AlertRecord.alert_id == alert_id)
            result = await session.execute(query)
            alert = result.scalar_one_or_none()

            if not alert:
                self.logger.warning(f"Alert not found for resolution: {alert_id}")
                return False

            if alert.resolved:
                self.logger.info(f"Alert already resolved: {alert_id}")
                return True

            alert.resolved = True
            alert.resolved_time = datetime.now(timezone.utc)
            alert.resolved_by = resolved_by
            alert.resolution_notes = resolution_notes

            await session.commit()

            self.logger.info(f"Resolved alert: {alert_id} by {resolved_by}")
            return True

    async def get_alerts(
        self,
        level: Optional[AlertLevel] = None,
        category: Optional[AlertCategory] = None,
        source: Optional[AlertSource] = None,
        acknowledged: Optional[bool] = None,
        resolved: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve alerts with filtering.

        Args:
            level: Optional level filter
            category: Optional category filter
            source: Optional source filter
            acknowledged: Optional acknowledged filter
            resolved: Optional resolved filter
            start_time: Optional start time filter
            end_time: Optional end time filter
            limit: Maximum number of results

        Returns:
            List of alerts as dictionaries
        """
        async with self.database.get_session_context() as session:
            query = select(AlertRecord)

            conditions = []
            if level:
                conditions.append(AlertRecord.level == level)
            if category:
                conditions.append(AlertRecord.category == category)
            if source:
                conditions.append(AlertRecord.source == source)
            if acknowledged is not None:
                conditions.append(AlertRecord.acknowledged == acknowledged)
            if resolved is not None:
                conditions.append(AlertRecord.resolved == resolved)
            if start_time:
                conditions.append(AlertRecord.timestamp >= start_time)
            if end_time:
                conditions.append(AlertRecord.timestamp <= end_time)

            if conditions:
                query = query.where(and_(*conditions))

            query = query.order_by(desc(AlertRecord.timestamp)).limit(limit)

            result = await session.execute(query)
            alerts = result.scalars().all()

            return [alert.to_dict() for alert in alerts]

    async def get_alert_summary(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get alert summary statistics.

        Args:
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            Dictionary containing alert summary
        """
        if not start_time:
            start_time = datetime.now(timezone.utc) - timedelta(hours=24)
        if not end_time:
            end_time = datetime.now(timezone.utc)

        async with self.database.get_session_context() as session:
            # Total alerts
            total_query = select(func.count(AlertRecord.id)).where(
                and_(
                    AlertRecord.timestamp >= start_time,
                    AlertRecord.timestamp <= end_time,
                )
            )
            total_result = await session.execute(total_query)
            total_alerts = total_result.scalar() or 0

            # Alerts by level
            level_query = (
                select(AlertRecord.level, func.count(AlertRecord.id))
                .where(
                    and_(
                        AlertRecord.timestamp >= start_time,
                        AlertRecord.timestamp <= end_time,
                    )
                )
                .group_by(AlertRecord.level)
            )

            level_result = await session.execute(level_query)
            alerts_by_level = {
                level.value: count for level, count in level_result.fetchall()
            }

            # Acknowledged alerts
            ack_query = select(func.count(AlertRecord.id)).where(
                and_(
                    AlertRecord.timestamp >= start_time,
                    AlertRecord.timestamp <= end_time,
                    AlertRecord.acknowledged == True,
                )
            )
            ack_result = await session.execute(ack_query)
            acknowledged_alerts = ack_result.scalar() or 0

            # Resolved alerts
            resolved_query = select(func.count(AlertRecord.id)).where(
                and_(
                    AlertRecord.timestamp >= start_time,
                    AlertRecord.timestamp <= end_time,
                    AlertRecord.resolved == True,
                )
            )
            resolved_result = await session.execute(resolved_query)
            resolved_alerts = resolved_result.scalar() or 0

            return {
                "time_period": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "duration_hours": (end_time - start_time).total_seconds() / 3600,
                },
                "summary": {
                    "total_alerts": total_alerts,
                    "acknowledged_alerts": acknowledged_alerts,
                    "resolved_alerts": resolved_alerts,
                    "unresolved_alerts": total_alerts - resolved_alerts,
                    "alerts_by_level": alerts_by_level,
                },
            }

    def _generate_fingerprint(
        self, title: str, message: str, level: AlertLevel, category: AlertCategory
    ) -> str:
        """Generate a fingerprint for alert deduplication.

        Args:
            title: Alert title
            message: Alert message
            level: Alert level
            category: Alert category

        Returns:
            Fingerprint string
        """
        content = f"{title}:{message}:{level.value}:{category.value}"
        return hashlib.md5(content.encode()).hexdigest()

    async def _should_deduplicate(self, fingerprint: str) -> bool:
        """Check if alert should be deduplicated.

        Args:
            fingerprint: Alert fingerprint

        Returns:
            True if should be deduplicated, False otherwise
        """
        # Check in-memory cache first
        if fingerprint in self._recent_alerts:
            last_time = self._recent_alerts[fingerprint]
            if datetime.now(timezone.utc) - last_time < timedelta(
                minutes=self.dedup_window_minutes
            ):
                return True

        # Check database for recent similar alerts
        cutoff_time = datetime.now(timezone.utc) - timedelta(
            minutes=self.dedup_window_minutes
        )

        async with self.database.get_session_context() as session:
            query = select(func.count(AlertRecord.id)).where(
                and_(
                    AlertRecord.fingerprint == fingerprint,
                    AlertRecord.timestamp >= cutoff_time,
                )
            )
            result = await session.execute(query)
            count = result.scalar() or 0

            return count > 0

    async def _is_rate_limited(self, fingerprint: str) -> bool:
        """Check if alert is rate limited.

        Args:
            fingerprint: Alert fingerprint

        Returns:
            True if rate limited, False otherwise
        """
        # Check in-memory cache first
        current_count = self._alert_counts.get(fingerprint, 0)
        if current_count >= self.max_alerts_per_window:
            return True

        # Check database for recent alerts of same type
        cutoff_time = datetime.now(timezone.utc) - timedelta(
            minutes=self.rate_limit_window_minutes
        )

        async with self.database.get_session_context() as session:
            query = select(func.count(AlertRecord.id)).where(
                and_(
                    AlertRecord.fingerprint == fingerprint,
                    AlertRecord.timestamp >= cutoff_time,
                )
            )
            result = await session.execute(query)
            count = result.scalar() or 0

            return count >= self.max_alerts_per_window
