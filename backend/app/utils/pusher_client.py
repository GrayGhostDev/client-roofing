"""
iSwitch Roofs CRM - Pusher Real-time Client
Version: 1.0.0
Date: 2025-10-01
"""

import pusher
from flask import current_app, g
from typing import Dict, Any, Optional
import logging
import json

logger = logging.getLogger(__name__)


_pusher_client = None


def get_pusher_client() -> Optional[pusher.Pusher]:
    """
    Get Pusher client instance (singleton).

    Returns:
        pusher.Pusher: Pusher client instance or None if not configured

    Raises:
        ValueError: If Pusher credentials are incomplete
    """
    global _pusher_client

    if _pusher_client is None:
        try:
            app_id = current_app.config.get("PUSHER_APP_ID")
            key = current_app.config.get("PUSHER_KEY")
            secret = current_app.config.get("PUSHER_SECRET")
            cluster = current_app.config.get("PUSHER_CLUSTER", "us2")

            # Return None if Pusher is not configured (optional feature)
            if not all([app_id, key, secret]):
                logger.warning("Pusher credentials not configured. Real-time features disabled.")
                return None

            _pusher_client = pusher.Pusher(
                app_id=app_id,
                key=key,
                secret=secret,
                cluster=cluster,
                ssl=True,
            )
            logger.debug("Created new Pusher client instance")
        except RuntimeError:
            # If outside application context, return None
            logger.debug("Outside Flask application context, Pusher client not available")
            return None
        except Exception as e:
            logger.error(f"Error creating Pusher client: {str(e)}")
            return None

    return _pusher_client


