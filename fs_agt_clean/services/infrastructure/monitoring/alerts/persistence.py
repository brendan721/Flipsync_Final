"""Alert persistence layer for storing and retrieving alerts."""

import abc
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Union

try:
    import aiofiles

    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False
    aiofiles = None

try:
    import aiosqlite

    AIOSQLITE_AVAILABLE = True
except ImportError:
    AIOSQLITE_AVAILABLE = False
    aiosqlite = None

from fs_agt_clean.core.monitoring.alerts.models import Alert, AlertSeverity
from fs_agt_clean.core.protocols.alerting_protocol import AlertStatus

from ..alert_types import AlertType
from ..metric_types import MetricType


class AlertStorage(Protocol):
    """Protocol for alert storage implementations."""

    async def store_alert(self, alert: Alert) -> bool:
        """Store an alert.

        Args:
            alert: Alert to store

        Returns:
            bool: True if alert was stored successfully
        """
        ...

    async def get_alerts(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[AlertSeverity] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Alert]:
        """Get alerts with filtering and pagination.

        Args:
            start_time: Filter by start time
            end_time: Filter by end time
            severity: Filter by severity
            limit: Maximum number of alerts to return
            bool(offset: Number of alerts to skip

        Returns:
            List of alerts matching the filters
        """
        ...

    async def delete_alerts(
        self,
        older_than: Optional[datetime] = None,
        severity: Optional[AlertSeverity] = None,
    ) -> int:
        """Delete alerts with optional filtering.

        Args:
            older_than: Delete alerts older than this time
            severity: Delete alerts with this severity

        Returns:
            Number of alerts deleted
        """
        ...

    async def get_alert_count(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[AlertSeverity] = None,
    ) -> int:
        """Get count of alerts with optional filtering.

        Args:
            start_time: Filter by start time
            end_time: Filter by end time
            severity: Filter by severity

        Returns:
            Number of alerts matching the filters
        """
        ...


class BaseAlertStorage(abc.ABC):
    """Base class for alert storage implementations."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the alert storage.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

    @abc.abstractmethod
    async def store_alert(self, alert: Alert) -> bool:
        """Store an alert.

        Args:
            alert: Alert to store

        Returns:
            bool: True if alert was stored successfully

        Raises:
            IOError: If storage operation fails
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def get_alerts(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[AlertSeverity] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Alert]:
        """Get alerts with filtering and pagination.

        Args:
            start_time: Filter by start time
            end_time: Filter by end time
            severity: Filter by severity
            limit: Maximum number of alerts to return
            offset: Number of alerts to skip

        Returns:
            List of alerts matching the filters

        Raises:
            IOError: If retrieval operation fails
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def delete_alerts(
        self,
        older_than: Optional[datetime] = None,
        severity: Optional[AlertSeverity] = None,
    ) -> int:
        """Delete alerts with optional filtering.

        Args:
            older_than: Delete alerts older than this time
            severity: Delete alerts with this severity

        Returns:
            Number of alerts deleted

        Raises:
            IOError: If deletion operation fails
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def get_alert_count(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[AlertSeverity] = None,
    ) -> int:
        """Get count of alerts with optional filtering.

        Args:
            start_time: Filter by start time
            end_time: Filter by end time
            severity: Filter by severity

        Returns:
            Number of alerts matching the filters

        Raises:
            IOError: If count operation fails
        """
        raise NotImplementedError


