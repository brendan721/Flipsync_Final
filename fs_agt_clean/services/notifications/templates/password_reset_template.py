"""
Password reset email template.

This module provides email templates for password reset.
"""

from datetime import datetime
from typing import Any, Dict

from fs_agt.services.notifications.templates.base_template import BaseTemplate


class PasswordResetTemplate(BaseTemplate):
    """Password reset email template."""

    def __init__(self):
        """Initialize the template."""
        super().__init__(
            template_id="password_reset",
            category="auth",
            subject="FlipSync Password Reset",
        )

    def get_email_content(self, data: Dict[str, Any]) -> str:
        """Get email content.

        Args:
            data: Template data including:
                - username: UnifiedUser's name or username
                - reset_link: Password reset link
                - expiry_hours: Hours until the reset link expires

        Returns:
            str: HTML email content
        """
        username = data.get("username", "UnifiedUser")
        reset_link = data.get("reset_link", "#")
        expiry_hours = data.get("expiry_hours", 24)

        return f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #4a86e8;
                    color: white;
                    padding: 10px 20px;
                    text-align: center;
                }}
                .content {{
                    padding: 20px;
                    background-color: #f9f9f9;
                }}
                .button {{
                    display: inline-block;
                    background-color: #4a86e8;
                    color: white;
                    padding: 10px 20px;
                    text-decoration: none;
                    border-radius: 4px;
                    margin: 20px 0;
                }}
                .footer {{
                    font-size: 12px;
                    color: #777;
                    text-align: center;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>FlipSync Password Reset</h1>
                </div>
                <div class="content">
                    <p>Hello {username},</p>
                    <p>We received a request to reset your password for your FlipSync account. If you didn't make this request, you can safely ignore this email.</p>
                    <p>To reset your password, click the button below:</p>
                    <p style="text-align: center;">
                        <a href="{reset_link}" class="button">Reset Password</a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p>{reset_link}</p>
                    <p>This link will expire in {expiry_hours} hours.</p>
                    <p>If you have any questions, please contact our support team.</p>
                </div>
                <div class="footer">
                    <p>&copy; {datetime.now().year} FlipSync. All rights reserved.</p>
                    <p>This is an automated message, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """

    def get_text_content(self, data: Dict[str, Any]) -> str:
        """Get plain text email content.

        Args:
            data: Template data including:
                - username: UnifiedUser's name or username
                - reset_link: Password reset link
                - expiry_hours: Hours until the reset link expires

        Returns:
            str: Plain text email content
        """
        username = data.get("username", "UnifiedUser")
        reset_link = data.get("reset_link", "#")
        expiry_hours = data.get("expiry_hours", 24)

        return f"""
        FlipSync Password Reset

        Hello {username},

        We received a request to reset your password for your FlipSync account. If you didn't make this request, you can safely ignore this email.

        To reset your password, click the link below:

        {reset_link}

        This link will expire in {expiry_hours} hours.

        If you have any questions, please contact our support team.

        © {datetime.now().year} FlipSync. All rights reserved.
        This is an automated message, please do not reply.
        """