class PusherService:
    """
    Service class for Pusher real-time operations.
    Provides high-level interface for broadcasting events.
    """

    # Channel naming conventions
    CHANNEL_GLOBAL = "global"
    CHANNEL_LEADS = "leads"
    CHANNEL_CUSTOMERS = "customers"
    CHANNEL_PROJECTS = "projects"
    CHANNEL_TEAM = "team"
    CHANNEL_ANALYTICS = "analytics"

    # Event types
    EVENT_LEAD_CREATED = "lead:created"
    EVENT_LEAD_UPDATED = "lead:updated"
    EVENT_LEAD_ASSIGNED = "lead:assigned"
    EVENT_LEAD_CONVERTED = "lead:converted"

    EVENT_CUSTOMER_CREATED = "customer:created"
    EVENT_CUSTOMER_UPDATED = "customer:updated"

    EVENT_PROJECT_CREATED = "project:created"
    EVENT_PROJECT_UPDATED = "project:updated"
    EVENT_PROJECT_STATUS_CHANGED = "project:status_changed"

    EVENT_INTERACTION_CREATED = "interaction:created"
    EVENT_APPOINTMENT_CREATED = "appointment:created"
    EVENT_APPOINTMENT_REMINDER = "appointment:reminder"

    EVENT_NOTIFICATION = "notification"
    EVENT_ALERT = "alert"
    EVENT_METRICS_UPDATED = "metrics:updated"

    def __init__(self):
        """Initialize Pusher service."""
        self.client = get_pusher_client()

    def is_available(self) -> bool:
        """Check if Pusher is configured and available."""
        return self.client is not None

    def trigger(
        self,
        channel: str,
        event: str,
        data: Dict[str, Any],
        socket_id: Optional[str] = None,
    ) -> bool:
        """
        Trigger an event on a channel.

        Args:
            channel (str): Channel name
            event (str): Event name
            data (dict): Event data
            socket_id (str, optional): Socket ID to exclude from receiving the event

        Returns:
            bool: True if event was triggered successfully
        """
        if not self.is_available():
            logger.debug(f"Pusher not available. Skipping event: {event}")
            return False

        try:
            self.client.trigger(channel, event, data, socket_id)
            logger.info(f"Triggered event '{event}' on channel '{channel}'")
            return True
        except Exception as e:
            logger.error(f"Error triggering Pusher event: {str(e)}")
            return False

    def trigger_batch(
        self, batch: list[Dict[str, Any]], socket_id: Optional[str] = None
    ) -> bool:
        """
        Trigger multiple events in a single API call.

        Args:
            batch (list): List of events with 'channel', 'name', and 'data' keys
            socket_id (str, optional): Socket ID to exclude

        Returns:
            bool: True if batch was triggered successfully
        """
        if not self.is_available():
            logger.debug("Pusher not available. Skipping batch events")
            return False

        try:
            self.client.trigger_batch(batch, socket_id)
            logger.info(f"Triggered batch of {len(batch)} events")
            return True
        except Exception as e:
            logger.error(f"Error triggering Pusher batch: {str(e)}")
            return False

    # Lead Events
    def broadcast_lead_created(self, lead_data: Dict[str, Any]) -> bool:
        """Broadcast that a new lead was created."""
        return self.trigger(
            self.CHANNEL_LEADS,
            self.EVENT_LEAD_CREATED,
            {
                "lead_id": lead_data.get("id"),
                "source": lead_data.get("source"),
                "name": f"{lead_data.get('first_name')} {lead_data.get('last_name')}",
                "temperature": lead_data.get("temperature"),
                "score": lead_data.get("lead_score"),
                "assigned_to": lead_data.get("assigned_to"),
                "timestamp": lead_data.get("created_at"),
            },
        )

    def broadcast_lead_updated(self, lead_id: str, updates: Dict[str, Any]) -> bool:
        """Broadcast that a lead was updated."""
        return self.trigger(
            self.CHANNEL_LEADS,
            self.EVENT_LEAD_UPDATED,
            {"lead_id": lead_id, "updates": updates, "timestamp": updates.get("updated_at")},
        )

    def broadcast_lead_assigned(
        self, lead_id: str, assigned_to: str, assigned_by: str
    ) -> bool:
        """Broadcast that a lead was assigned to a team member."""
        return self.trigger(
            self.CHANNEL_LEADS,
            self.EVENT_LEAD_ASSIGNED,
            {
                "lead_id": lead_id,
                "assigned_to": assigned_to,
                "assigned_by": assigned_by,
            },
        )

    def broadcast_lead_converted(self, lead_id: str, customer_id: str) -> bool:
        """Broadcast that a lead was converted to a customer."""
        batch = [
            {
                "channel": self.CHANNEL_LEADS,
                "name": self.EVENT_LEAD_CONVERTED,
                "data": {"lead_id": lead_id, "customer_id": customer_id},
            },
            {
                "channel": self.CHANNEL_CUSTOMERS,
                "name": self.EVENT_CUSTOMER_CREATED,
                "data": {"customer_id": customer_id, "from_lead": lead_id},
            },
        ]
        return self.trigger_batch(batch)

    # Project Events
    def broadcast_project_created(self, project_data: Dict[str, Any]) -> bool:
        """Broadcast that a new project was created."""
        return self.trigger(
            self.CHANNEL_PROJECTS,
            self.EVENT_PROJECT_CREATED,
            {
                "project_id": project_data.get("id"),
                "customer_id": project_data.get("customer_id"),
                "project_type": project_data.get("project_type"),
                "quoted_amount": project_data.get("quoted_amount"),
            },
        )

    def broadcast_project_status_changed(
        self, project_id: str, old_status: str, new_status: str
    ) -> bool:
        """Broadcast that a project status changed."""
        return self.trigger(
            self.CHANNEL_PROJECTS,
            self.EVENT_PROJECT_STATUS_CHANGED,
            {
                "project_id": project_id,
                "old_status": old_status,
                "new_status": new_status,
            },
        )

    # Notification Events
    def send_notification(
        self, user_id: str, title: str, message: str, notification_type: str = "info"
    ) -> bool:
        """
        Send a notification to a specific user.

        Args:
            user_id (str): User ID to send notification to
            title (str): Notification title
            message (str): Notification message
            notification_type (str): Type (info, success, warning, error)

        Returns:
            bool: True if notification was sent
        """
        channel = f"private-user-{user_id}"
        return self.trigger(
            channel,
            self.EVENT_NOTIFICATION,
            {
                "title": title,
                "message": message,
                "type": notification_type,
            },
        )

    def send_global_notification(
        self, title: str, message: str, notification_type: str = "info"
    ) -> bool:
        """Send a notification to all connected users."""
        return self.trigger(
            self.CHANNEL_GLOBAL,
            self.EVENT_NOTIFICATION,
            {
                "title": title,
                "message": message,
                "type": notification_type,
            },
        )

    # Analytics Events
    def broadcast_metrics_update(self, metrics: Dict[str, Any]) -> bool:
        """Broadcast updated metrics to dashboard."""
        return self.trigger(self.CHANNEL_ANALYTICS, self.EVENT_METRICS_UPDATED, metrics)

    # Interaction Events
    def broadcast_interaction_created(
        self, interaction_data: Dict[str, Any]
    ) -> bool:
        """Broadcast that a new interaction was logged."""
        return self.trigger(
            self.CHANNEL_GLOBAL,
            self.EVENT_INTERACTION_CREATED,
            {
                "interaction_id": interaction_data.get("id"),
                "interaction_type": interaction_data.get("interaction_type"),
                "lead_id": interaction_data.get("lead_id"),
                "customer_id": interaction_data.get("customer_id"),
                "team_member_id": interaction_data.get("team_member_id"),
            },
        )

    # Appointment Events
    def broadcast_appointment_created(
        self, appointment_data: Dict[str, Any]
    ) -> bool:
        """Broadcast that a new appointment was created."""
        return self.trigger(
            self.CHANNEL_TEAM,
            self.EVENT_APPOINTMENT_CREATED,
            {
                "appointment_id": appointment_data.get("id"),
                "assigned_to": appointment_data.get("assigned_to"),
                "scheduled_datetime": appointment_data.get("scheduled_datetime"),
                "appointment_type": appointment_data.get("appointment_type"),
            },
        )

    def send_appointment_reminder(
        self, user_id: str, appointment_data: Dict[str, Any]
    ) -> bool:
        """Send appointment reminder to a specific user."""
        channel = f"private-user-{user_id}"
        return self.trigger(
            channel,
            self.EVENT_APPOINTMENT_REMINDER,
            {
                "appointment_id": appointment_data.get("id"),
                "scheduled_datetime": appointment_data.get("scheduled_datetime"),
                "location": appointment_data.get("location_address"),
                "lead_name": appointment_data.get("lead_name"),
            },
        )

    def authenticate_channel(self, socket_id: str, channel_name: str, user_id: str) -> Dict:
        """
        Authenticate a user for a private or presence channel.

        Args:
            socket_id (str): Socket ID from client
            channel_name (str): Channel name to authenticate for
            user_id (str): User ID requesting authentication

        Returns:
            dict: Authentication data to return to client
        """
        if not self.is_available():
            return {"error": "Pusher not configured"}

        try:
            # For presence channels, include user info
            if channel_name.startswith("presence-"):
                user_data = {"user_id": user_id}
                auth = self.client.authenticate(channel_name, socket_id, user_data)
            else:
                # For private channels
                auth = self.client.authenticate(channel_name, socket_id)

            return auth
        except Exception as e:
            logger.error(f"Error authenticating Pusher channel: {str(e)}")
            return {"error": str(e)}


# Helper function to get service instance
def get_pusher_service() -> PusherService:
    """Get PusherService instance."""
    return PusherService()
