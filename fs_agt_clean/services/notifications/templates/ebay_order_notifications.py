"""
eBay order notification templates.

This module contains templates for eBay order notifications.
"""

from datetime import datetime
from typing import Any, Dict

from fs_agt.services.notifications.channels import NotificationChannel
from fs_agt.services.notifications.templates.base import NotificationTemplate


class OrderReceivedTemplate(NotificationTemplate):
    """Template for order received notifications."""

    template_id = "order_received"
    default_channel = NotificationChannel.EMAIL
    available_channels = [
        NotificationChannel.EMAIL,
        NotificationChannel.SMS,
        NotificationChannel.PUSH,
    ]

    def get_title(self, data: Dict[str, Any]) -> str:
        """Get notification title."""
        return "New eBay Order Received"

    def get_email_content(self, data: Dict[str, Any]) -> str:
        """Get email content."""
        order_id = data.get("order_id", "unknown")
        return f"""
        <h2>New eBay Order Received</h2>
        <p>You have received a new order on eBay.</p>
        <p><strong>Order ID:</strong> {order_id}</p>
        <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """

    def get_sms_content(self, data: Dict[str, Any]) -> str:
        """Get SMS content."""
        order_id = data.get("order_id", "unknown")
        return f"New eBay order received. Order ID: {order_id}"


class OrderShippedTemplate(NotificationTemplate):
    """Template for order shipped notifications."""

    template_id = "order_shipped"
    default_channel = NotificationChannel.EMAIL
    available_channels = [
        NotificationChannel.EMAIL,
        NotificationChannel.SMS,
        NotificationChannel.PUSH,
    ]

    def get_title(self, data: Dict[str, Any]) -> str:
        """Get notification title."""
        return "eBay Order Shipped"

    def get_email_content(self, data: Dict[str, Any]) -> str:
        """Get email content."""
        order_id = data.get("order_id", "unknown")
        tracking_number = data.get("tracking_number", "N/A")
        return f"""
        <h2>eBay Order Shipped</h2>
        <p>Your eBay order has been shipped.</p>
        <p><strong>Order ID:</strong> {order_id}</p>
        <p><strong>Tracking Number:</strong> {tracking_number}</p>
        <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """

    def get_sms_content(self, data: Dict[str, Any]) -> str:
        """Get SMS content."""
        order_id = data.get("order_id", "unknown")
        tracking_number = data.get("tracking_number", "N/A")
        return f"eBay order shipped. Order ID: {order_id}, Tracking: {tracking_number}"


class OrderDeliveredTemplate(NotificationTemplate):
    """Template for order delivered notifications."""

    template_id = "order_delivered"
    default_channel = NotificationChannel.EMAIL
    available_channels = [
        NotificationChannel.EMAIL,
        NotificationChannel.SMS,
        NotificationChannel.PUSH,
    ]

    def get_title(self, data: Dict[str, Any]) -> str:
        """Get notification title."""
        return "eBay Order Delivered"

    def get_email_content(self, data: Dict[str, Any]) -> str:
        """Get email content."""
        order_id = data.get("order_id", "unknown")
        return f"""
        <h2>eBay Order Delivered</h2>
        <p>Your eBay order has been delivered.</p>
        <p><strong>Order ID:</strong> {order_id}</p>
        <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """

    def get_sms_content(self, data: Dict[str, Any]) -> str:
        """Get SMS content."""
        order_id = data.get("order_id", "unknown")
        return f"eBay order delivered. Order ID: {order_id}"


class OrderCanceledTemplate(NotificationTemplate):
    """Template for order canceled notifications."""

    template_id = "order_canceled"
    default_channel = NotificationChannel.EMAIL
    available_channels = [
        NotificationChannel.EMAIL,
        NotificationChannel.SMS,
        NotificationChannel.PUSH,
    ]

    def get_title(self, data: Dict[str, Any]) -> str:
        """Get notification title."""
        return "eBay Order Canceled"

    def get_email_content(self, data: Dict[str, Any]) -> str:
        """Get email content."""
        order_id = data.get("order_id", "unknown")
        return f"""
        <h2>eBay Order Canceled</h2>
        <p>Your eBay order has been canceled.</p>
        <p><strong>Order ID:</strong> {order_id}</p>
        <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """

    def get_sms_content(self, data: Dict[str, Any]) -> str:
        """Get SMS content."""
        order_id = data.get("order_id", "unknown")
        return f"eBay order canceled. Order ID: {order_id}"


class PaymentReceivedTemplate(NotificationTemplate):
    """Template for payment received notifications."""

    template_id = "payment_received"
    default_channel = NotificationChannel.EMAIL
    available_channels = [
        NotificationChannel.EMAIL,
        NotificationChannel.SMS,
        NotificationChannel.PUSH,
    ]

    def get_title(self, data: Dict[str, Any]) -> str:
        """Get notification title."""
        return "Payment Received for eBay Order"

    def get_email_content(self, data: Dict[str, Any]) -> str:
        """Get email content."""
        order_id = data.get("order_id", "unknown")
        amount = data.get("amount", "N/A")
        return f"""
        <h2>Payment Received for eBay Order</h2>
        <p>Payment has been received for your eBay order.</p>
        <p><strong>Order ID:</strong> {order_id}</p>
        <p><strong>Amount:</strong> {amount}</p>
        <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """

    def get_sms_content(self, data: Dict[str, Any]) -> str:
        """Get SMS content."""
        order_id = data.get("order_id", "unknown")
        amount = data.get("amount", "N/A")
        return (
            f"Payment received for eBay order. Order ID: {order_id}, Amount: {amount}"
        )


# Export all templates
EBAY_ORDER_TEMPLATES = {
    "order_received": OrderReceivedTemplate(),
    "order_shipped": OrderShippedTemplate(),
    "order_delivered": OrderDeliveredTemplate(),
    "order_canceled": OrderCanceledTemplate(),
    "payment_received": PaymentReceivedTemplate(),
}
