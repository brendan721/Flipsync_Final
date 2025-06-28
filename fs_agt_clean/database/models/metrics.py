"""
Database models for metrics and monitoring data.

This module defines SQLAlchemy models for storing historical metrics,
alerts, and monitoring data in the FlipSync system.
"""

import enum
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from fs_agt_clean.database.models.unified_base import Base


class MetricType(enum.Enum):
    """Types of metrics."""

    GAUGE = "gauge"
    COUNTER = "counter"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class MetricCategory(enum.Enum):
    """Categories of metrics."""

    SYSTEM = "system"
    PERFORMANCE = "performance"
    BUSINESS = "business"
    SECURITY = "security"
    AGENT = "agent"
    CONVERSATION = "conversation"
    DECISION = "decision"
    MOBILE = "mobile"
    API = "api"


class AlertLevel(enum.Enum):
    """Alert levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertCategory(enum.Enum):
    """Alert categories."""

    SYSTEM = "system"
    PERFORMANCE = "performance"
    SECURITY = "security"
    BUSINESS = "business"
    AGENT = "agent"
    CONVERSATION = "conversation"
    DECISION = "decision"
    MOBILE = "mobile"
    API = "api"


class AlertSource(enum.Enum):
    """Alert sources."""

    SYSTEM = "system"
    USER = "user"
    AGENT = "agent"
    MONITORING = "monitoring"
    SECURITY = "security"


class MetricDataPoint(Base):
    """Model for storing individual metric data points."""

    __tablename__ = "metric_data_points"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    value = Column(Float, nullable=False)
    type = Column(SQLEnum(MetricType), nullable=False, default=MetricType.GAUGE)
    category = Column(
        SQLEnum(MetricCategory), nullable=False, default=MetricCategory.SYSTEM
    )
    labels = Column(JSON, nullable=True)  # Key-value pairs for labels/tags
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    agent_id = Column(
        String(255), nullable=True, index=True
    )  # Optional agent identifier
    service_name = Column(
        String(255), nullable=True, index=True
    )  # Service that generated the metric

    # Indexes for efficient querying
    __table_args__ = (
        Index("idx_metric_name_timestamp", "name", "timestamp"),
        Index("idx_metric_category_timestamp", "category", "timestamp"),
        Index("idx_metric_agent_timestamp", "agent_id", "timestamp"),
        Index("idx_metric_service_timestamp", "service_name", "timestamp"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "value": self.value,
            "type": self.type.value,
            "category": self.category.value,
            "labels": self.labels or {},
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id,
            "service_name": self.service_name,
        }


class SystemMetrics(Base):
    """Model for storing system-level metrics snapshots."""

    __tablename__ = "system_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    # System metrics
    cpu_usage_percent = Column(Float, nullable=True)
    memory_total_bytes = Column(BigInteger, nullable=True)
    memory_used_bytes = Column(BigInteger, nullable=True)
    memory_usage_percent = Column(Float, nullable=True)
    disk_total_bytes = Column(BigInteger, nullable=True)
    disk_used_bytes = Column(BigInteger, nullable=True)
    disk_usage_percent = Column(Float, nullable=True)
    network_bytes_sent = Column(BigInteger, nullable=True)
    network_bytes_received = Column(BigInteger, nullable=True)

    # Process metrics
    process_cpu_percent = Column(Float, nullable=True)
    process_memory_percent = Column(Float, nullable=True)
    process_memory_rss = Column(BigInteger, nullable=True)
    process_memory_vms = Column(BigInteger, nullable=True)
    process_num_threads = Column(Integer, nullable=True)
    process_num_fds = Column(Integer, nullable=True)

    # Additional metadata
    hostname = Column(String(255), nullable=True)
    service_name = Column(String(255), nullable=True, index=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "system": {
                "cpu_usage_percent": self.cpu_usage_percent,
                "memory": {
                    "total_bytes": self.memory_total_bytes,
                    "used_bytes": self.memory_used_bytes,
                    "usage_percent": self.memory_usage_percent,
                },
                "disk": {
                    "total_bytes": self.disk_total_bytes,
                    "used_bytes": self.disk_used_bytes,
                    "usage_percent": self.disk_usage_percent,
                },
                "network": {
                    "bytes_sent": self.network_bytes_sent,
                    "bytes_received": self.network_bytes_received,
                },
            },
            "process": {
                "cpu_percent": self.process_cpu_percent,
                "memory_percent": self.process_memory_percent,
                "memory_rss": self.process_memory_rss,
                "memory_vms": self.process_memory_vms,
                "num_threads": self.process_num_threads,
                "num_fds": self.process_num_fds,
            },
            "hostname": self.hostname,
            "service_name": self.service_name,
        }


class UnifiedAgentMetrics(Base):
    """Model for storing agent-specific metrics."""

    __tablename__ = "agent_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(255), nullable=False, index=True)
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    # UnifiedAgent status
    status = Column(String(50), nullable=False)
    uptime_seconds = Column(Float, nullable=True)
    error_count = Column(Integer, nullable=False, default=0)
    last_error_time = Column(DateTime(timezone=True), nullable=True)
    last_success_time = Column(DateTime(timezone=True), nullable=True)

    # Performance metrics
    requests_total = Column(Integer, nullable=True, default=0)
    requests_success = Column(Integer, nullable=True, default=0)
    requests_failed = Column(Integer, nullable=True, default=0)
    avg_response_time_ms = Column(Float, nullable=True)
    peak_response_time_ms = Column(Float, nullable=True)

    # Resource usage
    cpu_usage_percent = Column(Float, nullable=True)
    memory_usage_percent = Column(Float, nullable=True)

    # Additional metadata
    agent_metadata = Column(JSON, nullable=True)

    # Indexes for efficient querying
    __table_args__ = (
        Index("idx_agent_metrics_agent_timestamp", "agent_id", "timestamp"),
        Index("idx_agent_metrics_status_timestamp", "status", "timestamp"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
            "uptime_seconds": self.uptime_seconds,
            "error_count": self.error_count,
            "last_error_time": (
                self.last_error_time.isoformat() if self.last_error_time else None
            ),
            "last_success_time": (
                self.last_success_time.isoformat() if self.last_success_time else None
            ),
            "performance": {
                "requests_total": self.requests_total,
                "requests_success": self.requests_success,
                "requests_failed": self.requests_failed,
                "avg_response_time_ms": self.avg_response_time_ms,
                "peak_response_time_ms": self.peak_response_time_ms,
            },
            "resources": {
                "cpu_usage_percent": self.cpu_usage_percent,
                "memory_usage_percent": self.memory_usage_percent,
            },
            "metadata": self.agent_metadata or {},
        }


class AlertRecord(Base):
    """Model for storing alert records."""

    __tablename__ = "alert_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(String(255), nullable=False, unique=True, index=True)
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    level = Column(SQLEnum(AlertLevel), nullable=False, index=True)
    category = Column(SQLEnum(AlertCategory), nullable=False, index=True)
    source = Column(SQLEnum(AlertSource), nullable=False, index=True)

    # Alert details and metadata
    details = Column(JSON, nullable=True)
    labels = Column(JSON, nullable=True)

    # Timestamps
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    acknowledged = Column(Boolean, nullable=False, default=False)
    acknowledged_time = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(String(255), nullable=True)

    # Correlation and tracking
    correlation_id = Column(String(255), nullable=True, index=True)
    fingerprint = Column(String(255), nullable=True, index=True)  # For deduplication

    # Resolution
    resolved = Column(Boolean, nullable=False, default=False)
    resolved_time = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(255), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Indexes for efficient querying
    __table_args__ = (
        Index("idx_alert_level_timestamp", "level", "timestamp"),
        Index("idx_alert_category_timestamp", "category", "timestamp"),
        Index("idx_alert_source_timestamp", "source", "timestamp"),
        Index("idx_alert_acknowledged_timestamp", "acknowledged", "timestamp"),
        Index("idx_alert_resolved_timestamp", "resolved", "timestamp"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "alert_id": self.alert_id,
            "title": self.title,
            "message": self.message,
            "level": self.level.value,
            "category": self.category.value,
            "source": self.source.value,
            "details": self.details or {},
            "labels": self.labels or {},
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged,
            "acknowledged_time": (
                self.acknowledged_time.isoformat() if self.acknowledged_time else None
            ),
            "acknowledged_by": self.acknowledged_by,
            "correlation_id": self.correlation_id,
            "fingerprint": self.fingerprint,
            "resolved": self.resolved,
            "resolved_time": (
                self.resolved_time.isoformat() if self.resolved_time else None
            ),
            "resolved_by": self.resolved_by,
            "resolution_notes": self.resolution_notes,
        }


class Metric(Base):
    """Base metric model for storing metric definitions."""

    __tablename__ = "metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    metric_type = Column(SQLEnum(MetricType), nullable=False)
    category = Column(SQLEnum(MetricCategory), nullable=False)
    unit = Column(String(50))
    tags = Column(JSON, default=dict)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "metric_type": self.metric_type.value if self.metric_type else None,
            "category": self.category.value if self.category else None,
            "unit": self.unit,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class MetricSeries(Base):
    """Model for storing time series metric data."""

    __tablename__ = "metric_series"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_id = Column(UUID(as_uuid=True), ForeignKey("metrics.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    value = Column(Float, nullable=False)
    labels = Column(JSON, default=dict)
    source = Column(String(255))

    # Relationship
    metric = relationship("Metric", backref="series_data")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "metric_id": str(self.metric_id),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "value": self.value,
            "labels": self.labels,
            "source": self.source,
        }


class MetricAggregation(Base):
    """Model for storing aggregated metric data."""

    __tablename__ = "metric_aggregations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_id = Column(UUID(as_uuid=True), ForeignKey("metrics.id"), nullable=False)
    aggregation_type = Column(String(50), nullable=False)  # sum, avg, min, max, count
    time_window = Column(String(50), nullable=False)  # 1m, 5m, 1h, 1d, etc.
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False, index=True)
    value = Column(Float, nullable=False)
    sample_count = Column(Integer, default=1)
    labels = Column(JSON, default=dict)

    # Relationship
    metric = relationship("Metric", backref="aggregations")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "metric_id": str(self.metric_id),
            "aggregation_type": self.aggregation_type,
            "time_window": self.time_window,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "value": self.value,
            "sample_count": self.sample_count,
            "labels": self.labels,
        }


class MetricThreshold(Base):
    """Model for storing metric thresholds for alerting."""

    __tablename__ = "metric_thresholds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_name = Column(String(255), nullable=False, unique=True, index=True)
    warning_threshold = Column(Float, nullable=True)
    critical_threshold = Column(Float, nullable=True)

    # Threshold configuration
    enabled = Column(Boolean, nullable=False, default=True)
    comparison_operator = Column(
        String(10), nullable=False, default=">="
    )  # >=, <=, ==, !=

    # Metadata
    description = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "metric_name": self.metric_name,
            "warning_threshold": self.warning_threshold,
            "critical_threshold": self.critical_threshold,
            "enabled": self.enabled,
            "comparison_operator": self.comparison_operator,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "updated_by": self.updated_by,
        }