class FileAlertStorage(BaseAlertStorage):
    """File-based implementation of alert storage."""

    def __init__(
        self,
        storage_path: Union[str, Path],
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        rotation_count: int = 5,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize file storage.

        Args:
            storage_path: Directory or file path for alert logs.
            max_file_size: Max size in bytes before rotating.
            rotation_count: Number of backup files to keep.
            config: Optional configuration dictionary.
        """
        super().__init__(config)

        if not AIOFILES_AVAILABLE:
            raise ImportError(
                "aiofiles is required for FileAlertStorage but not available"
            )

        self.storage_path = Path(storage_path)
        self.max_file_size = max_file_size
        self.rotation_count = rotation_count
        self._ensure_storage_path()
        self._lock = asyncio.Lock()

    def _ensure_storage_path(self) -> None:
        """Ensure storage directory exists. If path is file, use parent dir."""
        path = (
            self.storage_path.parent
            if self.storage_path.is_file()
            else self.storage_path
        )
        path.mkdir(parents=True, exist_ok=True)

    async def _rotate_files(self) -> None:
        """Rotate log files if current file exceeds max size."""
        # Don't rotate if path is a directory
        if not self.storage_path.is_file():
            return
        if self.storage_path.stat().st_size < self.max_file_size:
            return

        async with self._lock:
            # Delete oldest backup if rotation count is exceeded
            oldest_backup = self.storage_path.with_suffix(
                f".{self.rotation_count}"  # Shorten line (E501 fix attempt)
            )
            if oldest_backup.exists():
                oldest_backup.unlink()

            # Shift existing backups
            for i in range(self.rotation_count - 1, 0, -1):
                src = self.storage_path.with_suffix(f".{i}")
                dst = self.storage_path.with_suffix(f".{i + 1}")
                if src.exists():
                    src.rename(dst)

            # Rotate current log file
            if self.storage_path.exists():
                self.storage_path.rename(
                    self.storage_path.with_suffix(
                        ".1"
                    )  # Shorten line (E501 fix attempt)
                )

    async def store_alert(self, alert: Alert) -> bool:
        """Store an alert in a JSON line file."""
        try:
            await self._rotate_files()
            # Use model_dump_json for Pydantic v2+, or dict() for v1
            alert_json = alert.model_dump_json() + "\n"
            async with self._lock:
                async with aiofiles.open(self.storage_path, mode="a") as f:
                    await f.write(alert_json)
                return True
        except Exception as e:
            # Add proper logging
            raise IOError(f"Failed to store alert: {e}")

    async def get_alerts(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[AlertSeverity] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Alert]:
        """Get alerts from file storage with filtering and pagination."""
        alerts_list = []
        current_offset = 0
        found_count = 0

        files_to_check = [self.storage_path]
        files_to_check.extend(
            self.storage_path.with_suffix(f".{i}")
            for i in range(1, self.rotation_count + 1)
        )

        try:
            for file_path in files_to_check:
                if not file_path.exists():
                    continue

                async with aiofiles.open(file_path, mode="r") as f:
                    lines = await f.readlines()
                    # Read in reverse for recent alerts first
                    for line in reversed(lines):
                        try:
                            # Use model_validate_json for Pydantic v2+,
                            # or parse_raw for v1
                            alert = Alert.model_validate_json(line.strip())

                            # Apply filters
                            if start_time and alert.timestamp < start_time:
                                continue
                            if end_time and alert.timestamp > end_time:
                                continue
                            if severity and alert.severity != severity:
                                continue

                            # Handle pagination
                            if current_offset < offset:
                                current_offset += 1
                                continue

                            alerts_list.append(alert)
                            found_count += 1
                            if limit is not None and found_count >= limit:
                                # Return early if limit reached
                                return alerts_list

                        except json.JSONDecodeError:
                            # Log error - malformed line
                            continue
                        except Exception:
                            # Log other potential parsing/validation errors
                            continue

            # Return whatever was found across files
            return alerts_list

        except Exception as e:
            # Log error
            raise IOError(f"Failed to retrieve alerts from file: {e}")

    async def delete_alerts(
        self,
        older_than: Optional[datetime] = None,
        severity: Optional[AlertSeverity] = None,
    ) -> int:
        """Delete alerts from file storage with optional filtering."""
        deleted_count = 0
        files_to_check = [self.storage_path]
        files_to_check.extend(
            self.storage_path.with_suffix(f".{i}")
            for i in range(1, self.rotation_count + 1)
        )

        async with self._lock:
            for file_path in files_to_check:
                if not file_path.exists():
                    continue

                temp_file_path = file_path.with_suffix(".tmp")
                try:
                    async with (
                        aiofiles.open(file_path, mode="r") as infile,
                        aiofiles.open(temp_file_path, mode="w") as outfile,
                    ):
                        async for line in infile:
                            keep_line = True
                            try:
                                alert = Alert.model_validate_json(line.strip())
                                if older_than and alert.timestamp < older_than:
                                    keep_line = False
                                if severity and alert.severity != severity:
                                    keep_line = False
                            except Exception:
                                # Keep malformed lines or log error?
                                pass  # Decide on handling

                            if keep_line:
                                await outfile.write(line)
                            else:
                                deleted_count += 1

                    # Replace original file with temp file
                    file_path.unlink()
                    temp_file_path.rename(file_path)

                except Exception as e:
                    # Clean up temp file on error
                    if temp_file_path.exists():
                        temp_file_path.unlink()
                    # Log error
                    raise IOError(
                        f"Failed to delete alerts in {file_path}: {e}"  # Reformat E501
                    )
        return deleted_count

    async def get_alert_count(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[AlertSeverity] = None,
    ) -> int:
        """Get count of alerts from file storage with optional filtering."""
        count = 0
        files_to_check = [self.storage_path]
        files_to_check.extend(
            self.storage_path.with_suffix(f".{i}")
            for i in range(1, self.rotation_count + 1)
        )

        try:
            for file_path in files_to_check:
                if not file_path.exists():
                    continue
                async with aiofiles.open(file_path, mode="r") as f:
                    async for line in f:
                        try:
                            alert = Alert.model_validate_json(line.strip())
                            # Apply filters
                            if start_time and alert.timestamp < start_time:
                                continue
                            if end_time and alert.timestamp > end_time:
                                continue
                            if severity and alert.severity != severity:
                                continue
                            count += 1
                        except Exception:
                            # Skip malformed lines
                            continue
            return count
        except Exception as e:
            # Log error
            raise IOError(f"Failed to count alerts: {e}")


class SQLiteAlertStorage(BaseAlertStorage):
    """SQLite-based alert storage implementation."""

    def __init__(
        self,
        db_path: Union[str, Path],
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the SQLite alert storage.

        Args:
            db_path: Path to SQLite database file
            config: Optional configuration dictionary
        """
        super().__init__(config)

        if not AIOSQLITE_AVAILABLE:
            raise ImportError(
                "aiosqlite is required for SQLiteAlertStorage but not available"
            )

        self.db_path = Path(db_path)
        self._db_initialized = False

    async def _ensure_database(self) -> None:
        """Ensure the SQLite database and alerts table exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    severity TEXT,
                    alert_type TEXT,
                    component TEXT,
                    source TEXT,
                    metric_type TEXT,  # Changed from metric_name (E501 fix)
                    metric_value REAL,
                    threshold REAL,
                    message TEXT,
                    metadata TEXT
                )
                """
            )
            cursor = await db.execute("PRAGMA index_list(alerts)")
            indexes = [row[1] for row in await cursor.fetchall()]
            if "idx_alerts_timestamp" not in indexes:
                await db.execute(
                    "CREATE INDEX idx_alerts_timestamp ON alerts (timestamp)"
                )
            if "idx_alerts_severity" not in indexes:
                await db.execute(
                    "CREATE INDEX idx_alerts_severity ON alerts (severity)"
                )
            if "idx_alerts_component" not in indexes:
                await db.execute(
                    "CREATE INDEX idx_alerts_component ON alerts (component)"
                )
            if "idx_alerts_metric_type" not in indexes:
                await db.execute(
                    "CREATE INDEX idx_alerts_metric_type ON alerts (metric_type)"
                )
            await db.commit()

    async def store_alert(self, alert: Alert) -> bool:
        """Store an alert in the SQLite database."""
        try:
            # Ensure database is initialized
            if not self._db_initialized:
                await self._ensure_database()
                self._db_initialized = True

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """INSERT INTO alerts (
                        id, timestamp, severity, alert_type, component, source,
                        metric_type, metric_value, threshold, message, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        alert.id,
                        alert.timestamp.isoformat(),
                        alert.severity.value,
                        alert.alert_type.value,
                        alert.component,
                        alert.source,
                        alert.metric_type.value,
                        alert.metric_value,
                        alert.threshold,
                        alert.message,
                        json.dumps(alert.labels) if alert.labels else None,
                    ),
                )
                await db.commit()
                return True
        except Exception as e:
            raise IOError(f"Failed to store alert: {e}")

    async def get_alerts(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[AlertSeverity] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Alert]:
        """Get alerts from SQLite database with filtering and pagination."""
        try:
            # Ensure database is initialized
            if not self._db_initialized:
                await self._ensure_database()
                self._db_initialized = True

            query = [
                "SELECT id, timestamp, severity, alert_type, component, source, ",
                "metric_type, metric_value, threshold, message, metadata ",
                "FROM alerts WHERE 1=1",
            ]
            params = []

            if start_time:
                query.append("AND timestamp >= ?")
                params.append(start_time.isoformat())
            if end_time:
                query.append("AND timestamp <= ?")
                params.append(end_time.isoformat())
            if severity:
                query.append("AND severity = ?")
                params.append(severity.value)

            query.append("ORDER BY timestamp DESC")

            if limit is not None:
                query.append("LIMIT ? OFFSET ?")
                # Revert conversion to string, pass as int
                params.extend([limit, offset])
            elif offset:
                query.append("OFFSET ?")
                # Revert conversion to string, pass as int
                params.append(offset)

            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(" ".join(query), params)
                rows = await cursor.fetchall()

                alerts_list = []
                for row in rows:
                    try:
                        alert_data = {
                            "id": row["id"],
                            "timestamp": datetime.fromisoformat(row["timestamp"]),
                            "severity": AlertSeverity(row["severity"]),
                            "alert_type": AlertType(row["alert_type"]),
                            "component": row["component"],
                            "source": row["source"],
                            "metric_type": MetricType(row["metric_type"]),
                            "metric_value": row["metric_value"],
                            "threshold": row["threshold"],
                            "message": row["message"],
                            "labels": (
                                json.loads(row["metadata"]) if row["metadata"] else {}
                            ),
                            "status": AlertStatus.ACTIVE,
                        }
                        alerts_list.append(Alert(**alert_data))
                    except Exception as parse_error:
                        # Add logging for parsing errors
                        # Reformat print statement (E501 fix)
                        print(f"Error parsing alert row {row['id']}: " f"{parse_error}")
                        continue  # Skip malformed rows

                return alerts_list
        except Exception as e:
            raise IOError(f"Failed to retrieve alerts: {e}")

    async def delete_alerts(
        self,
        older_than: Optional[datetime] = None,
        severity: Optional[AlertSeverity] = None,
    ) -> int:
        """Delete alerts from SQLite database with optional filtering.

        Args:
            older_than: Delete alerts older than this time
            severity: Delete alerts with this severity

        Returns:
            Number of alerts deleted

        Raises:
            IOError: If database operation fails
        """
        try:
            # Ensure database is initialized
            if not self._db_initialized:
                await self._ensure_database()
                self._db_initialized = True

            query = ["DELETE FROM alerts WHERE 1=1"]
            params = []

            if older_than:
                query.append("AND timestamp < ?")
                params.append(older_than.isoformat())
            if severity:
                query.append("AND severity = ?")
                params.append(severity.value)

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(" ".join(query), params)
                deleted = cursor.rowcount
                await db.commit()
                return deleted
        except Exception as e:
            raise IOError(f"Failed to delete alerts: {e}")

    async def get_alert_count(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[AlertSeverity] = None,
    ) -> int:
        """Get count of alerts from SQLite database with optional filtering.

        Args:
            start_time: Filter by start time
            end_time: Filter by end time
            severity: Filter by severity

        Returns:
            Number of alerts matching the filters

        Raises:
            IOError: If database operation fails
        """
        try:
            # Ensure database is initialized
            if not self._db_initialized:
                await self._ensure_database()
                self._db_initialized = True

            query = ["SELECT COUNT(*) FROM alerts WHERE 1=1"]
            params = []

            if start_time:
                query.append("AND timestamp >= ?")
                params.append(start_time.isoformat())
            if end_time:
                query.append("AND timestamp <= ?")
                params.append(end_time.isoformat())
            if severity:
                query.append("AND severity = ?")
                params.append(severity.value)

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(" ".join(query), params)
                row = await cursor.fetchone()
                return row[0] if row else 0
        except Exception as e:
            raise IOError(f"Failed to count alerts: {e}")
