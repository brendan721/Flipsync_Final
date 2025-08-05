"""
Base email template.

This module provides a base class for email templates.
"""

from typing import Any, Dict


class BaseTemplate:
    """Base class for email templates."""

    def __init__(self, template_id: str, category: str, subject: str):
        """Initialize the template.

        Args:
            template_id: Template identifier
            category: Template category
            subject: Email subject
        """
        self.template_id = template_id
        self.category = category
        self.subject = subject

    def get_email_content(self, data: Dict[str, Any]) -> str:
        """Get HTML email content.

        Args:
            data: Template data

        Returns:
            str: HTML email content
        """
        raise NotImplementedError("Subclasses must implement get_email_content")

    def get_text_content(self, data: Dict[str, Any]) -> str:
        """Get plain text email content.

        Args:
            data: Template data

        Returns:
            str: Plain text email content
        """
        raise NotImplementedError("Subclasses must implement get_text_content")
