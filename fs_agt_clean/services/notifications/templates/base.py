from abc import ABC, abstractmethod
from typing import Any, Dict, List, Set

# Assuming NotificationChannel is correctly located here based on previous tracebacks
# If this causes issues, we may need to find its actual definition.
# Optional import with graceful fallback
try:
    from fs_agt_clean.services.notifications.channels import NotificationChannel
except ImportError:
    # Create mock NotificationChannel for graceful fallback
    class NotificationChannel:
        EMAIL = "email"
        PUSH = "push"
        SMS = "sms"
        SLACK = "slack"


class NotificationTemplate(ABC):
    """Base class for notification templates."""

    template_id: str
    default_channel: NotificationChannel
    available_channels: List[NotificationChannel] | Set[NotificationChannel]

    @abstractmethod
    def get_title(self, data: Dict[str, Any]) -> str:
        """Get notification title."""
        pass

    # Provide default implementations or make abstract if necessary
    def get_email_content(self, data: Dict[str, Any]) -> str:
        """Get email content (optional)."""
        # Default to using get_body if not overridden
        return self.get_body(data)

    def get_slack_content(self, data: Dict[str, Any]) -> str:
        """Get Slack content (optional)."""
        # Default to using get_body if not overridden
        return self.get_body(data)

    def get_body(self, data: Dict[str, Any]) -> str:
        """Get generic notification body (fallback)."""
        # Default implementation or make abstract
        title = self.get_title(data)
        details = ", ".join(f'{k}="{v}"' for k, v in data.items())
        return f"{title}\nDetails: {details}"
