"""Event constants for FlipSync."""

# Resource events
RESOURCE_ALLOCATED = "resource.allocated"
RESOURCE_RELEASED = "resource.released"
RESOURCE_FAILED = "resource.failed"
RESOURCE_UPDATED = "resource.updated"

# System events
SYSTEM_STARTUP = "system.startup"
SYSTEM_SHUTDOWN = "system.shutdown"
SYSTEM_ERROR = "system.error"
SYSTEM_WARNING = "system.warning"

# Service events
SERVICE_STARTED = "service.started"
SERVICE_STOPPED = "service.stopped"
SERVICE_ERROR = "service.error"
SERVICE_READY = "service.ready"

# Monitoring events
METRIC_RECORDED = "metric.recorded"
ALERT_TRIGGERED = "alert.triggered"
THRESHOLD_EXCEEDED = "threshold.exceeded"

# Task events
TASK_CREATED = "task.created"
TASK_STARTED = "task.started"
TASK_COMPLETED = "task.completed"
TASK_FAILED = "task.failed"
TASK_CANCELLED = "task.cancelled"

# UnifiedUser events
USER_LOGIN = "user.login"
USER_LOGOUT = "user.logout"
USER_ACTION = "user.action"
USER_ERROR = "user.error"

# Data events
DATA_CREATED = "data.created"
DATA_UPDATED = "data.updated"
DATA_DELETED = "data.deleted"
DATA_SYNCED = "data.synced"

# Integration events
INTEGRATION_CONNECTED = "integration.connected"
INTEGRATION_DISCONNECTED = "integration.disconnected"
INTEGRATION_ERROR = "integration.error"
INTEGRATION_SYNCED = "integration.synced"
