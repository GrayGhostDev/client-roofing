"""
Email Service using SendGrid
Version: 1.0.0

Handles email delivery through SendGrid API with templates, tracking, and analytics.
"""

import os
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import json

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Email, To, Content, Attachment, FileContent, FileName,
    FileType, Disposition, ContentId, Personalization,
    TrackingSettings, ClickTracking, OpenTracking, SubscriptionTracking,
    Ganalytics, MailSettings, SandBoxMode
)
from python_http_client.exceptions import HTTPError

from app.models.notification import NotificationStatus, NotificationPriority
from app.config import Config


logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SendGrid."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Email Service.

        Args:
            api_key: SendGrid API key (defaults to environment variable)
        """
        self.api_key = api_key or os.environ.get('SENDGRID_API_KEY')
        if not self.api_key:
            logger.warning("SendGrid API key not configured")
            self.client = None
        else:
            self.client = SendGridAPIClient(self.api_key)

        # Default settings
        self.from_email = os.environ.get('FROM_EMAIL', 'noreply@iswitchroofs.com')
        self.from_name = os.environ.get('COMPANY_NAME', 'iSwitch Roofs')
        self.sandbox_mode = os.environ.get('SENDGRID_SANDBOX_MODE', 'false').lower() == 'true'

    def send_email(self,
                   to_email: str,
                   subject: str,
                   html_content: str,
                   plain_content: Optional[str] = None,
                   from_email: Optional[str] = None,
                   from_name: Optional[str] = None,
                   reply_to: Optional[str] = None,
                   cc_emails: Optional[List[str]] = None,
                   bcc_emails: Optional[List[str]] = None,
                   attachments: Optional[List[Dict[str, Any]]] = None,
                   custom_args: Optional[Dict[str, str]] = None,
                   send_at: Optional[int] = None,
                   categories: Optional[List[str]] = None,
                   enable_tracking: bool = True) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Send an email via SendGrid.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content
            plain_content: Plain text content (auto-generated if not provided)
            from_email: Sender email (defaults to configured)
            from_name: Sender name
            reply_to: Reply-to email address
            cc_emails: CC recipients
            bcc_emails: BCC recipients
            attachments: List of attachment dictionaries
            custom_args: Custom arguments for tracking
            send_at: Unix timestamp to send at (scheduling)
            categories: Email categories for analytics
            enable_tracking: Enable open/click tracking

        Returns:
            Tuple of (success, message_id, response_data)
        """
        if not self.client:
            logger.error("SendGrid client not initialized")
            return False, None, {"error": "Email service not configured"}

        try:
            # Create message
            message = Mail()

            # Set from
            message.from_email = Email(
                from_email or self.from_email,
                from_name or self.from_name
            )

            # Set to
            message.add_to(To(to_email))

            # Set subject and content
            message.subject = subject
            message.add_content(Content("text/html", html_content))

            if plain_content:
                message.add_content(Content("text/plain", plain_content))

            # Add CC/BCC
            if cc_emails:
                for cc in cc_emails:
                    message.add_cc(cc)

            if bcc_emails:
                for bcc in bcc_emails:
                    message.add_bcc(bcc)

            # Set reply-to
            if reply_to:
                message.reply_to = reply_to

            # Add attachments
            if attachments:
                for att in attachments:
                    attachment = Attachment()
                    attachment.file_content = FileContent(att['content'])
                    attachment.file_name = FileName(att['filename'])
                    attachment.file_type = FileType(att.get('type', 'application/octet-stream'))
                    attachment.disposition = Disposition('attachment')

                    if 'content_id' in att:
                        attachment.content_id = ContentId(att['content_id'])

                    message.add_attachment(attachment)

            # Add custom args for tracking
            if custom_args:
                for key, value in custom_args.items():
                    message.add_custom_arg(key, value)

            # Set send time (scheduling)
            if send_at:
                message.send_at = send_at

            # Add categories
            if categories:
                for category in categories[:10]:  # Max 10 categories
                    message.add_category(category)

            # Tracking settings
            if enable_tracking:
                message.tracking_settings = TrackingSettings(
                    click_tracking=ClickTracking(enable=True),
                    open_tracking=OpenTracking(enable=True)
                )

            # Mail settings
            if self.sandbox_mode:
                message.mail_settings = MailSettings(
                    sandbox_mode=SandBoxMode(enable=True)
                )

            # Send email
            response = self.client.send(message)

            # Extract message ID from response
            message_id = None
            if hasattr(response, 'headers') and 'X-Message-Id' in response.headers:
                message_id = response.headers['X-Message-Id']

            logger.info(f"Email sent successfully to {to_email} (ID: {message_id})")
            return True, message_id, {
                "status_code": response.status_code,
                "message_id": message_id
            }

        except HTTPError as e:
            error_message = str(e)
            try:
                error_data = json.loads(e.body) if hasattr(e, 'body') else {}
            except:
                error_data = {}

            logger.error(f"SendGrid API error: {error_message}")
            return False, None, {
                "error": error_message,
                "details": error_data
            }

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False, None, {"error": str(e)}

    def send_template_email(self,
                           to_email: str,
                           template_id: str,
                           template_data: Optional[Dict[str, Any]] = None,
                           from_email: Optional[str] = None,
                           from_name: Optional[str] = None,
                           custom_args: Optional[Dict[str, str]] = None,
                           send_at: Optional[int] = None) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Send an email using a SendGrid dynamic template.

        Args:
            to_email: Recipient email address
            template_id: SendGrid template ID
            template_data: Dynamic template data
            from_email: Sender email
            from_name: Sender name
            custom_args: Custom arguments for tracking
            send_at: Unix timestamp to send at

        Returns:
            Tuple of (success, message_id, response_data)
        """
        if not self.client:
            return False, None, {"error": "Email service not configured"}

        try:
            message = Mail(
                from_email=Email(from_email or self.from_email, from_name or self.from_name),
                to_emails=to_email
            )

            # Set template ID and data
            message.template_id = template_id
            if template_data:
                message.dynamic_template_data = template_data

            # Add custom args
            if custom_args:
                for key, value in custom_args.items():
                    message.add_custom_arg(key, value)

            # Schedule send
            if send_at:
                message.send_at = send_at

            # Send email
            response = self.client.send(message)

            message_id = None
            if hasattr(response, 'headers') and 'X-Message-Id' in response.headers:
                message_id = response.headers['X-Message-Id']

            logger.info(f"Template email sent to {to_email} (Template: {template_id})")
            return True, message_id, {"status_code": response.status_code}

        except Exception as e:
            logger.error(f"Failed to send template email: {str(e)}")
            return False, None, {"error": str(e)}

    def send_bulk_emails(self,
                        recipients: List[Dict[str, Any]],
                        subject: str,
                        html_content: str,
                        plain_content: Optional[str] = None,
                        from_email: Optional[str] = None,
                        from_name: Optional[str] = None,
                        categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Send bulk emails to multiple recipients.

        Args:
            recipients: List of recipient dictionaries with email and optional personalization
            subject: Email subject
            html_content: HTML content (can include substitution tags)
            plain_content: Plain text content
            from_email: Sender email
            from_name: Sender name
            categories: Email categories

        Returns:
            Dictionary with send results
        """
        if not self.client:
            return {"success": False, "error": "Email service not configured"}

        results = {
            "total": len(recipients),
            "sent": 0,
            "failed": 0,
            "errors": []
        }

        try:
            message = Mail()

            # Set from
            message.from_email = Email(
                from_email or self.from_email,
                from_name or self.from_name
            )

            # Set subject
            message.subject = subject

            # Add content
            message.add_content(Content("text/html", html_content))
            if plain_content:
                message.add_content(Content("text/plain", plain_content))

            # Add personalizations for each recipient
            for recipient in recipients:
                personalization = Personalization()
                personalization.add_to(Email(recipient['email']))

                # Add substitutions if provided
                if 'substitutions' in recipient:
                    for key, value in recipient['substitutions'].items():
                        personalization.add_substitution(key, value)

                # Add custom args if provided
                if 'custom_args' in recipient:
                    for key, value in recipient['custom_args'].items():
                        personalization.add_custom_arg(key, value)

                message.add_personalization(personalization)

            # Add categories
            if categories:
                for category in categories[:10]:
                    message.add_category(category)

            # Send email
            response = self.client.send(message)

            if response.status_code in [200, 202]:
                results["sent"] = len(recipients)
                results["success"] = True
            else:
                results["failed"] = len(recipients)
                results["errors"].append(f"Status code: {response.status_code}")

        except Exception as e:
            logger.error(f"Bulk email send failed: {str(e)}")
            results["failed"] = len(recipients)
            results["errors"].append(str(e))
            results["success"] = False

        return results

    def validate_email(self, email: str) -> bool:
        """
        Validate email address format and deliverability.

        Args:
            email: Email address to validate

        Returns:
            True if valid, False otherwise
        """
        # Basic format validation
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(email_pattern, email):
            return False

        # Could add SendGrid email validation API here if configured
        # This would check deliverability, not just format

        return True

    def add_to_suppression_list(self, email: str, group_id: int) -> bool:
        """
        Add email to suppression group (unsubscribe list).

        Args:
            email: Email address to suppress
            group_id: Suppression group ID

        Returns:
            True if successful
        """
        if not self.client:
            return False

        try:
            data = {
                "recipient_emails": [email]
            }

            response = self.client.client.suppression.group(group_id).suppressions.post(
                request_body=data
            )

            return response.status_code in [200, 201]

        except Exception as e:
            logger.error(f"Failed to add to suppression list: {str(e)}")
            return False

    def remove_from_suppression_list(self, email: str, group_id: int) -> bool:
        """
        Remove email from suppression group.

        Args:
            email: Email address
            group_id: Suppression group ID

        Returns:
            True if successful
        """
        if not self.client:
            return False

        try:
            response = self.client.client.suppression.group(group_id).suppressions._(email).delete()
            return response.status_code in [200, 204]

        except Exception as e:
            logger.error(f"Failed to remove from suppression list: {str(e)}")
            return False

    def get_email_activity(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Get activity/status for a sent email.

        Args:
            message_id: SendGrid message ID

        Returns:
            Activity data or None
        """
        if not self.client:
            return None

        try:
            # Query email activity
            # Note: This requires Email Activity Feed to be enabled in SendGrid
            query_params = {
                "query": f"msg_id={message_id}",
                "limit": 1
            }

            response = self.client.client.messages.get(query_params=query_params)

            if response.status_code == 200:
                data = json.loads(response.body)
                if data.get('messages'):
                    return data['messages'][0]

            return None

        except Exception as e:
            logger.error(f"Failed to get email activity: {str(e)}")
            return None

    def schedule_email(self,
                      to_email: str,
                      subject: str,
                      html_content: str,
                      send_at: datetime,
                      **kwargs) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Schedule an email to be sent later.

        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML content
            send_at: Datetime to send the email
            **kwargs: Additional email parameters

        Returns:
            Tuple of (success, message_id, response_data)
        """
        # Convert datetime to unix timestamp
        send_at_timestamp = int(send_at.timestamp())

        return self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            send_at=send_at_timestamp,
            **kwargs
        )

    def cancel_scheduled_email(self, batch_id: str) -> bool:
        """
        Cancel a scheduled email batch.

        Args:
            batch_id: SendGrid batch ID

        Returns:
            True if successful
        """
        if not self.client:
            return False

        try:
            response = self.client.client.user.scheduled_sends.post(
                request_body={
                    "batch_id": batch_id,
                    "status": "cancel"
                }
            )

            return response.status_code in [200, 201]

        except Exception as e:
            logger.error(f"Failed to cancel scheduled email: {str(e)}")
            return False


# Singleton instance
email_service = EmailService()