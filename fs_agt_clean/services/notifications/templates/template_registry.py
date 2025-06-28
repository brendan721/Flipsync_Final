"""
Email template registry.

This module provides a registry for all email templates.
"""

import logging
from typing import Dict, List, Optional

from fs_agt.services.notifications.email_service import EmailService
from fs_agt.services.notifications.templates.base_template import BaseTemplate
from fs_agt.services.notifications.templates.password_reset_template import (
    PasswordResetTemplate,
)

logger = logging.getLogger(__name__)


class TemplateRegistry:
    """Registry for email templates."""

    def __init__(self, email_service: EmailService):
        """Initialize the template registry.

        Args:
            email_service: Email service to register templates with
        """
        self.email_service = email_service
        self.templates: Dict[str, BaseTemplate] = {}

    def register_template(self, template: BaseTemplate) -> None:
        """Register a template with the email service.

        Args:
            template: Template to register
        """
        template_id = template.template_id
        if template_id in self.templates:
            logger.warning(f"Template {template_id} already registered, overwriting")

        # Add to internal registry
        self.templates[template_id] = template

        # Register with email service
        self.email_service.add_template(
            template_id=template_id,
            subject_template=template.subject,
            html_template=template.get_email_content({}),
            text_template=template.get_text_content({}),
        )

        logger.info(f"Registered template {template_id}")

    def get_template(self, template_id: str) -> Optional[BaseTemplate]:
        """Get a template by ID.

        Args:
            template_id: Template ID

        Returns:
            Optional[BaseTemplate]: Template if found
        """
        return self.templates.get(template_id)

    def get_all_templates(self) -> List[BaseTemplate]:
        """Get all registered templates.

        Returns:
            List[BaseTemplate]: All templates
        """
        return list(self.templates.values())

    def register_default_templates(self) -> None:
        """Register all default templates."""
        # Register password reset template
        self.register_template(PasswordResetTemplate())

        logger.info("Registered default templates")
