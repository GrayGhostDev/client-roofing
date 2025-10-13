"""
Notification Service
Version: 1.0.0

Main notification service that orchestrates email, SMS, and real-time notifications.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any

from app.config import get_supabase_client
from app.models.notification_schemas import (
    NotificationChannel,
    NotificationPreferences,
    NotificationStatus,
    NotificationType,
)
from app.services.email_service import email_service
from app.services.realtime_service import realtime_service
from app.services.sms_service import sms_service
from app.utils.notification_templates import notification_templates

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Main notification service for orchestrating all notification channels.
    """

    def __init__(self):
        """Initialize Notification Service."""
        self.email_service = email_service
        self.sms_service = sms_service
        self.realtime_service = realtime_service
        self.templates = notification_templates

        # Get Supabase client for database operations
        try:
            self.supabase = get_supabase_client()
        except:
            logger.warning("Supabase client not configured")
            self.supabase = None

        # Retry configuration
        self.max_retries = 3
        self.retry_delays = [60, 300, 900]  # 1 min, 5 min, 15 min

        # Rate limiting
        self.rate_limits = {
            "email": {"per_minute": 100, "per_hour": 1000},
            "sms": {"per_minute": 10, "per_hour": 100},
        }

    def send_notification(
        self,
        type: str | NotificationType,
        data: dict[str, Any],
        recipient_id: str | None = None,
        channels: list[str] | None = None,
        priority: str = "normal",
    ) -> dict[str, Any]:
        """
        Send a notification through specified channels.

        Args:
            type: Notification type
            data: Notification data and template variables
            recipient_id: Recipient user ID
            channels: Channels to use (defaults to user preferences)
            priority: Notification priority

        Returns:
            Dictionary with send results
        """
        results = {"success": False, "channels": {}, "notification_id": None}

        try:
            # Get recipient information
            recipient = self._get_recipient_info(recipient_id, data)
            if not recipient:
                logger.error(f"Recipient not found: {recipient_id}")
                return results

            # Get user preferences
            preferences = self._get_user_preferences(recipient_id)

            # Determine channels to use
            if not channels:
                channels = self._determine_channels(type, preferences, priority)

            # Check quiet hours
            if self._is_quiet_hours(preferences):
                if priority not in ["urgent", "high"]:
                    logger.info(f"Delaying notification due to quiet hours for user {recipient_id}")
                    # Schedule for end of quiet hours
                    return self._schedule_notification(type, data, recipient_id, channels, priority)

            # Save notification to database
            notification = self._save_notification(
                type=type, channels=channels, recipient=recipient, data=data, priority=priority
            )

            if notification:
                results["notification_id"] = notification.get("id")

            # Send through each channel
            for channel in channels:
                channel_result = self._send_channel_notification(
                    channel=channel,
                    type=type,
                    recipient=recipient,
                    data=data,
                    notification_id=results["notification_id"],
                )
                results["channels"][channel] = channel_result

            # Update overall success
            results["success"] = any(r.get("success") for r in results["channels"].values())

            # Update notification status
            if notification:
                status = (
                    NotificationStatus.SENT if results["success"] else NotificationStatus.FAILED
                )
                self._update_notification_status(notification["id"], status)

        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
            results["error"] = str(e)

        return results

    def _send_channel_notification(
        self,
        channel: str,
        type: str | NotificationType,
        recipient: dict[str, Any],
        data: dict[str, Any],
        notification_id: str | None = None,
    ) -> dict[str, Any]:
        """Send notification through specific channel."""
        result = {"success": False}

        try:
            if channel == NotificationChannel.EMAIL.value:
                result = self._send_email_notification(type, recipient, data, notification_id)

            elif channel == NotificationChannel.SMS.value:
                result = self._send_sms_notification(type, recipient, data, notification_id)

            elif channel == NotificationChannel.IN_APP.value:
                result = self._send_realtime_notification(type, recipient, data, notification_id)

            elif channel == NotificationChannel.PUSH.value:
                # Push notifications would be implemented here
                logger.info("Push notifications not yet implemented")
                result = {"success": False, "error": "Not implemented"}

        except Exception as e:
            logger.error(f"Failed to send {channel} notification: {str(e)}")
            result = {"success": False, "error": str(e)}

        return result

    def _send_email_notification(
        self,
        type: str | NotificationType,
        recipient: dict[str, Any],
        data: dict[str, Any],
        notification_id: str | None = None,
    ) -> dict[str, Any]:
        """Send email notification."""
        # Convert enum to string if needed
        type_str = type.value if hasattr(type, "value") else str(type)

        # Render template
        html_content = self.templates.render_template("email", type_str, data, "html")
        plain_content = self.templates.render_template("email", type_str, data, "plain")
        subject = self.templates.get_email_subject(type_str, data)

        if not all([html_content, subject]):
            logger.error(f"Failed to render email template for {type_str}")
            return {"success": False, "error": "Template rendering failed"}

        # Add tracking
        custom_args = {}
        if notification_id:
            custom_args["notification_id"] = str(notification_id)
        custom_args["notification_type"] = type_str

        # Send email
        success, message_id, response = self.email_service.send_email(
            to_email=recipient.get("email"),
            subject=subject,
            html_content=html_content,
            plain_content=plain_content,
            custom_args=custom_args,
            categories=[type_str, "crm_notification"],
        )

        return {"success": success, "message_id": message_id, "response": response}

    def _send_sms_notification(
        self,
        type: str | NotificationType,
        recipient: dict[str, Any],
        data: dict[str, Any],
        notification_id: str | None = None,
    ) -> dict[str, Any]:
        """Send SMS notification."""
        # Convert enum to string if needed
        type_str = type.value if hasattr(type, "value") else str(type)

        # Map notification type to SMS template
        sms_template_map = {
            "lead_created": "lead_hot_alert" if data.get("temperature") == "hot" else None,
            "lead_hot": "lead_hot_alert",
            "lead_assigned": "lead_assigned",
            "appointment_reminder": "appointment_reminder_1day",
            "appointment_scheduled": "appointment_confirmation",
            "project_started": "project_started",
            "project_completed": "project_completed",
            "review_request": "review_request",
        }

        template_name = sms_template_map.get(type_str)
        if not template_name:
            logger.debug(f"No SMS template for notification type {type_str}")
            return {"success": False, "error": "No SMS template"}

        # Render message
        message = self.templates.render_template("sms", template_name, data)
        if not message:
            return {"success": False, "error": "Template rendering failed"}

        # Send SMS
        success, message_sid, response = self.sms_service.send_sms(
            to_phone=recipient.get("phone"), message=message
        )

        return {"success": success, "message_sid": message_sid, "response": response}

    def _send_realtime_notification(
        self,
        type: str | NotificationType,
        recipient: dict[str, Any],
        data: dict[str, Any],
        notification_id: str | None = None,
    ) -> dict[str, Any]:
        """Send real-time in-app notification."""
        # Convert enum to string if needed
        type_str = type.value if hasattr(type, "value") else str(type)

        # Format notification for real-time delivery
        notification_data = {
            "id": str(notification_id) if notification_id else None,
            "type": type_str,
            "title": data.get("title", f"New {type_str.replace('_', ' ').title()}"),
            "message": data.get("message", ""),
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Send to user's private channel
        success = self.realtime_service.trigger_event(
            channel=f"private-user-{recipient.get('id')}",
            event="notification",
            data=notification_data,
        )

        return {"success": success}

    def send_bulk_notifications(
        self,
        type: str | NotificationType,
        recipients: list[dict[str, Any]],
        template_data: dict[str, Any],
        channels: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Send notifications to multiple recipients.

        Args:
            type: Notification type
            recipients: List of recipient dictionaries
            template_data: Base template data
            channels: Channels to use

        Returns:
            Dictionary with bulk send results
        """
        results = {"total": len(recipients), "sent": 0, "failed": 0, "errors": []}

        for recipient in recipients:
            try:
                # Merge recipient data with template data
                data = {**template_data}
                data.update(recipient)

                # Send notification
                result = self.send_notification(
                    type=type, data=data, recipient_id=recipient.get("id"), channels=channels
                )

                if result["success"]:
                    results["sent"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(
                        {
                            "recipient": recipient.get("email") or recipient.get("phone"),
                            "error": result.get("error", "Unknown error"),
                        }
                    )

            except Exception as e:
                results["failed"] += 1
                results["errors"].append(
                    {"recipient": recipient.get("email") or recipient.get("phone"), "error": str(e)}
                )

        return results

    def _get_recipient_info(
        self, recipient_id: str | None, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Get recipient information from ID or data."""
        recipient = {}

        # Try to get from database if ID provided
        if recipient_id and self.supabase:
            try:
                result = (
                    self.supabase.from_("users")
                    .select("*")
                    .eq("id", recipient_id)
                    .single()
                    .execute()
                )
                if result.data:
                    recipient = result.data
            except:
                pass

        # Override with provided data
        recipient.update(
            {
                "id": recipient_id or data.get("recipient_id"),
                "email": data.get("email") or data.get("recipient_email") or recipient.get("email"),
                "phone": data.get("phone") or data.get("recipient_phone") or recipient.get("phone"),
                "first_name": data.get("first_name") or recipient.get("first_name"),
                "last_name": data.get("last_name") or recipient.get("last_name"),
            }
        )

        # Must have at least email or phone
        if not (recipient.get("email") or recipient.get("phone")):
            return None

        return recipient

    def _get_user_preferences(self, user_id: str | None) -> NotificationPreferences | None:
        """Get user notification preferences."""
        if not user_id or not self.supabase:
            return None

        try:
            result = (
                self.supabase.from_("notification_preferences")
                .select("*")
                .eq("user_id", user_id)
                .single()
                .execute()
            )

            if result.data:
                return NotificationPreferences(**result.data)

        except:
            pass

        return None

    def _determine_channels(
        self,
        type: str | NotificationType,
        preferences: NotificationPreferences | None,
        priority: str,
    ) -> list[str]:
        """Determine which channels to use for notification."""
        channels = []

        # Convert enum to string if needed
        type_str = type.value if hasattr(type, "value") else str(type)
        type_enum = NotificationType(type_str) if isinstance(type_str, str) else type

        # Default channels if no preferences
        if not preferences:
            channels = [NotificationChannel.EMAIL.value]
            if priority in ["urgent", "high"]:
                channels.append(NotificationChannel.SMS.value)
            channels.append(NotificationChannel.IN_APP.value)
            return channels

        # Check if type is enabled
        if type_enum in preferences.disabled_types:
            return []

        # Add channels based on preferences
        if preferences.email_enabled:
            channels.append(NotificationChannel.EMAIL.value)

        if preferences.sms_enabled and priority in ["urgent", "high"]:
            channels.append(NotificationChannel.SMS.value)

        if preferences.in_app_enabled:
            channels.append(NotificationChannel.IN_APP.value)

        return channels

    def _is_quiet_hours(self, preferences: NotificationPreferences | None) -> bool:
        """Check if current time is within user's quiet hours."""
        if not preferences or not preferences.quiet_hours_enabled:
            return False

        try:
            from datetime import datetime

            import pytz

            # Get user's current time
            tz = pytz.timezone(preferences.timezone)
            user_time = datetime.now(tz)
            current_hour = user_time.hour
            current_minute = user_time.minute

            # Parse quiet hours
            start_parts = preferences.quiet_hours_start.split(":")
            start_hour = int(start_parts[0])
            start_minute = int(start_parts[1])

            end_parts = preferences.quiet_hours_end.split(":")
            end_hour = int(end_parts[0])
            end_minute = int(end_parts[1])

            # Convert to minutes for easier comparison
            current_minutes = current_hour * 60 + current_minute
            start_minutes = start_hour * 60 + start_minute
            end_minutes = end_hour * 60 + end_minute

            # Check if in quiet hours
            if start_minutes <= end_minutes:
                # Normal case (e.g., 22:00 - 08:00 doesn't cross midnight)
                return start_minutes <= current_minutes <= end_minutes
            else:
                # Crosses midnight (e.g., 22:00 - 08:00)
                return current_minutes >= start_minutes or current_minutes <= end_minutes

        except Exception as e:
            logger.error(f"Failed to check quiet hours: {str(e)}")
            return False

    def _schedule_notification(
        self,
        type: str | NotificationType,
        data: dict[str, Any],
        recipient_id: str | None,
        channels: list[str],
        priority: str,
        send_at: datetime | None = None,
    ) -> dict[str, Any]:
        """Schedule a notification for later delivery."""
        # This would integrate with a job queue (Celery, RQ, etc.)
        # For now, we'll save it to database for processing
        if not self.supabase:
            return {"success": False, "error": "Cannot schedule without database"}

        if not send_at:
            # Default to 1 hour from now
            send_at = datetime.utcnow() + timedelta(hours=1)

        type_str = type.value if hasattr(type, "value") else str(type)

        scheduled_notification = {
            "type": type_str,
            "channels": channels,
            "recipient_id": recipient_id,
            "data": json.dumps(data),
            "priority": priority,
            "scheduled_for": send_at.isoformat(),
            "status": NotificationStatus.PENDING.value,
            "created_at": datetime.utcnow().isoformat(),
        }

        result = (
            self.supabase.from_("scheduled_notifications").insert(scheduled_notification).execute()
        )

        if result.data:
            return {"success": True, "scheduled_id": result.data[0]["id"]}

        return {"success": False}

    def _save_notification(
        self,
        type: str | NotificationType,
        channels: list[str],
        recipient: dict[str, Any],
        data: dict[str, Any],
        priority: str,
    ) -> dict | None:
        """Save notification to database."""
        if not self.supabase:
            return None

        try:
            type_str = type.value if hasattr(type, "value") else str(type)

            notification_data = {
                "type": type_str,
                "channel": channels[0] if channels else NotificationChannel.EMAIL.value,
                "priority": priority,
                "recipient_id": recipient.get("id"),
                "recipient_email": recipient.get("email"),
                "recipient_phone": recipient.get("phone"),
                "recipient_name": f"{recipient.get('first_name', '')} {recipient.get('last_name', '')}".strip(),
                "subject": data.get("subject"),
                "content": json.dumps(data),
                "status": NotificationStatus.PENDING.value,
                "created_at": datetime.utcnow().isoformat(),
            }

            result = self.supabase.from_("notifications").insert(notification_data).execute()

            if result.data:
                return result.data[0]

        except Exception as e:
            logger.error(f"Failed to save notification: {str(e)}")

        return None

    def _update_notification_status(
        self,
        notification_id: str,
        status: NotificationStatus,
        additional_data: dict | None = None,
    ):
        """Update notification status in database."""
        if not self.supabase:
            return

        try:
            update_data = {"status": status.value, "updated_at": datetime.utcnow().isoformat()}

            if status == NotificationStatus.SENT:
                update_data["sent_at"] = datetime.utcnow().isoformat()
            elif status == NotificationStatus.DELIVERED:
                update_data["delivered_at"] = datetime.utcnow().isoformat()
            elif status == NotificationStatus.OPENED:
                update_data["opened_at"] = datetime.utcnow().isoformat()
            elif status == NotificationStatus.CLICKED:
                update_data["clicked_at"] = datetime.utcnow().isoformat()

            if additional_data:
                update_data.update(additional_data)

            self.supabase.from_("notifications").update(update_data).eq(
                "id", notification_id
            ).execute()

        except Exception as e:
            logger.error(f"Failed to update notification status: {str(e)}")

    def retry_failed_notification(self, notification_id: str) -> bool:
        """Retry a failed notification."""
        if not self.supabase:
            return False

        try:
            # Get notification
            result = (
                self.supabase.from_("notifications")
                .select("*")
                .eq("id", notification_id)
                .single()
                .execute()
            )

            if not result.data:
                return False

            notification = result.data

            # Check retry count
            retry_count = notification.get("retry_count", 0)
            if retry_count >= self.max_retries:
                logger.info(f"Max retries exceeded for notification {notification_id}")
                return False

            # Parse data
            data = json.loads(notification.get("content", "{}"))

            # Resend
            result = self.send_notification(
                type=notification["type"], data=data, recipient_id=notification.get("recipient_id")
            )

            # Update retry count
            self.supabase.from_("notifications").update(
                {
                    "retry_count": retry_count + 1,
                    "next_retry_at": (
                        datetime.utcnow() + timedelta(seconds=self.retry_delays[retry_count])
                    ).isoformat(),
                }
            ).eq("id", notification_id).execute()

            return result["success"]

        except Exception as e:
            logger.error(f"Failed to retry notification: {str(e)}")
            return False

    def process_scheduled_notifications(self):
        """Process scheduled notifications that are due."""
        if not self.supabase:
            return

        try:
            # Get due notifications
            result = (
                self.supabase.from_("scheduled_notifications")
                .select("*")
                .lte("scheduled_for", datetime.utcnow().isoformat())
                .eq("status", NotificationStatus.PENDING.value)
                .execute()
            )

            if not result.data:
                return

            for scheduled in result.data:
                try:
                    # Parse data
                    data = json.loads(scheduled.get("data", "{}"))
                    channels = scheduled.get("channels", [])

                    # Send notification
                    result = self.send_notification(
                        type=scheduled["type"],
                        data=data,
                        recipient_id=scheduled.get("recipient_id"),
                        channels=channels,
                        priority=scheduled.get("priority", "normal"),
                    )

                    # Update status
                    status = (
                        NotificationStatus.SENT if result["success"] else NotificationStatus.FAILED
                    )
                    self.supabase.from_("scheduled_notifications").update(
                        {"status": status.value, "processed_at": datetime.utcnow().isoformat()}
                    ).eq("id", scheduled["id"]).execute()

                except Exception as e:
                    logger.error(
                        f"Failed to process scheduled notification {scheduled['id']}: {str(e)}"
                    )

        except Exception as e:
            logger.error(f"Failed to process scheduled notifications: {str(e)}")


# Singleton instance
notification_service = NotificationService()
