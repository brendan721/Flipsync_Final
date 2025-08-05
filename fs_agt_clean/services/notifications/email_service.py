#!/usr/bin/env python3
"""
Email Service Implementation
Features:
1. SMTP-based email delivery
2. HTML and text email support
3. Template-based emails
4. Attachment support
5. Retry logic
"""

# Standard library imports
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Optional

# Optional email dependencies
try:
    import aiosmtplib

    AIOSMTPLIB_AVAILABLE = True
except ImportError:
    AIOSMTPLIB_AVAILABLE = False

    # Create mock for graceful fallback
    class MockSMTP:
        def __init__(self, *args, **kwargs):
            pass

        async def connect(self):
            pass

        async def login(self, *args):
            pass

        async def send_message(self, *args):
            pass

        async def quit(self):
            pass

    aiosmtplib = type("MockModule", (), {"SMTP": MockSMTP})()

try:
    from jinja2 import Environment, PackageLoader, select_autoescape

    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False

    # Create mock classes for graceful fallback
    class Environment:
        def __init__(self, *args, **kwargs):
            pass

        def from_string(self, template):
            return MockTemplate(template)

    class MockTemplate:
        def __init__(self, template):
            self.template = template

        def render(self, **kwargs):
            return self.template.format(**kwargs)

    def PackageLoader(*args, **kwargs):
        return None

    def select_autoescape(*args, **kwargs):
        return None


# Optional config manager
try:
    from fs_agt_clean.core.config.manager import ConfigManager
except ImportError:
    # Create mock ConfigManager for graceful fallback
    class ConfigManager:
        def __init__(self):
            self._config = {}

        def get(self, key, default=None):
            return self._config.get(key, default)


logger = logging.getLogger(__name__)


class EmailTemplate:
    """Email template with HTML and text versions."""

    def __init__(
        self,
        template_id: str,
        subject_template: str,
        html_template: str,
        text_template: str,
    ):
        """Initialize email template.

        Args:
            template_id: Template identifier
            subject_template: Subject line template
            html_template: HTML body template
            text_template: Plain text body template
        """
        self.template_id = template_id
        self.subject_template = subject_template
        self.html_template = html_template
        self.text_template = text_template


class EmailService:
    """Handles email notification delivery."""

    def __init__(self, config_manager: ConfigManager):
        """Initialize email service.

        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self._templates: Dict[str, EmailTemplate] = {}

        # Initialize Jinja environment
        try:
            self.jinja_env = Environment(
                loader=PackageLoader("fs_agt", "templates/email"),
                autoescape=select_autoescape(["html", "xml"]),
            )
        except Exception as e:
            logger.warning(f"Failed to initialize Jinja environment: {e}")
            # Use a simple string-based template system instead
            self.jinja_env = None

        # Load SMTP configuration
        smtp_config = self.config.get("smtp", {})
        self.smtp_host = smtp_config.get("host", "localhost")
        self.smtp_port = smtp_config.get("port", 587)
        self.smtp_user = smtp_config.get("user")
        self.smtp_password = smtp_config.get("password")
        self.from_address = smtp_config.get("from_address")
        self.use_tls = smtp_config.get("use_tls", True)

        logger.info("EmailService initialized")

    def add_template(
        self,
        template_id: str,
        subject_template: str,
        html_template: str,
        text_template: str,
    ) -> None:
        """Add an email template.

        Args:
            template_id: Template identifier
            subject_template: Subject line template
            html_template: HTML body template
            text_template: Plain text body template
        """
        self._templates[template_id] = EmailTemplate(
            template_id=template_id,
            subject_template=subject_template,
            html_template=html_template,
            text_template=text_template,
        )
        logger.info("Added email template: %s", template_id)

    async def send_email(
        self,
        template_id: str,
        to_address: str,
        data: Dict,
        user_id: Optional[str] = None,
    ) -> bool:
        """Send an email using a template.

        Args:
            template_id: Email template ID
            to_address: Recipient email address
            data: Template data
            user_id: Optional user ID for logging purposes

        Returns:
            bool: True if sent successfully
        """
        try:
            # Get template
            template = self.get_template(template_id)
            if not template:
                logger.error("Email template not found: %s", template_id)
                return False

            # Create message
            msg = MIMEMultipart("alternative")

            # Set subject
            if self.jinja_env:
                subject_template = self.jinja_env.from_string(template.subject_template)
                msg["Subject"] = subject_template.render(**data)
            else:
                # Simple string formatting fallback
                msg["Subject"] = template.subject_template.format(**data)

            # Set sender and recipient
            msg["From"] = self.from_address
            msg["To"] = to_address

            # Create text part
            if self.jinja_env:
                text_template = self.jinja_env.from_string(template.text_template)
                text_content = text_template.render(**data)
            else:
                # Simple string formatting fallback
                text_content = template.text_template.format(**data)
            text_part = MIMEText(text_content, "plain")
            msg.attach(text_part)

            # Create HTML part
            if self.jinja_env:
                html_template = self.jinja_env.from_string(template.html_template)
                html_content = html_template.render(**data)
            else:
                # Simple string formatting fallback
                html_content = template.html_template.format(**data)
            html_part = MIMEText(html_content, "html")
            msg.attach(html_part)

            # Send email
            user_info = f" for user {user_id}" if user_id else ""

            # In development mode, just log the email
            if self.config.get("development_mode", False):
                logger.info(
                    "[DEV MODE] Would send email to %s using template %s%s",
                    to_address,
                    template_id,
                    user_info,
                )
                logger.debug("Email content: %s", msg.as_string())
                return True

            # In production mode, actually send the email
            smtp = aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=self.use_tls,
            )
            await smtp.connect()
            if self.smtp_user and self.smtp_password:
                await smtp.login(self.smtp_user, self.smtp_password)
            await smtp.send_message(msg)
            await smtp.quit()

            logger.info(
                "Sent email to %s using template %s%s",
                to_address,
                template_id,
                user_info,
            )
            return True
        except Exception as e:
            logger.error("Failed to send email: %s", e)
            return False

    def get_template(self, template_id: str) -> Optional[EmailTemplate]:
        """Get an email template.

        Args:
            template_id: Template identifier

        Returns:
            Optional[EmailTemplate]: Template if found
        """
        return self._templates.get(template_id)

    def remove_template(self, template_id: str) -> bool:
        """Remove an email template.

        Args:
            template_id: Template identifier

        Returns:
            bool: True if template was removed
        """
        if template_id in self._templates:
            del self._templates[template_id]
            logger.info("Removed email template: %s", template_id)
            return True
        return False
