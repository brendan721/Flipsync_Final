"""
eBay token notification templates.

This module contains templates for eBay token-related notifications.
"""

from datetime import datetime
from typing import Any, Dict

from fs_agt.services.notifications.channels import NotificationChannel
from fs_agt.services.notifications.templates.base import NotificationTemplate


class TokenExpiringTemplate(NotificationTemplate):
    """Template for token expiration notifications."""

    template_id = "token_expiring"
    default_channel = NotificationChannel.EMAIL
    available_channels = [NotificationChannel.EMAIL, NotificationChannel.SLACK]

    def get_title(self, data: Dict[str, Any]) -> str:
        """Get notification title."""
        return "eBay Token Expiring Soon"

    def get_email_content(self, data: Dict[str, Any]) -> str:
        """Get email content."""
        user_id = data.get("user_id", "unknown")
        days_left = data.get("days_left", "unknown")
        expiry_date = data.get("expiry_date", "unknown")

        return f"""
        <h2>eBay Token Expiring Soon</h2>
        <p>Your eBay API token is expiring soon.</p>
        <p><strong>UnifiedUser ID:</strong> {user_id}</p>
        <p><strong>Days Left:</strong> {days_left}</p>
        <p><strong>Expiry Date:</strong> {expiry_date}</p>
        <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Please refresh your token as soon as possible to avoid service interruption.</p>
        """

    def get_slack_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get Slack content."""
        user_id = data.get("user_id", "unknown")
        days_left = data.get("days_left", "unknown")
        expiry_date = data.get("expiry_date", "unknown")

        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "⚠️ eBay Token Expiring Soon",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*UnifiedUser ID:*\n{user_id}"},
                        {"type": "mrkdwn", "text": f"*Days Left:*\n{days_left}"},
                    ],
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Expiry Date:*\n{expiry_date}"}
                    ],
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "plain_text",
                            "text": f"Alert sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        }
                    ],
                },
            ]
        }


class TokenRefreshedTemplate(NotificationTemplate):
    """Template for token refresh notifications."""

    template_id = "token_refreshed"
    default_channel = NotificationChannel.EMAIL
    available_channels = [NotificationChannel.EMAIL, NotificationChannel.SLACK]

    def get_title(self, data: Dict[str, Any]) -> str:
        """Get notification title."""
        return "eBay Token Refreshed Successfully"

    def get_email_content(self, data: Dict[str, Any]) -> str:
        """Get email content."""
        user_id = data.get("user_id", "unknown")
        new_expiry_date = data.get("new_expiry_date", "unknown")

        return f"""
        <h2>eBay Token Refreshed Successfully</h2>
        <p>Your eBay API token has been refreshed successfully.</p>
        <p><strong>UnifiedUser ID:</strong> {user_id}</p>
        <p><strong>New Expiry Date:</strong> {new_expiry_date}</p>
        <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """

    def get_slack_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get Slack content."""
        user_id = data.get("user_id", "unknown")
        new_expiry_date = data.get("new_expiry_date", "unknown")

        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "✅ eBay Token Refreshed Successfully",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*UnifiedUser ID:*\n{user_id}"},
                        {
                            "type": "mrkdwn",
                            "text": f"*New Expiry Date:*\n{new_expiry_date}",
                        },
                    ],
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "plain_text",
                            "text": f"Refreshed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        }
                    ],
                },
            ]
        }


class TokenRefreshFailedTemplate(NotificationTemplate):
    """Template for token refresh failure notifications."""

    template_id = "token_refresh_failed"
    default_channel = NotificationChannel.EMAIL
    available_channels = [NotificationChannel.EMAIL, NotificationChannel.SLACK]

    def get_title(self, data: Dict[str, Any]) -> str:
        """Get notification title."""
        return "eBay Token Refresh Failed"

    def get_email_content(self, data: Dict[str, Any]) -> str:
        """Get email content."""
        user_id = data.get("user_id", "unknown")
        error = data.get("error", "Unknown error")

        return f"""
        <h2>eBay Token Refresh Failed</h2>
        <p>An error occurred while refreshing your eBay API token.</p>
        <p><strong>UnifiedUser ID:</strong> {user_id}</p>
        <p><strong>Error:</strong> {error}</p>
        <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Please check your eBay developer account and try again.</p>
        """

    def get_slack_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get Slack content."""
        user_id = data.get("user_id", "unknown")
        error = data.get("error", "Unknown error")

        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "❌ eBay Token Refresh Failed",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*UnifiedUser ID:*\n{user_id}"},
                    ],
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Error:*\n```{error}```"},
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "plain_text",
                            "text": f"Error occurred at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        }
                    ],
                },
            ]
        }


# Export all templates
EBAY_TOKEN_TEMPLATES = {
    "token_expiring": TokenExpiringTemplate(),
    "token_refreshed": TokenRefreshedTemplate(),
    "token_refresh_failed": TokenRefreshFailedTemplate(),
}
