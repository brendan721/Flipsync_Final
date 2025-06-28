"""Fixed monitoring alerts validation module with Pydantic v1 compatibility."""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, field_validator


# Enums
class AlertSeverity(str, Enum):
    """Alert severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class MetricType(str, Enum):
    """Types of metrics that can be monitored."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    RATE = "rate"
    DELTA = "delta"


# Alert validation error class
class AlertValidationError(Exception):
    """Exception raised when alert validation fails."""

    def __init__(self, message: str, errors: Optional[Dict[str, List[str]]] = None):
        """
        Initialize an alert validation error.

        Args:
            message: Error message
            errors: Dictionary of field-specific errors
        """
        super().__init__(message)
        self.message = message
        self.errors = errors or {}


# Fixed models with v1 compatible validators
class AlertValidator(BaseModel):
    """Validator for alert models."""

    severity: AlertSeverity
    metric_type: MetricType
    threshold: float
    metric_value: float

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    @field_validator("severity")
    def validate_severity(cls, severity: AlertSeverity) -> AlertSeverity:
        """Validate alert severity."""
        return severity

    @field_validator("metric_type")
    def validate_metric_type(cls, metric_type: MetricType) -> MetricType:
        """Validate metric type."""
        return metric_type

    @field_validator("threshold", mode="before")
    def validate_threshold(cls, threshold: float, info) -> float:
        """Validate threshold value."""
        # Get metric type from info.data dict
        values = info.data
        threshold_value = float(threshold)

        # Get metric type from values dict
        metric_type = values.get("metric_type")
        if threshold_value < 0 and metric_type not in {
            MetricType.COUNTER,
            MetricType.RATE,
            MetricType.DELTA,
        }:
            raise ValueError(
                f"Negative thresholds not allowed for metric type {metric_type}"
            )

        return threshold_value

    @field_validator("metric_value", mode="before")
    def validate_metric_value(cls, value: float) -> float:
        """Validate metric value."""
        return float(value)


# Add validation function for alerts
def validate_alert(alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate alert data.

    Args:
        alert_data: Dictionary containing alert data

    Returns:
        Validated alert data

    Raises:
        AlertValidationError: If validation fails
    """
    try:
        # Extract the fields needed for validation
        validation_data = {
            "severity": alert_data.get("severity", AlertSeverity.MEDIUM),
            "metric_type": alert_data.get("metric_type", MetricType.GAUGE),
            "threshold": alert_data.get("threshold", 0.0),
            "metric_value": alert_data.get("metric_value", 0.0),
        }

        # Validate using the AlertValidator
        validator = AlertValidator(**validation_data)

        # Update the alert_data with validated values
        alert_data["severity"] = validator.severity
        alert_data["metric_type"] = validator.metric_type
        alert_data["threshold"] = validator.threshold
        alert_data["metric_value"] = validator.metric_value

        return alert_data
    except Exception as e:
        # Convert any validation error to AlertValidationError
        error_details = {}
        if hasattr(e, "errors") and callable(getattr(e, "errors", None)):
            error_details = e.errors()

        raise AlertValidationError(str(e), error_details)


# Add a utility function for model serialization compatibility
def get_dict(obj):
    """Get dictionary representation, compatible with Pydantic v1 and v2."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    elif hasattr(obj, "dict"):
        return obj.dict()
    else:
        return obj.__dict__
